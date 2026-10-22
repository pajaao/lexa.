"""Caput-first disclosure, preserved content, keyboard and before/after captures."""
from pathlib import Path
import functools
import http.server
import json
import subprocess
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect
from support import chromium_executable

ROOT=Path(__file__).resolve().parents[2]
candidate='--candidate' in sys.argv
OUT=ROOT/('test-results/previous-wordings-release/browser' if candidate else 'test-results/previous-wordings-ux')
OUT.mkdir(parents=True,exist_ok=True)
before='--before' in sys.argv
rows=json.loads((ROOT/('data/previous-wordings/candidate.json' if candidate else 'tests/fixtures/previous-wordings-simple.json')).read_text(encoding='utf-8'))['records']
groups={}
for r in rows: groups.setdefault((r['codeId'],r['articleId']),[]).append(r)
for key,items in groups.items():
    items.sort(key=lambda r:(r['sequence']['order'],r['id']))
    groups[key]=[r for r in items if r['part']!='caput' or not any(o['part']=='article' and o['unitLabel']=='Trecho da fonte: caput e pena' and ' '.join(o['text'].split()).startswith(' '.join(r['text'].split())+' Pena') for o in items)]
caput_only=next(k for k,v in groups.items() if v and all(r['part']=='caput' for r in v))
other_only=next(k for k,v in groups.items() if v and all(r['part'] in {'penalty','paragraph'} for r in v))
multiple=next(k for k,v in groups.items() if any(r['part']=='caput' for r in v) and sum(r['part']!='caput' for r in v)>1 and k!=('penal','215'))
reader=json.loads((ROOT/'experiments/previous-wordings-simple/20261021-associations-corrected/reader.json').read_text(encoding='utf-8'))
empty=next((c,a) for c,v in reader.items() for a in v['articles'] if (c,a) not in groups)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


with tempfile.TemporaryDirectory(prefix='previous-groups-',dir=ROOT/'test-results') as directory:
    subprocess.run(['node','--input-type=module','-e',"import {stagePages} from './scripts/build-pages.mjs'; await stagePages("+json.dumps(directory)+(",{previousWordingsCandidate:true});" if candidate else ",{legislativeHistorySimple:true});")],cwd=ROOT,check=True)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=directory))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--no-proxy-server'])
            for width in (390,1280):
                context=browser.new_context(viewport={'width':width,'height':950},service_workers='block')
                page=context.new_page(); errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                for code,article in ([('penal','215')] if before else [('penal','215'),caput_only,other_only,multiple,empty]):
                    page.goto(f'http://127.0.0.1:{server.server_port}/#/{code}/{article}')
                    trigger=page.locator(f'#art-{article} [data-legislative-history]')
                    if (code,article)==empty:
                        expect(trigger).to_have_count(0); continue
                    trigger.scroll_into_view_if_needed()
                    original=page.locator(f'#art-{article} .legal-unit').all_text_contents(); y=page.evaluate('scrollY')
                    trigger.click(); panel=page.locator('.legislative-panel'); expect(panel).to_be_visible()
                    expected=groups[(code,article)]; caps=[r for r in expected if r['part']=='caput']; others=[r for r in expected if r['part']!='caput']
                    if not before:
                        disclosure=panel.locator('.legislative-other')
                        if caps and others:
                            expect(disclosure).to_have_count(1)
                            expect(disclosure).not_to_have_attribute('open','')
                            expect(disclosure.locator('summary').first).to_have_text(f'Outras redações anteriores ({len(others)})')
                            expect(panel.locator('.legislative-text:visible')).to_have_text([r['text'] for r in caps])
                            if (code,article)==('penal','215'):
                                page.screenshot(path=str(OUT/f'215-after-{width}.png'))
                            summary=disclosure.locator('summary').first
                            summary.focus();page.keyboard.press('Enter')
                            expect(disclosure).to_have_attribute('open','')
                            expect(disclosure.locator('.legislative-text')).to_have_text([r['text'] for r in others])
                            if (code,article)==('penal','215'):
                                page.screenshot(path=str(OUT/f'215-expanded-{width}.png'))
                            page.keyboard.press('Space');expect(disclosure).not_to_have_attribute('open','')
                            summary.click();expect(disclosure).to_have_attribute('open','')
                        else:
                            expect(disclosure).to_have_count(0)
                        expect(panel.locator('.legislative-text')).to_have_text([r['text'] for r in (caps+others if caps and others else expected)])
                        # Every reference and note is still present, including nested disclosures.
                        for r in expected:
                            if r['reference']: assert r['reference'] in panel.text_content()
                            for note in r['notes']: assert note in panel.text_content()
                    elif (code,article)==('penal','215'):
                        page.screenshot(path=str(OUT/f'215-before-{width}.png'))
                    assert panel.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                    page.keyboard.press('Escape');expect(panel).not_to_be_visible();expect(trigger).to_be_focused()
                    assert abs(page.evaluate('scrollY')-y)<2
                    assert page.locator(f'#art-{article} .legal-unit').all_text_contents()==original
                assert not errors,errors
                context.close()
            browser.close()
    finally:
        server.shutdown();server.server_close()
print(json.dumps(dict(before=before,caputOnly=caput_only,otherOnly=other_only,multiple=multiple,empty=empty,status='PASS'),ensure_ascii=False))
