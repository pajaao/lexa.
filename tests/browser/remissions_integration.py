"""Optional infrastructure only: SHA, lazy/offline loading and two real legal editions."""
from pathlib import Path
import json,shutil,subprocess,tempfile,threading,sys
from playwright.sync_api import sync_playwright,expect,Error as PlaywrightError
from support import chromium_executable
from performance import BenchmarkServer,BenchmarkHandler,library_ready,reader_ready
ROOT=Path(__file__).resolve().parents[2]
CALL="""async()=>{
 const base=document.querySelector('script[type=module][src]').src;
 const {loadRemissions}=await import(new URL('optional/remissions-runtime.js',base));
 const [store,second]=await Promise.all([loadRemissions(),loadRemissions()]);if(store!==second)throw Error('duplicate store');
 return {generation:store.generation,edition:store.edition,targets:store.outgoing('civil','927').map(e=>store.norm(e[2])+'/'+e[3]),incoming:store.incoming('civil','186').some(e=>store.norm(e[0])==='civil'&&e[1]==='927'),empty:!store.hasConnections('civil','999999')};
}"""
FRESH="""async()=>{
 const base=document.querySelector('script[type=module][src]').src;
 const [{initialCatalog},{fetchVerifiedJson},{createRemissionsLoader}]=await Promise.all([import(new URL('collections.js',base)),import(new URL('loading.js',base)),import(new URL('optional/remissions.js',base))]);
 const store=await createRemissionsLoader({catalog:initialCatalog,fetchJSON:fetchVerifiedJson})();
 return {generation:store.generation,edition:store.edition};
}"""
with tempfile.TemporaryDirectory(prefix='lexa-remissions-') as directory:
 root=Path(directory);subprocess.run(['node',str(ROOT/'tests/browser/build_remissions_fixtures.mjs'),str(root)],check=True,cwd=ROOT)
 meta=json.loads((root/'meta.json').read_text());site=root/'site';shutil.copytree(root/'v1',site)
 server=BenchmarkServer(site);server.paths=[]
 class AuditHandler(BenchmarkHandler):
  def do_GET(self):
   self.server.paths.append(self.path);super().do_GET()
 server.RequestHandlerClass=AuditHandler
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 base=f'http://127.0.0.1:{server.server_port}/'
 def replace(name):
  shutil.rmtree(site);shutil.copytree(root/name,site)
 def home(context):
  page=context.new_page();page.set_default_timeout(45000);page.goto(base);library_ready(page,14);return page
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
   context=browser.new_context();requests=[];context.on('request',lambda req:requests.append(req.url));page=home(context)
   page.wait_for_function("navigator.serviceWorker.controller&&document.querySelector('#pwa-status').dataset.offlineMode==='partial'")
   assert not any('/data/' in u or '/optional/' in u for u in requests),requests
   result=page.evaluate(CALL);assert result['targets']==['civil/186','civil/187'] and result['incoming'] and result['empty']
   assert len([u for u in server.paths if '/data/remissions.' in u])==1,server.paths
   assert not any('/data/civil.' in u or '/data/cpc.' in u for u in requests)
   context.set_offline(True);page.reload();library_ready(page,14);assert page.evaluate(CALL)['generation']==result['generation']
   page.goto(base+'#/civil/186');expect(page.locator('.load-error')).to_be_visible() if page.locator('.load-error').count() else page.wait_for_function("document.querySelector('#app').textContent.includes('Não foi possível')")
   page.goto(base);library_ready(page,14);assert page.evaluate(CALL)['generation']==result['generation'];context.set_offline(False)
   print('PASS lazy: instalação sem remissões, uma requisição explícita, índice offline sem textos de destino.',flush=True)
   other=home(context);assert other.evaluate(CALL)['generation']==result['generation']
   replace('v2');page.evaluate('async()=>{await(await navigator.serviceWorker.getRegistration()).update()}');expect(page.locator('#pwa-update')).to_be_visible()
   assert page.evaluate(CALL)['generation']==result['generation'];assert other.evaluate(CALL)['generation']==result['generation']
   with page.expect_navigation():page.locator('#pwa-refresh').click()
   library_ready(page,14);new=page.evaluate(CALL);assert new['generation']!=result['generation']
   context.set_offline(True);old=other.evaluate(FRESH);assert old['generation']==result['generation'];assert old['edition']!=new['edition']
   assert page.evaluate(FRESH)['generation']==new['generation']
   context.close();print('PASS update: consentimento, duas abas/edições jurídicas e índices antigos/novos isolados offline.',flush=True)
   # Network and SHA failures without a service-worker cache hiding the fault.
   for mode in ['network','sha']:
    c=browser.new_context(service_workers='block');q=home(c)
    if mode=='network':q.route('**/data/remissions.*.json',lambda route:route.abort())
    else:q.route('**/data/remissions.*.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
    try:
     q.evaluate(CALL);raise AssertionError('Expected explicit loading failure')
    except PlaywrightError as error:
     message=str(error)
     if mode=='sha':assert 'não corresponde' in message,message
     else:assert 'fetch' in message.lower(),message
    q.unroute('**/data/remissions.*.json');assert q.evaluate(CALL)['targets']==['civil/186','civil/187'];c.close()
   print('PASS errors: falha de rede e SHA sem grafo parcial, recuperação após nova tentativa.',flush=True)
   c=browser.new_context();q=home(c);q.wait_for_function('navigator.serviceWorker.controller');q.locator('.pwa-help').evaluate('(el)=>el.open=true');q.locator('#pwa-cache-all').click();q.wait_for_function("document.querySelector('#pwa-status').dataset.offlineMode==='full'")
   c.set_offline(True);assert q.evaluate(CALL)['targets']==['civil/186','civil/187'];q.goto(base+'#/civil/186');reader_ready(q);c.close()
   print('PASS full: preparo explícito inclui índice, módulos opcionais e normas de destino.',flush=True)
   replace('disabled');c=browser.new_context();seen=[];c.on('request',lambda req:seen.append(req.url));q=home(c);q.wait_for_function('navigator.serviceWorker.controller')
   assert not any('remissions' in u for u in seen),seen
   catalog=q.evaluate('async()=>{const {initialCatalog}=await import(new URL("collections.js",document.querySelector("script[type=module][src]").src));return initialCatalog}');assert 'remissions' not in catalog;c.close()
   print('PASS disabled: build padrão sem índice, módulos opcionais ou nova interface.',flush=True)
   browser.close()
 finally:server.shutdown();server.server_close();thread.join()
