"""The mobile index reuses the hierarchy and preserves reader position."""
from pathlib import Path
import functools
import http.server
import threading
from playwright.sync_api import sync_playwright, expect
from support import artifact_path, chromium_executable


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


root = Path(__file__).resolve().parents[2]
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(root/'dist')))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), args=['--no-sandbox', '--no-proxy-server'])
        for width in (320, 390):
            for motion in ('reduce', 'no-preference'):
                context = browser.new_context(viewport={'width': width, 'height': 812}, has_touch=True, reduced_motion=motion, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(base+'#/cf/5')
                anchor = page.locator('#art-5 .legal-unit').nth(4)
                anchor.scroll_into_view_if_needed()
                page.wait_for_function("Math.abs(document.querySelector('.reading-controls').getBoundingClientRect().top)<1")
                before = anchor.bounding_box()['y']
                position = page.evaluate('scrollY')
                tree = page.locator('#index-list').element_handle()
                trigger = page.locator('.mobile-index-toggle')
                panel = page.locator('.reader-index-panel')
                close = page.get_by_role('button', name='Fechar índice', exact=True)

                def open_index():
                    trigger.click()
                    expect(panel).to_be_visible()
                    panel.evaluate('el=>Promise.all(el.getAnimations().map(animation=>animation.finished))')
                    expect(close).to_be_focused()

                trigger.focus()
                page.keyboard.press('Enter')
                expect(panel).to_be_visible()
                panel.evaluate('el=>Promise.all(el.getAnimations().map(animation=>animation.finished))')
                expect(close).to_be_focused()
                expect(trigger).to_have_attribute('aria-expanded', 'true')
                expect(page.locator('#index-list [aria-current="location"]')).to_be_visible()
                assert tree.evaluate('el=>el===document.querySelector("#index-list")')
                assert abs(anchor.bounding_box()['y']-before) < 2
                assert page.locator('#index-list').count() == 1
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.keyboard.press('Shift+Tab')
                assert page.evaluate('document.activeElement.closest(".reader-index-panel")!==null')
                page.keyboard.press('Tab')
                expect(close).to_be_focused()
                page.screenshot(path=artifact_path(f'index-open-{width}-{motion}.png'))
                page.locator('#index-list details').evaluate_all('nodes=>nodes.forEach(el=>el.open=true)')
                body = page.locator('.index-panel-body')
                top = body.evaluate('el=>el.scrollTop')
                body.hover()
                page.mouse.wheel(0, 500)
                page.wait_for_function('top=>document.querySelector(".index-panel-body").scrollTop>top', arg=top)
                assert abs(anchor.bounding_box()['y']-before) < 2
                page.keyboard.press('Escape')
                expect(panel).to_be_hidden()
                expect(trigger).to_be_focused()
                assert abs(page.evaluate('scrollY')-position) < 2
                assert abs(anchor.bounding_box()['y']-before) < 2
                open_index()
                page.mouse.click(4, 100)
                expect(panel).to_be_hidden()
                expect(trigger).to_be_focused()
                open_index()
                heading = page.locator('.index-panel-heading').bounding_box()
                x, y = heading['x']+70, heading['y']+20
                session = context.new_cdp_session(page)
                session.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                session.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x+85, 'y': y+2}]})
                session.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                expect(panel).to_be_hidden()
                expect(trigger).to_be_focused()
                open_index()
                close.press('Enter')
                expect(panel).to_be_hidden()
                assert abs(page.evaluate('scrollY')-position) < 2
                page.locator('#focus-mode').click()
                open_index()
                close.click()
                expect(page.locator('#focus-mode')).to_have_attribute('aria-pressed', 'true')
                page.locator('#focus-mode').click()
                page.locator('.reading-settings>summary').click()
                expect(page.locator('.reading-sheet')).to_be_visible()
                page.keyboard.press('Escape')
                open_index()
                expect(page.locator('.reading-sheet')).to_be_hidden()
                page.locator('#index-list .index-entry').first.focus()
                page.keyboard.press('Enter')
                expect(panel).to_be_hidden()
                expect(page.locator('#articles .article .article-heading>a').first).to_be_focused()
                page.wait_for_function("document.querySelector('#articles .article').getBoundingClientRect().top>=document.querySelector('.reading-controls').getBoundingClientRect().bottom")
                open_index()
                page.set_viewport_size({'width': 1366, 'height': 900})
                expect(panel).to_be_hidden()
                assert page.locator('.reader-layout>aside #index-list').count() == 1
                assert page.evaluate('document.body.style.position') != 'fixed'
                page.locator('.reader-index').evaluate('el=>el.open=true')
                expect(page.locator('#index-list')).to_be_visible()
                page.set_viewport_size({'width': width, 'height': 812})
                open_index()
                page.evaluate("location.hash='#/sv/13'")
                expect(page.locator('#art-13')).to_be_visible()
                assert page.evaluate('document.body.style.position') != 'fixed'
                assert not errors, errors
                context.close()
        browser.close()
        print('PASS mobile index: 320/390, keyboard, independent scroll, four close methods, touch swipe, current location, selection, focus mode, settings, desktop and cleanup.')
finally:
    server.shutdown()
    server.server_close()
    thread.join()
