"""Validate clipboard interaction, denied permission fallback and mobile layout."""
from pathlib import Path
import functools,http.server,threading
from support import chromium_executable
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  context=browser.new_context(permissions=['clipboard-read','clipboard-write'],service_workers='block')
  page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  base=f'http://127.0.0.1:{server.server_port}/'
  for route,ident,expected in [('civil','186','aquele que'),('cf','adct-1','ADCT'),('sv','9','Cancelada'),('ctn','52','52 a 58')]:
   page.goto(base+f'#/{route}/{ident}')
   article=page.locator('#art-'+ident);expect(article).to_be_visible()
   article.locator('.article-copy>summary').click();article.locator('[data-copy-text]').click()
   expect(page.locator('#toast')).to_contain_text('Texto e referência copiados')
   text=page.evaluate('navigator.clipboard.readText()')
   assert expected.lower() in text.lower()
   assert 'Fonte oficial para conferência: https://' in text
   assert base+f'#/{route}/{ident}' in text
   assert not article.locator('.article-copy').evaluate('e=>e.open')
   article.locator('.article-copy>summary').click();article.locator('[data-copy]').click()
   assert page.evaluate('navigator.clipboard.readText()')==base+f'#/{route}/{ident}'
  # An actual rejected API call must open selectable content without navigation.
  page.evaluate("()=>{navigator.clipboard.writeText=()=>Promise.reject(new Error('denied'));}")
  page.goto(base+'#/cf/5');page.locator('#focus-mode').click();page.locator('#art-5 .article-copy>summary').click();page.locator('#art-5 [data-copy-text]').click()
  expect(page.locator('#copy-dialog')).to_be_visible()
  assert 'Art. 5' in page.locator('#copy-content').input_value()
  assert page.locator('#copy-content').input_value().endswith(base+'#/cf/5')
  page.locator('#copy-select').click()
  assert page.locator('#copy-content').evaluate('e=>e.selectionEnd-e.selectionStart===e.value.length')
  for width in [320,390,1280]:
   page.set_viewport_size({'width':width,'height':900})
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
   assert page.locator('#copy-dialog').bounding_box()['width']<=width
   page.screenshot(path=f'/tmp/lexa-copy-dialog-{width}.png')
  page.keyboard.press('Escape');expect(page.locator('#copy-dialog')).not_to_be_visible()
  assert page.locator('body').evaluate("e=>e.classList.contains('reading-focus')")
  page.keyboard.press('Escape');assert page.locator('#art-5 .article-copy').evaluate('e=>!e.open')
  page.keyboard.press('Escape');assert page.locator('body').evaluate("e=>!e.classList.contains('reading-focus')")
  page.goto(base+'#/sv/13')
  for width in [320,390,1280]:
   page.set_viewport_size({'width':width,'height':900})
   page.locator('#art-13 .article-copy>summary').click()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
   page.screenshot(path=f'/tmp/lexa-copy-menu-{width}.png')
   page.locator('#art-13 .article-copy>summary').click()
  assert not errors,errors
  browser.close();print('Cópia validada: texto e link reais, CF/ADCT, súmulas, intervalo agrupado, permissão negada, seleção manual e telas menores.')
finally:server.shutdown();server.server_close()
