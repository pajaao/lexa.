"""Legislative history demo isolation, keyboard, mobile and reading continuity."""
from pathlib import Path
import functools
import http.server
import json
import subprocess
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect
from support import artifact_path, chromium_executable

ROOT = Path(__file__).resolve().parents[2]


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def previous_rows(rows,code,article):
    rows=sorted([r for r in rows if r['codeId']==code and r['articleId']==article and r.get('wording',{}).get('status')=='previous'],key=lambda r:(r['sequence']['order'],r['id']))
    return [r for r in rows if r['part']!='caput' or not any(other['part']=='article' and other.get('unitLabel')=='Trecho da fonte: caput e pena' and ' '.join(other['text'].split()).startswith(' '.join(r['text'].split())+' Pena') for other in rows)]

all_previous_data=json.loads((ROOT/'experiments/html-history/existing-records.json').read_text(encoding='utf-8'))
for name in ['legislative-history-html.json','previous-wordings-html.json']:
    all_previous_data+=json.loads((ROOT/'tests/fixtures'/name).read_text(encoding='utf-8'))['records']

ARTIFACTS = ROOT/'test-results'
ARTIFACTS.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='lexa-legislative-', dir=ARTIFACTS) as temporary:
    directory = str(Path(temporary)/'site')
    script = "import {stagePages} from './scripts/build-pages.mjs'; await stagePages(" + json.dumps(directory) + ",{legislativeHistoryDemo:true});"
    subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT, check=True)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=directory))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), args=['--no-sandbox', '--no-proxy-server'])
            for width in (320, 390, 1280):
                context = browser.new_context(viewport={'width': width, 'height': 850}, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}/#/penal/1')
                button = page.locator('#art-1 [data-legislative-history]')
                expect(button).to_be_visible()
                original = page.locator('#art-1 .legal-unit').all_text_contents()
                button.scroll_into_view_if_needed()
                button.focus()
                before = page.evaluate('scrollY')
                anchor = button.bounding_box()['y']
                page.keyboard.press('Enter')
                panel = page.locator('.legislative-panel')
                close = panel.get_by_role('button', name='Fechar redações anteriores')
                expect(panel).to_be_visible()
                expect(close).to_be_focused()
                expect(panel.locator('.legislative-timeline li')).to_have_count(2)
                expect(panel.locator('.legislative-demo')).to_contain_text('fictícios')
                expect(panel.locator('.legislative-sources summary')).to_have_count(1)
                panel.locator('.legislative-sources summary').click()
                expect(panel).to_contain_text('Fonte não informada.')
                expect(panel).to_contain_text('Referência legislativa não informada.')
                expect(panel.locator('.legislative-text').nth(1)).to_contain_text('sem depender de uma data de vigência.')
                notes = panel.get_by_text('Notas editoriais', exact=True)
                notes.click()
                expect(panel).to_contain_text('Nota fictícia:')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert panel.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                assert panel.bounding_box()['width'] <= (width if width < 700 else 561)
                close.focus()
                page.keyboard.press('Shift+Tab')
                expect(panel.locator('summary').last).to_be_focused()
                page.keyboard.press('Tab')
                expect(close).to_be_focused()
                page.screenshot(path=artifact_path(f'legislative-history-{width}.png'))
                page.keyboard.press('Escape')
                expect(panel).to_be_hidden()
                expect(button).to_be_focused()
                assert abs(page.evaluate('scrollY') - before) < 2
                assert abs(button.bounding_box()['y'] - anchor) < 2
                assert page.locator('#art-1 .legal-unit').all_text_contents() == original
                # Explicit close also restores reading and the trigger.
                button.click()
                close.click()
                expect(button).to_be_focused()
                assert abs(page.evaluate('scrollY') - before) < 2
                if width == 1280:
                    button.click()
                    bounds = panel.bounding_box()
                    inside = {'x': bounds['x'] + 30, 'y': 110}
                    outside = {'x': bounds['x'] - 30, 'y': 110}
                    page.mouse.click(**inside)
                    expect(panel).to_be_visible()
                    # A gesture crossing either boundary is not an outside click.
                    for start, end in ((inside, outside), (outside, inside)):
                        page.mouse.move(**start)
                        page.mouse.down()
                        page.mouse.move(**end)
                        page.mouse.up()
                        expect(panel).to_be_visible()
                    page.mouse.click(**outside)
                    expect(panel).to_be_hidden()
                    expect(button).to_be_focused()
                    assert abs(page.evaluate('scrollY') - before) < 2
                    assert page.locator('#art-1 .legal-unit').all_text_contents() == original
                # Only articles with eligible records expose the action.
                expect(page.locator('#art-2 [data-legislative-history]')).to_have_count(0)
                expect(page.locator('[data-legislative-history]')).to_have_count(1)
                button.click()
                # Route changes while the modal is open must release body lock.
                page.evaluate("location.hash='#/civil/1'")
                expect(page.locator('.reader-top h1')).to_have_text('Código Civil')
                assert page.evaluate("document.body.style.position!=='fixed'")
                assert not errors, errors
                context.close()
            # The explicit preview combines the preserved baseline and pending batches.
            pilot_dir = str(Path(temporary)/'pilot')
            subprocess.run(['node','--input-type=module','-e',"import {stagePages} from './scripts/build-pages.mjs'; await stagePages("+json.dumps(pilot_dir)+",{legislativeHistoryPilot:true});"], cwd=ROOT, check=True)
            production = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(Path(temporary)/'pilot')))
            threading.Thread(target=production.serve_forever, daemon=True).start()
            try:
                for width in (390, 1280):
                    context = browser.new_context(viewport={'width': width, 'height': 850}, service_workers='block')
                    page = context.new_page()
                    # Original General Part must never appear under reorganized IDs.
                    quarantine=json.loads((ROOT/'experiments/html-history/association-review/20261021/results.json').read_text(encoding='utf-8'))['quarantined']
                    for blocked_article in ('4','5'):
                        page.goto(f'http://127.0.0.1:{production.server_port}/#/penal/{blocked_article}')
                        blocked_trigger=page.locator(f'#art-{blocked_article} [data-legislative-history]')
                        if blocked_trigger.count():
                            blocked_trigger.click()
                            blocked_text=page.locator('.legislative-text').all_text_contents()
                            assert not any(row['text'] in blocked_text for row in quarantine if row['articleId']==blocked_article)
                            page.keyboard.press('Escape')
                    page.goto(f'http://127.0.0.1:{production.server_port}/#/penal/215')
                    button = page.locator('#art-215 [data-legislative-history]')
                    expect(button).to_be_visible()
                    # The reader renders only a window of articles; each eligible
                    # article is checked individually below rather than counted globally.
                    # Other revoked articles may now have previous wordings too.

                    original = page.locator('#art-215 .legal-unit').all_text_contents()
                    button.scroll_into_view_if_needed()
                    position = page.evaluate('scrollY')
                    button.click()
                    panel = page.locator('.legislative-panel')
                    expected215=previous_rows(all_previous_data,'penal','215')
                    expect(panel.locator('.legislative-timeline li')).to_have_count(len(expected215))
                    expect(panel.locator('.legislative-wording')).to_have_text(['Redação anterior']*len(expected215))
                    expect(panel.locator('.legislative-demo')).to_contain_text('não autorizado para publicação')
                    expect(panel.locator('.legislative-text').nth(0)).to_have_text('Art. 215 - Ter conjunção carnal com mulher honesta, mediante fraude:')
                    expect(panel.locator('.legislative-text').nth(1)).to_have_text('Art. 215. Ter conjunção carnal com mulher, mediante fraude:')
                    assert 'livre manifestação de vontade da vítima' not in ' '.join(panel.locator('.legislative-text').all_text_contents())
                    expect(panel.get_by_text('Notas editoriais', exact=True)).to_have_count(sum(bool(r['notes']) for r in expected215))
                    for disclosure in panel.get_by_text('Fonte e contexto documental', exact=True).all():
                        disclosure.click()
                    expect(panel.get_by_role('link', name='Consultar fonte')).to_have_count(len(expected215))
                    assert 'EXEMPLO FICTÍCIO' not in panel.inner_text()
                    assert panel.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                    page.screenshot(path=artifact_path(f'legislative-pilot-215-{width}.png'))
                    page.keyboard.press('Escape')
                    expect(button).to_be_focused()
                    assert abs(page.evaluate('scrollY') - position) < 2
                    assert page.locator('#art-215 .legal-unit').all_text_contents() == original
                    for article_id in ('44','45','46','75','213','275','277','332','342','172','180','206','218','272','282','310','311','339','343'):
                        page.goto(f'http://127.0.0.1:{production.server_port}/#/penal/{article_id}')
                        trigger = page.locator(f'#art-{article_id} [data-legislative-history]')
                        trigger.scroll_into_view_if_needed()
                        before_text = page.locator(f'#art-{article_id} .legal-unit').all_text_contents()
                        trigger.click()
                        count = len(previous_rows(all_previous_data,'penal',article_id))
                        expect(panel.locator('.legislative-timeline li')).to_have_count(count)
                        latest = 'Redação mais recente documentada' if article_id == '339' else 'Redação atual na edição consultada'
                        expect(panel.locator('.legislative-wording')).to_have_text(['Redação anterior']*count)
                        expect(panel.locator('.legislative-sources summary')).to_have_count(1)
                        panel.locator('.legislative-sources summary').click()
                        expect(panel).to_contain_text('homologação jurídica independente pendente')
                        page.keyboard.press('Escape')
                        expect(trigger).to_be_focused()
                        assert page.locator(f'#art-{article_id} .legal-unit').all_text_contents() == before_text
                    batch = json.loads((ROOT/'tests/fixtures/legislative-history-batch.json').read_text(encoding='utf-8'))['records']
                    html = json.loads((ROOT/'tests/fixtures/legislative-history-html.json').read_text(encoding='utf-8'))['records']
                    for article_id in dict.fromkeys(row['articleId'] for row in batch):
                        records = previous_rows(all_previous_data,'penal',article_id)
                        page.goto(f'http://127.0.0.1:{production.server_port}/#/penal/{article_id}')
                        trigger = page.locator(f'#art-{article_id} [data-legislative-history]')
                        trigger.scroll_into_view_if_needed()
                        before_text = page.locator(f'#art-{article_id} .legal-unit').all_text_contents()
                        position = page.evaluate('scrollY')
                        trigger.click()
                        expect(panel.locator('.legislative-timeline li')).to_have_count(len(records))
                        assert panel.locator('.legislative-text').all_text_contents() == [row['text'] for row in records]
                        assert panel.locator('.legislative-timeline h3').all_text_contents() == [row['unitLabel'] for row in records]
                        expect(panel.locator('.legislative-sources summary')).to_have_count(1)
                        panel.locator('.legislative-sources summary').click()
                        expect(panel.get_by_role('link',name='Consultar fonte')).to_have_count(len(records))
                        if article_id=='155':
                            page.screenshot(path=artifact_path(f'legislative-batch-{width}.png'))
                        assert panel.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                        page.keyboard.press('Escape')
                        expect(trigger).to_be_focused()
                        assert abs(page.evaluate('scrollY')-position)<2
                        assert page.locator(f'#art-{article_id} .legal-unit').all_text_contents()==before_text
                    # One complete article per positive HTML source, plus an alínea case.
                    targets = dict((row['codeId'],None) for row in html)
                    selections = [next(row for row in html if row['codeId']==code) for code in targets]
                    selections.append(next(row for row in html if row['part']=='letter'))
                    selections.extend(next(row for row in html if row['codeId']=='cf' and row['articleId']==id) for id in ['16','18','20'])
                    additions=json.loads((ROOT/'tests/fixtures/previous-wordings-html.json').read_text(encoding='utf-8'))['records']
                    selections.append(next(row for row in additions if row['codeId']=='cpc'))
                    selections.append(next(row for row in additions if row['codeId']=='cf' and row['articleId'].startswith('adct-')))
                    selections.append(next(row for row in additions if row['codeId']=='cpp' and row['articleId'].isdigit() and 363<int(row['articleId'])<406))
                    for code,article_id in [('cpp','439'),('clt','73'),('licitacoes','191')]:
                        selections.append(next(row for row in additions if row['codeId']==code and row['articleId']==article_id))
                    prior = json.loads((ROOT/'experiments/html-history/existing-records.json').read_text(encoding='utf-8'))
                    for selected in selections:
                        code, article_id = selected['codeId'], selected['articleId']
                        records = previous_rows(all_previous_data,code,article_id)
                        page.goto(f'http://127.0.0.1:{production.server_port}/#/{code}/{article_id}')
                        trigger = page.locator(f'#art-{article_id} [data-legislative-history]')
                        trigger.scroll_into_view_if_needed()
                        position = page.evaluate('scrollY')
                        before_text = page.locator(f'#art-{article_id} .legal-unit').all_text_contents()
                        if code=='cf' and article_id in {'16','18','20'}:
                            expect(page.locator(f'#art-{article_id} del')).to_have_count(0)
                            expect(page.locator(f'#art-{article_id} .deleted-note')).to_have_count(0)
                        if code=='cf' and article_id=='6':
                            expect(page.locator('#art-6 .legal-unit')).to_have_count(2)
                            expect(page.locator('#art-6 del')).to_have_count(0)
                            expect(page.locator('#art-6 .deleted-note')).to_have_count(0)
                            page.evaluate('navigator.clipboard.writeText=async text=>{window.__copied=text;}')
                            page.locator('#art-6 .article-copy>summary').click()
                            page.locator('#art-6 [data-copy-text]').click()
                            expect(page.locator('#toast')).to_contain_text('Texto e referência copiados')
                            copied = page.evaluate('window.__copied')
                            assert 'transporte' in copied
                            for row in records:
                                if row['wording']['status']=='previous':
                                    assert row['text'] not in copied
                        trigger.click()
                        expect(panel.locator('.legislative-timeline li')).to_have_count(len(records))
                        assert panel.locator('.legislative-text').all_text_contents()==[row['text'] for row in records]
                        assert panel.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                        panel.locator('.legislative-sources summary').click()
                        expect(panel.get_by_role('link',name='Consultar fonte')).to_have_count(len(records))
                        page.screenshot(path=artifact_path(f'legislative-html-{code}-{width}.png'))
                        page.keyboard.press('Escape')
                        expect(trigger).to_be_focused()
                        assert abs(page.evaluate('scrollY')-position)<2
                        assert page.locator(f'#art-{article_id} .legal-unit').all_text_contents()==before_text
                    page.goto(f'http://127.0.0.1:{production.server_port}/#/penal/216')
                    page.locator('#art-216 [data-legislative-history]').click()
                    texts=panel.locator('.legislative-text').all_text_contents()
                    assert any('Induzir mulher honesta' in text for text in texts)
                    assert any('Induzir alguém' in text for text in texts)
                    assert all('superior hierárquico' not in text for text in texts)
                    page.keyboard.press('Escape')
                    context.close()
            finally:
                production.shutdown()
            browser.close()
    finally:
        server.shutdown()
print('Histórico legislativo: 320, 390 e 1280 px; teclado, leitura, estados opcionais e navegação aprovados.')
