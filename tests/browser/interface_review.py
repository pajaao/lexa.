"""Sentence spacing, examples and continuous/focused article alignment."""
from pathlib import Path
import functools,http.server,threading,re
from support import chromium_executable
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def assert_article_readable(article):
 heading=article.locator('.article-heading>a').bounding_box()
 caput=article.locator('.legal-unit').first.bounding_box()
 assert heading and caput and abs(heading['x']-caput['x'])<1
 assert article.locator('.legal-unit').evaluate_all('''els=>els.length>0 && els.every(el=>{
  const style=getComputedStyle(el),box=el.getBoundingClientRect(),article=el.closest('.article').getBoundingClientRect();
  return parseFloat(style.fontSize)>=16 && parseFloat(style.lineHeight)>=1.5*parseFloat(style.fontSize)
   && box.left>=article.left && box.right<=article.right+1;
 })''')
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage'])
  page=b.new_page(viewport={'width':375,'height':812},service_workers='block');base=f'http://127.0.0.1:{server.server_port}/'
  for route,selector in [('', '.hero-copy>p,.consultation-guide p'),('#/favoritos','.favorites-intro'),('#/atualizacoes','.updates-hero>p')]:
   page.goto(base+route)
   for text in page.locator(selector).all_inner_texts():assert not re.search(r'[.,][A-Za-zÀ-ÿ]',text),text
  assert '0 alterações' not in page.locator('.history-stats').inner_text()
  expect(page.locator('.history-stats')).to_contain_text('Acompanhando desde')
  page.goto(base)
  for term,expected in [('Art. 5 CF','#/cf/5'),('SV 13','#/sv/13')]:
   button=page.get_by_role('button',name=term,exact=True);button.focus();page.keyboard.press('Enter')
   expect(page.locator('#quick-reference a')).to_have_attribute('href',expected)
   expect(page.locator('#library-search')).to_have_value(term)
  page.get_by_role('button',name='dignidade',exact=True).click()
  expect(page.locator('.text-result-group')).to_have_count(12)
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
  for width in [375,1280]:
   page.set_viewport_size({'width':width,'height':900})
   for dark in [False,True]:
    page.goto(base+'#/cf');expect(page.locator('#art-1')).to_be_visible()
    page.evaluate('(dark)=>document.documentElement.classList.toggle("dark",dark)',dark)
    ordinary=page.locator('#articles .article:not(.focused-article)')
    assert ordinary.count()>0
    assert ordinary.evaluate_all('els=>els.every(el=>parseFloat(getComputedStyle(el).paddingLeft)===0 && parseFloat(getComputedStyle(el).paddingRight)===0)')
    assert_article_readable(page.locator('#art-1'))
    page.goto(base+'#/cf/5');expect(page.locator('#art-5')).to_be_visible()
    page.evaluate('(dark)=>document.documentElement.classList.toggle("dark",dark)',dark)
    selected=page.locator('#art-5')
    expect(selected).to_have_class(re.compile(r'\bfocused-article\b'))
    # Only the selected article has an inset beside its highlight border.
    assert selected.evaluate('el=>parseFloat(getComputedStyle(el).paddingLeft)')==(9 if width<=700 else 14)
    assert_article_readable(selected)
    assert page.locator('#theme svg').bounding_box()['width']==18
  b.close();print('Interface: frases separadas, exemplos por teclado, histórico, recuo e SVG validados.')
finally:server.shutdown();server.server_close()
