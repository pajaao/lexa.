"""Leitor editorial: proporções, continuidade jurídica e barras responsivas."""
from pathlib import Path
import functools
import http.server
import threading
from playwright.sync_api import sync_playwright, expect
from support import artifact_path, chromium_executable

root = Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0),
    functools.partial(Quiet, directory=str(root/'dist')))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}/'

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(),
            args=['--no-sandbox', '--disable-dev-shm-usage', '--no-proxy-server'])
        errors = []
        for width in (320, 390, 768, 1366):
            for dark in (False, True):
                context = browser.new_context(viewport={'width': width, 'height': 880},
                    service_workers='block', reduced_motion='reduce')
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(base + '#/cf/1')
                expect(page.locator('#art-1')).to_be_visible()
                expect(page.locator('#art-1 .legal-unit')).not_to_have_count(0)
                if dark:
                    page.locator('#theme').click()

                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
                assert page.locator('#art-1').evaluate(
                    "el=>getComputedStyle(el).borderTopWidth") == '0px'
                assert page.locator('#art-1').evaluate(
                    "el=>getComputedStyle(el).borderTopLeftRadius") == '0px'
                expect(page.locator('.source-details>summary')).to_be_visible()
                expect(page.locator('.reader-top a[href*="atualizacoes"]')).to_have_count(1)
                assert page.locator('#art-1').evaluate(
                    "el=>getComputedStyle(el).backgroundColor") == 'rgba(0, 0, 0, 0)'

                reading = page.locator('.reading')
                if width >= 1100:
                    assert reading.bounding_box()['width'] >= 850, reading.bounding_box()
                    assert page.locator('.reader-layout aside').bounding_box()['width'] >= 260
                if width <= 700:
                    controls = page.locator('.reading-controls')
                    assert controls.bounding_box()['height'] <= 100
                    buttons = [
                        page.locator('.mobile-search-toggle'),
                        page.locator('.mobile-index-toggle'),
                        page.locator('.reading-settings>summary'),
                        page.locator('#focus-mode')
                    ]
                    coords = [b.bounding_box() for b in buttons]
                    assert all(box['height'] >= 44 and box['width'] >= 44 for box in coords), coords
                    assert len({round(box['y']) for box in coords}) == 1, coords
                    assert all(coords[i+1]['x'] - (coords[i]['x'] + coords[i]['width']) >= 6
                        for i in range(3)), coords
                    expect(page.locator('.reader-options>#focus-mode')).to_have_count(0)
                    page.locator('.reading-settings>summary').click()
                    expect(page.locator('.reading-sheet')).to_be_visible()
                    page.keyboard.press('Escape')
                    expect(page.locator('.reading-sheet')).to_be_hidden()
                else:
                    expect(page.locator('.reading-settings')).not_to_have_attribute('open', '')
                    controls = page.locator('.reading-controls')
                    before = controls.bounding_box()['height']
                    page.locator('.reading-settings>summary').click()
                    expect(page.locator('#font-up')).to_be_visible()
                    assert abs(controls.bounding_box()['height'] - before) < 2
                    page.locator('.reading-settings>summary').click()
                    expect(page.locator('#font-up')).to_be_hidden()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                if width in (390, 1366):
                    page.screenshot(path=artifact_path(
                        f'reader-editorial-{width}-{"dark" if dark else "light"}.png'))
                context.close()
        assert not errors, errors
        browser.close()
        print('PASS leitor editorial: 320–1366px, claro/escuro, texto contínuo, barra compacta e proveniência.')
finally:
    server.shutdown()
    server.server_close()
    thread.join()
