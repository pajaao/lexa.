import {readerModel} from './reader-model.js';
import {articleCopyText} from './copy.js';
import {sectionPath,unitKind} from './structure.js';
import {normalize,searchArticles,articleById,articleLabel,parseReference,searchLibraryReferences} from './data.js';
import {escape,number,codeHref,collectionDate,sourcePanel,highlight,sectionHeadings} from './presentation.js';

export function reader(code, requested, params, context) {
 const {app,state,readingPreferences,storageWrite,historyArticleIds,copyContent,toast}=context;
 const target=requested?articleById(code,requested):null;
 let scope=target?.scope || (params.get('scope')==='adct'?'adct':'main');
 let query=params.get('q') || (requested&&!target?requested:'');
 let onlySaved=params.get('saved')==='1';
 let page=0, sectionId=null;
 const pageSize=15;
 document.title=`${escape(code.short)} · ${escape(code.name)} — Lexa`;
 const source=code.source;
 const isSumula=code.kind==='sumulas';
 app.innerHTML=`<section class="reader-top"><a class="back" href="#">← Voltar à biblioteca</a><div class="eyebrow">${escape(code.area)}</div><h1>${escape(code.name)}</h1><p>${escape(code.law)} <span>·</span> <a href="#/atualizacoes?codigo=${escape(code.id)}">Histórico de versões</a> <span>·</span> <a href="${escape(code.url)}" target="_blank" rel="noopener noreferrer">Fonte oficial ↗</a></p><div class="reading-notice"><strong>${escape(source.edition)}</strong> <br>${['official_html','official_stf'].includes(source.kind)?'Coleta da fonte oficial · '+collectionDate(source):isSumula?'Data de consulta declarada no PDF · 16/10/2026':'Importação do PDF fornecido · '+source.importedAt.split('-').reverse().join('/')} · Confira as notas de vigência.</div><details class="source-details"><summary>Sobre esta versão e a fonte de origem</summary>${sourcePanel(source)}</details></section><div class="reader-layout"><aside><details class="reader-index" ${window.innerWidth>700?'open':''}><summary>${isSumula?'Índice das súmulas':'Índice da legislação'}</summary><p class="index-note">${isSumula?'Escolha um intervalo para navegar pelas súmulas.':'Expanda as divisões e escolha o trecho que deseja ler.'}</p><div id="index-list"></div></details></aside><section class="reading">${code.id==='cf'?'<div class="scope-tabs" role="group" aria-label="Parte da Constituição"><button data-scope="main">Constituição</button><button data-scope="adct">ADCT</button></div>':''}<div class="reading-controls"><div class="reading-context"><span class="reading-position"><strong>${escape(code.short)}</strong><span id="reading-location">Leitura</span></span><button id="focus-mode" aria-pressed="false">Modo de foco</button></div><div class="reading-toolbar"><label class="search"><span>⌕</span><input id="article-search" placeholder="${isSumula?'Buscar expressão ou súmula (ex.: SV 13)':'Buscar expressão ou artigo (ex.: 5 ou 54-A)'}" aria-label="${isSumula?'Buscar nas súmulas vinculantes':'Buscar nesta legislação'}"></label></div><details class="reading-settings" ${window.innerWidth>700?'open':''}><summary>Ajustes de leitura <span id="font-size" role="status"></span></summary><div class="reading-adjustments"><div class="font-controls" role="group" aria-label="Tamanho da fonte"><button id="font-down" aria-label="Diminuir fonte">A−</button><button id="font-up" aria-label="Aumentar fonte">A+</button></div><div class="reading-spacing-control"><label for="reading-spacing">Espaçamento</label><select id="reading-spacing"><option value="standard">Padrão</option><option value="comfortable">Confortável</option><option value="wide">Amplo</option></select></div><button id="reset-reading">Restaurar leitura</button></div></details></div><div class="reader-options"><button id="saved-filter" aria-pressed="${onlySaved}">☆ Meus favoritos</button><button id="clear-section" hidden>Limpar divisão selecionada ×</button><span id="results-label" role="status"></span></div><div id="introduction"></div><div id="articles"></div><nav class="pagination" aria-label="Páginas de leitura"><button id="previous-page">← Anteriores</button><span id="page-label"></span><button id="next-page">Próximos →</button></nav></section></div>`;
 const input=document.querySelector('#article-search');input.value=query;
 let active=true, positionTimer, focusMode=false;
 const reading=document.querySelector('.reading');
 const controls=document.querySelector('.reading-controls');
 const updateReadingOffset=()=>reading.style.setProperty('--reading-offset',Math.ceil(controls.getBoundingClientRect().height+24)+'px');
 const controlsObserver=typeof ResizeObserver!=='undefined'?new ResizeObserver(updateReadingOffset):null;
 controlsObserver?.observe(controls);updateReadingOffset();
 function rememberPosition(){
  if(!active)return;
  const entries=[...document.querySelectorAll('#articles .article')];
  const line=Math.min(window.innerHeight*0.45,300);
  const current=entries.find(el=>{const rect=el.getBoundingClientRect();return rect.bottom>line&&rect.top<=line;});
  if(current){storageWrite('lexa-last-reading',{codeId:code.id,articleId:current.id.slice(4)});updateLocation(current.dataset.sectionId);}
 }
 const onScroll=()=>{clearTimeout(positionTimer);positionTimer=setTimeout(rememberPosition,180);};
 window.addEventListener('scroll',onScroll,{passive:true});
 state.cleanupReader=()=>{rememberPosition();controlsObserver?.disconnect();active=false;clearTimeout(positionTimer);window.removeEventListener('scroll',onScroll);document.body.classList.remove('reading-focus');};
 function applyPreferences(){
  reading.style.setProperty('--reading-size',readingPreferences.size+'px');
  reading.dataset.spacing=readingPreferences.spacing;
  document.querySelector('#reading-spacing').value=readingPreferences.spacing;
  document.querySelector('#font-size').textContent=readingPreferences.size+' px';
  document.querySelector('#font-down').disabled=readingPreferences.size===16;
  document.querySelector('#font-up').disabled=readingPreferences.size===26;
 }
 function savePreferences(){applyPreferences();if(!storageWrite('lexa-reading',readingPreferences))toast('Ajustes temporários: armazenamento indisponível');}
 document.querySelector('#reading-spacing').onchange=e=>{readingPreferences.spacing=e.target.value;savePreferences();};
 document.querySelector('#reset-reading').onclick=()=>{readingPreferences.size=19;readingPreferences.spacing='standard';savePreferences();};
 const focusButton=document.querySelector('#focus-mode');
 function setFocus(value){
  const line=Math.min(window.innerHeight*0.45,300);
  const anchor=[...document.querySelectorAll('#articles .article')].find(el=>{const rect=el.getBoundingClientRect();return rect.top<=line&&rect.bottom>line;});
  const top=anchor?.getBoundingClientRect().top;
  focusMode=value;document.body.classList.toggle('reading-focus',value);
  focusButton.setAttribute('aria-pressed',String(value));focusButton.textContent=value?'Sair do foco':'Modo de foco';
  if(anchor)window.scrollBy({top:anchor.getBoundingClientRect().top-top,behavior:'instant'});
  else focusButton.scrollIntoView({block:'nearest'});
 }
 focusButton.onclick=()=>setFocus(!focusMode);
 const onEscape=e=>{if(e.key==='Escape'&&focusMode&&!document.querySelector('#copy-dialog').open){setFocus(false);focusButton.focus();}};
 document.addEventListener('keydown',onEscape);
 const previousCleanup=state.cleanupReader;state.cleanupReader=()=>{document.removeEventListener('keydown',onEscape);previousCleanup();};
 applyPreferences();
 const {sectionMap,trees,bySection}=readerModel(code);
 let expanded=new Set(),indexInitialized=false,indexMarkupKey=null,selectionCache=null;
 function selectedArticles(){
  if(selectionCache&&selectionCache.query===query&&selectionCache.scope===scope&&selectionCache.sectionId===sectionId&&selectionCache.onlySaved===onlySaved&&selectionCache.saved===state.saved)return selectionCache.articles;
  const ids=sectionId?.startsWith('branch:')?trees.get(scope).nodes.get(sectionId.slice(7))?.sectionIds:null;
  const articles=searchArticles(code,query,scope).filter(a=>(!sectionId||(ids?ids.includes(a.sectionId):a.sectionId===sectionId))&&(!onlySaved||state.saved.includes(code.id+'/'+a.id)));
  selectionCache={query,scope,sectionId,onlySaved,saved:state.saved,articles};return articles;
 }
 function updateLocation(id){
  const section=sectionMap.get(id);if(!section)return;
  const locationLabel=document.querySelector('#reading-location');
  locationLabel.textContent=sectionPath(section).slice(-2).join(' › ');locationLabel.title=section.title;
  document.querySelectorAll('#index-list [data-section]').forEach(button=>{
   if(button.dataset.section===id)button.setAttribute('aria-current','location');else button.removeAttribute('aria-current');
  });
 }
 function drawIndex(currentSection){
  const key=JSON.stringify([scope,sectionId,query]);
  if(indexInitialized&&!query&&!sectionId&&indexMarkupKey===key){
   if(currentSection)updateLocation(currentSection);else document.querySelectorAll('#index-list [aria-current]').forEach(button=>button.removeAttribute('aria-current'));
   return;
  }
  indexMarkupKey=key;
  const tree=trees.get(scope);
  if(!indexInitialized||query||sectionId){for(const node of tree.nodes.values())if(node.sectionIds.includes(currentSection))expanded.add(node.id);indexInitialized=true;}
  const range=entries=>{const first=entries[0],last=entries.at(-1);return first?`${articleLabel(first)}${entries.length>1?' – '+articleLabel(last):''}`:'';};
  const render=node=>{
   const title=escape(node.label);
   const renderSection=id=>`<button class="index-entry ${sectionId===id?'selected':''}" data-section="${id}"><span>${node.children.length?'Ler os artigos desta divisão':title}</span><small>${escape(range(bySection.get(id)||[]))}</small></button>`;
   const body=node.items.map(item=>item.kind==='section'?renderSection(item.id):render(item.node)).join('');
   if(!node.children.length)return body;
   return `<details class="index-branch" data-node="${node.id}" ${expanded.has(node.id)?'open':''}><summary>${title}<small>${escape(range(node.articles))}</small></summary><div class="index-children"><button class="index-all ${sectionId==='branch:'+node.id?'selected':''}" data-branch="${node.id}" aria-pressed="${sectionId==='branch:'+node.id}">Ler esta divisão · ${node.articles.length} entradas</button>${body}</div></details>`;
  };
  document.querySelector('#index-list').innerHTML=tree.roots.map(render).join('');
  document.querySelectorAll('#index-list [data-node]').forEach(details=>details.addEventListener('toggle',()=>{if(details.open)expanded.add(details.dataset.node);else expanded.delete(details.dataset.node);}));
  document.querySelectorAll('#index-list [data-section],#index-list [data-branch]').forEach(button=>button.onclick=event=>{
   sectionId=button.dataset.branch?'branch:'+button.dataset.branch:button.dataset.section;
   query='';input.value='';page=0;draw();if(window.innerWidth<=700)document.querySelector('.reader-index').open=false;scrollReading(event.detail===0);
  });
  updateLocation(currentSection);
 }
 function scrollReading(focusContent=false){
  requestAnimationFrame(()=>{
   if(!active)return;
   updateReadingOffset();
   const first=document.querySelector('#articles .article, #articles .empty');if(!first)return;
   const link=first.querySelector('.article-heading>a, h3');
   const offset=Math.ceil(controls.getBoundingClientRect().height)+24;
   // Keep as much legislative context as fits, while showing the first article.
   // A sticky toolbar is not a document-position target for a new content page.
   const headings=[...(first.previousElementSibling?.querySelectorAll('.legal-heading')||[])];
   const paragraph=first.querySelector('.legal-unit');
   const end=paragraph?paragraph.getBoundingClientRect().top+parseFloat(getComputedStyle(paragraph).lineHeight):link.getBoundingClientRect().bottom;
   const destination=headings.find(heading=>end-heading.getBoundingClientRect().top<=window.innerHeight-offset-24)||first;
   const top=window.scrollY+destination.getBoundingClientRect().top-offset;
   if(first.matches('.article')){
    storageWrite('lexa-last-reading',{codeId:code.id,articleId:first.id.slice(4)});
    updateLocation(first.dataset.sectionId);
   }
   if(focusContent){if(link.tagName!=='A')link.tabIndex=-1;link.focus({preventScroll:true});}
   window.scrollTo({top:Math.max(0,top),behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  });
 }
 function draw(){
  const list=selectedArticles();
  const otherReference=!list.length?searchLibraryReferences(query)?.find(result=>result.code.id!==code.id):null;
  const searchNotes=query.trim()&&!/^(?:(?:sv|sumula(?: vinculante)?)\s*(?:n[º°o.]?\s*)?)?\d+\.?$/i.test(normalize(query));
  const pages=Math.max(1,Math.ceil(list.length/pageSize));page=Math.min(page,pages-1);
  const visible=list.slice(page*pageSize,(page+1)*pageSize);
  document.querySelector('#results-label').textContent=`${number(list.length)} ${list.length===1?'entrada':'entradas'}${query?(list.length===1?' encontrada':' encontradas'):''}`;
  document.querySelector('#saved-filter').setAttribute('aria-pressed',String(onlySaved));
  document.querySelector('#clear-section').hidden=!sectionId;
  document.querySelectorAll('[data-scope]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.scope===scope)));
  document.querySelector('#introduction').innerHTML=code.id==='cf'&&scope==='main'&&!query&&!onlySaved&&!sectionId&&page===0?code.introductions.map(intro=>`<details class="preamble"><summary>${escape(intro.title)}</summary><p>${escape(intro.text)}</p></details>`).join(''):'';
  let last=null;
  document.querySelector('#articles').innerHTML=visible.map(a=>{
   const heading=last!==a.sectionId?sectionHeadings(sectionMap.get(a.sectionId),sectionMap.get(last)):'';
   last=a.sectionId;
   const hasDeleted=a.paragraphs.some(p=>p.runs.some(r=>r.deleted));
   return `${heading}<article id="art-${a.id}" data-section-id="${a.sectionId}" class="article ${target?.id===a.id?'focused-article':''}"><div class="article-heading"><a href="${codeHref(code,a.id)}">${articleLabel(a)}</a><div><button data-save="${a.id}" aria-label="Favoritar ${articleLabel(a)}" aria-pressed="${state.saved.includes(code.id+'/'+a.id)}">${state.saved.includes(code.id+'/'+a.id)?'★':'☆'}</button><details class="article-copy"><summary aria-label="Opções de cópia de ${articleLabel(a)}">Copiar <span aria-hidden="true">⌄</span></summary><div class="copy-menu"><button data-copy-text="${a.id}">${isSumula?'Enunciado e referência':'Texto e referência'}</button><button data-copy="${a.id}">Copiar link</button></div></details></div></div>${a.status==='cancelled'?`<p class="sumula-status">Cancelada — conforme indicado ${source.kind==='official_stf'?'na fonte consultada':'no PDF'}</p>`:a.status==='pending'?`<p class="sumula-status">Pendente de publicação — conforme indicado ${source.kind==='official_stf'?'na fonte consultada':'no PDF'}</p>`:a.status==='suspended'?'<p class="sumula-status">Suspensa — conforme indicado na fonte consultada</p>':''}${a.title?`<h3 class="article-title">${highlight(a.title,query)}</h3>`:''}${hasDeleted?'<p class="deleted-note">Trechos riscados na fonte original estão preservados como redações anteriores ou suprimidas.</p>':''}${a.paragraphs.map((p,index)=>`<p class="legal-unit unit-${unitKind(p,index)}${p.runs.every(r=>r.deleted||!r.text.trim())?' deleted-paragraph':''}">${p.runs.map(r=>r.deleted?`<del>${highlight(r.text,query)}</del>`:highlight(r.text,query)).join('')}</p>`).join('')}${a.notes?.length?`<details class="sumula-notes" ${searchNotes&&a.notes.some(p=>normalize(p.runs.map(r=>r.text).join('')).includes(normalize(query)))?'open':''}><summary>Precedentes, jurisprudência e observações</summary><div>${a.notes.map(p=>`<${p.heading?'h4':'p'}>${p.runs.map(r=>highlight(r.text,query)).join('')}</${p.heading?'h4':'p'}>`).join('')}</div></details>`:''}<div class="article-source">${['official_html','official_stf'].includes(source.kind)?'Fonte: '+(isSumula?'STF':'Planalto')+' · coleta em '+collectionDate(source):escape(source.filename)+' · página '+a.page+(a.endPage&&a.endPage!==a.page?' a '+a.endPage:'')}${a.url?` · <a href="${escape(a.url)}" target="_blank" rel="noopener noreferrer">Página desta súmula no STF ↗</a>`:''}${a.rangeEnd?' · revogação agrupada no documento':''}${historyArticleIds.has(code.id+'/'+a.id)?` · <a href="#/atualizacoes?codigo=${escape(code.id)}&artigo=${a.id}">${isSumula?'Ver alterações desta súmula':'Ver alterações deste artigo'} →</a>`:''}</div></article>`;
  }).join('')||`<div class="empty"><h3>${onlySaved?'Nenhum favorito nesta seleção':isSumula?'Nenhuma súmula encontrada':'Nenhum artigo encontrado'}</h3><p>${onlySaved?'Use a estrela ao lado de uma entrada para guardá-la neste navegador.':'Tente outra expressão, limpe o filtro de divisão ou confira a parte selecionada.'}</p>${otherReference?`<p><a href="${codeHref(otherReference.code,otherReference.article.id)}">Abrir ${articleLabel(otherReference.article)} · ${escape(otherReference.code.name)} →</a></p>`:''}<button id="reset-search">Limpar filtros</button></div>`;
  document.querySelector('#reset-search')?.addEventListener('click',()=>{query='';sectionId=null;onlySaved=false;input.value='';page=0;draw();});
  document.querySelector('#page-label').textContent=list.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,list.length)} de ${number(list.length)}`:'Sem resultados';
  document.querySelector('#previous-page').disabled=page===0;
  document.querySelector('#next-page').disabled=page>=pages-1;
  document.querySelectorAll('[data-save]').forEach(b=>b.onclick=()=>{const key=code.id+'/'+b.dataset.save;state.saved=state.saved.includes(key)?state.saved.filter(x=>x!==key):[...state.saved,key];try{localStorage.setItem('lexa-saved',JSON.stringify(state.saved));toast(state.saved.includes(key)?(isSumula?'Súmula salva neste dispositivo':'Artigo salvo neste dispositivo'):'Marcação removida');}catch{toast('Marcação temporária: armazenamento indisponível');}draw();});
  document.querySelectorAll('.article-copy').forEach(menu=>menu.addEventListener('toggle',()=>{
   if(menu.open)document.querySelectorAll('.article-copy').forEach(other=>{if(other!==menu)other.open=false;});
  }));
  document.querySelectorAll('[data-copy],[data-copy-text]').forEach(button=>button.onclick=async()=>{
   const id=button.dataset.copyText||button.dataset.copy;
   const article=articleById(code,id),link=location.href.split('#')[0]+codeHref(code,id);
   const text=button.dataset.copyText?articleCopyText(code,article,link):link;
   await copyContent(text,button,button.dataset.copyText?'Texto e referência copiados':isSumula?'Link da súmula copiado':'Link do artigo copiado');
  });
  drawIndex(visible[0]?.sectionId);
  requestAnimationFrame(()=>{if(active)rememberPosition();});
 }
 if(target){const index=selectedArticles().findIndex(a=>a.id===target.id);page=Math.max(0,Math.floor(index/pageSize));}
 let debounce;
 input.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(()=>{query=input.value;const ref=parseReference(query);if(ref&&(!ref.codeId||ref.codeId===code.id)){if(ref.scope)scope=ref.scope;sectionId=null;}page=0;draw();},120);});
 document.querySelector('#font-down').onclick=()=>{readingPreferences.size=Math.max(16,readingPreferences.size-1);savePreferences();};
 document.querySelector('#font-up').onclick=()=>{readingPreferences.size=Math.min(26,readingPreferences.size+1);savePreferences();};
 document.querySelector('#saved-filter').onclick=()=>{onlySaved=!onlySaved;page=0;draw();};
 document.querySelector('#clear-section').onclick=()=>{sectionId=null;page=0;draw();};
 document.querySelectorAll('[data-scope]').forEach(b=>b.onclick=()=>{scope=b.dataset.scope;indexInitialized=false;query='';input.value='';sectionId=null;page=0;draw();});
 document.querySelector('#previous-page').onclick=event=>{page--;draw();scrollReading(event.detail===0);};
 document.querySelector('#next-page').onclick=event=>{page++;draw();scrollReading(event.detail===0);};
 draw();
 if(target)requestAnimationFrame(()=>{if(active){document.getElementById('art-'+target.id)?.scrollIntoView({block:'start'});rememberPosition();}});
}
