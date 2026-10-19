"""A partial edition survives an update with another reader tab still open."""
from pathlib import Path
import hashlib,json,re,shutil,tempfile,threading
from playwright.sync_api import sync_playwright,expect
from support import chromium_executable
from performance import BenchmarkServer,reader_ready

with tempfile.TemporaryDirectory() as directory:
 site=Path(directory)/'site';shutil.copytree(Path(__file__).resolve().parents[2]/'dist',site,ignore=shutil.ignore_patterns('*.pdf'))
 server=BenchmarkServer(site);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
   context=browser.new_context();page=context.new_page();page.set_default_timeout(30000)
   base=f'http://127.0.0.1:{server.server_port}/'
   page.goto(base+'#/civil/186');reader_ready(page)
   page.wait_for_function("navigator.serviceWorker.controller && document.querySelector('#pwa-available').textContent.includes('Código Civil')")
   other=context.new_page();other.goto(base+'#/civil/186');reader_ready(other)
   old_module=other.locator('script[type=module]').get_attribute('src')
   old_namespace=next((site/'app').iterdir()).name
   new_namespace=hashlib.sha256(b'new-native-namespace').hexdigest()
   shutil.copytree(site/'app'/old_namespace,site/'app'/new_namespace);shutil.rmtree(site/'app'/old_namespace)
   html=(site/'index.html').read_text(encoding='utf-8').replace(old_namespace,new_namespace).replace('<body','<body data-test-version="partial-v2"',1);(site/'index.html').write_bytes(html.encode('utf-8'))
   worker=(site/'sw.js').read_text(encoding='utf-8');worker=re.sub(r"const VERSION = '[a-f0-9]{64}'",f"const VERSION = '{hashlib.sha256(b'partial-v2').hexdigest()}'",worker)
   specs=json.loads(re.search(r'const INTEGRITY = ([^;]+);',worker)[1])
   for spec in specs:
    spec['file']=spec['file'].replace(old_namespace,new_namespace)
    if spec['file']=='index.html':spec['sha256']=hashlib.sha256((site/'index.html').read_bytes()).hexdigest()
   worker=re.sub(r'const INTEGRITY = [^;]+;',lambda _: 'const INTEGRITY = '+json.dumps(specs)+';',worker);(site/'sw.js').write_bytes(worker.encode('utf-8'))
   audit=server.begin()
   page.evaluate('async()=>{await (await navigator.serviceWorker.getRegistration()).update()}')
   expect(page.locator('#pwa-update')).to_be_visible(timeout=30000)
   with page.expect_navigation():page.locator('#pwa-refresh').click()
   expect(page.locator('body')).to_have_attribute('data-test-version','partial-v2')
   expect(page.locator('#pwa-status')).to_have_attribute('data-offline-mode','partial')
   context.set_offline(True);page.reload();reader_ready(page)
   assert 'Art. 186' in page.locator('#articles').inner_text()
   assert other.evaluate('(url)=>fetch(url).then(response=>response.ok)',old_module)
   assert other.locator('body').get_attribute('data-test-version') is None
   assert page.evaluate("async()=> (await caches.keys()).filter(key=>key.startsWith('lexa-offline:')).length") == 2
   browser.close()
  print('Atualização parcial: norma consultada preservada offline, outra aba continua na edição anterior e caches limitados a duas edições.')
 finally:server.shutdown();server.server_close();thread.join()
