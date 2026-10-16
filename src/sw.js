/* The build replaces the version with a hash of the complete offline package. */
const VERSION = '__LEXA_VERSION__';
const HTML_SHA256 = '__LEXA_HTML_SHA256__';
const PREFIX = 'lexa-offline:' + encodeURIComponent(self.registration.scope) + ':';
const CACHE = PREFIX + VERSION;
const asset = path => new URL(path, self.registration.scope).href;
const SHELL = asset('index.html');
const FILES = ['index.html','manifest.webmanifest','favicon.svg','favicon.ico','apple-touch-icon.png','icon-192.png','icon-512.png','icon-maskable-512.png'].map(asset);
self.addEventListener('install', event => {
 // Reject incomplete or failed downloads; never activate a partial legal base.
 event.waitUntil((async()=>{
  const responses = await Promise.all(FILES.map(async url => {
   const response=await fetch(new Request(url,{cache:'reload'}));
   if(!response.ok || response.type==='opaque')throw new Error('Pacote offline incompleto');
   // Consume each body promptly so the large HTML does not hold fetch slots.
   const body=await response.arrayBuffer();
   if(url===SHELL){
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',body)),byte=>byte.toString(16).padStart(2,'0')).join('');
    if(digest!==HTML_SHA256)throw new Error('Edição offline não corresponde à versão publicada');
   }
   return new Response(body,{status:response.status,headers:response.headers});
  }));
  const cache = await caches.open(CACHE);
  await Promise.all(responses.map((response,index)=>cache.put(FILES[index],response)));
 })());
});
self.addEventListener('activate', event => {
 event.waitUntil((async()=>{
  for(const key of await caches.keys())if(key.startsWith(PREFIX)&&key!==CACHE)await caches.delete(key);
  await self.clients.claim();
 })());
});
self.addEventListener('message', event => {
 if(event.data?.type==='ACTIVATE_UPDATE')self.skipWaiting();
});
self.addEventListener('fetch', event => {
 if(event.request.method!=='GET')return;
 const url=new URL(event.request.url);
 const base=new URL(self.registration.scope);
 if(url.origin!==base.origin)return;
 const navigation=event.request.mode==='navigate'&&(url.pathname===base.pathname||url.pathname===base.pathname+'index.html');
 const key=navigation?SHELL:FILES.find(file=>new URL(file).pathname===url.pathname);
 // PDFs, official sources and other projects on this host are never intercepted.
 if(!key)return;
 event.respondWith((async()=>{
  const cached=await (await caches.open(CACHE)).match(key);
  return cached||fetch(event.request);
 })());
});
