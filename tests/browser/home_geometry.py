"""Validate the approved editorial geometry without moving hybrid home content."""
from pathlib import Path
import functools, http.server, threading
from playwright.sync_api import sync_playwright, expect
from support import artifact_path, chromium_executable

root = Path(__file__).resolve().parents[2]

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(root/'dist')))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
content = '.hero h1,.hero>p,.hero>.field-label,.hero-search,.search-examples button,.search-examples>span,.hero-note>span,.library,.code-card:first-child'

def positions(page):
    return page.locator(content).evaluate_all('(els)=>els.map(el=>el.getBoundingClientRect().toJSON())')

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), args=['--no-sandbox', '--no-proxy-server'])
        for width in (320, 390, 768, 1199, 1200, 1440, 1920):
            for dark in (False, True):
                context = browser.new_context(viewport={'width':width,'height':1000}, service_workers='block', reduced_motion='reduce')
                page = context.new_page();page.goto(base)
                expect(page.locator('.code-card')).to_have_count(14)
                if dark: page.locator('#theme').click()
                page.evaluate('document.fonts.ready')
                hidden = page.add_style_tag(content='.hero-geometry{display:none!important}')
                baseline = positions(page)
                text = page.locator('.hero').inner_text()
                hidden.evaluate('(el)=>el.remove()')
                assert positions(page) == baseline, width
                assert page.locator('.hero').inner_text() == text
                assert page.locator('.hero').get_attribute('data-geometry') is None
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                expected_font = 28 if width<=400 else 30 if width<=700 else 36
                assert page.locator('.hero h1').evaluate('el=>parseFloat(getComputedStyle(el).fontSize)') == expected_font
                decorations = page.locator('.hero-geometry')
                expect(decorations).to_have_count(2)
                for decoration in decorations.all():
                    expect(decoration).to_have_attribute('aria-hidden','true')
                    expect(decoration).to_have_attribute('focusable','false')
                    expect(decoration.locator('text,a,image,g')).to_have_count(0)
                    expect(decoration.locator('path')).to_have_count(1)
                    expect(decoration.locator('circle')).to_have_count(2)
                    style = decoration.evaluate('el=>{const s=getComputedStyle(el);return {pointer:s.pointerEvents,alpha:Number(s.opacity),stroke:parseFloat(s.strokeWidth)}}')
                    assert style == {'pointer':'none','alpha':.4,'stroke':1}, style
                    if width < 1200:
                        expect(decoration).to_be_hidden()
                    else:
                        expect(decoration).to_be_visible()
                        box = decoration.bounding_box()
                        assert box['width'] == 128
                        # All central content stays outside both side regions.
                        for protected in baseline[:-2]:
                            assert box['x']+box['width']<=protected['left'] or box['x']>=protected['right'], (width, box, protected)
                assert 'img' not in page.locator('.hero').aria_snapshot()
                page.keyboard.press('/')
                expect(page.locator('#library-search')).to_be_focused()
                page.locator('#library-search').blur();page.mouse.move(width-1,0)
                if width in (390, 1200, 1440):
                    page.screenshot(path=artifact_path(f'geometry-final-{width}-{"dark" if dark else "light"}.png'))
                if width >= 1200:
                    page.emulate_media(forced_colors='active')
                    expect(page.locator('.hero-geometry:visible')).to_have_count(0)
                    page.emulate_media(forced_colors='none',media='print')
                    expect(page.locator('.hero-geometry:visible')).to_have_count(0)
                context.close()
        browser.close()
    print('Geometria editorial consolidada: dimensões/contraste aprovados, composição e textos preservados, margens livres, foco/ARIA; 320–1920 px, claro/escuro, alto contraste e impressão.')
finally:
    server.shutdown();server.server_close()
