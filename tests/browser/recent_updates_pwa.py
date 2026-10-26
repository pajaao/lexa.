"""Build-derived summaries stay tied to the edition, including PWA updates."""
from pathlib import Path
import json,subprocess,tempfile,threading
from playwright.sync_api import sync_playwright,expect
from support import chromium_executable
from performance import BenchmarkServer
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as directory:
 folder=Path(directory);old=folder/'old';new=folder/'new'
 # Real recorded history in two test builds; legal source files are never edited.
 subprocess.run(['node','--input-type=module','-e',"""
 import {stagePages} from './scripts/build-pages.mjs';
 import {updateHistory} from './data/history/legislation.js';
 import {sumulaUpdates} from './data/history/sumulas.js';
 const history=[...updateHistory,...sumulaUpdates];
 await stagePages(process.argv[1],{history:history.filter(event=>event.kind!=='text')});
 await stagePages(process.argv[2],{history});
 """,str(old),str(new)],cwd=root,check=True,stdout=subprocess.DEVNULL)
 expected=json.loads((new/'catalog.json').read_text(encoding='utf-8'))['recentUpdates']
 assert expected,'O histórico de teste deve conter ao menos uma diferença textual real registrada.'
 server=BenchmarkServer(old);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server']);context=browser.new_context();page=context.new_page();page.set_default_timeout(30000);errors=[]
   page.on('pageerror',lambda error:errors.append(str(error)))
   base=f'http://127.0.0.1:{server.server_port}/'
   page.goto(base);expect(page.locator('#cards .code-card')).to_have_count(14)
   expect(page.locator('.legislative-indicator')).to_have_count(0)
   expect(page.locator('.legislative-indicator')).to_have_count(0)
   expect(page.locator('.hero-note')).not_to_contain_text('Alterações registradas')
   page.wait_for_function("navigator.serviceWorker.controller && document.querySelector('#pwa-status').dataset.offlineMode==='partial'")
   page.goto(base+'#/sobre-e-ajustes');page.locator('.pwa-help').evaluate('(element)=>element.open=true');page.locator('#pwa-cache-all').click()
   expect(page.locator('#pwa-status')).to_have_attribute('data-offline-mode','full',timeout=90000)
   page.goto(base)
   context.set_offline(True);server.directory=new.resolve();context.set_offline(False)
   page.evaluate('async()=>{await (await navigator.serviceWorker.getRegistration()).update()}')
   expect(page.locator('#pwa-update')).to_be_visible(timeout=60000)
   # Cached new files cannot silently change the old page's edition.
   expect(page.locator('.legislative-indicator')).to_have_count(0)
   with page.expect_navigation():page.locator('#pwa-refresh').click()
   expect(page.locator('.legislative-indicator')).to_have_count(1)
   expect(page.locator('.legislative-indicator')).to_have_attribute('href','#/atualizacoes')
   context.set_offline(True);page.reload()
   expect(page.locator('.legislative-indicator')).to_have_count(1)
   page.locator('.legislative-indicator').click()
   expect(page.locator('#history-code')).to_have_value('')
   expect(page.locator('#history-article')).to_have_value('')
   expect(page.locator('.article-change')).not_to_have_count(0)
   page.goto(base);expect(page.locator('.legislative-indicator')).to_have_count(1)
   fresh=browser.new_context();initial=fresh.new_page();initial.goto(base)
   initial.wait_for_function("navigator.serviceWorker.controller && document.querySelector('#pwa-status').dataset.offlineMode==='partial'")
   expect(initial.locator('.legislative-indicator')).to_have_count(1)
   assert initial.evaluate('''async()=>{
    const keys=await caches.keys();
    const files=(await Promise.all(keys.map(async key=>(await (await caches.open(key)).keys()).map(request=>request.url)))).flat();
    return files.every(url=>!url.includes('/data/'));
   }''')
   fresh.set_offline(True);initial.reload();expect(initial.locator('.legislative-indicator')).to_have_count(1);fresh.close()
   assert not errors,errors
   browser.close();print('Resumo PWA: edição sem diferenças neutra; atualização consentida traz eventos reais da mesma edição; resumo e detalhes funcionam offline e permanecem após consulta.')
 finally:server.shutdown();server.server_close();thread.join()
