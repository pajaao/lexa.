"""Check manual/foreground updates with the real worker and temporary editions."""
from pathlib import Path
import functools, hashlib, http.server, json, re, shutil, tempfile, threading
from playwright.sync_api import sync_playwright, expect
from support import chromium_executable, artifact_path

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as temporary:
    site = Path(temporary)/'lexa.'
    shutil.copytree(root/'dist', site)
    original_html = (site/'index.html').read_text(encoding='utf-8')
    original_worker = (site/'sw.js').read_text(encoding='utf-8')
    failure = {'shell': False, 'worker': False}

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()
        def do_GET(self):
            path = self.path.split('?')[0]
            if (failure['shell'] and path == '/lexa./index.html') or (failure['worker'] and path == '/lexa./sw.js'):
                self.send_error(503)
            else:
                super().do_GET()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=temporary))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/lexa./'

    def deploy(version):
        html = original_html.replace('<body>', f'<body data-test-version="{version}">').encode('utf-8')
        (site/'index.html').write_bytes(html)
        worker = re.sub(r"const VERSION = '[a-f0-9]{64}'", f"const VERSION = '{hashlib.sha256(version.encode()).hexdigest()}'", original_worker)
        specs = json.loads(re.search(r'const INTEGRITY = ([^;]+);', worker)[1])
        for spec in specs:
            if spec['file'] == 'index.html': spec['sha256'] = hashlib.sha256(html).hexdigest()
        worker = re.sub(r'const INTEGRITY = [^;]+;', lambda _: 'const INTEGRITY = '+json.dumps(specs)+';', worker)
        (site/'sw.js').write_bytes(worker.encode('utf-8'))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), args=['--no-sandbox', '--no-proxy-server'])
            for width in (320, 390, 1280):
                deploy('v1')
                context = browser.new_context(viewport={'width': width, 'height': 844})
                context.add_init_script('''
                    window.checkCalls=0;window.clockOffset=0;window.holdCheck=false;
                    window.testVisibility='visible';
                    Object.defineProperty(document,'visibilityState',{get:()=>window.testVisibility});
                    const now=Date.now;Date.now=()=>now()+window.clockOffset;
                    const update=ServiceWorkerRegistration.prototype.update;
                    ServiceWorkerRegistration.prototype.update=async function(){
                        window.checkCalls++;
                        if(window.holdCheck)await new Promise(resolve=>window.releaseCheck=resolve);
                        return update.call(this);
                    };
                ''')
                page = context.new_page()
                page.goto(base+'#/cf/60')
                page.wait_for_function('navigator.serviceWorker.controller !== null')
                check = page.get_by_role('button', name='Verificar atualizações', exact=True)
                status = page.locator('#pwa-check-status')
                page.goto(base+'#/sobre-e-ajustes');page.locator('.pwa-help').evaluate('(el)=>el.open=true')
                expect(check).to_be_enabled()
                expect(check).to_have_attribute('aria-describedby', 'pwa-check-status')
                expect(status).to_have_attribute('role', 'status')
                expect(status).to_have_attribute('aria-live', 'polite')
                check.focus()
                page.keyboard.press('Enter')
                expect(status).to_have_attribute('data-state', 'current')
                expect(check).to_be_focused()
                page.screenshot(path=artifact_path(f'pwa-check-current-{width}.png'))

                # Exercise throttling without waiting five real minutes.
                page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
                assert page.evaluate('window.checkCalls') == 1
                page.evaluate("window.clockOffset+=300001;window.testVisibility='hidden';document.dispatchEvent(new Event('visibilitychange'))")
                assert page.evaluate('window.checkCalls') == 1
                page.evaluate('''()=>{
                    window.testVisibility='visible';window.holdCheck=true;
                    document.dispatchEvent(new Event('visibilitychange'));
                    document.dispatchEvent(new Event('visibilitychange'));
                    window.dispatchEvent(new Event('online'));
                    document.querySelector('#pwa-check').click();
                }''')
                expect(status).to_have_attribute('data-state', 'checking')
                expect(check).to_have_attribute('aria-busy', 'true')
                expect(check).to_be_disabled()
                assert page.evaluate('window.checkCalls') == 2
                page.evaluate('window.holdCheck=false;window.releaseCheck()')
                expect(status).to_have_attribute('data-state', 'current')
                expect(check).not_to_have_attribute('aria-busy', 'true')

                failure['worker'] = True
                check.click()
                expect(status).to_have_attribute('data-state', 'error')
                expect(page.locator('#pwa-update')).to_be_hidden()
                failure['worker'] = False
                check.click()
                expect(status).to_have_attribute('data-state', 'current')

                context.set_offline(True)
                check.click()
                expect(status).to_have_attribute('data-state', 'error')
                expect(check).to_be_enabled()
                expect(page.locator('#pwa-update')).to_be_hidden()
                context.set_offline(False)
                page.wait_for_function('navigator.onLine')
                check.click()
                expect(status).to_have_attribute('data-state', 'current')

                # Real foreground-triggered edition change, with no consent to activate yet.
                page.goto(base+'#/cf/60');page.locator('[data-save="60"]').click()
                if width <= 700:
                    page.locator('.reading-settings>summary').click()
                    page.locator('#font-up').click()
                    page.locator('.sheet-close').click()
                else:
                    page.locator('.reading-settings>summary').click()
                    page.locator('#font-up').click()
                page.locator('#art-60').scroll_into_view_if_needed()
                snapshot = page.evaluate('({hash:location.hash,storage:JSON.stringify(localStorage),y:scrollY})')
                deploy('v2')
                page.evaluate("window.clockOffset+=300001;document.dispatchEvent(new Event('visibilitychange'))")
                expect(status).to_have_attribute('data-state', 'available')
                expect(page.locator('#pwa-update')).to_be_visible()
                assert page.locator('body').get_attribute('data-test-version') == 'v1'
                assert page.evaluate('({hash:location.hash,storage:JSON.stringify(localStorage),y:scrollY})') == snapshot
                page.screenshot(path=artifact_path(f'pwa-check-{width}.png'))
                with page.expect_navigation(): page.locator('#pwa-refresh').click()
                assert page.locator('body').get_attribute('data-test-version') == 'v2'
                assert page.evaluate('JSON.stringify(localStorage)') == snapshot['storage']
                expect(page.locator('#font-size')).to_have_text('20 px')
                expect(page.locator('[data-save="60"]')).to_have_attribute('aria-pressed', 'true')

                # A failed preparation must not be reported as an up-to-date edition.
                deploy('v3');failure['shell'] = True
                page.goto(base+'#/sobre-e-ajustes');page.locator('.pwa-help').evaluate('(el)=>el.open=true')
                check.click()
                expect(status).to_have_attribute('data-state', 'error')
                expect(page.locator('#pwa-update')).to_be_hidden()
                assert page.locator('body').get_attribute('data-test-version') == 'v2'
                failure['shell'] = False
                check.click()
                expect(status).to_have_attribute('data-state', 'available')
                assert page.locator('body').get_attribute('data-test-version') == 'v2'
                context.close()

            unsupported = browser.new_context()
            unsupported.add_init_script('delete Navigator.prototype.serviceWorker')
            page = unsupported.new_page();page.goto(base)
            page.goto(base+'#/sobre-e-ajustes');page.locator('.pwa-help').evaluate('(el)=>el.open=true')
            expect(page.locator('#pwa-check')).to_be_disabled()
            expect(page.locator('#pwa-check-status')).to_have_attribute('data-state', 'unsupported')
            unsupported.close();browser.close()
        print('Verificação PWA validada: manual/teclado, retomada, frequência, concorrência, rede, instalação rejeitada, consentimento, dados/leitura e ausência de suporte; 320, 390 e 1280 px.')
    finally:
        server.shutdown()
