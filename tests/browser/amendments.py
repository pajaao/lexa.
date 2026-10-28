"""Candidate library, full original reader, bidirectional links and offline navigation."""
from pathlib import Path
import functools,http.server,threading,subprocess,json
from playwright.sync_api import sync_playwright,expect
from support import chromium_executable,artifact_path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['node','--input-type=module','-e',"import {stagePages} from './scripts/build-pages.mjs';await stagePages('test-results/amendments-preview',{amendmentsCandidate:true});"],cwd=ROOT,check=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'test-results/amendments-preview')))
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox'])
  context=browser.new_context(service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base);expect(page.locator('.constitution-amendments')).to_be_visible()
  assert page.locator('.constitution-card>a').count()==2 and page.locator('a a').count()==0
  assert not any('/data/ec-' in r['name'] for r in page.evaluate('performance.getEntriesByType("resource").map(x=>({name:x.name}))'))
  page.locator('.constitution-amendments').click();expect(page.locator('.amendment-entry')).to_have_count(5)
  page.locator('#amendment-more').click();expect(page.locator('.amendment-entry')).to_have_count(10)
  page.locator('#amendment-search').fill('115');expect(page.locator('.amendment-entry')).to_have_count(1)
  page.locator('.amendment-entry').click();expect(page.locator('.reader-top h1')).to_have_text('Emenda Constitucional nº 115')
  assert page.locator('#articles .article').count()==4
  original=json.loads((ROOT/'data/amendments/candidate/documents/ec-115.json').read_text(encoding='utf-8'))
  actual=page.locator('#articles .legal-unit').all_text_contents()
  assert actual==[b['text'].replace('\r\n','\n').replace('\r','\n') for b in original['blocks']] # HTML DOM canonicalizes line endings; source bytes are checked separately.
  assert page.locator('.ec-citation').count()>0
  expect(page.locator('.amendment-heading')).to_contain_text('Câmara dos Deputados')
  expect(page.locator('.article-source').first).to_contain_text('Câmara dos Deputados')
  page.locator('.amendment-related a[href="#/cf/5?emenda=115"]').click();expect(page.locator('#art-5')).to_be_visible()
  expect(page.locator('#art-5 a.amendment-note[href^="#/emendas/115"]')).to_have_count(1)
  assert page.locator('#art-5 a.amendment-note[data-previous="true"]').count()==0
  page.locator('#art-5 a.amendment-note[href^="#/emendas/115"]').click();expect(page.locator('.reader-top h1')).to_contain_text('115')
  expect(page.locator('.amendment-related a.back').last).to_have_attribute('href','#/cf/5')
  for n,article in [(103,'40'),(58,'29')]:
   page.goto(base+f'#/cf/{article}');expect(page.locator(f'#art-{article}')).to_be_visible()
   assert page.locator(f'#art-{article} a.amendment-note[href^="#/emendas/{n}"]').count()>0
  page.goto(base+'#/cf/40');expect(page.locator('#art-40')).to_be_visible()
  page.locator('#art-40 [data-legislative-history]').click()
  expect(page.locator('.legislative-panel[open] a.amendment-note[data-previous="true"]')).not_to_have_count(0)
  page.locator('.legislative-heading button').click()
  page.goto(base+'#/emendas');expect(page.locator('#amendment-search')).to_be_visible()
  page.locator('#amendment-search').fill('2022');expect(page.locator('#amendment-count')).to_contain_text('emendas')
  assert all('2022' in x for x in page.locator('.amendment-entry div>span').all_text_contents())
  page.locator('#amendment-search').fill('inexistente-zxyz');expect(page.locator('.empty')).to_contain_text('Nenhuma emenda')
  page.locator('#amendment-search').fill('');page.locator('#amendment-order').select_option('antigas');expect(page.locator('.amendment-entry>strong').first).to_have_text('1')
  page.locator('#amendment-search').focus();page.keyboard.press('Tab');expect(page.locator('#amendment-order')).to_be_focused()
  page.locator('.amendment-entry').first.focus()
  assert page.locator('.amendment-entry').first.evaluate("e=>getComputedStyle(e).outlineStyle!=='none'")
  # Visual review at approved widths and the additional 320px accessibility boundary.
  for width,height in [(1440,1000),(390,844),(320,844)]:
   page.set_viewport_size({'width':width,'height':height})
   for theme in ['light','dark']:
    page.evaluate('(t)=>{localStorage.setItem("lexa-theme",t);document.documentElement.dataset.theme=t;document.documentElement.classList.toggle("dark",t==="dark")}',theme)
    for route,name in [('#','home'),('#/emendas','library'),('#/emendas/115','reader'),('#/cf/5','context')]:
     page.goto(base+route)
     expect(page.locator('.constitution-amendments') if name=='home' else page.locator('.amendments-library') if name=='library' else page.locator('#art-1') if name=='reader' else page.locator('#art-5')).to_be_visible()
     assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),(width,theme,name)
     if name=='library':
      ratios=page.evaluate('''()=>{const rgb=s=>s.match(/[\\d.]+/g).slice(0,3).map(Number);const lum=c=>c.map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);return ['.amendment-search-help','#amendment-count','.amendment-entry small'].map(s=>{const e=document.querySelector(s);let bg=e;while(getComputedStyle(bg).backgroundColor==='rgba(0, 0, 0, 0)'&&bg.parentElement)bg=bg.parentElement;const a=lum(rgb(getComputedStyle(e).color)),b=lum(rgb(getComputedStyle(bg).backgroundColor));return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);});}''')
      assert all(r>=4.5 for r in ratios),(width,theme,ratios)
      assert page.locator('#amendment-search').bounding_box()['height']>=44 and page.locator('#amendment-order').bounding_box()['height']>=44
     page.screenshot(path=artifact_path(f'ec-{name}-{width}-{theme}.png'),full_page=name=='home')
  assert not errors,errors
  context.close()
  # A corrupted payload must fail closed rather than display an altered original.
  bad=browser.new_context(service_workers='block');bad.route('**/data/ec-115.*.json',lambda r:r.fulfill(status=200,content_type='application/json',body='{}'))
  broken=bad.new_page();broken.goto(base+'#/emendas/115');expect(broken.locator('.loading-panel h1')).to_have_text('Não foi possível abrir esta edição');assert broken.locator('#articles .article').count()==0;bad.close()
  # PWA worker is enabled here; only visited EC payloads must be needed offline.
  context=browser.new_context();page=context.new_page();page.goto(base+'#/emendas/115');expect(page.locator('#art-1')).to_be_visible()
  page.evaluate('navigator.serviceWorker.ready.then(()=>true)');page.reload();expect(page.locator('#art-1')).to_be_visible()
  page.wait_for_function('navigator.serviceWorker.controller!==null')
  page.wait_for_function(r'async()=>{const names=await caches.keys();for(const n of names){const keys=await (await caches.open(n)).keys();if(keys.some(x=>/data\/ec-115\./.test(x.url)))return true;}return false;}')
  context.set_offline(True);page.reload();expect(page.locator('#art-1')).to_be_visible();expect(page.locator('.reader-top h1')).to_contain_text('115')
  context.close();browser.close()
 print('ECs: navegação, texto integral, filtros, 320/390/1440px, dois temas e leitura offline visitada aprovados.')
finally:server.shutdown();server.server_close()
