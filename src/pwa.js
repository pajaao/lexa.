import {offlineStatusText} from './interface-copy.js';
import {initialCatalog} from './collections.js';
import {loadedResourceFiles} from './loading.js';

export function setupPwa(){
 if(typeof navigator==='undefined')return;
 const status=document.querySelector('#pwa-status'),available=document.querySelector('#pwa-available');
 const install=document.querySelector('#pwa-install'),prepare=document.querySelector('#pwa-cache-all');
 const banner=document.querySelector('#pwa-update'),update=document.querySelector('#pwa-refresh');
 const check=document.querySelector('#pwa-check'),checkStatus=document.querySelector('#pwa-check-status');
 const checkInterval=5*60*1000;
 let checkTask=null,lastCheck=0;
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
 function checkState(state,text){checkStatus.dataset.state=state;checkStatus.textContent=text;}
 if(!('serviceWorker' in navigator)||!['https:','http:'].includes(location.protocol)||!window.isSecureContext){
  checkState('unsupported','A verificação de atualizações depende de um navegador compatível e conexão segura.');
  status.textContent='A instalação e o acesso offline dependem de um navegador compatível e conexão segura.';return;
 }
 function showUpdate(){
  if((registration.waiting&&navigator.serviceWorker.controller)||reloadOnly){
   banner.hidden=false;checkState('available','Uma atualização está disponível. Use “Atualizar agora” para aplicá-la.');return true;
  }
  return false;
 }
 function waitForInstallation(worker){
  return new Promise((resolve,reject)=>{
   function changed(){
    if(!['installed','activated','redundant'].includes(worker.state))return;
    worker.removeEventListener('statechange',changed);
    if(worker.state==='redundant')reject(new Error('Instalação rejeitada'));else resolve();
   }
   worker.addEventListener('statechange',changed);changed();
  });
 }
 function checkUpdates(manual=false){
  if(!registration||checkTask)return checkTask;
  if(showUpdate())return;
  if(!manual&&Date.now()-lastCheck<checkInterval)return;
  // Keep keyboard focus; checkTask prevents repeated activation while aria-disabled.
  lastCheck=Date.now();check.setAttribute('aria-disabled','true');check.setAttribute('aria-busy','true');
  checkState('checking','Verificando atualizações…');
  checkTask=Promise.resolve().then(async()=>{
   try{
    if(!navigator.onLine)throw new Error('Sem conexão');
    await registration.update();
    if(registration.installing)await waitForInstallation(registration.installing);
    if(!showUpdate())checkState('current','O Lexa está atualizado.');
   }catch{
    if(!showUpdate())checkState('error','Não foi possível verificar ou preparar a atualização. Sua edição continua disponível. Tente novamente com conexão.');
   }finally{checkTask=null;check.removeAttribute('aria-disabled');check.removeAttribute('aria-busy');}
  });
  return checkTask;
 }
 check.addEventListener('click',()=>{checkUpdates(true);});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')checkUpdates();});
 navigator.serviceWorker.addEventListener('controllerchange',()=>{
  const previouslyControlled=controlled;controlled=true;
  if(reloading)location.reload();
  else if(previouslyControlled&&registration){reloadOnly=true;showUpdate();}
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
  registration=value;lastCheck=Date.now();check.disabled=false;showUpdate();
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
   window.addEventListener('online',()=>{if(lastStatus)display(lastStatus);refreshStatus();checkUpdates();});
   window.addEventListener('offline',()=>{if(lastStatus)display(lastStatus);refreshStatus();});
  });
 }).catch(()=>{
  checkState('error','Não foi possível iniciar a verificação de atualizações. Tente recarregar com conexão.');
  status.textContent='Não foi possível preparar a leitura offline. Tente novamente com conexão.';
 });
}
