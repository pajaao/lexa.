import {articleLabel} from './data.js';
import {escape,codeHref,highlight} from './presentation.js';
import {compactField} from './search-index.js';
import {selectLibraryMatch,libraryExcerpt} from './library-search.js';

// The mobile dialog owns only draft input/results. Reading state is committed
// by the reader only after a result is selected; cancel never redraws it.
export function setupReaderSearch({reading,field,input,trigger,mobile,code,getSelection,search,alternative,select,beforeOpen,desktopInput,pageSize}){
 const home=field.parentElement,next=field.nextSibling;
 const dialog=document.createElement('dialog');dialog.className='reader-search-panel';dialog.id='reader-search-panel';
 dialog.setAttribute('aria-labelledby','reader-search-title');
 dialog.innerHTML='<div class="reader-search-heading"><h2 id="reader-search-title">Buscar</h2><button class="reader-search-close">Cancelar</button></div><p class="reader-search-context"></p><div class="reader-search-input"></div><div class="reader-search-actions"><button class="reader-search-clear">Limpar pesquisa</button><p class="reader-search-status" role="status" aria-live="polite"></p></div><div class="reader-search-results" role="region" aria-label="Resultados da busca"></div>';
 reading.append(dialog);
 const results=dialog.querySelector('.reader-search-results'),status=dialog.querySelector('.reader-search-status');
 let session=null,draft=null,timer,desktopPending=false,limit=pageSize,matches=[],viewport=null;
 const closeButton=dialog.querySelector('.reader-search-close');
 const originalHint=input.getAttribute('enterkeyhint');
 function updateViewport(){
  if(!session)return;
  const visible=window.visualViewport;
  dialog.style.setProperty('--search-height',(visible?.height||window.innerHeight)+'px');
  dialog.style.setProperty('--search-top',(visible?.offsetTop||0)+'px');
  dialog.classList.toggle('short-search',(visible?.height||window.innerHeight)<=500);
 }
 function excerpt(article,value){
  const fields=[...article.paragraphs.map(p=>compactField('text',p.runs)),
   ...(article.title?[compactField('title',[{text:article.title}])]:[]),
   ...(article.notes||[]).map(p=>compactField('notes',p.runs))];
  const match=selectLibraryMatch(fields,value);
  if(!match)return '';
  const preview=libraryExcerpt(match,180);
  return `<p>${preview.leading?'…':''}${preview.runs.map(run=>run.deleted?`<del>${highlight(run.text,value)}</del>`:highlight(run.text,value)).join('')}${preview.trailing?'…':''}</p>${match.kind==='notes'?'<small>Precedentes, jurisprudência ou observações</small>':''}${match.deleted?'<small>Ocorrência em trecho riscado na fonte</small>':''}`;
 }
 function choose(article){
  if(!session)return;
  const value=input.value,selection=session.selection;
  close(false);draft=value;select(article,value,selection);
 }
 function render(){
  if(!session)return;
  const value=input.value;
  matches=search(value,session.selection);
  const other=!matches.length?alternative(value):null;
  status.textContent=`${matches.length} ${matches.length===1?'entrada encontrada':'entradas encontradas'}`;
  results.innerHTML=matches.length?`<ul>${matches.slice(0,limit).map(article=>`<li><a href="${escape(codeHref(code,article.id)+'?q='+encodeURIComponent(value))}" data-search-result="${escape(article.id)}"><strong>${escape(articleLabel(article))} · ${escape(code.short)}</strong>${article.title?`<span>${highlight(article.title,value)}</span>`:''}<small>${escape(article.section||'')}</small>${excerpt(article,value)}</a></li>`).join('')}</ul>${matches.length>limit?'<button class="reader-search-more">Mostrar mais resultados</button>':''}`:'<p class="reader-search-empty">Nenhuma entrada nesta seleção. Tente outra expressão ou confira os filtros da leitura.</p>';
  results.querySelectorAll('[data-search-result]').forEach(link=>link.onclick=event=>{
   if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
   event.preventDefault();choose(matches.find(article=>article.id===link.dataset.searchResult));
  });
  if(other){
   const link=document.createElement('a');link.className='reader-search-alternative';link.href=codeHref(other.code,other.article.id);
   link.textContent=`Abrir ${articleLabel(other.article)} · ${other.code.name}`;
   link.onclick=event=>{if(!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey)close(false);};
   results.append(link);
  }
  results.querySelector('.reader-search-more')?.addEventListener('click',()=>{
   limit+=pageSize;render();results.querySelectorAll('[data-search-result]')[limit-pageSize]?.focus({preventScroll:true});
  });
 }
 function onInput(){
  clearTimeout(timer);
  if(session){
   draft=input.value;limit=pageSize;matches=[];results.replaceChildren();results.scrollTop=0;status.textContent='Pesquisando…';
   timer=setTimeout(render,120);
  }else{draft=input.value;desktopPending=true;timer=setTimeout(()=>{desktopPending=false;desktopInput(input.value);},120);}
 }
 input.addEventListener('input',onInput);
 function close(restoreFocus=true){
  if(!session)return;
  clearTimeout(timer);desktopPending=false;
  const previous=session;session=null;draft=input.value;matches=[];
  viewport?.removeEventListener('resize',updateViewport);viewport?.removeEventListener('scroll',updateViewport);viewport=null;
  dialog.close();home.insertBefore(field,next);input.value=previous.value;
  if(originalHint===null)input.removeAttribute('enterkeyhint');else input.setAttribute('enterkeyhint',originalHint);
  document.body.style.cssText=previous.bodyStyle;
  window.scrollTo({left:previous.x,top:previous.y,behavior:'instant'});
  trigger.setAttribute('aria-expanded','false');
  if(restoreFocus)trigger.focus({preventScroll:true});
 }
 function open(){
  if(!mobile.matches||session)return;
  beforeOpen();clearTimeout(timer);desktopPending=false;
  session={selection:getSelection(),value:input.value,x:window.scrollX,y:window.scrollY,bodyStyle:document.body.style.cssText};
  dialog.querySelector('.reader-search-context').textContent=[code.name,session.selection.scope==='adct'?'ADCT':'',session.selection.sectionId?'Divisão selecionada':'',session.selection.onlySaved?'Somente favoritos':''].filter(Boolean).join(' · ');
  input.value=draft??input.value;limit=pageSize;
  dialog.querySelector('.reader-search-input').append(field);
  input.setAttribute('enterkeyhint','search');
  document.body.style.position='fixed';document.body.style.top=-session.y+'px';document.body.style.left='0';document.body.style.right='0';
  viewport=window.visualViewport;viewport?.addEventListener('resize',updateViewport);viewport?.addEventListener('scroll',updateViewport);
  updateViewport();trigger.setAttribute('aria-expanded','true');dialog.showModal();input.focus({preventScroll:true});render();
 }
 trigger.onclick=open;closeButton.onclick=()=>close();
 dialog.querySelector('.reader-search-clear').onclick=()=>{input.value='';draft='';limit=pageSize;clearTimeout(timer);render();input.focus({preventScroll:true});};
 dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
 dialog.addEventListener('close',()=>{if(!dialog.open)close();});
 dialog.addEventListener('keydown',event=>{
  if(event.key==='Enter'&&event.target===input){
   event.preventDefault();clearTimeout(timer);render();
   if(matches.length===1)choose(matches[0]);else results.querySelector('a')?.focus();
  }
  if(event.key!=='Tab')return;
  const targets=[...dialog.querySelectorAll('button,input,a')].filter(el=>!el.disabled&&el.getClientRects().length);
  const destination=event.shiftKey&&document.activeElement===targets[0]?targets.at(-1):
   !event.shiftKey&&document.activeElement===targets.at(-1)?targets[0]:null;
  if(destination){event.preventDefault();destination.focus({preventScroll:true});}
 });
 function responsive(){
  const focused=field.contains(document.activeElement)||Boolean(session);
  if(desktopPending){clearTimeout(timer);desktopPending=false;desktopInput(input.value);}
  close(false);
  trigger.setAttribute('aria-controls',mobile.matches?dialog.id:field.id);
  if(mobile.matches)trigger.setAttribute('aria-haspopup','dialog');else trigger.removeAttribute('aria-haspopup');
  if(focused)(mobile.matches?trigger:input).focus({preventScroll:true});
 }
 responsive();mobile.addEventListener('change',responsive);
 return {open,close,get isOpen(){return dialog.open;},cleanup(){close(false);clearTimeout(timer);input.removeEventListener('input',onInput);mobile.removeEventListener('change',responsive);dialog.remove();}};
}
