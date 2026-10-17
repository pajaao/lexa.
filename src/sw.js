/* The build hashes every file in the complete offline edition. */
const VERSION = '__LEXA_VERSION__';
const INTEGRITY = __LEXA_INTEGRITY_MANIFEST__;
const PREFIX = 'lexa-offline:' + encodeURIComponent(self.registration.scope) + ':';
const CACHE = PREFIX + VERSION;
const asset=path=>new URL(path,self.registration.scope).href;
const SHELL=asset('index.html');
const FILES=INTEGRITY.map(spec=>asset(spec.file));
async function verified(response,spec){
 if(!response?.ok||response.type==='opaque')throw new Error('Pacote offline incompleto');
 const bytes=await response.arrayBuffer();
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),byte=>byte.toString(16).padStart(2,'0')).join('');
 if(hash!==spec.sha256)throw new Error('Arquivo offline não corresponde à edição publicada');
 return new Response(bytes,{status:response.status,headers:response.headers});
}
self.addEventListener('install',event=>{
 event.waitUntil((async()=>{
  const previous=(await caches.keys()).filter(key=>key.startsWith(PREFIX)&&key!==CACHE);
  const cache=await caches.open(CACHE);let next=0,failure;
  // Reuse immutable data from this application's prior edition, verifying again.
  // Settle every writer before deleting a rejected partial cache.
  await Promise.all(Array.from({length:4},async()=>{
   while(next<INTEGRITY.length&&!failure){
    const spec=INTEGRITY[next++],url=asset(spec.file);
    try{
     const immutable=/^data\/[^/]+\.[a-f0-9]{64}\.json$/.test(spec.file);
     let response;
     if(immutable)for(const key of previous){response=await (await caches.open(key)).match(url);if(response)break;}
     response??=await fetch(new Request(url,{cache:immutable?'default':'reload'}));
     await cache.put(url,await verified(response,spec));
    }catch(error){failure=error;}
   }
  }));
  if(failure){await caches.delete(CACHE);throw failure;}
 })());
});
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{
  for(const key of await caches.keys())if(key.startsWith(PREFIX)&&key!==CACHE)await caches.delete(key);
  await self.clients.claim();
 })());
});
self.addEventListener('message',event=>{if(event.data?.type==='ACTIVATE_UPDATE')self.skipWaiting();});
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const url=new URL(event.request.url),base=new URL(self.registration.scope);
 if(url.origin!==base.origin)return;
 const navigation=event.request.mode==='navigate'&&(url.pathname===base.pathname||url.pathname===base.pathname+'index.html');
 const key=navigation?SHELL:FILES.find(file=>new URL(file).pathname===url.pathname);
 if(!key)return; // PDFs, external sources and other projects are not intercepted.
 event.respondWith((async()=>await (await caches.open(CACHE)).match(key)||fetch(event.request))());
});
