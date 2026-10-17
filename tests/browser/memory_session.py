"""Long-session working set; structural cache assertions, no absolute RAM gate."""
from pathlib import Path
import argparse,json,threading
from playwright.sync_api import sync_playwright,expect
from performance import BenchmarkServer,Probe,library_ready,reader_ready,search_ready
from support import chromium_executable
root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory',nargs='?',type=Path,default=root/'dist')
parser.add_argument('--before',action='store_true',help='Record a previous build without imposing the new cache contract')
parser.add_argument('--output',type=Path)
args=parser.parse_args();directory=args.directory.resolve()
catalog=json.loads((directory/'catalog.json').read_text());specs=catalog['collections']
server=BenchmarkServer(directory);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
snapshots=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  context=browser.new_context(service_workers='block',viewport={'width':375,'height':812});page=context.new_page();probe=Probe(page,context,server,4,True)
  base=f'http://127.0.0.1:{server.server_port}/';page.goto(base);library_ready(page,len(specs))
  page.locator('#library-search').fill('dignidade');search_ready(page,'dignidade',12)
  snapshots.append({'point':'search','heap_bytes':probe.heap(),'loaded':page.evaluate('collections.filter(c=>c.loaded).length')})
  for turn in range(2):
   for spec in specs:
    page.goto(base+'#/'+spec['id']);reader_ready(page)
    if not args.before:assert page.evaluate('collections.filter(c=>c.loaded).length')<=3
   snapshots.append({'point':'after_round_'+str(turn+1),'heap_bytes':probe.heap(),'loaded':page.evaluate('collections.filter(c=>c.loaded).length')})
  page.evaluate("localStorage.setItem('lexa-saved',JSON.stringify(['civil/186','cf/60','sv/13']))")
  page.reload();reader_ready(page);page.goto(base+'#/favoritos')
  expect(page.locator('#favorites-count')).to_have_text('3 favoritos')
  page.locator('.favorite-link[href="#/civil/186"]').click();expect(page.locator('#art-186')).to_be_visible()
  assert page.evaluate("JSON.parse(localStorage.getItem('lexa-saved')).includes('civil/186')")
  if not args.before:assert page.evaluate('collections.filter(c=>c.loaded).length')<=3
  page.goto(base);page.locator('#library-search').fill('dignidade');search_ready(page,'dignidade',12)
  actual=page.evaluate("searchLibraryText('dignidade').map(g=>({id:g.code.id,ids:g.matches.map(m=>m.article.id)}))")
  assert actual==json.loads((root/'tests/fixtures/dignidade-results.json').read_text())
  browser.close()
 report={'cpu':4,'rounds':2,'collections':len(specs),'memory':'page V8 heap after GC; not total browser RAM','snapshots':snapshots}
 if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
finally:server.shutdown();server.server_close();thread.join()
