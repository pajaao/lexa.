"""Presentation-only continuity reduction and reversible full original transcription."""
from pathlib import Path
import functools,http.server,threading,subprocess,json,re
from playwright.sync_api import sync_playwright,expect
from support import chromium_executable,artifact_path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['node','--input-type=module','-e',"import {stagePages} from './scripts/build-pages.mjs';await stagePages('test-results/amendments-preview',{amendmentsCandidate:true});"],cwd=ROOT,check=True)
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT/'test-results/amendments-preview')));threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox']);page=browser.new_page(service_workers='block');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  for number in [123,115,103,19,29,132]:
   doc=json.loads((ROOT/f'data/amendments/candidate/documents/ec-{number}.json').read_text(encoding='utf-8'))
   page.goto(base+f'#/emendas/{number}');expect(page.locator('#art-1')).to_be_visible()
   # Retain every textual block in the same DOM, including hidden continuity.
   actual=page.locator('#articles .legal-unit').all_text_contents()
   visible_ids=page.locator('#articles .legal-unit').evaluate_all('els=>els.map(x=>Number(x.dataset.sourceBlock))')
   assert actual==[b['text'].replace('\r\n','\n').replace('\r','\n') for b in doc['blocks'] if b['id'] in visible_ids]
   assert all(re.fullmatch(r'[\s.…]+',s) for s in page.locator('.ec-continuity-only').all_text_contents())
   for text in page.locator('.legal-unit:visible').all_inner_texts():assert not re.fullmatch(r'[\s.…]+',text)
   assert page.locator('.ec-citation').evaluate_all("els=>els.every(e=>getComputedStyle(e).backgroundColor==='rgba(0, 0, 0, 0)')")
   toggle=page.locator('.amendment-transcription-toggle');toggle.focus();page.keyboard.press('Enter');expect(toggle).to_have_attribute('aria-pressed','true')
   assert page.locator('#articles .legal-unit').evaluate_all('els=>els.every(e=>e.getClientRects().length>0)')
   assert page.locator('#articles .legal-unit').all_text_contents()==actual
   toggle.click();expect(toggle).to_have_attribute('aria-pressed','false')
  for width,height in [(1440,1000),(390,844)]:
   page.set_viewport_size({'width':width,'height':height})
   for theme in ['light','dark']:
    page.evaluate('(t)=>localStorage.setItem("lexa-theme",t)',theme);page.goto(base+'#/emendas/123/2');page.reload();expect(page.locator('#art-2')).to_be_visible()
    article=page.locator('#art-2');article.scroll_into_view_if_needed()
    expect(article).to_contain_text('Art. 225.');expect(article).to_contain_text('§ 1º');expect(article).to_contain_text('VIII - manter regime fiscal favorecido')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    assert article.locator('.ec-continuity-only:visible').count()==0
    page.screenshot(path=artifact_path(f'ec123-after-{width}-{theme}.png'))
    page.locator('.amendment-transcription-toggle').click();article.scroll_into_view_if_needed();page.screenshot(path=artifact_path(f'ec123-integral-{width}-{theme}.png'))
    assert article.locator('.ec-continuity-dots:visible').count()>0
  # Search and article navigation redraw the same reader; full mode stays active.
  page.goto(base+'#/emendas/123');expect(page.locator('#art-1')).to_be_visible();page.locator('.amendment-transcription-toggle').click()
  page.locator('.mobile-search-toggle').click();page.locator('#article-search').fill('biocombustíveis');expect(page.locator('#art-2')).to_be_visible()
  expect(page.locator('.amendment-transcription-toggle')).to_have_attribute('aria-pressed','true')
  page.goto(base+'#/cf/5');expect(page.locator('#art-5')).to_be_visible();assert page.locator('.amendment-transcription-toggle').count()==0
  assert not page.locator('#app').evaluate("e=>e.classList.contains('amendment-full')")
  assert not errors,errors
  browser.close()
 print('Refinamento: EC123/115/103/19/29/132, transcrição literal reversível, teclado, busca, CF sem alteração e quatro capturas aprovados.')
finally:server.shutdown();server.server_close()
