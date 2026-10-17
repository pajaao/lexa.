"""Exercise the real service-worker lifecycle on a GitHub Pages-style subpath.
Requires Playwright for Python and /usr/bin/chromium; run npm run build first.
"""
from pathlib import Path
import functools, hashlib, http.server, re, shutil, tempfile, threading, json
from support import chromium_executable
from playwright.sync_api import sync_playwright, expect

root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as temporary:
    site=Path(temporary)/'lexa.'
    shutil.copytree(root/'dist',site)
    failure={'enabled':False};requests=[]
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.webmanifest':'application/manifest+json'}
        def log_message(self,*args):pass
        def end_headers(self):
            self.send_header('Cache-Control','no-store')
            super().end_headers()
        def do_GET(self):
            requests.append(self.path.split('?')[0])
            if failure['enabled'] and self.path.split('?')[0]=='/lexa./index.html':
                self.send_error(503);return
            super().do_GET()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=temporary))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    def deploy(version):
        html=(site/'index.html').read_text()
        html=re.sub(r'<body[^>]*>',f'<body data-test-version="{version}">',html,count=1)
        (site/'index.html').write_text(html)
        worker=(site/'sw.js').read_text()
        worker=re.sub(r"const VERSION = '[a-f0-9]{64}'",f"const VERSION = '{hashlib.sha256(version.encode()).hexdigest()}'",worker)
        specs=json.loads(re.search(r'const INTEGRITY = ([^;]+);',worker)[1])
        for spec in specs:
            if spec['file']=='index.html':spec['sha256']=hashlib.sha256(html.encode()).hexdigest()
        worker=re.sub(r'const INTEGRITY = [^;]+;',lambda _: 'const INTEGRITY = '+json.dumps(specs)+';',worker)
        (site/'sw.js').write_text(worker)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
            context=browser.new_context();page=context.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            base=f'http://127.0.0.1:{server.server_port}/lexa./'
            page.goto(base+'#/cf/60')
            page.wait_for_function('navigator.serviceWorker.controller !== null',timeout=20000)
            scope=page.evaluate('(async()=> (await navigator.serviceWorker.ready).scope)()')
            assert scope==base
            manifest=page.evaluate("(async()=>await (await fetch('./manifest.webmanifest')).json())()")
            assert manifest['start_url']=='./' and manifest['scope']=='./'
            page.evaluate("caches.open('unrelated-project').then(cache=>cache.put('/unrelated',new Response('keep')))")
            page.locator('#font-up').click()
            page.locator('[data-save="60"]').click()
            assert page.evaluate("(async()=> (await Promise.all((await caches.keys()).map(async key=>(await (await caches.open(key)).keys()).map(r=>r.url)))).flat().every(url=>!url.endsWith('.pdf')))()")
            context.set_offline(True)
            assert page.evaluate("fetch('./favicon.svg?v=1').then(response=>response.ok)")
            page.reload();expect(page.locator('#art-60')).to_contain_text('A Constituição poderá ser emendada')
            expect(page.locator('#font-size')).to_have_text('20 px')
            assert page.locator('[data-save="60"]').get_attribute('aria-pressed')=='true'
            page.goto(base);page.locator('#library-search').fill('dignidade')
            expect(page.locator('.text-result-group')).to_have_count(12)
            page.locator('.text-result[href="#/cf/1?q=dignidade"]').click();expect(page.locator('#art-1 mark')).to_have_count(1)
            page.goto(base+'#/sv/13');expect(page.locator('#art-13')).to_be_visible()
            page.goto(base+'#/favoritos');expect(page.locator('.favorite-link[href="#/cf/60"]')).to_be_visible()
            page.goto(base+'#/atualizacoes');expect(page.locator('.updates-hero')).to_be_visible()
            # There is no offline promise for PDFs or external official sources.
            assert page.evaluate("fetch('./sources/missing.pdf').then(()=>false,()=>true)")
            context.set_offline(False)
            before_json=len([path for path in requests if '/data/' in path])
            deploy('v2')
            page.evaluate('(async()=> (await navigator.serviceWorker.getRegistration()).update())()')
            expect(page.locator('#pwa-update')).to_be_visible(timeout=20000)
            assert len([path for path in requests if '/data/' in path])==before_json,'Atualização só de shell baixou dados inalterados'
            assert page.locator('body').get_attribute('data-test-version') is None
            with page.expect_navigation():page.locator('#pwa-refresh').click()
            expect(page.locator('body')).to_have_attribute('data-test-version','v2')
            assert page.evaluate("JSON.parse(localStorage.getItem('lexa-saved')).includes('cf/60')")
            assert page.evaluate("JSON.parse(localStorage.getItem('lexa-reading')).size")==20
            assert page.evaluate("caches.has('unrelated-project')")
            assert page.evaluate("(async()=> (await caches.keys()).filter(k=>k.startsWith('lexa-offline:')).length)()")==1
            context.set_offline(True);page.reload();expect(page.locator('body')).to_have_attribute('data-test-version','v2')
            context.set_offline(False)
            # A failed precache must leave the usable prior edition intact.
            deploy('v3');failure['enabled']=True
            page.evaluate('''async()=>{
                const registration=await navigator.serviceWorker.getRegistration();
                await new Promise((resolve,reject)=>{
                    const timer=setTimeout(()=>reject(new Error('Atualização não terminou')),20000);
                    registration.addEventListener('updatefound',()=>{
                        const worker=registration.installing;
                        worker.addEventListener('statechange',()=>{if(worker.state==='redundant'){clearTimeout(timer);resolve();}});
                    },{once:true});
                    registration.update().catch(reject);
                });
            }''')
            assert page.locator('#pwa-update').is_hidden()
            context.set_offline(True);page.reload();expect(page.locator('body')).to_have_attribute('data-test-version','v2')
            # A new immutable legal file with the wrong bytes must also be rejected.
            context.set_offline(False);failure['enabled']=False;deploy('v4')
            worker=(site/'sw.js').read_text()
            specs=json.loads(re.search(r'const INTEGRITY = ([^;]+);',worker)[1])
            spec=next(item for item in specs if item['file'].startswith('data/clt.'))
            original=(site/spec['file']).read_bytes();new_bytes=original+b' '
            new_hash=hashlib.sha256(new_bytes).hexdigest()
            spec['file']='data/clt.'+new_hash+'.json';spec['sha256']=new_hash
            (site/spec['file']).write_bytes(original) # deliberately wrong bytes
            worker=re.sub(r'const INTEGRITY = [^;]+;',lambda _: 'const INTEGRITY = '+json.dumps(specs)+';',worker)
            (site/'sw.js').write_text(worker)
            page.evaluate('''async()=>{
                const r=await navigator.serviceWorker.getRegistration();
                await new Promise((resolve,reject)=>{
                    const timer=setTimeout(()=>reject(new Error('Instalação adulterada não terminou')),20000);
                    r.addEventListener('updatefound',()=>{const w=r.installing;w.addEventListener('statechange',()=>{if(w.state==='redundant'){clearTimeout(timer);resolve();}});},{once:true});
                    r.update().catch(reject);
                });
            }''')
            assert page.locator('#pwa-update').is_hidden()
            context.set_offline(True);page.goto(base+'#/clt/922');expect(page.locator('#art-922')).to_be_visible()
            assert page.locator('body').get_attribute('data-test-version')=='v2'
            assert page.evaluate("(async()=> (await caches.keys()).filter(k=>k.startsWith('lexa-offline:')).length)()")==1
            fresh=browser.new_context();first=fresh.new_page();first.goto(base)
            expect(first.locator('#pwa-status')).to_contain_text('Não foi possível preparar',timeout=20000)
            assert first.evaluate('navigator.serviceWorker.controller===null')
            assert first.evaluate("(async()=> (await caches.keys()).filter(k=>k.startsWith('lexa-offline:')).length)()")==0
            fresh.close()
            assert not errors,errors
            browser.close()
            print('PWA validada: subpasta, leitura offline, atualização consentida, preservação de favoritos/preferências, limpeza isolada e reutilização sem download de JSON e rejeição de shell incompleto e JSON adulterado.')
    finally:server.shutdown();server.server_close()
