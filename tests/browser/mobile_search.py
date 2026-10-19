"""Mobile search is a draft until selection, including filtered reading state."""
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
snapshot = '''()=>({html:document.querySelector('#articles').innerHTML,
 page:document.querySelector('#page-label').textContent,scope:document.querySelector('#reading-scope')?.textContent,
 filter:document.querySelector('#saved-filter').getAttribute('aria-pressed'),
 division:document.querySelector('#clear-section').hidden,hash:location.hash,
 last:localStorage.getItem('lexa-last-reading')})'''
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), args=['--no-sandbox', '--no-proxy-server'])
        for width in (320, 390):
            for motion in ('reduce', 'no-preference'):
                context = browser.new_context(viewport={'width': width, 'height': 812}, reduced_motion=motion, has_touch=True, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(base+'#/civil')
                page.locator('#next-page').click()
                page.wait_for_function("document.querySelector('#page-label').textContent.startsWith('16')")
                page.evaluate('''()=>new Promise(resolve=>{let y=scrollY,n=0;function frame(){n=y===scrollY?n+1:0;y=scrollY;if(n>=3)resolve();else requestAnimationFrame(frame);}requestAnimationFrame(frame);})''')
                page.wait_for_function("JSON.parse(localStorage.getItem('lexa-last-reading')).articleId===document.querySelector('#articles .article').id.slice(4)")
                before = page.evaluate(snapshot)
                position = page.evaluate('scrollY')
                trigger = page.locator('.mobile-search-toggle')
                dialog = page.locator('.reader-search-panel')
                field = page.locator('#article-search')
                cancel = page.get_by_role('button', name='Cancelar', exact=True)
                trigger.focus()
                page.keyboard.press('Enter')
                expect(dialog).to_be_visible()
                expect(field).to_be_focused()
                assert page.locator('#article-search').count() == 1
                field.fill('dignidade')
                expect(page.locator('.reader-search-results mark').first).to_be_visible()
                assert page.evaluate(snapshot) == before
                if width == 390:
                    page.evaluate("document.documentElement.classList.add('dark')")
                page.screenshot(path=artifact_path(f'search-open-{width}-{motion}.png'))
                results = page.locator('.reader-search-results')
                assert results.bounding_box()['height'] > 200
                page.keyboard.press('Tab')
                assert page.evaluate("document.activeElement.closest('.reader-search-panel')!==null")
                page.keyboard.press('Escape')
                expect(dialog).to_be_hidden()
                expect(trigger).to_be_focused()
                assert page.evaluate(snapshot) == before
                assert abs(page.evaluate('scrollY')-position) < 2
                trigger.click()
                expect(field).to_have_value('dignidade')
                page.get_by_role('button', name='Limpar pesquisa', exact=True).click()
                expect(field).to_have_value('')
                expect(page.locator('[data-search-result]')).to_have_count(15)
                page.locator('.reader-search-more').click()
                expect(page.locator('[data-search-result]')).to_have_count(30)
                results.hover()
                page.mouse.wheel(0, 400)
                page.wait_for_function("document.querySelector('.reader-search-results').scrollTop>0")
                assert page.evaluate(snapshot) == before
                cancel.click()
                assert page.evaluate(snapshot) == before
                trigger.click()
                field.fill('Art. 186 CC')
                cancel.click()  # cancel before the 120 ms debounce can commit
                page.wait_for_timeout(180)
                assert page.evaluate(snapshot) == before
                assert abs(page.evaluate('scrollY')-position) < 2
                trigger.click()
                expect(field).to_have_value('Art. 186 CC')
                expect(page.locator('[data-search-result="186"]')).to_be_visible()
                page.set_viewport_size({'width': width, 'height': 500})
                page.wait_for_function("document.querySelector('.reader-search-panel').getBoundingClientRect().bottom<=innerHeight")
                expect(field).to_be_visible()
                expect(cancel).to_be_visible()
                page.screenshot(path=artifact_path(f'search-short-{width}-{motion}.png'))
                field.press('Enter')
                expect(dialog).to_be_hidden()
                expect(page.locator('#art-186')).to_be_visible()
                page.wait_for_function("location.hash.startsWith('#/civil/186?')")
                page.wait_for_function("document.activeElement.closest('#art-186')!==null")
                assert page.locator('#art-186').get_attribute('class').find('focused-article') >= 0
                page.set_viewport_size({'width': width, 'height': 812})
                page.goto(base+'#/cf/5?q=liberdade')
                expect(page.locator('#art-5 mark').first).to_be_visible()
                queried = page.evaluate(snapshot)
                trigger.click()
                field.fill('nenhum-termo-assim')
                expect(page.locator('.reader-search-empty')).to_be_visible()
                cancel.click()
                assert page.evaluate(snapshot) == queried
                expect(field).to_have_value('liberdade')
                trigger.click()
                field.fill('liberdade')
                page.locator('[data-search-result="5"]').click()
                expect(dialog).to_be_hidden()
                expect(page.locator('#art-5 mark').first).to_be_visible()
                page.wait_for_function("document.activeElement.closest('#art-5')!==null")
                page.goto(base+'#/cf/5')
                page.locator('[data-save="5"]').click()
                page.locator('#saved-filter').click()
                page.locator('.mobile-index-toggle').click()
                page.locator('#index-list [aria-current="location"]').click()
                expect(page.locator('#clear-section')).to_be_visible()
                page.wait_for_function("JSON.parse(localStorage.getItem('lexa-last-reading')).articleId==='5'")
                filtered = page.evaluate(snapshot)
                trigger.click()
                field.fill('ADCT art. 1')
                expect(page.locator('.reader-search-status')).to_have_text('0 entradas encontradas')
                assert page.evaluate(snapshot) == filtered
                cancel.click()
                assert page.evaluate(snapshot) == filtered
                page.locator('#saved-filter').click()
                page.locator('#clear-section').click()
                page.locator('#focus-mode').click()
                trigger.click()
                field.fill('ADCT art. 1')
                expect(page.locator('[data-search-result="adct-1"]')).to_be_visible()
                page.locator('[data-search-result="adct-1"]').focus()
                page.keyboard.press('Enter')
                expect(dialog).to_be_hidden()
                expect(page.locator('#reading-scope')).to_have_text('ADCT')
                expect(page.locator('#focus-mode')).to_have_attribute('aria-pressed', 'true')
                expect(page.locator('#art-adct-1')).to_be_visible()
                trigger.click()
                field.fill('zzz-sem-resultado')
                expect(page.locator('.reader-search-empty')).to_be_visible()
                page.set_viewport_size({'width': 1366, 'height': 900})
                expect(trigger).to_have_attribute('aria-controls', 'article-search-field')
                expect(dialog).to_be_hidden()
                expect(field).to_be_visible()
                assert page.evaluate('document.body.style.position') != 'fixed'
                field.fill('ADCT art. 2')
                expect(page.locator('#art-adct-2')).to_be_visible()
                page.set_viewport_size({'width': width, 'height': 812})
                expect(trigger).to_have_attribute('aria-haspopup', 'dialog')
                page.keyboard.press('/')
                expect(field).to_be_focused()
                expect(field).to_have_value('ADCT art. 2')
                page.evaluate("location.hash='#/sv/13'")
                expect(page.locator('#art-13')).to_be_visible()
                assert page.evaluate('document.body.style.position') != 'fixed'
                trigger.click()
                field.fill('Art. 186 CC')
                expect(page.locator('.reader-search-alternative')).to_be_visible()
                page.locator('.reader-search-alternative').click()
                expect(page.locator('#art-186')).to_be_visible()
                assert not errors, errors
                context.close()
        browser.close()
        print('PASS mobile search: 320/390, draft results, selection, clear/cancel, page/division/favorites preserved, keyboard, focus, ADCT, reduced motion, short viewport, desktop and cleanup.')
finally:
    server.shutdown()
    server.server_close()
    thread.join()
