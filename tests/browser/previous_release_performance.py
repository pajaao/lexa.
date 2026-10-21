"""Record local cold-load/panel observations and verify candidate history offline."""
from pathlib import Path
import functools
import http.server
import json
import statistics
import threading
import time
from playwright.sync_api import sync_playwright,expect
from support import chromium_executable

ROOT=Path(__file__).resolve().parents[2]
SITE=ROOT/'test-results/previous-wordings-release/site'


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(SITE)))
threading.Thread(target=server.serve_forever,daemon=True).start()
samples=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--no-proxy-server'])
        for index in range(5):
            context=browser.new_context(viewport={'width':390,'height':850})
            page=context.new_page(); start=time.perf_counter()
            page.goto(f'http://127.0.0.1:{server.server_port}/#/cf/6')
            button=page.locator('#art-6 [data-legislative-history]');expect(button).to_be_visible()
            load=(time.perf_counter()-start)*1000
            start=time.perf_counter();button.click();expect(page.locator('.legislative-panel')).to_be_visible()
            opened=(time.perf_counter()-start)*1000
            expected=page.locator('.legislative-text').all_text_contents()
            page.keyboard.press('Escape')
            if index==0:
                page.wait_for_function('navigator.serviceWorker.controller !== null')
                context.set_offline(True);page.reload()
                page.locator('#art-6 [data-legislative-history]').click()
                expect(page.locator('.legislative-text')).to_have_text(expected)
                page.keyboard.press('Escape')
                context.set_offline(False)
            samples.append(dict(coldLoadMs=round(load,2),panelOpenMs=round(opened,2)))
            context.close()
        browser.close()
finally:
    server.shutdown();server.server_close()
result=dict(environment='Local Chromium, localhost, 390px, fresh contexts, no throttling; not a mobile network estimate',
            samples=samples,medianColdLoadMs=statistics.median(s['coldLoadMs'] for s in samples),
            medianPanelOpenMs=statistics.median(s['panelOpenMs'] for s in samples),offlineHistory='PASS')
(ROOT/'test-results/previous-wordings-ux/release-browser-performance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
