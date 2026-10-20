"""Validate restored original decoration and approved copy without redesign."""
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
                expect(page.locator('.hero-geometry,.hero-ornament')).to_have_count(0)
                art = page.locator('.hero-art')
                expect(art).to_have_count(1)
                expect(art).to_have_attribute('aria-hidden','true')
                expect(art.locator('.book')).to_have_count(2)
                expect(art.locator('button,a,input')).to_have_count(0)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                if width <= 900:
                    expect(art).to_be_hidden()
                else:
                    expect(art).to_be_visible()
                    # The restored illustration must remain outside the search field.
                    box = art.bounding_box()
                    search = page.locator('.hero-search').bounding_box()
                    assert box['x'] >= search['x']+search['width'], (width,box,search)
                expect(page.locator('.hero>p')).to_have_text('Pesquise normas, artigos e súmulas na biblioteca do Lexa.')
                expect(page.locator('.section-heading>p')).to_have_text('Consulte as normas e súmulas disponíveis.')
                page.keyboard.press('/')
                expect(page.locator('#library-search')).to_be_focused()
                page.locator('#library-search').blur();page.mouse.move(width-1,0)
                if width in (320,390,1440):
                    page.screenshot(path=artifact_path(f'original-restored-{width}-{"dark" if dark else "light"}.png'))
                context.close()
        browser.close()
    print('Interface original: livros decorativos acessíveis, busca livre de sobreposição, textos aprovados e teclado; 320–1920 px, claro/escuro.')
finally:
    server.shutdown();server.server_close()
