"""Shared control geometry and privacy disclosure across viewport sizes/themes."""
from pathlib import Path
import functools
import http.server
import json
import threading
from playwright.sync_api import sync_playwright, expect
from support import chromium_executable

ROOT = Path(__file__).resolve().parents[2]


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
original = json.loads((ROOT/'data/amendments/candidate/documents/ec-141.json').read_text(encoding='utf8'))
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable())
        for width in (320, 390, 981, 1456):
            for dark in (False, True):
                context = browser.new_context(viewport={'width': width, 'height': 830}, service_workers='block', reduced_motion='reduce')
                context.add_init_script("localStorage.setItem('lexa-theme'," + json.dumps('dark' if dark else 'light') + ")")
                page = context.new_page()
                page.goto(base+'#/sobre-e-ajustes')
                expect(page.locator('#privacy-title')).to_be_visible()
                expect(page.locator('footer a[href="#/privacidade"]')).to_have_count(0)
                disclosure = page.locator('.privacy-details > summary')
                disclosure.press('Enter')
                contact = page.locator('.privacy-document .privacy-contact')
                expect(contact).to_be_visible()
                assert contact.evaluate("el=>getComputedStyle(el).display==='inline' && parseFloat(getComputedStyle(el).paddingLeft)===0 && parseFloat(getComputedStyle(el).borderLeftWidth)===0")
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                context.set_offline(True)
                contact.click()
                expect(page.locator('#toast')).to_contain_text('O formulário precisa de internet')
                context.set_offline(False)
                disclosure.press('Enter')
                expect(contact).to_be_hidden()
                page.goto(base+'#/emendas/141')
                expect(page.locator('.reader-top h1')).to_have_text('Emenda Constitucional nº 141')
                expect(page.locator('.amendment-preamble')).to_have_text(original['preamble']['text'].strip())
                assert page.locator('.amendment-preamble').evaluate("el=>!/^\\s/.test(el.textContent) && getComputedStyle(el).whiteSpace==='normal'")
                # The index keeps its navigation target without a duplicate label.
                expect(page.locator('#index-list [data-section="1"] small')).to_have_count(0)
                summary = page.locator('#art-1 .article-copy > summary')
                summary.scroll_into_view_if_needed()
                assert summary.evaluate("el=>getComputedStyle(el).display==='inline-flex' && getComputedStyle(el).alignItems==='center'")
                summary.press('Enter')
                expect(page.locator('#art-1 [data-copy-text]')).to_be_visible()
                page.keyboard.press('Escape')
                expect(page.locator('#art-1 [data-copy-text]')).to_be_hidden()
                expect(summary).to_be_focused()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.goto(base)
                expect(page.locator('#library-search')).to_be_visible()
                icon = page.locator('.hero-search > span[aria-hidden]')
                assert icon.evaluate("el=>{const a=el.getBoundingClientRect(),b=el.parentElement.getBoundingClientRect();return Math.abs(a.y+a.height/2-b.y-b.height/2)<2 && getComputedStyle(el,'::before').borderTopStyle==='solid';}")
                context.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print('Polimento UI: privacidade expansível, link inline, preâmbulo, índice, cópia por teclado e lupa; quatro larguras e dois temas aprovados.')
