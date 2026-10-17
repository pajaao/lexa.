"""Check cache/transfer measurement semantics, never absolute speed thresholds."""
from pathlib import Path
import json
import threading
from playwright.sync_api import sync_playwright
from support import chromium_executable, app_evaluate
from performance import BenchmarkServer, Probe, library_ready, search_ready

root=Path(__file__).resolve().parents[2]
catalog=json.loads((root/'dist/catalog.json').read_text())
count=len(catalog['collections'])
server=BenchmarkServer(root/'dist')
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
  context=browser.new_context(service_workers='block');page=context.new_page()
  probe=Probe(page,context,server,1,False)
  page.goto(f'http://127.0.0.1:{server.server_port}/');library_ready(page,count)
  fixture=json.loads((root/'tests/fixtures/dignidade-results.json').read_text())
  cold=probe.measure('first','cold',lambda:page.locator('#library-search').fill('dignidade'),lambda:search_ready(page,'dignidade',len(fixture)))
  assert cold['transfer']['legal_json_network_bytes']>0
  assert cold['origin_body_bytes']>0
  assert cold['transfer']['unfinished_requests']==0
  page.reload();library_ready(page,count)
  assert app_evaluate(page,'collections.every(code=>!code.loaded)')
  warm=probe.measure('first','warm_http',lambda:page.locator('#library-search').fill('dignidade'),lambda:search_ready(page,'dignidade',len(fixture)))
  assert warm['transfer']['legal_json_network_bytes']==0,warm
  assert warm['transfer']['cached_requests']>=count,warm
  assert warm['transfer']['failed_requests']==0
  assert warm['transfer']['unfinished_requests']==0
  assert warm['js_heap_after_gc_bytes'] is None
  page.locator('#library-search').fill('educacao')
  page.wait_for_function("[...document.querySelectorAll('.text-result mark')].some(el=>el.textContent.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()==='educacao')")
  repeated=probe.measure('repeated','warm_memory',lambda:page.locator('#library-search').fill('dignidade'),lambda:search_ready(page,'dignidade',len(fixture)))
  assert repeated['transfer']['legal_json_network_bytes']==0
  assert repeated['transfer']['failed_requests']==0
  context.close();browser.close()
 print('Contrato do benchmark: dados frios transferem bytes; cache HTTP zera o download jurídico após reload; busca com dados em memória não baixa normas.')
finally:server.shutdown();server.server_close();thread.join()
