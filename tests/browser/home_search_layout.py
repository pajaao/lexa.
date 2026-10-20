"""Original home presentation, approved copy and functional search/navigation."""
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

def navigation_state(page, href):
    active = page.locator('header nav>a[aria-current="page"]')
    expect(active).to_have_count(1)
    expect(active).to_have_attribute('href', href)
    assert active.evaluate("el=>getComputedStyle(el).backgroundColor") != 'rgba(0, 0, 0, 0)'

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), args=['--no-sandbox', '--no-proxy-server'])
        for width in (320, 390, 768, 1024, 1199, 1200, 1366, 1440):
            for dark in (False, True):
                context = browser.new_context(viewport={'width': width, 'height': 900}, service_workers='block', reduced_motion='reduce')
                page = context.new_page();errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(base)
                if dark: page.locator('#theme').click()
                expect(page.get_by_role('heading', level=1)).to_have_text('O que você deseja consultar?')
                expect(page.get_by_role('heading', name='Explore a biblioteca', exact=True)).to_be_visible()
                expect(page.locator('.code-card')).to_have_count(14)
                navigation_state(page, '#')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
                boxes = page.locator('header nav>a,header nav>button,.search-examples button,.filters button').evaluate_all('(els)=>els.map(el=>el.getBoundingClientRect().toJSON())')
                for box in boxes:
                    assert box['height'] >= 24 and box['width'] >= 24, (width, box)
                assert page.locator('header nav>a,header nav>button').evaluate_all('(els)=>els.every(el=>el.scrollWidth<=el.clientWidth+1)'), width
                field = page.locator('.hero-search').bounding_box()
                assert field['width'] <= 580 and field['width'] > 200, (width, field)
                expect(page.locator('.hero-ornament')).to_have_count(0)
                assert page.locator('.hero-note').bounding_box()['y'] < page.locator('.library').bounding_box()['y']
                page.keyboard.press('/')
                expect(page.locator('#library-search')).to_be_focused()
                assert page.locator('.hero-search').evaluate("el=>getComputedStyle(el).outlineStyle") != 'none'
                page.locator('#library-search').blur()
                page.mouse.move(width-1, 0)
                page.screenshot(path=artifact_path(f'home-search-{width}-{"dark" if dark else "light"}.png'))
                # Reference search and keyboard submission retain their original route.
                page.get_by_role('button', name='Art. 5 CF', exact=True).focus()
                page.keyboard.press('Enter')
                expect(page.locator('#library-search')).to_have_value('Art. 5 CF')
                expect(page.locator('#quick-reference a')).to_have_attribute('href', '#/cf/5')
                page.locator('#library-search').press('Enter')
                expect(page.locator('#art-5')).to_be_visible()
                page.locator('header nav>a[href="#/favoritos"]').click()
                expect(page.locator('.favorites-page')).to_be_visible()
                navigation_state(page, '#/favoritos')
                page.locator('header nav>a[href="#/atualizacoes"]').click()
                expect(page.locator('.updates-hero')).to_be_visible()
                navigation_state(page, '#/atualizacoes')
                page.get_by_role('link', name='Lexa — início', exact=True).click()
                expect(page.locator('#library-search')).to_have_value('Art. 5 CF')
                navigation_state(page, '#')
                assert not errors, errors
                context.close()
        # Original navigation can wrap; every action must remain readable.
        context = browser.new_context(viewport={'width':320,'height':900}, service_workers='block')
        page = context.new_page();page.goto(base)
        page.add_style_tag(content='header nav{font-family:Verdana,sans-serif}')
        nav = page.locator('header nav>a,header nav>button')
        assert nav.evaluate_all('(els)=>els.every(el=>el.scrollWidth<=el.clientWidth+1)')
        context.close()
        context = browser.new_context(service_workers='block', forced_colors='active')
        page = context.new_page();page.goto(base)
        active = page.locator('header nav>a[aria-current="page"]')
        expect(active).to_have_attribute('aria-current','page')
        assert active.evaluate("el=>getComputedStyle(el).outlineStyle") != 'none'
        expect(page.locator('.hero-geometry:visible')).to_have_count(0)
        context.close()
        browser.close()
    print('Home original e textos aprovados: busca, teclado, navegação, alvos mínimos de 24 px; 320–1440 px, claro/escuro e alto contraste.')
finally:
    server.shutdown();server.server_close()
