"""Compact reader, native settings sheet and reading continuity on mobile."""
from pathlib import Path
import functools
import http.server
import threading
from playwright.sync_api import sync_playwright, expect
from support import artifact_path, chromium_executable

ROOT = Path(__file__).resolve().parents[2]


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT/'dist')))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), args=['--no-sandbox', '--no-proxy-server'])
        for width in (320, 390):
            for motion in ('reduce', 'no-preference'):
                context = browser.new_context(viewport={'width': width, 'height': 812}, reduced_motion=motion, has_touch=True, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(base+'#/cf/5')
                expect(page.locator('#art-5')).to_be_visible()
                page.locator('#art-5 .legal-unit').nth(4).scroll_into_view_if_needed()
                page.wait_for_function("Math.abs(document.querySelector('.reading-controls').getBoundingClientRect().top)<1")
                if width == 390:
                    page.evaluate("document.documentElement.classList.add('dark')")
                assert page.locator('.reading-controls').bounding_box()['height'] <= 64
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                expect(page.locator('#article-search')).to_be_hidden()
                page.screenshot(path=artifact_path(f'sheet-closed-{width}-{motion}.png'))
                summary = page.locator('.reading-settings>summary')
                sheet = page.locator('.reading-sheet')
                close = page.get_by_role('button', name='Fechar ajustes de leitura')
                anchor = page.locator('#art-5 .legal-unit').nth(4)
                before = anchor.bounding_box()['y']
                position = page.evaluate('scrollY')
                summary.focus()
                page.keyboard.press('Enter')
                expect(sheet).to_be_visible()
                expect(close).to_be_focused()
                assert abs(anchor.bounding_box()['y']-before) < 2
                assert page.locator('.reading-controls').bounding_box()['height'] <= 64
                assert page.locator('#font-up').count() == 1
                page.keyboard.press('Shift+Tab')
                expect(page.locator('#reset-reading')).to_be_focused()
                page.keyboard.press('Tab')
                expect(close).to_be_focused()
                page.screenshot(path=artifact_path(f'sheet-open-{width}-{motion}.png'))
                page.keyboard.press('Escape')
                expect(sheet).to_be_hidden()
                expect(summary).to_be_focused()
                assert abs(page.evaluate('scrollY')-position) < 2
                assert abs(anchor.bounding_box()['y']-before) < 2
                summary.click()
                visible_text = page.evaluate_handle("Array.from(document.querySelectorAll('#articles .legal-unit')).find(el=>el.getBoundingClientRect().bottom>document.querySelector('.reading-controls').getBoundingClientRect().bottom+12)")
                text_top = visible_text.evaluate('el=>el.getBoundingClientRect().top')
                page.locator('#font-up').click()
                assert abs(visible_text.evaluate('el=>el.getBoundingClientRect().top')-text_top) < 2
                expect(page.locator('#font-size')).to_have_text('20 px')
                assert page.locator('#art-5 .legal-unit').first.evaluate('el=>getComputedStyle(el).fontSize') == '20px'
                page.locator('#reading-spacing').select_option('comfortable')
                expect(page.locator('.reading')).to_have_attribute('data-spacing', 'comfortable')
                assert abs(visible_text.evaluate('el=>el.getBoundingClientRect().top')-text_top) < 2
                assert page.evaluate("JSON.parse(localStorage.getItem('lexa-reading')).size") == 20
                close.click()
                expect(summary).to_be_focused()
                summary.click()
                page.mouse.click(4, 4)
                expect(sheet).to_be_hidden()
                expect(summary).to_be_focused()
                summary.click()
                handle = page.locator('.sheet-handle').bounding_box()
                x, y = handle['x']+handle['width']/2, handle['y']+handle['height']/2
                session = context.new_cdp_session(page)
                session.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                session.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y+80}]})
                session.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                expect(sheet).to_be_hidden()
                expect(summary).to_be_focused()
                summary.click()
                page.locator('#reset-reading').click()
                expect(page.locator('#font-size')).to_have_text('19 px')
                expect(page.locator('.reading')).to_have_attribute('data-spacing', 'standard')
                page.set_viewport_size({'width': 1366, 'height': 900})
                expect(sheet).to_be_hidden()
                assert page.evaluate("document.body.style.position") != 'fixed'
                if not page.locator('.reading-settings').evaluate('el=>el.open'):
                    summary.click()
                expect(page.locator('#font-up')).to_be_visible()
                expect(page.locator('#article-search')).to_be_visible()
                assert page.locator('#font-up').count() == 1
                page.set_viewport_size({'width': width, 'height': 812})
                page.keyboard.press('/')
                expect(page.locator('#article-search')).to_be_focused()
                page.locator('#article-search').fill('dignidade')
                expect(page.locator('#articles mark').first).to_be_visible()
                page.keyboard.press('Escape')
                expect(page.locator('.mobile-search-toggle')).to_be_focused()
                expect(page.locator('#article-search')).to_be_hidden()
                summary.click()
                page.evaluate("location.hash='#/civil/186'")
                expect(page.locator('#art-186')).to_be_visible()
                assert page.evaluate("document.body.style.position") != 'fixed'
                assert not errors, errors
                context.close()
        browser.close()
        print('PASS: 320/390, reduced motion, modal focus, four close methods, immediate preferences, scroll continuity, search and desktop resize.')
finally:
    server.shutdown()
    server.server_close()
    thread.join()
