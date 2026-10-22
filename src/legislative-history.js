import {escape} from './presentation.js';
import {previousRecords,historicalParts,sourceLink,readingArticle} from './legislative-history-model.js';
import {legislativeHistoryData} from './legislative-history-data.js';

export function historyContent(data,codeId,articleId,currentArticle){
 const records=previousRecords(data,codeId,articleId);
 const caputs=records.filter(record=>record.part==='caput');
 const others=records.filter(record=>record.part!=='caput');
 const timeline=items=>'<ol class="legislative-timeline">'+items.map(record=>
   `<li><p class="legislative-wording">Redação anterior</p><h3>${escape(record.unitLabel||historicalParts[record.part])}</h3>${record.documentaryContext?`<p class="legislative-caution">${escape(record.documentaryContext)}</p>`:''}<p class="legislative-text">${escape(record.text)}</p><p class="legislative-reference">${record.reference?escape(record.reference):'Referência legislativa não informada.'}</p>${record.notes.length?`<details><summary>Notas editoriais</summary>${record.notes.map(note=>`<p>${escape(note)}</p>`).join('')}</details>`:''}</li>`
  ).join('')+'</ol>';
 const content=caputs.length&&others.length?timeline(caputs)+`<details class="legislative-other"><summary>Outras redações anteriores (${others.length})</summary>${timeline(others)}</details>`:timeline(records);
 const intro=data.candidate?'<p class="legislative-demo" role="note">Versão candidata local — publicação ainda não autorizada.</p>':data.preview?'<p class="legislative-demo" role="note">Piloto documental local — não autorizado para publicação. A confirmação local registrada não substitui homologação jurídica humana independente.</p>':data.demo?'<p class="legislative-demo" role="note">Demonstração — todos os registros abaixo são fictícios e não representam legislação.</p>':'';
 return intro+'<p class="legislative-caution">Redações anteriores presentes nas fontes consultadas. Os trechos são reproduzidos sem reconstruir versões completas do artigo.</p>'+(!records.length?
  '<p class="legislative-empty">Ainda não há redações anteriores homologadas disponíveis para este artigo. Isso não significa que ele nunca tenha sido alterado.</p>':
  content+'<details class="legislative-sources"><summary>Fonte e contexto documental</summary>'+records.map((record,index)=>{
   const url=sourceLink(record.source?.url);
   return `<section><h3>Redação ${index+1} · ${escape(record.unitLabel||historicalParts[record.part])}</h3><p>${record.reference?escape(record.reference):'Referência legislativa não informada.'}</p><p>${record.source?.label?escape(record.source.label):'Fonte não informada.'}</p>${record.source?.location?`<p>${escape(record.source.location)}</p>`:''}${url?`<p><a href="${escape(url)}" target="_blank" rel="noopener noreferrer">Consultar fonte ↗</a></p>`:''}<p>Ordem documental: ${escape(record.sequence.basis)}</p><p>${data.candidate?'Versão candidata; publicação ainda não autorizada.':data.publication?.authorized?'Registro documental autorizado para consulta.':data.preview?'Piloto local; homologação jurídica independente pendente.':data.demo?'Registro fictício de demonstração.':'Registro documental aprovado para apresentação.'}</p></section>`;
  }).join('')+'</details>');
}

export function setupLegislativeHistory({reading,code,beforeOpen,data=legislativeHistoryData}){
 const dialog=document.createElement('dialog');
 dialog.className='legislative-panel';dialog.id='legislative-history-panel';
 dialog.setAttribute('aria-labelledby','legislative-history-title');
 dialog.innerHTML='<div class="legislative-heading"><h2 id="legislative-history-title">Redações anteriores</h2><button type="button" aria-label="Fechar redações anteriores" autofocus>Fechar</button></div><div class="legislative-body"></div>';
 reading.append(dialog);
 let previous=null,outsidePointer=null;
 function close(restoreFocus=true){
  if(!previous)return;
  const saved=previous;previous=null;outsidePointer=null;
  if(dialog.open)dialog.close();
  document.body.style.cssText=saved.bodyStyle;
  window.scrollTo({left:saved.x,top:saved.y,behavior:'instant'});
  saved.button.setAttribute('aria-expanded','false');
  if(restoreFocus&&saved.button.isConnected)saved.button.focus({preventScroll:true});
 }
 function open(button){
  if(previous)return;
  beforeOpen();
  previous={x:window.scrollX,y:window.scrollY,bodyStyle:document.body.style.cssText,button};
  dialog.querySelector('h2').textContent=`Redações anteriores · ${code.short} · ${button.dataset.legislativeHistory}`;
  const body=dialog.querySelector('.legislative-body');
  body.innerHTML=historyContent(data,code.id,button.dataset.legislativeHistory,code.articles.find(article=>article.id===button.dataset.legislativeHistory));
  document.body.style.position='fixed';document.body.style.top=-previous.y+'px';
  document.body.style.left='0';document.body.style.right='0';
  button.setAttribute('aria-expanded','true');dialog.showModal();body.scrollTop=0;
  dialog.querySelector('button').focus({preventScroll:true});
 }
 const click=event=>{const button=event.target.closest('[data-legislative-history]');if(button&&reading.contains(button))open(button);};
 reading.addEventListener('click',click);
 dialog.querySelector('button').onclick=()=>close();
 dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
 dialog.addEventListener('close',()=>close());
 const isOutside=event=>{
  const rect=dialog.getBoundingClientRect();
  return event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom;
 };
 // Both ends must be on the backdrop: selecting text or dragging across the
 // panel boundary must not dismiss the history accidentally.
 dialog.addEventListener('pointerdown',event=>{
  outsidePointer=event.isPrimary&&event.button===0&&isOutside(event)?event.pointerId:null;
 });
 dialog.addEventListener('pointerup',event=>{
  const dismiss=outsidePointer===event.pointerId&&isOutside(event);
  outsidePointer=null;
  if(dismiss)close();
 });
 dialog.addEventListener('pointercancel',()=>{outsidePointer=null;});
 dialog.addEventListener('keydown',event=>{
  if(event.key!=='Tab')return;
  const targets=[...dialog.querySelectorAll('button,a[href],summary')].filter(el=>el.getClientRects().length);
  const destination=event.shiftKey&&document.activeElement===targets[0]?targets.at(-1):!event.shiftKey&&document.activeElement===targets.at(-1)?targets[0]:null;
  if(destination){event.preventDefault();destination.focus({preventScroll:true});}
 });
 return {readingArticle(article){return readingArticle(data,code.id,article);},hasRecords(articleId){return previousRecords(data,code.id,articleId).length>0;},get isOpen(){return dialog.open;},cleanup(){close(false);reading.removeEventListener('click',click);dialog.remove();}};
}
