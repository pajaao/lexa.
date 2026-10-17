/* Every cached file belongs to a build manifest and is verified before use. */
const VERSION = '__LEXA_VERSION__';
const INTEGRITY = __LEXA_INTEGRITY_MANIFEST__;
const COLLECTIONS = __LEXA_COLLECTION_FILES__;
const PREFIX='lexa-offline:'+encodeURIComponent(self.registration.scope)+':';
const CACHE=PREFIX+VERSION;
const asset=path=>new URL(path,self.registration.scope).href;
const SHELL=asset('index.html'),MARKER=asset('__lexa_offline_state__');
const specs=new Map(INTEGRITY.map(spec=>[asset(spec.file),spec]));
const pending=new Map();let preparing=null;
async function verified(response,spec){
 if(!response?.ok||response.type==='opaque')throw new Error('Arquivo indisponível');
 const body=await response.arrayBuffer();
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',body)),byte=>byte.toString(16).padStart(2,'0')).join('');
 if(digest!==spec.sha256)throw new Error('Arquivo não corresponde à edição publicada');
 return new Response(body,{status:response.status,headers:response.headers});
}
const immutable=file=>file.startsWith('data/')||/^app\/[a-f0-9]{64}\//.test(file);
async function previousCaches(){return (await caches.keys()).filter(key=>key.startsWith(PREFIX)&&key!==CACHE).reverse();}
async function metadata(key){try{return await (await (await caches.open(key)).match(MARKER))?.json();}catch{return null;}}
async function ensureFile(spec,previous=[]){
 const url=asset(spec.file);
 if(!pending.has(url))pending.set(url,(async()=>{
  const cache=await caches.open(CACHE);
  for(const key of [CACHE,...previous]){
   const stored=await (await caches.open(key)).match(url);
   if(!stored)continue;
   try{
    const response=await verified(stored,spec);
    if(key!==CACHE)await cache.put(url,response.clone());
    return response;
   }catch{if(key===CACHE)await cache.delete(url);}
  }
  let response=await fetch(new Request(url,{cache:immutable(spec.file)?'default':'reload'}));
  try{response=await verified(response,spec);}catch(error){
   // Repair a stale/corrupt HTTP cache once; ordinary valid downloads are shared.
   if(!immutable(spec.file))throw error;
   response=await verified(await fetch(new Request(url,{cache:'reload'})),spec);
  }
  await cache.put(url,response.clone());return response;
 })().finally(()=>pending.delete(url)));
 return (await pending.get(url)).clone();
}
async function writeState(full,previous){
 await (await caches.open(CACHE)).put(MARKER,new Response(JSON.stringify({version:VERSION,full,previous,integrity:INTEGRITY}),{headers:{'Content-Type':'application/json'}}));
}
async function fill(selected,previous,progress){
 let next=0,done=0,failure;
 await Promise.all(Array.from({length:3},async()=>{
  while(next<selected.length&&!failure){
   try{await ensureFile(selected[next++],previous);done++;progress?.(done,selected.length);}
   catch(error){failure=error;}
  }
 }));
 if(failure)throw failure;
}
async function status(){
 const cache=await caches.open(CACHE),keys=new Set((await cache.keys()).map(request=>request.url));
 return {type:'OFFLINE_STATUS',version:VERSION,
  complete:INTEGRITY.every(spec=>keys.has(asset(spec.file))),
  collections:COLLECTIONS.filter(code=>keys.has(asset(code.file))).map(code=>({id:code.id,name:code.name})),
  searchComplete:COLLECTIONS.every(code=>keys.has(asset(code.search))),
  cachedFiles:INTEGRITY.filter(spec=>keys.has(asset(spec.file))).length,totalFiles:INTEGRITY.length};
}
async function announce(message){for(const client of await self.clients.matchAll({type:'window'}))client.postMessage(message);}
self.addEventListener('install',event=>{
 event.waitUntil((async()=>{
  const previous=await previousCaches();let full=false;
  const retained=new Set();
  for(const key of previous){
   const old=await metadata(key),oldCache=await caches.open(key);
   const keys=new Set((await oldCache.keys()).map(request=>request.url));
   // Editions predating this marker always installed the complete library.
   if(old?.full||(!old&&keys.has(SHELL)))full=true;
   for(const spec of old?.integrity||[])if(spec.role&&keys.has(asset(spec.file)))retained.add(spec.role+':'+(spec.codeId||''));
  }
  await writeState(full,previous);
  const wanted=INTEGRITY.filter(spec=>full||!spec.file.startsWith('data/')||retained.has(spec.role+':'+(spec.codeId||'')));
  try{await fill(wanted,previous);await writeState(full,previous);}
  catch(error){await caches.delete(CACHE);throw error;}
 })());
});
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{
  const old=(await metadata(CACHE))?.previous||[];
  const clients=await self.clients.matchAll({type:'window',includeUncontrolled:true});
  // Keep one prior edition while another tab may still be reading its files.
  const keep=clients.length>1?old[0]:null;
  for(const key of old)if(key!==keep)await caches.delete(key);
  await self.clients.claim();
 })());
});
async function prepareAll(){
 if(!preparing)preparing=(async()=>{
  const old=(await metadata(CACHE))?.previous||[];
  await fill(INTEGRITY,await previousCaches(),(done,total)=>{announce({type:'OFFLINE_PROGRESS',done,total});});
  await writeState(true,old);await announce(await status());
 })().finally(()=>{preparing=null;});
 return preparing;
}
self.addEventListener('message',event=>{
 const reply=value=>event.ports[0]?.postMessage(value);
 if(event.data?.type==='ACTIVATE_UPDATE'){self.skipWaiting();return;}
 if(event.data?.type==='OFFLINE_STATUS')event.waitUntil(status().then(reply));
 if(event.data?.type==='PREPARE_OFFLINE')event.waitUntil(prepareAll().then(async()=>reply(await status())).catch(async()=>{const value={...await status(),error:true};await announce(value);reply(value);}));
 if(event.data?.type==='CACHE_VISITED')event.waitUntil((async()=>{
  const selected=(event.data.files||[]).map(file=>specs.get(asset(file))).filter(Boolean);
  try{await fill(selected,await previousCaches());}catch{}
  await announce(await status());
 })());
});
async function oldImmutable(url){
 for(const key of await previousCaches()){
  const stored=await (await caches.open(key)).match(url);if(!stored)continue;
  const old=await metadata(key);
  const filenameHash=/\.([a-f0-9]{64})\.json$/.exec(new URL(url).pathname)?.[1];
  const spec=filenameHash?{sha256:filenameHash}:old?.integrity?.find(spec=>asset(spec.file)===url);
  if(spec)try{return await verified(stored,spec);}catch{}
 }
 return null;
}
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const url=new URL(event.request.url),base=new URL(self.registration.scope);
 if(url.origin!==base.origin)return;
 const navigation=event.request.mode==='navigate'&&(url.pathname===base.pathname||url.pathname===base.pathname+'index.html');
 const key=navigation?SHELL:[...specs.keys()].find(file=>new URL(file).pathname===url.pathname);
 const legacy=!key&&(url.pathname.startsWith(base.pathname+'data/')||url.pathname.startsWith(base.pathname+'app/'));
 if(!key&&!legacy)return;
 const task=(async()=>{
  if(!key)return await oldImmutable(url.href)||fetch(event.request);
  const response=await ensureFile(specs.get(key),await previousCaches());
  return response;
 })();
 event.respondWith(task);
 if(key&&specs.get(key).file.startsWith('data/'))event.waitUntil(task.then(()=>announce({type:'OFFLINE_CHANGED'})).catch(()=>{}));
});
