"""Validate grouped whole-library text search, reader links and responsive UI."""
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
  context=browser.new_context(service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  base=f'http://127.0.0.1:{server.server_port}/'
  page.goto(base);search=page.locator('#library-search');search.fill('dignidade')
  expect(page.locator('.text-result-group')).to_have_count(12)
  assert page.locator('.text-result mark').count()>0
  cf227=page.locator('.text-result[href="#/cf/227?q=dignidade"]')
  assert cf227.locator('del').count()==0
  assert cf227.locator('.search-badge').count()==0
  assert cf227.locator('mark').inner_text()=='dignidade'
  cpc=page.locator('#search-group-cpc').locator('..').locator('..')
  assert cpc.locator('.text-result').count()==4
  cpc.locator('[data-more-code]').click();expect(cpc.locator('.text-result')).to_have_count(10)
  cpc.locator('[data-more-code]').click();expect(cpc.locator('.text-result')).to_have_count(11)
  page.locator('.text-result[href="#/cf/1?q=dignidade"]').click();expect(page.locator('#art-1 mark')).to_have_count(1)
  assert page.locator('#article-search').input_value()=='dignidade'
  page.locator('.reader-top .back').click();expect(search).to_have_value('dignidade')
  page.get_by_role('button',name='Penal',exact=True).click();expect(page.locator('.text-result-group')).to_have_count(4)
  assert page.locator('#search-group-penal').count()==1
  search.fill('Art. 60 CF');expect(page.locator('#quick-reference a')).to_have_attribute('href','#/cf/60')
  assert page.locator('.text-result-group').count()==0
  search.press('Enter');page.wait_for_url('**/#/cf/60');expect(page.locator('#art-60')).to_be_visible()
  page.locator('.reader-top .back').click();search.fill('educacao');expect(page.locator('.text-result-group')).to_have_count(12)
  assert 'Educação' in page.locator('#text-results').inner_text() or 'educação' in page.locator('#text-results').inner_text()
  search.fill('dignidade');expect(page.locator('.text-result-group')).to_have_count(12)
  sv=page.locator('#search-group-sv').locator('..').locator('..')
  expect(sv.locator('.search-badge').first).to_contain_text('precedentes')
  sv.locator('.text-result').first.click();expect(page.locator('.sumula-notes[open]').first).to_be_visible()
  page.locator('.reader-top .back').click();search.fill('a');expect(page.locator('#library-results')).to_contain_text('2 caracteres')
  search.fill('termoquenuncavaiexistirnalexa');expect(page.locator('#text-results')).to_contain_text('Nenhuma ocorrência')
  search.fill('CPC');expect(page.locator('.code-card[href="#/cpc"]')).to_be_visible()
  search.fill('a saúde, o trabalho, o lazer')
  historical=page.locator('.text-result[href^="#/cf/6?q="]')
  expect(historical.locator('.search-badge')).to_have_text('Ocorrência em trecho riscado na fonte')
  assert historical.locator('del mark').count()>0
  search.fill('dignidade');expect(page.locator('.text-result-group')).to_have_count(12)
  search.press('Enter');expect(page.locator('.text-search-heading h2')).to_be_focused()
  for width in [320,390,1280]:
   page.set_viewport_size({'width':width,'height':900})
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
   page.locator('#text-results').scroll_into_view_if_needed();page.screenshot(path=artifact_path(f'lexa-global-search-{width}.png'))
  # Leaving the page while a search is pending cannot run against the next view.
  search.fill('uma busca pendente');page.evaluate("location.hash='#/favoritos'");page.wait_for_timeout(300)
  expect(page.locator('.favorites-page')).to_be_visible()
  assert not errors,errors
  browser.close();print('Busca global validada: grupos, mais resultados, filtros, referências, acentos, notas, destaques no leitor, retorno à busca, vazio e celular.')
finally:server.shutdown();server.server_close()
