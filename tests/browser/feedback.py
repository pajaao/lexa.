"""Feedback links: context, keyboard, safe popup and real PWA offline reading.
Run npm run build first. External online destinations are stubbed; never submit.
"""
from pathlib import Path
import functools
import http.server
import threading
from urllib.parse import urlsplit, parse_qs
from playwright.sync_api import sync_playwright, expect
from support import chromium_executable

ROOT=Path(__file__).resolve().parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'dist')))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}/'
external='https://docs.google.com/forms/**'

def state(page):
    return page.evaluate('({url:location.href,y:scrollY})')

def activate(page,link):
    expect(link).to_have_attribute('target','_blank')
    expect(link).to_have_attribute('rel','noopener noreferrer')
    link.scroll_into_view_if_needed();link.focus();expect(link).to_be_focused()
    before=state(page)
    with page.expect_popup() as opened: page.keyboard.press('Enter')
    popup=opened.value;popup.wait_for_load_state()
    assert popup.evaluate('window.opener===null')
    popup.close();assert state(page)==before

try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--no-proxy-server'])
        for width in (390,1280):
            context=browser.new_context(viewport={'width':width,'height':900})
            context.route(external,lambda route:route.fulfill(body='External destination stub',content_type='text/html'))
            context.route('https://forms.gle/**',lambda route:route.fulfill(body='General feedback stub',content_type='text/html'))
            page=context.new_page()
            for code,article,query in [('penal','215','?q=fraude'),('cf','adct-1',''),('cpc','1042',''),('sv','13','')]:
                page.goto(base+f'#/{code}/{article}{query}')
                expect(page.locator('#art-'+article)).to_be_visible()
                link=page.locator('#art-'+article+' .article-feedback')
                params=parse_qs(urlsplit(link.get_attribute('href')).query)
                assert params['entry.1354902092']==[f'https://pajaao.github.io/lexa./#/{code}/{article}']
                assert params['usp']==['pp_url']
                activate(page,link)
            general=page.locator('footer .feedback-link')
            expect(general).to_have_attribute('href','https://forms.gle/2m4zgB2PKf9GdJMv7')
            activate(page,general)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.wait_for_function('navigator.serviceWorker.controller !== null')
            page.locator('.pwa-help>summary').click()
            page.locator('#pwa-cache-all').click()
            expect(page.locator('#pwa-status')).to_have_attribute('data-offline-mode','full',timeout=30000)
            context.unroute(external);context.set_offline(True)
            page.goto(base+'#/penal/215');expect(page.locator('#art-215')).to_be_visible()
            for selector in ['#art-215 .article-feedback','footer .feedback-link']:
                link=page.locator(selector);link.scroll_into_view_if_needed();link.focus()
                before=state(page);page_count=len(context.pages)
                page.keyboard.press('Enter')
                expect(page.locator('#toast')).to_have_text('O formulário precisa de internet. Conecte-se e tente novamente. Sua leitura continua disponível.')
                expect(page.locator('#toast')).to_have_class('visible')
                assert len(context.pages)==page_count
                assert state(page)==before
                expect(link).to_be_focused()
            context.set_offline(False)
            context.route(external,lambda route:route.fulfill(body='External destination stub',content_type='text/html'))
            activate(page,page.locator('#art-215 .article-feedback'))
            expect(page.locator('#art-215')).to_be_visible()
            context.close()
        browser.close()
    print('PASS: safe feedback links, keyboard, canonical context without search, desktop/mobile and offline PWA reading preserved with offline warning/no popup and online recovery; no submission.')
finally:
    server.shutdown();server.server_close();thread.join()
