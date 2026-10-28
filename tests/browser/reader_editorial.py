"""Leitor editorial: proporções, continuidade jurídica e barras responsivas."""
from pathlib import Path
import functools
import http.server
import threading
import re
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

def contrast(a, b):
    def luminance(color):
        rgb = [int(v)/255 for v in re.findall(r'\d+', color)[:3]]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(v*w for v, w in zip(linear, (.2126, .7152, .0722)))
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light+.05)/(dark+.05)

def colors(control):
    return control.evaluate('''el=>{const s=getComputedStyle(el);return {
        background:s.backgroundColor, text:s.color, border:s.borderTopColor,
        outline:s.outlineColor, outlineWidth:parseFloat(s.outlineWidth),
        outlineStyle:s.outlineStyle,
        surrounding:getComputedStyle(el.closest('.reading-controls')).backgroundColor
    }}''')

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(),
            args=['--no-sandbox', '--disable-dev-shm-usage', '--no-proxy-server'])
        errors = []
        focus_contrasts = []
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
                focus = page.locator('#focus-mode')
                normal = colors(focus)
                settings_colors = colors(page.locator('.reading-settings>summary'))
                assert (normal['background'], normal['text'], normal['border']) == (
                    settings_colors['background'], settings_colors['text'], settings_colors['border']), (width, dark, normal, settings_colors)
                if width <= 700:
                    search_colors = colors(page.locator('.mobile-search-toggle'))
                    assert (normal['background'], normal['text']) == (
                        search_colors['background'], search_colors['text']), (width, dark, normal, search_colors)
                assert contrast(normal['text'], normal['background']) >= 4.5
                page.keyboard.press('Tab')
                focus.focus()
                expect(focus).to_be_focused()
                keyboard = colors(focus)
                assert keyboard['outlineWidth'] >= 2 and keyboard['outlineStyle'] != 'none'
                assert contrast(keyboard['outline'], keyboard['surrounding']) >= 3
                page.keyboard.press('Space')
                expect(focus).to_have_attribute('aria-pressed', 'true')
                expect(page.locator('body')).to_have_class(re.compile(r'\breading-focus\b'))
                active = colors(focus)
                assert active['background'] != normal['background']
                assert contrast(active['text'], active['background']) >= 4.5
                focus_contrasts.append((width, dark, round(contrast(normal['text'], normal['background']), 2),
                    round(contrast(active['text'], active['background']), 2)))
                if width in (390, 1366):
                    page.screenshot(path=artifact_path(
                        f'focus-active-{width}-{"dark" if dark else "light"}.png'))
                page.keyboard.press('Escape')
                expect(focus).to_have_attribute('aria-pressed', 'false')
                expect(focus).to_be_focused()
                assert colors(focus)['background'] == normal['background']
                focus.click()
                expect(focus).to_have_attribute('aria-pressed', 'true')
                focus.click()
                expect(focus).to_have_attribute('aria-pressed', 'false')
                if width in (390, 1366):
                    page.screenshot(path=artifact_path(
                        f'reader-editorial-{width}-{"dark" if dark else "light"}.png'))
                context.close()
        assert not errors, errors
        browser.close()
        print('Contraste Foco (largura, escuro, normal, ativo):', focus_contrasts)
        print('PASS leitor editorial: 320–1366px, claro/escuro, texto contínuo, barra compacta e proveniência.')
finally:
    server.shutdown()
    server.server_close()
    thread.join()
