from pathlib import Path
import functools,http.server,threading
from support import artifact_path, chromium_executable
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  page=b.new_page(viewport={'width':1280,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  base=f'http://127.0.0.1:{server.server_port}/'
  page.goto(base+'#/cf/60');expect(page.locator('#art-60')).to_be_visible();page.wait_for_timeout(300)
  assert page.evaluate("JSON.parse(localStorage.getItem('lexa-last-reading')).articleId")=='60'
  page.locator('.reading-settings>summary').click();page.locator('#font-up').click();page.locator('#reading-spacing').select_option('comfortable')
  assert page.locator('#art-60>p').first.evaluate('e=>getComputedStyle(e).fontSize')=='20px'
  assert page.locator('#art-60>p').first.evaluate('e=>getComputedStyle(e).lineHeight')=='44px'
  before=page.locator('#art-60').evaluate('e=>e.getBoundingClientRect().top')
  page.locator('#focus-mode').click();assert abs(page.locator('#art-60').evaluate('e=>e.getBoundingClientRect().top')-before)<2
  assert page.locator('header').is_hidden();assert page.locator('aside').is_hidden()
  assert page.locator('#focus-mode').get_attribute('aria-pressed')=='true'
  page.keyboard.press('Escape');expect(page.locator('header')).to_be_visible()
  page.reload();expect(page.locator('#font-size')).to_have_text('20 px');assert page.locator('#reading-spacing').input_value()=='comfortable'
  page.goto(base+'#/sv/13');expect(page.locator('#art-13')).to_be_visible();page.wait_for_timeout(300)
  page.locator('.reader-top .back').click();expect(page.locator('.resume-reading>a')).to_have_attribute('href','#/sv/13')
  page.locator('.resume-reading>a').click();expect(page.locator('#art-13')).to_be_visible()
  page.locator('.reading-settings>summary').click();page.locator('#reset-reading').click();expect(page.locator('#font-size')).to_have_text('19 px');assert page.locator('#reading-spacing').input_value()=='standard'
  for width in [320,390,768,1280]:
   page.set_viewport_size({'width':width,'height':900});page.locator('#focus-mode').scroll_into_view_if_needed()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
   page.locator('#focus-mode').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('focus',width)
   page.screenshot(path=artifact_path(f'lexa-reading-{width}.png'),full_page=False)
   page.locator('#focus-mode').click()
  page.goto(base);page.locator('#forget-reading').click();assert page.locator('.resume-reading').count()==0;page.reload();assert page.locator('.resume-reading').count()==0
  # Malformed persisted state and unavailable storage must not block reading.
  page.evaluate("localStorage.setItem('lexa-reading','null');localStorage.setItem('lexa-last-reading',JSON.stringify({codeId:'cf',articleId:'<invalid>'}))")
  page.reload();assert page.locator('.resume-reading').count()==0
  blocked=b.new_context();blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
  q=blocked.new_page();q.on('pageerror',lambda e:errors.append(str(e)));q.goto(base+'#/cf/adct-1');expect(q.locator('#art-adct-1')).to_be_visible();q.locator('.reading-settings>summary').click();q.locator('#font-up').click();expect(q.locator('#toast')).to_contain_text('temporários');q.locator('#focus-mode').click();q.goto(base);assert not q.locator('body').evaluate("e=>e.classList.contains('reading-focus')")
  assert not errors,errors
  b.close();print('Leitura validada: fonte e espaçamento persistentes, restauração, foco/Escape, retomada de súmula, exclusão, celular e armazenamento indisponível; sem erros JS.')
finally:server.shutdown();server.server_close()
