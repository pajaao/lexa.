"""Fresh visits are partial; visited content and explicit full downloads work offline."""
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
from support import chromium_executable
from performance import BenchmarkServer, library_ready, reader_ready

server=BenchmarkServer(Path(__file__).resolve().parents[2]/'dist')
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  context=browser.new_context();page=context.new_page();page.set_default_timeout(90000)
  errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  requests=[];page.on('request',lambda request:requests.append(request.url))
  base=f'http://127.0.0.1:{server.server_port}/'
  page.goto(base);library_ready(page,14)
  page.wait_for_function("navigator.serviceWorker.controller && document.querySelector('#pwa-status').dataset.offlineMode==='partial'")
  assert not any('/data/' in url for url in requests),requests
  page.goto(base+'#/civil/186');reader_ready(page)
  page.wait_for_function("document.querySelector('#pwa-available').textContent.includes('Código Civil')")
  context.set_offline(True);page.reload();reader_ready(page)
  assert 'Art. 186' in page.locator('#articles').inner_text()
  context.set_offline(False)
  page.locator('.pwa-help').evaluate('(el)=>el.open=true')
  page.locator('#pwa-cache-all').click()
  page.wait_for_function("document.querySelector('#pwa-status').dataset.offlineMode==='full'")
  context.set_offline(True);page.goto(base+'#/cpc/1');reader_ready(page)
  page.goto(base);library_ready(page,14)
  page.locator('#library-search').fill('dignidade')
  page.wait_for_function("document.querySelectorAll('.text-result-group').length===12")
  assert not errors,errors
  browser.close()
 print('Política offline: primeira visita sem JSON jurídico, norma consultada preservada e preparo explícito permite leitor e busca global sem rede.')
finally:server.shutdown();server.server_close();thread.join()
