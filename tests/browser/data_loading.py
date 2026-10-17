"""Lazy legal data, retry, stale navigation and exact pre-refactor search results."""
from pathlib import Path
import functools,http.server,threading,json
from support import chromium_executable, app_evaluate
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage'])
  context=browser.new_context(service_workers='block');page=context.new_page();errors=[];requested=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  page.on('request',lambda req:requested.append(req.url))
  base=f'http://127.0.0.1:{server.server_port}/'
  page.goto(base);expect(page.locator('#cards .code-card')).to_have_count(14)
  assert not [url for url in requested if '/data/' in url]
  assert app_evaluate(page,'collections.every(code=>!code.loaded)')
  held=[]
  page.route('**/data/cf.*.json',lambda route:held.append(route))
  page.goto(base+'#/cf/5');expect(page.get_by_role('status').filter(has_text='Carregando Constituição')).to_be_visible()
  page.goto(base+'#/favoritos');expect(page.locator('.favorites-empty')).to_be_visible()
  assert len(held)==1;held.pop().continue_();page.unroute('**/data/cf.*.json')
  page.wait_for_timeout(100);expect(page.locator('.favorites-empty')).to_be_visible()
  page.goto(base+'#/cf/5');expect(page.locator('#art-5')).to_be_visible()
  assert not [url for url in requested if '/data/' in url and '/data/cf.' not in url]
  # An invalid response must not enter the model; retry loads the verified edition.
  page.route('**/data/civil.*.json',lambda route:route.fulfill(status=200,body='{}',content_type='application/json'))
  page.goto(base+'#/civil/186');expect(page.locator('#retry-load')).to_be_visible()
  assert app_evaluate(page,"!collections.find(code=>code.id==='civil').loaded")
  page.unroute('**/data/civil.*.json');page.locator('#retry-load').click()
  expect(page.locator('#art-186')).to_be_visible()
  page.goto(base);page.locator('#library-search').fill('dignidade')
  expect(page.locator('.text-result-group')).to_have_count(12)
  actual=app_evaluate(page,"searchLibraryText('dignidade').map(g=>({id:g.code.id,ids:g.matches.map(m=>m.article.id)}))")
  expected=json.loads((root/'tests/fixtures/dignidade-results.json').read_text())
  assert actual==expected
  assert sum(len(group['ids']) for group in actual)==52
  assert app_evaluate(page,'collections.every(code=>code.searchIndex)')
  assert app_evaluate(page,"!collections.find(code=>code.id==='clt').loaded")
  assert not errors,errors
  browser.close();print('Dados: home sem JSON jurídicos, carga por norma, navegação concorrente, integridade/retry e mesmos 52 resultados em 12 coleções.')
finally:server.shutdown();server.server_close()
