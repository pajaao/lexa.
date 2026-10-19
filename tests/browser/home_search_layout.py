"""Search-first hierarchy, navigation states and alignment in both themes."""
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
    assert active.evaluate("el=>getComputedStyle(el).backgroundColor") == 'rgba(0, 0, 0, 0)'
    assert active.evaluate("el=>parseFloat(getComputedStyle(el).borderBottomWidth)") == 2
    assert active.evaluate("el=>getComputedStyle(el).borderBottomStyle") == 'solid'
    assert active.evaluate("el=>getComputedStyle(el).borderBottomColor") != 'rgba(0, 0, 0, 0)'

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
                    assert box['height'] >= 44 and box['width'] >= 44, (width, box)
                nav = page.locator('header nav>a,header nav>button').evaluate_all('(els)=>els.map(el=>el.getBoundingClientRect().top)')
                assert max(nav)-min(nav) <= 1, (width, nav)
                assert page.locator('header nav>a,header nav>button').evaluate_all('(els)=>els.every(el=>el.scrollWidth<=el.clientWidth+1)'), width
                field = page.locator('.hero-search').bounding_box()
                assert abs(field['x']+field['width']/2-width/2) <= 1
                assert abs(field['width']-min(760, width-(40 if width<=700 else 88))) <= 1
                decorations = page.locator('.hero-ornament')
                expect(decorations).to_have_count(2)
                for decoration in decorations.all():
                    expect(decoration).to_have_attribute('aria-hidden', 'true')
                    expect(decoration).to_have_attribute('focusable', 'false')
                    assert decoration.evaluate("el=>getComputedStyle(el).pointerEvents") == 'none'
                    if width < 1200:
                        expect(decoration).to_be_hidden()
                    else:
                        expect(decoration).to_be_visible()
                        box = decoration.bounding_box()
                        assert box['x']+box['width']<=field['x'] or box['x']>=field['x']+field['width']
                gap = page.locator('.section-heading .eyebrow').bounding_box()['y']-page.locator('.hero-note').evaluate('el=>el.getBoundingClientRect().bottom')
                assert abs(gap-(32 if width<=700 else 36))<=1, (width, gap)
                assert page.locator('.hero-note').bounding_box()['y'] < page.locator('.library').bounding_box()['y']
                rows = page.locator('.code-card').evaluate_all('(cards)=>cards.map(card=>({row:card.getBoundingClientRect().top,footer:card.querySelector(".card-bottom").getBoundingClientRect().top}))')
                for row in {item['row'] for item in rows}:
                    footers = [item['footer'] for item in rows if item['row'] == row]
                    assert max(footers)-min(footers) <= 1, (width, footers)
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
        # Wider fallback metrics must not wrap or clip the narrow navigation.
        context = browser.new_context(viewport={'width':320,'height':900}, service_workers='block')
        page = context.new_page();page.goto(base)
        page.add_style_tag(content='header nav{font-family:Verdana,sans-serif}')
        nav = page.locator('header nav>a,header nav>button')
        tops = nav.evaluate_all('(els)=>els.map(el=>el.getBoundingClientRect().top)')
        assert max(tops)-min(tops)<=1, tops
        assert nav.evaluate_all('(els)=>els.every(el=>el.scrollWidth<=el.clientWidth+1)')
        context.close()
        context = browser.new_context(service_workers='block', forced_colors='active')
        page = context.new_page();page.goto(base)
        active = page.locator('header nav>a[aria-current="page"]')
        assert active.evaluate("el=>getComputedStyle(el).borderBottomStyle") == 'solid'
        assert active.evaluate("el=>getComputedStyle(el).borderBottomColor") != 'rgba(0, 0, 0, 0)'
        expect(page.locator('.hero-ornament:visible')).to_have_count(0)
        context.close()
        browser.close()
    print('Home: hierarquia, espaçamentos, ornamentos laterais não interativos, largura da busca, alvos de 44 px, teclado e navegação; 320–1440 px, claro/escuro e alto contraste, sem transbordamento.')
finally:
    server.shutdown();server.server_close()
