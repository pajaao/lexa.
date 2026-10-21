"""Exercise only the new simple preview, never the historical pilot fixtures."""
from pathlib import Path
import functools
import http.server
import json
import subprocess
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect
from support import artifact_path, chromium_executable

ROOT=Path(__file__).resolve().parents[2]
rows=json.loads((ROOT/'tests/fixtures/previous-wordings-simple.json').read_text(encoding='utf-8'))['records']
selected={}
for row in rows: selected.setdefault(row['codeId'],row['articleId'])
selected.update(cf='6',penal='215',cpp='439')


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


(ROOT/'test-results').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='simple-previous-',dir=ROOT/'test-results') as directory:
    script="import {stagePages} from './scripts/build-pages.mjs'; await stagePages("+json.dumps(directory)+",{legislativeHistorySimple:true});"
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=directory))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--no-proxy-server'])
            for width in (390,1280):
                context=browser.new_context(viewport={'width':width,'height':850},service_workers='block')
                page=context.new_page(); errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                for code,article in selected.items():
                    page.goto(f'http://127.0.0.1:{server.server_port}/#/{code}/{article}')
                    trigger=page.locator(f'#art-{article} [data-legislative-history]')
                    expect(trigger).to_be_visible(); trigger.scroll_into_view_if_needed()
                    before=page.locator(f'#art-{article} .legal-unit').all_text_contents()
                    position=page.evaluate('scrollY');trigger.click()
                    panel=page.locator('.legislative-panel');expect(panel).to_be_visible()
                    expected=sorted([r for r in rows if r['codeId']==code and r['articleId']==article],key=lambda r:(r['sequence']['order'],r['id']))
                    expected=[r for r in expected if r['part']!='caput' or not any(other['part']=='article' and other['unitLabel']=='Trecho da fonte: caput e pena' and ' '.join(other['text'].split()).startswith(' '.join(r['text'].split())+' Pena') for other in expected)]
                    caps=[r for r in expected if r['part']=='caput']; others=[r for r in expected if r['part']!='caput']
                    if caps and others:
                        expect(panel.locator('.legislative-other')).not_to_have_attribute('open','')
                        panel.locator('.legislative-other > summary').click()
                        expected=caps+others
                    expect(panel.locator('.legislative-text')).to_have_text([r['text'] for r in expected])
                    expect(panel.locator('.legislative-demo')).to_contain_text('não autorizado para publicação')
                    panel.get_by_text('Fonte e contexto documental',exact=True).click()
                    expect(panel.get_by_role('link',name='Consultar fonte')).to_have_count(len(expected))
                    assert panel.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                    if code=='penal': page.screenshot(path=artifact_path(f'simple-previous-215-{width}.png'))
                    page.keyboard.press('Escape');expect(panel).not_to_be_visible();expect(trigger).to_be_focused()
                    assert abs(page.evaluate('scrollY')-position)<2
                    assert page.locator(f'#art-{article} .legal-unit').all_text_contents()==before
                assert not errors,errors
                context.close()
            browser.close()
    finally:
        server.shutdown();server.server_close()
print(f'Simple preview PASS: {len(selected)} collections, 390/1280px, full text/source, keyboard and reading continuity.')
