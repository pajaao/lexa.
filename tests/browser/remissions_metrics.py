"""Measured observations, never timing gates. Usage: script BEFORE_SITE AFTER_SITE EXPERIMENT OUTPUT."""
import json,statistics,sys,threading,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from support import chromium_executable
from performance import BenchmarkServer,library_ready
before,after,experiment,output=map(Path,sys.argv[1:]);results={'conditions':{'runs':5,'cpuThrottle':4,'viewport':[1366,768],'device':'desktop emulation, not physical','network':'localhost HTTP, no bandwidth emulation','homeIncludes':'through library_ready for render, then SW install for total transfer','heap':'CDP JSHeapUsedSize after forced GC; page only, excludes service worker/system RAM'}}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=chromium_executable(),args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
 results['conditions']['chromium']=browser.version
 for name,path in [('before',before),('after',after),('experimental',experiment)]:
  server=BenchmarkServer(path);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}/';rows=[]
  try:
   for _ in range(5):
    context=browser.new_context(viewport={'width':1366,'height':768});page=context.new_page();page.set_default_timeout(45000);cdp=context.new_cdp_session(page);cdp.send('Performance.enable');cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});requests=[];context.on('request',lambda req:requests.append(req.url));audit=server.begin()
    started=time.perf_counter();page.goto(base);library_ready(page,14);render=(time.perf_counter()-started)*1000
    page.wait_for_function("navigator.serviceWorker.controller&&document.querySelector('#pwa-status').dataset.offlineMode==='partial'")
    assert not any('/data/' in u or '/optional/' in u for u in requests),requests
    cdp.send('HeapProfiler.collectGarbage');perf={v['name']:v['value'] for v in cdp.send('Performance.getMetrics')['metrics']};row={'libraryMs':render,'requestsThroughInstall':len(audit),'bodyBytesThroughInstall':sum(audit),'pageHeapAfterGC':perf['JSHeapUsedSize'],'pageScriptSeconds':perf['ScriptDuration'],'remissionsRequestsInitially':sum('/remissions.' in u for u in requests)}
    server.stop()
    if name=='experimental':
     call=page.evaluate('''async()=>{
      const started=performance.now(),base=document.querySelector('script[type=module][src]').src;
      const {loadRemissions}=await import(new URL('optional/remissions-runtime.js',base));
      const store=await loadRemissions();return {ms:performance.now()-started,edges:store.outgoing('civil','927').length};
     }''');assert call['edges']==2
     cdp.send('HeapProfiler.collectGarbage');heap={v['name']:v['value'] for v in cdp.send('Performance.getMetrics')['metrics']}['JSHeapUsedSize'];row.update(explicitApiMs=call['ms'],retainedIndexAndOptionalModulesBytes=heap-row['pageHeapAfterGC'])
     manifest=json.loads((path/'catalog.json').read_text());body=(path/manifest['remissions']['file']).read_text()
     row['parseOnlyRunsMs']=page.evaluate('body=>{const runs=[];for(let i=0;i<5;i++){const t=performance.now();JSON.parse(body);runs.push(performance.now()-t)}return runs}',body)
     row['parseOnlyMedianMs']=statistics.median(row['parseOnlyRunsMs'])
    rows.append(row);context.close()
   results[name]={'runs':rows,'medians':{k:statistics.median(r[k] for r in rows) for k in rows[0] if isinstance(rows[0][k],(int,float))}}
  finally:server.shutdown();server.server_close();thread.join()
 browser.close()
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps({k:v.get('medians',v) for k,v in results.items()},ensure_ascii=False,indent=2))
