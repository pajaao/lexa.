"""Exercise new federal laws in search, reader, hierarchy, favorites and copy."""
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
  b=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  page=b.new_page(viewport={'width':390,'height':900},service_workers='block');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  base=f'http://127.0.0.1:{server.server_port}/'
  cases=[('clt','1','Art. 1 CLT','Esta Consolidação estatui'),('cpp','3-A','Art. 3-A CPP','estrutura acusatória'),('eca','18-B','Art. 18-B ECA','castigo físico'),('lep','1','Art. 1 LEP','execução penal'),('maria-penha','24-A','Art. 24-A LMP','medidas protetivas'),('improbidade','11','Art. 11 LIA','princípios'),('licitacoes','178','Art. 178 LLCA','337-P')]
  for code,id,query,text in cases:
   page.goto(base);page.locator('#library-search').fill(query);expect(page.locator('#quick-reference a')).to_have_attribute('href',f'#/{code}/{id}')
   page.locator('#quick-reference a').click();expect(page.locator('#art-'+id)).to_contain_text(text,ignore_case=True)
   assert page.locator('.legal-heading').count()>0
   page.locator(f'[data-save="{id}"]').click()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.goto(base+'#/favoritos');expect(page.locator('.favorite-group')).to_have_count(7)
  for code,final in [('clt','922'),('cpp','811'),('eca','267'),('lep','204'),('maria-penha','46'),('improbidade','25'),('licitacoes','194')]:
   page.goto(base+f'#/{code}/{final}');expect(page.locator('#art-'+final)).to_be_visible()
  assert not errors,errors
  b.close();print('Sete normas validadas: referências, artigos com letras, texto, divisões, favoritos, artigos finais e tela de celular.')
finally:server.shutdown();server.server_close()
