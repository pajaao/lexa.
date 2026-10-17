"""Local benchmark: five fresh visits, Chromium CPU 4x, no external network. Optional argument: directory to serve."""
from pathlib import Path
import functools,http.server,threading,json,sys,statistics
from playwright.sync_api import sync_playwright
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=sys.argv[1] if len(sys.argv)>1 else str(Path(__file__).resolve().parents[2]/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
values=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for _ in range(5):
  c=b.new_context(service_workers='block',viewport={'width':375,'height':812});page=c.new_page()
  session=c.new_cdp_session(page);session.send('Emulation.setCPUThrottlingRate',{'rate':4})
  page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='commit')
  page.wait_for_function("document.querySelectorAll('#cards .code-card').length===14")
  values.append(round(page.evaluate('performance.now()')));c.close()
 b.close()
server.shutdown()
print(json.dumps({'runs_ms':values,'median_ms':statistics.median(values)}))
