"""Approved homepage/settings: real catalogue, navigation, contrast and geometry."""
from pathlib import Path
import functools,http.server,threading,json
from playwright.sync_api import sync_playwright,expect
from support import artifact_path,chromium_executable

ROOT=Path(__file__).resolve().parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
catalog=json.loads((ROOT/'dist/catalog.json').read_text(encoding='utf8'))
contrast=r'''els=>{
 const rgb=s=>s.match(/[\d.]+/g).map(Number);
 const lum=c=>c.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
 function bg(el){const layers=[];for(let n=el;n;n=n.parentElement)layers.unshift(rgb(getComputedStyle(n).backgroundColor));return layers.reduce((base,c)=>{const a=c.length>3?c[3]:1;return c.slice(0,3).map((x,i)=>x*a+base[i]*(1-a))},[255,255,255])}
 return els.filter(el=>el.getClientRects().length).map(el=>{const f=lum(rgb(getComputedStyle(el).color)),b=lum(bg(el));return {text:el.textContent.trim(),ratio:(Math.max(f,b)+.05)/(Math.min(f,b)+.05)}})
}'''
results=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--no-proxy-server'])
        for width,height in [(1440,900),(390,844)]:
            for dark in [False,True]:
                context=browser.new_context(viewport={'width':width,'height':height},service_workers='block',reduced_motion='reduce')
                page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base);expect(page.locator('.code-card')).to_have_count(len(catalog['collections']))
                if dark:page.locator('#theme').click()
                theme='dark' if dark else 'light'
                expect(page.locator('.hero-art,.features,.history-invite')).to_have_count(0)
                expect(page.locator('.legislative-indicator')).to_have_count(1 if catalog['recentUpdates'] else 0)
                assert page.locator('.hero-note').bounding_box()['height']<=60
                for selector in ['header nav a','#theme','.filters button','.search-examples button']:
                    for box in page.locator(selector).evaluate_all('(els)=>els.map(el=>el.getBoundingClientRect().toJSON())'):
                        assert box['width']>=44 and box['height']>=44,(selector,box)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                columns=page.locator('.cards').evaluate('el=>getComputedStyle(el).gridTemplateColumns.split(" ").length')
                assert columns==(3 if width==1440 else 1),columns
                ratios=page.locator('.hero .eyebrow,.hero-copy>p,.field-label,.search-examples button,.hero-note span,.legislative-indicator,.catalog-heading,.code-short,.code-card p,.filters button').evaluate_all(contrast)
                assert all(x['ratio']>=4.5 for x in ratios),[x for x in ratios if x['ratio']<4.5]
                page.keyboard.press('/');expect(page.locator('#library-search')).to_be_focused()
                page.locator('#library-search').blur()
                page.screenshot(path=artifact_path(f'issue46-home-{width}-{theme}.png'),full_page=True)
                page.locator('.settings-link').click();expect(page.locator('#settings-title')).to_be_focused()
                expect(page.locator('#app')).to_be_hidden()
                expect(page.locator('#settings-page')).to_be_visible()
                page.locator('.skip-link').evaluate('el=>el.click()');expect(page.locator('#settings-title')).to_be_focused()
                expect(page.locator('.feedback-link')).to_have_attribute('href','https://forms.gle/2m4zgB2PKf9GdJMv7')
                expect(page.locator('.feedback-link')).to_have_attribute('rel','noopener noreferrer')
                expect(page.locator('#settings-page')).to_contain_text('não certifica a vigência')
                expect(page.locator('.reading-storage-note')).to_contain_text('somente neste navegador')
                expect(page.locator(f'[data-theme="{theme}"]')).to_have_attribute('aria-pressed','true')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                settings_ratios=page.locator('#settings-page .eyebrow,#settings-page p,#settings-page a,#settings-page button').evaluate_all(contrast)
                assert all(x['ratio']>=4.5 for x in settings_ratios),[x for x in settings_ratios if x['ratio']<4.5]
                page.screenshot(path=artifact_path(f'issue46-settings-{width}-{theme}.png'),full_page=True)
                page.locator('[data-theme="light"]').click();expect(page.locator('[data-theme="light"]')).to_have_attribute('aria-pressed','true')
                page.locator('[data-theme="dark"]').click();expect(page.locator('[data-theme="dark"]')).to_have_attribute('aria-pressed','true')
                page.reload();expect(page.locator('[data-theme="dark"]')).to_have_attribute('aria-pressed','true')
                page.locator('.settings-back').click();expect(page.locator('.code-card')).to_have_count(14)
                expect(page.locator('#app')).to_be_focused()
                page.locator('.code-card[href="#/penal"]').click();expect(page.locator('#articles')).to_be_visible()
                page.goto(base+'#/penal/215');expect(page.locator('#art-215')).to_be_visible()
                page.wait_for_function("JSON.parse(localStorage.getItem('lexa-last-reading')||'null')?.codeId==='penal'")
                page.goto(base);expect(page.locator('.resume-link')).to_have_count(1)
                page.locator('#forget-reading').click();expect(page.locator('.resume-link')).to_have_count(0)
                assert not errors,errors
                results.append({'width':width,'theme':theme,'minimumHomeContrast':min(x['ratio'] for x in ratios),'minimumSettingsContrast':min(x['ratio'] for x in settings_ratios)})
                context.close()
        # Deleted/blocked browser storage must not prevent catalogue or settings use.
        context=browser.new_context(service_workers='block')
        context.add_init_script("Storage.prototype.getItem=()=>{throw Error('blocked')};Storage.prototype.setItem=()=>{throw Error('blocked')}")
        page=context.new_page();page.goto(base);expect(page.locator('.code-card')).to_have_count(14)
        page.goto(base+'#/sobre-e-ajustes');page.locator('[data-theme="dark"]').click()
        expect(page.locator('[data-theme="dark"]')).to_have_attribute('aria-pressed','true')
        context.close();browser.close()
    Path(artifact_path('issue46-visual-results.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: approved homepage/settings, real catalogue, metrics, conditional indicator, keyboard, theme persistence, blocked storage, AA contrast and four visual combinations.')
finally:server.shutdown();server.server_close()
