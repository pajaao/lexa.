export function setupPwa(){
 if(typeof navigator==='undefined')return;
 const status=document.querySelector('#pwa-status');
 const install=document.querySelector('#pwa-install');
 const banner=document.querySelector('#pwa-update');
 const update=document.querySelector('#pwa-refresh');
 let installPrompt=null,registration=null,reloading=false;
 function connection(){status.textContent=navigator.onLine?'Leitura offline preparada neste navegador.':'Você está offline. A leitura usa a edição salva neste navegador.';}
 window.addEventListener('beforeinstallprompt',event=>{
  event.preventDefault();installPrompt=event;install.hidden=false;
 });
 install.addEventListener('click',async()=>{
  if(!installPrompt)return;
  const prompt=installPrompt;installPrompt=null;install.hidden=true;
  try{await prompt.prompt();await prompt.userChoice;}catch{}
 });
 window.addEventListener('appinstalled',()=>{installPrompt=null;install.hidden=true;});
 if(!('serviceWorker' in navigator)||!['https:','http:'].includes(location.protocol)||!window.isSecureContext){
  status.textContent='A instalação e o acesso offline dependem de um navegador compatível e conexão segura.';return;
 }
 function showUpdate(){if(registration.waiting&&navigator.serviceWorker.controller)banner.hidden=false;}
 navigator.serviceWorker.addEventListener('controllerchange',()=>{if(reloading)location.reload();});
 update.addEventListener('click',()=>{
  if(!registration?.waiting)return;
  reloading=true;update.disabled=true;update.textContent='Atualizando…';
  registration.waiting.postMessage({type:'ACTIVATE_UPDATE'});
 });
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
   connection();window.addEventListener('online',connection);window.addEventListener('offline',connection);
  });
  // A long-lived installed app checks again when the reader comes back online.
  window.addEventListener('online',()=>registration.update().catch(()=>{}));
 }).catch(()=>{status.textContent='Não foi possível preparar a leitura offline. Tente novamente com conexão.';});
}
