"""Regressions for reader continuity and keyboard focus, without timing budgets."""
from pathlib import Path
import functools,http.server,threading
from playwright.sync_api import sync_playwright,expect
from support import artifact_path, chromium_executable

root=Path(__file__).resolve().parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(root/'dist')))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}/'
visible_start='''()=>{
 const first=document.querySelector('#articles .article');
 if(!first)return false;
 const heading=first.querySelector('.article-heading').getBoundingClientRect();
 const controls=document.querySelector('.reading-controls').getBoundingClientRect();
 const paragraph=first.querySelector('.legal-unit');
 const end=paragraph?paragraph.getBoundingClientRect().top+parseFloat(getComputedStyle(paragraph).lineHeight):heading.bottom;
 const title=first.previousElementSibling?.querySelector('.legal-heading:last-child');
 const titleRect=title?.getBoundingClientRect();
 const titleFits=!titleRect || end-titleRect.top>innerHeight-controls.bottom-48 || titleRect.top>=controls.bottom;
 return heading.top>=controls.bottom && heading.bottom<=innerHeight && end<=innerHeight && titleFits;
}'''
def check_start(page,label):
 try:
  page.wait_for_function(visible_start)
  # Check the final position, not an intermediate frame of smooth scrolling.
  page.evaluate('''()=>new Promise(resolve=>{
   let last=scrollY,stable=0;
   function frame(){stable=scrollY===last?stable+1:0;last=scrollY;
    if(stable>=3)resolve();else requestAnimationFrame(frame);
   }requestAnimationFrame(frame);
  })''')
  assert page.evaluate(visible_start)
 except Exception:
  page.screenshot(path=artifact_path('lexa-ux-navigation-failure.png'))
  raise AssertionError((label,page.evaluate('''()=>({scrollY,
   first:document.querySelector('#articles .article').getBoundingClientRect().toJSON(),
   controls:document.querySelector('.reading-controls').getBoundingClientRect().toJSON()})''')))
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert page.evaluate('''()=>{
  const first=document.querySelector('#articles .article');
  return document.querySelector('#index-list [aria-current="location"]')?.dataset.section===first.dataset.sectionId &&
   JSON.parse(localStorage.getItem('lexa-last-reading')).articleId===first.id.slice(4);
 }''')

try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  errors=[];cases=0
  for width,height in [(1366,768),(390,812),(320,700)]:
   for motion in ['no-preference','reduce']:
    context=browser.new_context(viewport={'width':width,'height':height},service_workers='block',reduced_motion=motion)
    page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
    for code in ['civil','cpc']:
     page.goto(base+'#/'+code);expect(page.locator('#articles .article')).to_have_count(15)
     original=page.locator('#articles .article').first.get_attribute('id')
     page.locator('#next-page').click()
     page.wait_for_function('id=>document.querySelector("#articles .article").id!==id',arg=original)
     expect(page.locator('#articles .article')).to_have_count(15);check_start(page,(width,motion,code,'next'))
     page.screenshot(path=artifact_path(f'lexa-ux-navigation-{width}-{code}-{motion}.png'))
     page.locator('#previous-page').click();expect(page.locator('#articles .article').first).to_have_attribute('id',original)
     check_start(page,(width,motion,code,'previous'))
     # Pointer selection of a hierarchical branch also returns to its content.
     if width<=700:page.locator('.mobile-index-toggle').click()
     else:page.locator('.reader-index').evaluate('(element)=>element.open=true')
     page.locator('[data-branch]').first.click();check_start(page,(width,motion,code,'branch'))
     if width<=700:assert not page.locator('.reader-index').evaluate('(element)=>element.open')
     cases+=1
    page.goto(base+'#/cf/5');page.locator('#art-5').wait_for()
    if width<=700:
     controls=page.locator('.reading-controls')
     assert controls.bounding_box()['height']<=64,controls.bounding_box()
     page.locator('#art-5 .legal-unit').nth(4).scroll_into_view_if_needed()
     page.wait_for_function("Math.abs(document.querySelector('.reading-controls').getBoundingClientRect().top)<1")
     assert page.locator('#reading-location').inner_text()!='Leitura'
     page.locator('.mobile-search-toggle').click()
     page.locator('#article-search').focus();expect(page.locator('#article-search')).to_be_focused()
     page.locator('.reader-search-close').click()
     button=page.get_by_role('button',name='Índice',exact=True)
     button.focus();page.keyboard.press('Enter')
     expect(page.locator('.index-panel-close')).to_be_focused()
     expect(button).to_have_attribute('aria-expanded','true')
    else:
     expect(page.locator('.mobile-index-toggle')).to_be_hidden()
    if width<=700:
     if not page.locator('.reader-index-panel').evaluate('el=>el.open'):page.locator('.mobile-index-toggle').click()
    else:page.locator('.reader-index').evaluate('(element)=>element.open=true')
    selection=page.locator('#index-list .index-entry').first
    selection.focus();page.keyboard.press('Enter')
    first_link=page.locator('#articles .article .article-heading>a').first
    expect(first_link).to_be_focused();check_start(page,(width,motion,'cf','keyboard'))
    page.screenshot(path=artifact_path(f'lexa-ux-keyboard-{width}-{motion}.png'))
    page.keyboard.press('Tab');expect(page.locator('#articles .article [data-save]').first).to_be_focused()
    cases+=1
    # A division can be empty with the existing favorites filter enabled.
    page.locator('#saved-filter').click()
    if width<=700:
     if not page.locator('.reader-index-panel').evaluate('el=>el.open'):page.locator('.mobile-index-toggle').click()
    else:page.locator('.reader-index').evaluate('(element)=>element.open=true')
    page.locator('#index-list .index-entry').first.focus();page.keyboard.press('Enter')
    empty_heading=page.locator('#articles .empty h3')
    expect(empty_heading).to_be_focused()
    page.wait_for_function('''()=>{
     const heading=document.querySelector('#articles .empty h3').getBoundingClientRect();
     return heading.top>=document.querySelector('.reading-controls').getBoundingClientRect().bottom && heading.bottom<=innerHeight;
    }''')
    page.keyboard.press('Tab');expect(page.locator('#reset-search')).to_be_focused()
    cases+=1;context.close()
  assert not errors,errors
  browser.close();print(f'Navegação: {cases} casos, três viewports, Civil/CPC, próximos/anteriores/índice e teclado na CF, com e sem movimento reduzido.')
finally:server.shutdown();server.server_close();thread.join()
