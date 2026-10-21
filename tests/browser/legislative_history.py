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
                close = panel.get_by_role('button', name='Fechar histórico do artigo')
                expect(panel).to_be_visible()
                expect(close).to_be_focused()
                expect(panel.locator('.legislative-timeline li')).to_have_count(2)
                expect(panel.locator('.legislative-demo')).to_contain_text('fictícios')
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
                # Another article must not inherit the first article's records.
                empty = page.locator('#art-2 [data-legislative-history]')
                empty.click()
                expect(panel.locator('.legislative-timeline li')).to_have_count(0)
                expect(panel).to_contain_text('Isso não significa que ele nunca tenha sido alterado.')
                # Route changes while the modal is open must release body lock.
                page.evaluate("location.hash='#/civil/1'")
                expect(page.locator('.reader-top h1')).to_have_text('Código Civil')
                assert page.evaluate("document.body.style.position!=='fixed'")
                assert not errors, errors
                context.close()
            # The normal package contains only the individually approved pilot.
            production = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT/'dist')))
            threading.Thread(target=production.serve_forever, daemon=True).start()
            try:
                for width in (390, 1280):
                    context = browser.new_context(viewport={'width': width, 'height': 850}, service_workers='block')
                    page = context.new_page()
                    page.goto(f'http://127.0.0.1:{production.server_port}/#/penal/215')
                    button = page.locator('#art-215 [data-legislative-history]')
                    expect(button).to_be_visible()
                    original = page.locator('#art-215 .legal-unit').all_text_contents()
                    button.scroll_into_view_if_needed()
                    position = page.evaluate('scrollY')
                    button.click()
                    panel = page.locator('.legislative-panel')
                    expect(panel.locator('.legislative-timeline li')).to_have_count(3)
                    expect(panel.locator('.legislative-demo')).to_have_count(0)
                    expect(panel.locator('.legislative-text').nth(0)).to_have_text('Art. 215 - Ter conjunção carnal com mulher honesta, mediante fraude:')
                    expect(panel.locator('.legislative-text').nth(1)).to_have_text('Art. 215. Ter conjunção carnal com mulher, mediante fraude:')
                    expect(panel.locator('.legislative-text').nth(2)).to_contain_text('livre manifestação de vontade da vítima:')
                    expect(panel.get_by_text('Notas editoriais', exact=True)).to_have_count(2)
                    for disclosure in panel.get_by_text('Fonte e contexto documental', exact=True).all():
                        disclosure.click()
                    expect(panel.get_by_role('link', name='Consultar fonte')).to_have_count(3)
                    assert 'EXEMPLO FICTÍCIO' not in panel.inner_text()
                    assert panel.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                    page.screenshot(path=artifact_path(f'legislative-pilot-215-{width}.png'))
                    page.keyboard.press('Escape')
                    expect(button).to_be_focused()
                    assert abs(page.evaluate('scrollY') - position) < 2
                    assert page.locator('#art-215 .legal-unit').all_text_contents() == original
                    context.close()
            finally:
                production.shutdown()
            browser.close()
    finally:
        server.shutdown()
print('Histórico legislativo: 320, 390 e 1280 px; teclado, leitura, estados opcionais e navegação aprovados.')
