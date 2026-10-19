"""Check hierarchy, chapter filters and unchanged legal wording in Chromium."""
from pathlib import Path
import functools,http.server,threading,json,subprocess
from support import artifact_path, chromium_executable
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2]
model=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import {collections} from './src/data.js'; console.log(JSON.stringify(collections));"],cwd=root))
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  context=browser.new_context(service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  base=f'http://127.0.0.1:{server.server_port}/'
  for code in model:
   page.goto(base+'#/'+code['id'])
   expect(page.locator('.article').first).to_be_visible()
   section=code['sections'][0]
   assert page.locator('.legal-heading').first.inner_text().split('\n')[0] in section['title']
   for article in code['articles'][:15]:
    expected=[''.join(r['text'] for r in para['runs']) for para in article['paragraphs']]
    actual=page.locator('#art-'+article['id']+'>p.legal-unit').all_text_contents()
    assert actual==expected,(code['id'],article['id'])
   assert page.locator('#index-list [aria-current="location"]').count()==1
   if code['id'] in ['civil','cpc']:
    assert page.locator('.legal-parte').count() and page.locator('.legal-livro').count() and page.locator('.legal-capitulo').count()
   index_entry=page.locator('#index-list .index-entry').first.element_handle()
   page.locator('#next-page').click()
   assert index_entry.evaluate('(el)=>el.isConnected'),'Índice foi reconstruído durante paginação simples'
   index_entry.dispose()
   assert page.locator('.legal-heading').count()>0
  page.goto(base+'#/civil')
  page.locator('[data-branch]').first.click()
  expect(page.locator('#clear-section')).to_be_visible()
  assert '2083' not in page.locator('#results-label').inner_text().replace('.','')
  page.locator('#clear-section').click()
  assert '2.083' in page.locator('#results-label').inner_text()
  page.locator('#article-search').fill('Art. 186 CC');page.wait_for_timeout(200)
  expect(page.locator('#art-186')).to_be_visible()
  assert page.locator('.legal-parte').count() and page.locator('.legal-livro').count()
  page.goto(base+'#/cf/adct-1');assert 'ADCT' in page.locator('#reading-location').inner_text()
  page.goto(base+'#/cf/5');expect(page.locator('#art-5 .unit-inciso').first).to_be_visible()
  page.locator('#art-5 .unit-paragraph').first.scroll_into_view_if_needed();page.wait_for_timeout(250)
  assert 'DIREITOS' in page.locator('#reading-location').inner_text()
  for width in [320,390,1280]:
   page.set_viewport_size({'width':width,'height':900})
   page.goto(base+'#/civil/1')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
   page.locator('.legal-parte').first.scroll_into_view_if_needed()
   page.screenshot(path=artifact_path(f'lexa-hierarchy-{width}.png'))
  assert not errors,errors
  browser.close();print('Hierarquia validada nas coleções cadastradas: texto preservado, árvore, filtros, paginação, busca, ADCT, posição atual e telas menores.')
finally:server.shutdown();server.server_close()
