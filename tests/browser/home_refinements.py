"""Single reference results, grouped mobile settings and build-derived history."""
from pathlib import Path
import json,threading
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright,expect
from support import artifact_path, chromium_executable
from performance import BenchmarkServer
root=Path(__file__).resolve().parents[2]
catalog=json.loads((root/'dist/catalog.json').read_text(encoding='utf-8'));recent=catalog['recentUpdates']
server=BenchmarkServer(root/'dist');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}/'
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server']);errors=[]
  for width,height in [(1366,768),(375,812),(320,700)]:
   context=browser.new_context(viewport={'width':width,'height':height},service_workers='block');page=context.new_page();requested=[]
   page.on('pageerror',lambda error:errors.append(str(error)));page.on('request',lambda request:requested.append(request.url))
   page.goto(base);expect(page.locator('#cards .code-card')).to_have_count(14)
   assert not [url for url in requested if '/data/' in url]
   expect(page.locator('.history-invite')).to_have_count(1)
   expect(page.locator('.recent-updates>li')).to_have_count(len(recent))
   for query,code,article in [('Art. 5 CF','cf','5'),('Art. 186 CC','civil','186'),('SV 13','sv','13')]:
    page.locator('#library-search').fill(query);link=page.locator('#quick-reference a')
    expect(link).to_have_count(1);expect(link).to_have_attribute('href',f'#/{code}/{article}')
    assert page.locator('#cards a').count()==0
    assert page.locator('#text-results a').count()==0
    assert link.locator('small').inner_text()
    for _ in range(4):page.keyboard.press('Tab')
    expect(link).to_be_focused()
    page.keyboard.press('Enter');expect(page.locator('#art-'+article)).to_be_visible()
    page.goto(base)
   page.locator('#library-search').fill('Art. 99999 CF')
   expect(page.locator('#quick-reference')).to_contain_text('Referência não encontrada')
   expect(page.locator('#quick-reference a')).to_have_count(0);expect(page.locator('#cards a')).to_have_count(0)
   page.locator('#library-search').fill('art. 5º');expect(page.locator('#quick-reference a')).to_have_count(13)
   hrefs=page.locator('#quick-reference a').evaluate_all('(links)=>links.map(link=>link.getAttribute("href"))')
   assert len(set(hrefs))==len(hrefs);assert page.locator('#cards a').count()==0
   page.locator('#library-search').fill('dignidade');expect(page.locator('.text-result-group')).to_have_count(12)
   expect(page.locator('#library-results')).to_contain_text('52 entradas')
   assert page.locator('#quick-reference').is_hidden()
   page.locator('#library-search').fill('');expect(page.locator('#cards .code-card')).to_have_count(14)
   page.locator('#library-search').fill('Art. 186 CC');expect(page.locator('#quick-reference a')).to_have_count(1)
   page.screenshot(path=artifact_path(f'lexa-ux2-reference-{width}.png'))
   if recent:
    event=recent[0];article=event['articles'][0]['articleId']
    href='#/atualizacoes?'+urlencode({'codigo':event['codeId'],'artigo':article})
    page.locator(f'.recent-articles a[href="{href}"]').first.click()
    expect(page.locator('#history-code')).to_have_value(event['codeId']);expect(page.locator('#history-article')).to_have_value(article)
    expect(page.locator('.article-change')).not_to_have_count(0)
    page.goto(base);expect(page.locator('.recent-updates>li')).to_have_count(len(recent))
    page.reload();expect(page.locator('.recent-updates>li')).to_have_count(len(recent))
   if width<700:
    page.goto(base+'#/cf/5');page.locator('#art-5').wait_for()
    assert not page.locator('.reading-settings').evaluate('(element)=>element.open')
    page.locator('.reading-settings>summary').click()
    controls=page.locator('#font-down,#font-up,#reading-spacing,#reset-reading')
    for box in controls.evaluate_all('(els)=>els.map(el=>el.getBoundingClientRect().toJSON())'):
     assert box['width']>=44 and box['height']>=44,box
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert page.locator('.reading-settings').evaluate('(el)=>el.getBoundingClientRect().right<=innerWidth')
    page.locator('#font-down').focus();page.keyboard.press('Tab');expect(page.locator('#font-up')).to_be_focused()
    page.keyboard.press('Tab');expect(page.get_by_label('Espaçamento',exact=True)).to_be_focused()
    page.keyboard.press('Tab');expect(page.locator('#reset-reading')).to_be_focused()
    page.locator('#font-up').click();expect(page.locator('#font-size')).to_have_text('20 px')
    page.get_by_label('Espaçamento',exact=True).select_option('comfortable')
    page.screenshot(path=artifact_path(f'lexa-ux2-settings-{width}.png'))
    page.locator('#reset-reading').click();expect(page.locator('#font-size')).to_have_text('19 px')
    expect(page.locator('#reading-spacing')).to_have_value('standard')
   context.close()
  assert not errors,errors
  browser.close();print('Home: referências únicas e diretas, 13 referências ambíguas preservadas, busca textual/estados vazios, ajustes móveis de 44 px e teclado, resumo persistente e links filtrados; sem histórico na carga inicial.')
finally:server.shutdown();server.server_close();thread.join()
