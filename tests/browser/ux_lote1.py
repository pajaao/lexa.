"""Lote 1: visual/context labels, real responsive index, existing reader flows.
No timing budgets, no simulated navigation and no AI/remission resources.
"""
from pathlib import Path
import functools,http.server,threading,json,argparse
from playwright.sync_api import sync_playwright,expect
from support import chromium_executable
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--site',type=Path,default=ROOT/'dist');parser.add_argument('--capture-only',action='store_true');parser.add_argument('--artifacts',type=Path,default=ROOT/'test-results/ux-lote1');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(args.site)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/';observations=[]
def contrast(first,second):
 def luminance(value):
  values=[int(value.strip().lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
  return sum(weight*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v,weight in zip(values,(.2126,.7152,.0722)))
 a,b=sorted((luminance(first),luminance(second)))
 return (b+.05)/(a+.05)
def check_palette(page):
 colors=page.evaluate('Object.fromEntries(["ink","muted","bg","surface","soft","action","on-action","control-border","focus-ring"].map(key=>[key,getComputedStyle(document.documentElement).getPropertyValue("--"+key).trim()]))')
 ratios={}
 for front,back,minimum in [('ink','surface',4.5),('muted','bg',4.5),('muted','soft',4.5),('on-action','action',4.5),('control-border','surface',3),('focus-ring','bg',3)]:
  ratio=contrast(colors[front],colors[back]);assert ratio>=minimum,(front,back,ratio);ratios[front+'/'+back]=round(ratio,2)
 return ratios
def no_overflow(page):assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),page.viewport_size
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  for width,height in [(1366,768),(390,812),(320,700)]:
   for dark in [False,True]:
    context=browser.new_context(viewport={'width':width,'height':height},service_workers='block',reduced_motion='reduce');page=context.new_page();page.set_default_timeout(20000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(base);expect(page.locator('.code-card')).to_have_count(14);page.evaluate('(dark)=>document.documentElement.classList.toggle("dark",dark)',dark)
    palette=check_palette(page) if not args.capture_only else {}
    no_overflow(page);page.screenshot(path=str(args.artifacts/f'home-{width}-{"dark" if dark else "light"}.png'))
    page.locator('.library').scroll_into_view_if_needed();page.screenshot(path=str(args.artifacts/f'library-{width}-{"dark" if dark else "light"}.png'));page.evaluate('scrollTo(0,0)')
    if not args.capture_only:
     expect(page.get_by_label('Buscar norma, artigo ou palavra',exact=True)).to_be_visible()
     search=page.locator('#library-search');search.focus();assert page.evaluate('getComputedStyle(document.querySelector(".hero-search")).outlineStyle')!='none'
     search.fill('Art. 5 CF');search.press('Enter');expect(page.locator('#art-5')).to_be_visible()
    else:page.goto(base+'#/cf/5');expect(page.locator('#art-5')).to_be_visible()
    page.evaluate('(dark)=>document.documentElement.classList.toggle("dark",dark)',dark)
    no_overflow(page)
    if not args.capture_only:
     page.wait_for_function('document.querySelector("#art-5 .article-heading").getBoundingClientRect().top >= document.querySelector(".reading-controls").getBoundingClientRect().bottom')
    if not args.capture_only:
     if width<=700:page.locator('.mobile-search-toggle').click()
     expect(page.get_by_label('Buscar nesta legislação',exact=True)).to_be_visible();expect(page.locator('.edition-label')).to_have_text('Edição consultada');expect(page.locator('#reading-scope')).to_have_text('Constituição Federal')
    if width<=700 and not args.capture_only:page.locator('.reader-search-close').click()
    page.screenshot(path=str(args.artifacts/f'reader-{width}-{"dark" if dark else "light"}.png'))
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(args.artifacts/f'edition-{width}-{"dark" if dark else "light"}.png'))
    if width<701:
     trigger=page.locator('.mobile-index-toggle');trigger.focus();trigger.press('Space')
     expect(page.locator('.reader-index-panel')).to_be_visible();expect(page.locator('#index-list')).to_be_visible()
     assert page.locator('#index-list [data-section]:visible').count()>0
     assert page.locator('.reader-layout').evaluate('el=>getComputedStyle(el).display')=='block'
     page.screenshot(path=str(args.artifacts/f'index-{width}-{"dark" if dark else "light"}.png'))
     page.locator('.index-panel-close').click()
    if not args.capture_only:
     page.goto(base+'#/cf/adct-1');expect(page.locator('#art-adct-1')).to_be_visible();expect(page.locator('#reading-scope')).to_have_text('ADCT');no_overflow(page)
     page.goto(base+'#/civil/186');expect(page.locator('#art-186')).to_be_visible();page.wait_for_function('JSON.parse(localStorage.getItem("lexa-last-reading"))?.articleId==="186"');settings=page.locator('.reading-settings')
     if settings.get_attribute('open') is None:settings.locator(':scope > summary').click()
     page.locator('#font-up').click();expect(page.locator('#font-size')).to_have_text('20 px');page.locator('#reading-spacing').select_option('comfortable');expect(page.locator('.reading')).to_have_attribute('data-spacing','comfortable')
     if width<=700:page.locator('.sheet-close').click()
     page.locator('#focus-mode').click();expect(page.locator('#focus-mode')).to_have_attribute('aria-pressed','true');page.locator('#focus-mode').click()
     page.locator('#art-186 [data-save]').click();page.locator('#saved-filter').click();expect(page.locator('#saved-filter')).to_have_text('Mostrar todos');expect(page.locator('#articles .article')).to_have_count(1)
     page.goto(base+'#/favoritos');expect(page.locator('.favorite-link')).to_have_count(1);page.reload();expect(page.locator('.favorite-link')).to_have_count(1)
     page.locator('.favorite-link').click();expect(page.locator('#art-186')).to_be_visible();page.goto(base)
     expect(page.locator('.resume-reading')).to_contain_text('ÚLTIMO ARTIGO CONSULTADO');expect(page.locator('.resume-reading>a')).to_have_text('Abrir artigo →');expect(page.locator('.resume-reading>a')).to_have_attribute('href','#/civil/186')
     search=page.locator('#library-search');search.fill('zzzxxyyinexistente');expect(page.locator('.empty')).to_be_visible();no_overflow(page)
    assert not errors,errors
    observations.append({'width':width,'theme':'dark' if dark else 'light','overflow':False,'mobileIndexExpanded':width<701,'physicalDevice':False,'paletteContrastRatios':palette})
    context.close()
  if not args.capture_only:
   # Actual SHA rejection followed by recovery, with no worker hiding the fault.
   context=browser.new_context(service_workers='block');page=context.new_page();page.set_default_timeout(20000)
   catalog=json.loads((args.site/'catalog.json').read_text());civil=next(c for c in catalog['collections'] if c['id']=='civil')
   pattern='**/'+civil['file'];page.route(pattern,lambda route:route.fulfill(status=200,body='{}',content_type='application/json'));page.goto(base+'#/civil/186')
   expect(page.locator('.loading-panel')).to_contain_text('não corresponde à edição publicada');assert 'Verifique a conexão' not in page.locator('.loading-panel').inner_text()
   page.unroute(pattern);page.locator('#retry-load').click();expect(page.locator('#art-186')).to_be_visible();context.close()
  browser.close()
 args.artifacts.joinpath('observations.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2))
 print('PASS Lote 1: 1366/390/320, claro/escuro, índice, busca, CF/ADCT, ajustes, foco, favoritos, retomada, estado vazio e SHA/recuperação.' if not args.capture_only else 'Baseline captures complete.')
finally:server.shutdown();server.server_close()
