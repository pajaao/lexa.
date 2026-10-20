"""Validate existing favorites and compact reading controls in real Chromium."""
from pathlib import Path
import functools,http.server,threading
from support import artifact_path, chromium_executable
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  context=browser.new_context(service_workers='block',viewport={'width':390,'height':844});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  base=f'http://127.0.0.1:{server.server_port}/'
  page.goto(base)
  page.evaluate("localStorage.setItem('lexa-saved',JSON.stringify(['cf/60','cf/adct-1','civil/186','sv/13','sv/9','cf/60','unknown/1','cf/99999']))")
  page.reload();page.goto(base+'#/favoritos')
  expect(page.locator('#favorites-count')).to_have_text('7 favoritos')
  assert page.locator('.favorite-group').count()==4
  expect(page.locator('.favorite-link[href="#/sv/9"]').locator('..').locator('.favorite-status')).to_contain_text('Cancelada')
  assert page.locator('.favorite-link[href="#/cf/adct-1"]').count()==1
  assert page.locator('.favorite-link[href="#/sv/13"]').count()==1
  assert 'não foi encontrada' in page.locator('[data-remove-favorite="cf/99999"]').locator('..').inner_text()
  page.locator('#favorites-search').fill('Art. 186 CC');expect(page.locator('#favorites-count')).to_have_text('1 favorito encontrado')
  page.locator('.favorite-link').click();expect(page.locator('#art-186')).to_be_visible()
  assert not page.locator('.reading-settings').evaluate('e=>e.open')
  assert page.locator('#font-up').is_hidden()
  assert page.locator('.reading-controls').bounding_box()['height']<170
  page.locator('.reading-settings>summary').click();page.locator('#font-up').click()
  expect(page.locator('#font-size')).to_have_text('20 px')
  page.locator('#reading-spacing').select_option('wide')
  page.locator('.sheet-close').click()
  assert page.locator('#font-up').is_hidden()
  page.reload();expect(page.locator('#font-size')).to_have_text('20 px')
  page.locator('.reading-settings>summary').click();assert page.locator('#reading-spacing').input_value()=='wide'
  page.locator('.sheet-close').click()
  page.locator('[data-save="186"]').click()
  page.goto(base+'#/favoritos');assert page.locator('.favorite-link[href="#/civil/186"]').count()==0
  page.locator('[data-remove-favorite="cf/60"]').click();page.reload()
  assert page.locator('.favorite-link[href="#/cf/60"]').count()==0
  assert not page.evaluate("JSON.parse(localStorage.getItem('lexa-saved')).includes('cf/60')")
  page.locator('#favorites-search').fill('nenhumresultado');expect(page.locator('.favorites-empty')).to_contain_text('Nenhum favorito encontrado')
  page.locator('#favorites-search').fill('')
  for width in [320,390,1280]:
   page.set_viewport_size({'width':width,'height':900})
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('favorites',width)
   page.screenshot(path=artifact_path(f'lexa-favorites-{width}.png'))
   page.goto(base+'#/cf/5');expect(page.locator('#art-5')).to_be_visible()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('reading',width)
   page.screenshot(path=artifact_path(f'lexa-compact-{width}.png'))
   page.goto(base+'#/favoritos')
  while page.locator('[data-remove-favorite]').count():page.locator('[data-remove-favorite]').first.click()
  expect(page.locator('.favorites-empty')).to_contain_text('Nenhum favorito salvo')
  page.reload();expect(page.locator('#favorites-count')).to_have_text('0 favoritos')
  assert not errors,errors
  browser.close();print('Favoritos e barra compacta validados: marcações antigas, agrupamento, ADCT, súmulas, busca, remoção, persistência, estado vazio e telas de 320/390/1280px.')
finally:server.shutdown();server.server_close()
