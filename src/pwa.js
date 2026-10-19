import {offlineStatusText} from './interface-copy.js';
import {initialCatalog} from './collections.js';
import {loadedResourceFiles} from './loading.js';

export function setupPwa(){
 if(typeof navigator==='undefined')return;
 const status=document.querySelector('#pwa-status'),available=document.querySelector('#pwa-available');
 const install=document.querySelector('#pwa-install'),prepare=document.querySelector('#pwa-cache-all');
 const banner=document.querySelector('#pwa-update'),update=document.querySelector('#pwa-refresh');
 let installPrompt=null,registration=null,reloading=false,reloadOnly=false,preparing=false,lastStatus=null,statusTask=null,controlled=Boolean(navigator.serviceWorker?.controller);
 const size=(initialCatalog.offlineBytes/1e6).toLocaleString('pt-BR',{maximumFractionDigits:1});
 const prepareLabel=`Preparar biblioteca completa offline (~${size} MB)`;
 function display(value){
  lastStatus=value;status.dataset.offlineMode=value.complete?'full':'partial';
  status.textContent=offlineStatusText(value.complete,navigator.onLine);
  available.textContent=value.complete?'Todas as legislações, súmulas, busca e histórico desta edição estão disponíveis offline.':
   (value.collections.length?'Normas disponíveis: '+value.collections.map(code=>code.name).join('; ')+'. ':'Nenhuma norma completa foi guardada ainda. ')+
   (value.searchComplete?'Busca global disponível offline. Abrir uma norma ainda não guardada precisa de conexão.':'Prepare a biblioteca completa para pesquisar todo o acervo sem conexão.');
  prepare.hidden=false;prepare.disabled=value.complete||preparing;prepare.textContent=value.complete?'Biblioteca completa preparada':prepareLabel;
  if(value.error)status.textContent='Não foi possível completar o preparo. Os conteúdos já guardados continuam disponíveis. Tente novamente com conexão.';
 }
 function message(type,extra={}){
  return new Promise((resolve,reject)=>{
   const worker=registration?.active;if(!worker){reject(new Error('Sem worker ativo'));return;}
   const channel=new MessageChannel(),timer=setTimeout(()=>{channel.port1.close();reject(new Error('Sem resposta offline'));},type==='PREPARE_OFFLINE'?900000:15000);
   channel.port1.onmessage=event=>{clearTimeout(timer);channel.port1.close();resolve(event.data);};
   worker.postMessage({type,...extra},[channel.port2]);
  });
 }
 function refreshStatus(){
  if(!statusTask)statusTask=message('OFFLINE_STATUS').then(display).catch(()=>{}).finally(()=>{statusTask=null;});
  return statusTask;
 }
 function cacheVisited(){registration?.active?.postMessage({type:'CACHE_VISITED',files:loadedResourceFiles()});}
 window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installPrompt=event;install.hidden=false;});
 install.addEventListener('click',async()=>{
  if(!installPrompt)return;const prompt=installPrompt;installPrompt=null;install.hidden=true;
  try{await prompt.prompt();await prompt.userChoice;}catch{}
 });
 window.addEventListener('appinstalled',()=>{installPrompt=null;install.hidden=true;});
 if(!('serviceWorker' in navigator)||!['https:','http:'].includes(location.protocol)||!window.isSecureContext){
  status.textContent='A instalação e o acesso offline dependem de um navegador compatível e conexão segura.';return;
 }
 function showUpdate(){if(registration.waiting&&navigator.serviceWorker.controller)banner.hidden=false;}
 navigator.serviceWorker.addEventListener('controllerchange',()=>{
  const previouslyControlled=controlled;controlled=true;
  if(reloading)location.reload();
  else if(previouslyControlled&&registration){reloadOnly=true;banner.hidden=false;}
 });
 navigator.serviceWorker.addEventListener('message',event=>{
  const value=event.data;
  if(value?.type==='OFFLINE_STATUS'){preparing=false;display(value);}
  if(value?.type==='OFFLINE_CHANGED')refreshStatus();
  if(value?.type==='OFFLINE_PROGRESS'){
   preparing=true;prepare.disabled=true;status.dataset.offlineMode='preparing';
   status.textContent=`Preparando biblioteca offline: ${value.done} de ${value.total} arquivos.`;
  }
 });
 prepare.addEventListener('click',async()=>{
  preparing=true;prepare.disabled=true;
  try{const value=await message('PREPARE_OFFLINE');preparing=false;display(value);}
  catch{preparing=false;prepare.disabled=false;status.textContent='Não foi possível completar o preparo. Tente novamente com conexão.';}
 });
 update.addEventListener('click',()=>{
  if(reloadOnly&&!registration?.waiting){location.reload();return;}
  if(!registration?.waiting)return;
  reloading=true;update.disabled=true;update.textContent='Atualizando…';registration.waiting.postMessage({type:'ACTIVATE_UPDATE'});
 });
 window.addEventListener('lexa-resource-ready',()=>{if(registration?.active&&!navigator.serviceWorker.controller)cacheVisited();});
 navigator.serviceWorker.register('./sw.js',{scope:'./',updateViaCache:'none'}).then(value=>{
  registration=value;showUpdate();
  function watchInstallation(){
   const worker=registration.installing;
   worker?.addEventListener('statechange',()=>{
    if(worker.state==='installed')showUpdate();
    if(worker.state==='redundant'&&!navigator.serviceWorker.controller)status.textContent='Não foi possível preparar a leitura offline. Tente recarregar com conexão.';
   });
  }
  watchInstallation();registration.addEventListener('updatefound',watchInstallation);
  navigator.serviceWorker.ready.then(()=>{
   cacheVisited();refreshStatus();
   window.addEventListener('online',()=>{if(lastStatus)display(lastStatus);refreshStatus();registration.update().catch(()=>{});});
   window.addEventListener('offline',()=>{if(lastStatus)display(lastStatus);refreshStatus();});
  });
 }).catch(()=>{status.textContent='Não foi possível preparar a leitura offline. Tente novamente com conexão.';});
}
