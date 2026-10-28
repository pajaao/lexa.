"""Editorial favorites/history: state, undo, complete comparison, responsive themes and cached offline data."""
from pathlib import Path
import functools,http.server,threading,json,re
from playwright.sync_api import sync_playwright,expect
from support import chromium_executable,artifact_path
root=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
catalog=json.loads((root/'dist/catalog.json').read_text(encoding='utf-8'))
history=json.loads((root/'dist'/catalog['history']['file']).read_text(encoding='utf-8'))
event=next(x for x in history if x['kind']=='text');change=event['changes'][0]
def expected_text(version):
 return ((version.get('title') or '')+' '+ ' '.join(''.join(r['text'] for r in p['runs']) for p in version['paragraphs'])).strip()
def normalize(s):return re.sub(r'\s+',' ',s).strip()
def check_overflow(page):assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
def contrast(a,b):
 def lum(color):
  rgb=[int(x)/255 for x in re.findall(r'\d+',color)[:3]]
  return sum((x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4)*w for x,w in zip(rgb,[.2126,.7152,.0722]))
 a,b=sorted([lum(a),lum(b)]);return (b+.05)/(a+.05)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server']);errors=[];contrast_measurements=[]
  for width in [320,390,1440]:
   for dark in [False,True]:
    context=browser.new_context(viewport={'width':width,'height':844 if width<700 else 900},service_workers='block',reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(base);page.evaluate('dark=>{localStorage.setItem("lexa-saved",JSON.stringify(["cf/1","cf/5","civil/186","sv/13"]));localStorage.setItem("lexa-theme",dark?"dark":"light")}',dark);page.reload();page.goto(base+'#/favoritos')
    expect(page.locator('.favorite-group')).to_have_count(3);expect(page.locator('#favorites-count')).to_have_text('4 favoritos');check_overflow(page)
    for button in page.locator('[data-remove-favorite]').all():assert button.bounding_box()['height']>=44
    page.screenshot(path=artifact_path(f'favorites-editorial-{width}-{"dark" if dark else "light"}.png'))
    for selector in ['.favorites-privacy','.favorite-group-label','.favorite-entry p']:
     for item in page.locator(selector).all():
      colors=item.evaluate('el=>({text:getComputedStyle(el).color,bg:getComputedStyle(document.body).backgroundColor})');assert contrast(colors['text'],colors['bg'])>=4.5,colors
    search=page.locator('#favorites-search');search.fill('Art. 186 CC');expect(page.locator('#favorites-count')).to_have_text('1 favorito encontrado')
    page.locator('.favorite-link').click();expect(page.locator('#art-186')).to_be_visible();page.reload();expect(page.locator('#art-186')).to_be_visible();page.go_back();expect(page.locator('#favorites-search')).to_have_value('Art. 186 CC');expect(page.locator('.favorite-link')).to_have_count(1)
    search=page.locator('#favorites-search');search.fill('');page.locator('[data-remove-favorite="civil/186"]').click();expect(page.locator('.favorite-link[href="#/civil/186"]')).to_have_count(0);expect(page.locator('#favorites-undo')).to_be_visible()
    page.locator('#favorites-undo').focus();page.keyboard.press('Enter');expect(page.locator('.favorite-link[href="#/civil/186"]')).to_have_count(1);assert page.evaluate('JSON.parse(localStorage.getItem("lexa-saved")).includes("civil/186")')
    page.reload();expect(page.locator('.favorite-link[href="#/civil/186"]')).to_have_count(1)
    search=page.locator('#favorites-search');search.fill('naoexiste');expect(page.locator('.favorites-empty')).to_contain_text('Nenhum favorito encontrado');search.fill('')
    page.goto(base+'#/atualizacoes');expect(page.locator('.update-event')).to_have_count(12)
    first=page.locator(f'[data-history-event="{event["id"]}"]');first.locator(':scope>summary').click();comparison=first.locator('.article-change').first;comparison.locator(':scope>summary').click();expect(comparison).to_have_attribute('data-loaded','true')
    comparison.evaluate('el=>el.dataset.identityTest="preserved"');before=comparison.locator('.comparison-container').inner_html()
    for side,version in [(0,change['before']),(1,change['after'])]:
     paragraphs=comparison.locator('.comparison-grid>section').nth(side).locator(':scope>p:not(.comparison-edition)');actual=' '.join(paragraphs.all_text_contents());assert normalize(actual)==normalize(expected_text(version))
     assert paragraphs.locator('del').count()>0
    # append must preserve the exact existing DOM, open state and loaded comparison.
    page.locator('#history-more').click();expect(page.locator('.update-event')).to_have_count(len(history));expect(first).to_have_attribute('open','');expect(comparison).to_have_attribute('open','');expect(comparison).to_have_attribute('data-identity-test','preserved');assert comparison.locator('.comparison-container').inner_html()==before
    expect(page.locator('.update-event>summary').nth(12)).to_be_focused()
    # Direct contextual links preserve collection/article filters and comparison integrity.
    page.goto(base+f'#/atualizacoes?codigo={event["codeId"]}&artigo={change["articleId"]}');expect(page.locator('#history-code')).to_have_value(event['codeId']);expect(page.locator('#history-article')).to_have_value(change['articleId']);expect(page.locator('.update-event')).to_have_count(1)
    comparison=page.locator('.article-change').first;comparison.locator(':scope>summary').focus();page.keyboard.press('Enter');expect(comparison).to_have_attribute('data-loaded','true')
    expect(comparison.locator('.comparison-footer a')).to_contain_text('versão atual do Lexa');expect(page.locator('.event-footer a[target="_blank"]')).to_have_attribute('rel','noopener noreferrer')
    grid=comparison.locator('.comparison-grid');boxes=[grid.locator(':scope>section').nth(i).bounding_box() for i in range(2)]
    if width>700:assert abs(boxes[0]['y']-boxes[1]['y'])<2
    else:assert boxes[1]['y']>=boxes[0]['y']+boxes[0]['height']-1
    history_colors=page.locator('.history-help,.history-stats span,.event-meta time,.event-heading p,.comparison-edition,.diff-legend').evaluate_all('''els=>els.map(el=>{
     let parent=el,background;
     while(parent){background=getComputedStyle(parent).backgroundColor;if(background!=="rgba(0, 0, 0, 0)"&&background!=="transparent")break;parent=parent.parentElement;}
     return {text:getComputedStyle(el).color,background};
    })''')
    ratios=[contrast(pair['text'],pair['background']) for pair in history_colors]
    assert all(ratio>=4.5 for ratio in ratios),ratios
    contrast_measurements.append((width,dark,round(min(ratios),2)))
    page.keyboard.press('Tab');page.locator('#history-code').focus()
    assert page.locator('#history-code').evaluate('el=>parseFloat(getComputedStyle(el).outlineWidth)>=2&&getComputedStyle(el).outlineStyle!=="none"')
    for stat in page.locator('.history-stats span').all():
     assert stat.evaluate('el=>el.scrollWidth<=el.clientWidth'),stat.inner_text()
    check_overflow(page);page.evaluate('scrollTo(0,0)');page.screenshot(path=artifact_path(f'history-editorial-{width}-{"dark" if dark else "light"}.png'))
    comparison.evaluate('el=>el.scrollIntoView({block:"start"})');page.screenshot(path=artifact_path(f'comparison-editorial-{width}-{"dark" if dark else "light"}.png'))
    context.close()
  context=browser.new_context(service_workers='block');page=context.new_page();page.goto(base);page.evaluate('localStorage.setItem("lexa-saved",JSON.stringify(["unknown/1","cf/99999","sv/9"]))');page.reload();page.goto(base+'#/favoritos');expect(page.locator('.favorite-status').filter(has_text='Indisponível')).to_have_count(2);expect(page.locator('.favorite-status').filter(has_text='Cancelada')).to_have_count(1)
  while page.locator('[data-remove-favorite]').count():page.locator('[data-remove-favorite]').first.click()
  expect(page.locator('.favorites-empty')).to_contain_text('Nenhum favorito salvo');expect(page.locator('#favorites-search')).to_be_hidden();page.locator('#favorites-undo').click();expect(page.locator('[data-remove-favorite]')).to_have_count(1);context.close()
  # Cached history is still available after losing connection and reloading.
  context=browser.new_context();page=context.new_page();page.goto(base);page.wait_for_function('navigator.serviceWorker.controller');page.goto(base+'#/atualizacoes');expect(page.locator('.update-event')).to_have_count(12)
  context.set_offline(True);page.reload();expect(page.locator('.update-event')).to_have_count(12);page.locator('.update-event>summary').first.click();check_overflow(page);context.close()
  assert not errors,errors
  browser.close();print('Contraste mínimo dos textos secundários do histórico (largura, escuro, razão):',contrast_measurements);print('PASS favoritos/histórico editorial: 320/390/1440 claro/escuro; filtro/retorno, desfazer/persistência, indisponíveis, estados vazios, append sem remontagem, filtros contextuais, texto integral/riscados, fontes e histórico offline.')
finally:server.shutdown();server.server_close()
