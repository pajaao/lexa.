import {loadFailureText} from './interface-copy.js';
import {reader} from './reader.js';
import {initialCatalog} from './collections.js';
import {copyContent} from './clipboard.js';
import {escape,number,codeHref,collectionDate,highlight,diffColumn} from './presentation.js';
import {recordedUpdates} from './history-store.js';
import {loadCollection,loadHistory,loadSearchIndexes,loadSearchIndex,activateCollection} from './loading.js';
import { searchLibraryText, libraryExcerpt } from './library-search.js';
import { setupPwa } from './pwa.js';
import { collections, normalize, articleById, articleLabel, parseReference, searchLibraryReferences } from './data.js';
import { filterUpdates, compareVersions, historySummary } from './history.js';

const app = document.querySelector('#app');
const total = collections.filter(c=>c.kind!=='sumulas').reduce((n,c)=>n+c.articleCount,0);
let category = 'Todas as áreas';
let libraryQuery='';
let saved = [];
try { const value=JSON.parse(localStorage.getItem('lexa-saved') || '[]'); if(Array.isArray(value))saved=value.filter(x=>typeof x==='string'); } catch {}
// Preferences and reading position belong only to this browser.
const storageRead=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}};
const storageWrite=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true;}catch{return false;}};
const storedPreferences=storageRead('lexa-reading',{});
const readingPreferences={
 size:Number.isInteger(storedPreferences?.size)&&storedPreferences.size>=16&&storedPreferences.size<=26?storedPreferences.size:19,
 spacing:['standard','comfortable','wide'].includes(storedPreferences?.spacing)?storedPreferences.spacing:'standard'
};
function lastReading(){
 const value=storageRead('lexa-last-reading',null);
 const code=collections.find(c=>c.id===value?.codeId);
 let article=code&&typeof value.articleId==='string'?articleById(code,value.articleId):null;
 if(code&&!code.loaded&&/^(?:adct-)?\d+(?:-[A-Z]+)*$/.test(value.articleId))article={id:value.articleId,number:value.articleId.replace('adct-',''),scope:value.articleId.startsWith('adct-')?'adct':'main',kind:code.kind==='sumulas'?'vinculante':undefined};
 return article?{code,article}:null;
}
let cleanupReader=()=>{};
let toastTimer;
function toast(message,duration=2500) { const el=document.querySelector('#toast'); clearTimeout(toastTimer); el.textContent=message; el.classList.add('visible'); toastTimer=setTimeout(()=>el.classList.remove('visible'),duration); }
document.addEventListener('click',event=>{
 if(navigator.onLine!==false||!event.target.closest('.feedback-link,.article-feedback'))return;
 event.preventDefault();
 toast('O formulário precisa de internet. Conecte-se e tente novamente. Sua leitura continua disponível.',8000);
});
document.querySelector('.skip-link').addEventListener('click',event=>{event.preventDefault();const target=document.querySelector('#settings-page').hidden?app:document.querySelector('#settings-title');target.focus();target.scrollIntoView({block:'start'});});
const historyArticleIds=new Set([...recordedUpdates.flatMap(event=>event.changes.map(change=>event.codeId+'/'+change.articleId)),...collections.flatMap(code=>(code.changedArticleIds||[]).map(id=>code.id+'/'+id))]);

const favoritesView={query:'',scroll:0,href:null};
let favoriteUndo=null;
function favoritesPage(params=new URLSearchParams()){
 document.title='Meus favoritos — Lexa';
 if(params.has('q'))favoritesView.query=params.get('q');
 app.innerHTML=`<section class="favorites-page"><a class="back" href="#">Biblioteca / sua seleção</a><h1>Meus favoritos</h1><p class="favorites-intro">Artigos e súmulas que você guardou, reunidos por norma.</p><p class="favorites-privacy">As marcações ficam somente neste navegador.</p><div class="favorites-layout"><div class="favorites-main"><div id="favorites-search-field"><label class="field-label" for="favorites-search">Localizar um dispositivo salvo</label><div class="search favorites-search"><span aria-hidden="true">⌕</span><input id="favorites-search" placeholder="Norma, artigo ou palavra…" value="${escape(favoritesView.query)}"></div></div><div class="favorites-totals"><p id="favorites-count" role="status"></p><span>Agrupados por legislação</span></div><div id="favorites-feedback" class="favorites-feedback" hidden><span role="status"></span><button type="button" id="favorites-undo">Desfazer</button></div><div id="favorites-list"></div></div><aside class="favorites-help" aria-label="Sobre os favoritos"><div class="eyebrow">Sua biblioteca pessoal</div><h2>Salve o que importa.</h2><p>Use a estrela junto aos artigos para encontrá-los aqui depois.</p><div class="eyebrow">Privacidade</div><p>Seus favoritos não dependem de conta e não são sincronizados entre dispositivos.</p><p>Ao remover uma marcação, você poderá desfazer a ação.</p></aside></div></section>`;
 const input=document.querySelector('#favorites-search'),feedback=document.querySelector('#favorites-feedback');
 let undoTimer;
 const entries=()=>[...new Set(saved)].map(key=>{
  const separator=key.indexOf('/'),code=collections.find(c=>c.id===key.slice(0,separator));
  const article=code&&articleById(code,key.slice(separator+1));
  return {key,code,article};
 });
 function showUndo(message){
  clearTimeout(undoTimer);
  const available=favoriteUndo&&favoriteUndo.until>Date.now();
  feedback.hidden=!available;
  if(!available)return;
  feedback.querySelector('[role=status]').textContent=message||'Favorito removido. Você pode desfazer esta ação.';
  undoTimer=setTimeout(()=>{if(document.activeElement===document.querySelector('#favorites-undo'))(document.querySelector('[data-remove-favorite]')||document.querySelector('.favorites-empty a')||input).focus({preventScroll:true});feedback.hidden=true;favoriteUndo=null;},favoriteUndo.until-Date.now());
 }
 function draw(){
  const q=normalize(input.value).trim(),all=entries();
  const references=searchLibraryReferences(input.value);
  const matches=all.filter(({key,code,article})=>!q||(references!==null?references.some(result=>result.code.id===code?.id&&result.article.id===article?.id):normalize(code?code.name+' '+code.short+' '+(article?articleLabel(article)+' '+article.text:key):key).includes(q)));
  const groups=collections.map(code=>({code,items:matches.filter(item=>item.code?.id===code.id)}));
  const unknown=matches.filter(item=>!item.code);if(unknown.length)groups.push({code:null,items:unknown});
  document.querySelector('#favorites-search-field').hidden=!all.length;
  document.querySelector('#favorites-count').textContent=`${matches.length} ${matches.length===1?'favorito':'favoritos'}${q?(matches.length===1?' encontrado':' encontrados'):''}`;
  document.querySelector('#favorites-list').innerHTML=matches.length?groups.filter(group=>group.items.length).map(({code,items},groupIndex)=>`<section class="favorite-group"><div class="favorite-group-label">${String(groupIndex+1).padStart(2,'0')} / ${escape(code?.area||'Indisponíveis')}</div><h2>${code?escape(code.name):'Marcações indisponíveis'} <span>${items.length} ${code?.kind==='sumulas'?'súmula(s)':'artigo(s)'}</span></h2><ul>${items.map(({key,article})=>{
   const label=article?articleLabel(article):key;
   const paragraph=article?.paragraphs.find(p=>p.runs.some(run=>!run.deleted&&run.text.trim()));
   const preview=paragraph?.runs.filter(run=>!run.deleted).map(run=>run.text).join('')||article?.text||'';
   return `<li class="favorite-entry"><div>${article?`<a class="favorite-link" href="${codeHref(code,article.id)}"><strong>${escape(label)}</strong><span aria-hidden="true">→</span></a>${['cancelled','pending','suspended'].includes(article.status)?`<small class="favorite-status">${{cancelled:'Cancelada',pending:'Pendente de publicação',suspended:'Suspensa'}[article.status]} — conforme indicado na edição</small>`:''}<p>${escape(preview.slice(0,220))}${preview.length>220?'…':''}</p><a class="favorite-open" href="${codeHref(code,article.id)}" aria-label="Abrir ${escape(label)} de ${escape(code.short)}">Abrir ${escape(code.short)} ↗</a>`:`<strong>${escape(label)}</strong><small class="favorite-status">Indisponível nesta edição</small><p>Esta referência não foi encontrada na edição atual. A marcação foi mantida para sua conferência.</p>`}</div><button data-remove-favorite="${escape(key)}" aria-label="Remover favorito ${escape(label)}${code?' de '+escape(code.short):''}">Remover</button></li>`;
  }).join('')}</ul></section>`).join(''):`<div class="favorites-empty"><span aria-hidden="true">☆</span><h2>${all.length?'Nenhum favorito encontrado':'Nenhum favorito salvo'}</h2><p>${all.length?'Tente o nome da norma, o número ou uma palavra do texto.':'Use a estrela ao lado de um artigo ou súmula para salvá-lo nos favoritos.'}</p><a href="#">Voltar à biblioteca</a></div>`;
  document.querySelectorAll('[data-remove-favorite]').forEach(button=>button.onclick=()=>{
   const key=button.dataset.removeFavorite,position=saved.indexOf(key);
   const buttons=[...document.querySelectorAll('[data-remove-favorite]')],index=buttons.indexOf(button);
   saved=saved.filter(item=>item!==key);
   favoriteUndo={key,position,until:Date.now()+8000};
   const persisted=storageWrite('lexa-saved',saved);
   draw();showUndo(persisted?'Favorito removido.':'Remoção temporária: armazenamento indisponível.');
   const remaining=document.querySelectorAll('[data-remove-favorite]');(remaining[Math.min(index,remaining.length-1)]||document.querySelector('#favorites-undo')).focus({preventScroll:true});
  });
 }
 document.querySelector('#favorites-undo').onclick=()=>{
  if(!favoriteUndo||favoriteUndo.until<=Date.now())return;
  const {key,position}=favoriteUndo;
  if(!saved.includes(key))saved.splice(Math.min(position,saved.length),0,key);
  const persisted=storageWrite('lexa-saved',saved);favoriteUndo=null;clearTimeout(undoTimer);feedback.hidden=true;draw();
  ([...document.querySelectorAll('[data-remove-favorite]')].find(button=>button.dataset.removeFavorite===key)||input).focus({preventScroll:true});
  toast(persisted?'Favorito restaurado':'Restauração temporária: armazenamento indisponível');
 };
 input.addEventListener('input',()=>{favoritesView.query=input.value;favoritesView.scroll=0;favoritesView.href=null;const query=new URLSearchParams();if(input.value)query.set('q',input.value);history.replaceState(history.state,'','#/favoritos'+(query.size?'?'+query:''));draw();});
 cleanupReader=()=>{clearTimeout(undoTimer);favoritesView.query=input.value;favoritesView.scroll=scrollY;favoritesView.href=document.activeElement?.closest('.favorite-link,.favorite-open')?.getAttribute('href')||null;};
 draw();showUndo();
 requestAnimationFrame(()=>{if(!document.querySelector('.favorites-page'))return;window.scrollTo({top:favoritesView.scroll,behavior:'instant'});if(favoritesView.href)[...document.querySelectorAll('.favorite-link,.favorite-open')].find(link=>link.getAttribute('href')===favoritesView.href)?.focus({preventScroll:true});});
}

function recentUpdatesSection(){
 // This build projection contains only incorporated textual changes, not baselines or processing events.
 const events=(initialCatalog?.recentUpdates||[]).filter(event=>event.totalChanges>0&&collections.some(code=>code.id===event.codeId));
 return events.length?'<a class="legislative-indicator" href="#/atualizacoes" aria-label="Consultar alterações legislativas registradas">Alterações<span class="indicator-full"> registradas</span> ↗</a>':'';
}

function home() {
 const resume=lastReading();
 let homeActive=true,searchSequence=0;
 document.title='Lexa — Consulta à legislação brasileira';
 app.innerHTML=`<section class="hero editorial-hero"><div class="hero-copy"><div class="eyebrow">Consulte a legislação</div><h1>O que você deseja consultar?</h1><p>Pesquise normas, artigos e súmulas na biblioteca do Lexa.</p><label class="field-label" for="library-search">Buscar norma, artigo ou palavra</label><div class="search hero-search"><span aria-hidden="true">⌕</span><input id="library-search" placeholder="Ex.: art. 5 CF, SV 13, dignidade"><kbd aria-hidden="true">/</kbd></div><div class="search-examples" role="group" aria-label="Exemplos de busca"><span>Exemplos</span>${['Art. 5 CF','SV 13','dignidade'].map(query=>`<button type="button" data-example="${escape(query)}">${escape(query)}</button>`).join('')}</div><div class="quick-reference" id="quick-reference" aria-label="Resultados por referência" hidden></div></div><aside class="consultation-guide" aria-label="Como consultar"><div class="eyebrow">Como consultar</div><p><b>01</b><span>Referência exata<small>Art. 5 CF ou SV 13</small></span></p><p><b>02</b><span>Expressão no texto<small>Ex.: dignidade</small></span></p></aside><div class="hero-note"><span><strong>${collections.filter(c=>c.kind!=='sumulas').length}</strong> legislações <i aria-hidden="true"></i> <strong>${number(total)}</strong> entradas <i aria-hidden="true"></i> <strong>${collections.find(c=>c.id==='sv').articleCount}</strong> súmulas</span>${recentUpdatesSection()}</div></section>${resume?`<section class="resume-reading" aria-label="Continuar leitura"><a class="resume-link" href="${codeHref(resume.code,resume.article.id)}"><span class="eyebrow">Continuar leitura</span><p><strong>${escape(resume.code.name)}</strong> · ${articleLabel(resume.article)}</p></a><button id="forget-reading" aria-label="Remover esta consulta da página inicial">×</button></section>`:''}<section class="library"><div class="section-heading"><div class="eyebrow">Biblioteca / acervo</div><h2>Explore a biblioteca</h2><p>Navegue pelas legislações e refine a consulta por área do Direito.</p></div><div class="filters" aria-label="Filtrar por área">${['Todas as áreas','Constitucional','Civil','Penal','Processual','Consumidor','Tributário','Trabalho','Infância e Juventude','Mulher','Administrativo','Súmulas'].map(x=>`<button class="${x===category?'active':''}" data-category="${x}" aria-pressed="${x===category}">${x}</button>`).join('')}</div><p id="library-results" class="library-results" role="status"></p><div class="catalog-heading"><span>Legislações e súmulas disponíveis</span><span>${collections.length} no acervo</span></div><div class="cards" id="cards"></div><div id="text-results" class="text-results"></div></section>`;
 document.querySelector('#library-search').value=libraryQuery;
 document.querySelector('#forget-reading')?.addEventListener('click',()=>{try{localStorage.removeItem('lexa-last-reading');}catch{}document.querySelector('.resume-reading').remove();});
 const findReferences=query=>{
  const results=searchLibraryReferences(query);
  return results===null?null:results.filter(({code})=>parseReference(query).codeId||category==='Todas as áreas'||code.area.includes(category));
 };
 let textGroups=[],visibleCounts=new Map(),currentQuery='';
 const draw=async()=>{
  const sequence=++searchSequence;
  currentQuery=document.querySelector('#library-search').value.trim();libraryQuery=document.querySelector('#library-search').value;
  const q=normalize(currentQuery);
  document.querySelector('#text-results').innerHTML='';
  visibleCounts=new Map();
  const ref=parseReference(currentQuery);
  const selected=collections.filter(code=>(!ref?.codeId||code.id===ref.codeId)&&(ref?.codeId||category==='Todas as áreas'||code.area.includes(category)));
  if((ref||q.length>=2)&&selected.some(code=>!code.searchIndex)){
   document.querySelector('#quick-reference').hidden=true;
   const status=document.querySelector('#library-results');
   status.textContent=ref?'Carregando referências…':'Carregando índice…';
   try{await loadSearchIndexes(selected);}catch(error){
    if(homeActive&&sequence===searchSequence){status.textContent=loadFailureText(error);document.querySelector('#text-results').innerHTML='<button class="text-more" id="retry-search">Tentar novamente</button>';document.querySelector('#retry-search').onclick=draw;}
    return;
   }
   if(!homeActive||sequence!==searchSequence)return;
  }
  const references=findReferences(q);
  const quick=document.querySelector('#quick-reference');
  quick.hidden=references===null;
  quick.innerHTML='';
  if(references!==null){
   quick.innerHTML=references.length?references.map(({code,article})=>`<a href="${codeHref(code,article.id)}"><span><strong>${articleLabel(article)}</strong><small>${escape(code.name)}</small></span><b aria-hidden="true">→</b></a>`).join(''):'<p>Referência não encontrada. Confira o número e a sigla.</p>';
   if(parseReference(q).codeId){category='Todas as áreas';document.querySelectorAll('[data-category]').forEach(button=>{button.classList.toggle('active',button.dataset.category===category);button.setAttribute('aria-pressed',String(button.dataset.category===category));});}
   document.querySelector('#library-results').textContent=`${references.length} ${references.length===1?'referência encontrada':'referências encontradas'}`;
   document.querySelector('#cards').innerHTML='';
   return;
  }
  document.querySelector('#library-results').textContent='';
  const filtered=collections.filter(c=>(category==='Todas as áreas'||c.area.includes(category))&&normalize(c.name+' '+c.short+' '+c.area+' '+c.description).includes(q));
  document.querySelector('#cards').innerHTML=filtered.map(c=>c.id==='cf'&&initialCatalog.amendments?`<div class="code-card constitution-card"><a class="constitution-main" href="${codeHref(c)}"><div class="card-top"><span class="code-short">${escape(c.short)} / Legislação</span><span class="catalog-number">${String(collections.indexOf(c)+1).padStart(2,'0')}</span></div><h3>${escape(c.name)}</h3><p>${escape(c.description)}</p></a><a class="constitution-amendments" href="#/emendas">Emendas Constitucionais →</a></div>`:`<a class="code-card" href="${codeHref(c)}"><div class="card-top"><span class="code-short">${escape(c.short)} / ${c.kind==='sumulas'?'súmulas':'legislação'}</span><span class="catalog-number">${String(collections.indexOf(c)+1).padStart(2,'0')}</span></div><h3>${escape(c.name)}</h3><p>${escape(c.description)}</p></a>`).join('');
  textGroups=q.length>=2?searchLibraryText(currentQuery,category):[];
  const count=textGroups.reduce((sum,group)=>sum+group.matches.length,0);
  if(q){
   document.querySelector('#library-results').textContent=q.length<2?'Digite pelo menos 2 caracteres para buscar nos textos.':`${number(count)} ${count===1?'entrada encontrada':'entradas encontradas'} nos textos · ${textGroups.length} ${textGroups.length===1?'coleção':'coleções'}${filtered.length?' · '+filtered.length+' coleção(ões) pelo nome ou descrição':''}`;
   drawTextResults();
  }
 };
 function drawTextResults(){
  const results=document.querySelector('#text-results');
  if(normalize(currentQuery).length<2){results.innerHTML='';return;}
  results.innerHTML=textGroups.length?`<div class="text-search-heading"><h2>Ocorrências nos textos</h2><p>Resultados por coleção, na ordem dos dispositivos. Redações riscadas e notas de aplicação também podem aparecer, com identificação.</p></div>`+textGroups.map(({code,matches})=>{
   const limit=visibleCounts.get(code.id)||4;
   return `<section class="text-result-group" aria-labelledby="search-group-${escape(code.id)}"><div class="text-group-heading"><h3 id="search-group-${escape(code.id)}">${escape(code.name)}</h3><span>${number(matches.length)} ${matches.length===1?'entrada':'entradas'}</span></div><ul>${matches.slice(0,limit).map(({article,match})=>{
    const excerpt=libraryExcerpt(match),riscado=excerpt.runs.some(run=>run.deleted);
    const status={cancelled:'Cancelada',pending:'Pendente de publicação',suspended:'Suspensa'}[article.status];
    return `<li><a class="text-result" href="${codeHref(code,article.id)}?q=${encodeURIComponent(currentQuery)}"><div class="text-result-title"><strong>${articleLabel(article)}</strong><span aria-hidden="true">→</span></div>${status?`<span class="search-badge">${status} — conforme a edição</span>`:''}${match.kind==='notes'?'<span class="search-badge">Ocorrência em precedentes, jurisprudência ou observações</span>':match.kind==='title'?'<span class="search-badge">Ocorrência no título do artigo</span>':''}${match.deleted?'<span class="search-badge">Ocorrência em trecho riscado na fonte</span>':riscado?'<span class="search-badge">Contém trecho riscado na fonte</span>':''}<p>${excerpt.leading?'…':''}${excerpt.runs.map(run=>run.deleted?`<del>${highlight(run.text,currentQuery)}</del>`:highlight(run.text,currentQuery)).join('')}${excerpt.trailing?'…':''}</p><small>${escape(article.section||'')}</small></a></li>`;
   }).join('')}</ul>${matches.length>limit?`<button class="text-more" data-more-code="${escape(code.id)}">Mostrar mais de ${escape(code.short)} · ${number(matches.length-limit)} restantes</button>`:''}</section>`;
  }).join(''):'<div class="empty"><h3>Nenhuma ocorrência nos textos</h3><p>Tente uma expressão mais curta ou selecione outra área. A busca procura o texto digitado, sem distinção de acentos.</p></div>';
  results.querySelectorAll('[data-more-code]').forEach(button=>button.onclick=()=>{
   const id=button.dataset.moreCode,previous=visibleCounts.get(id)||4;
   visibleCounts.set(id,previous+6);drawTextResults();
   document.querySelector(`#search-group-${id}`)?.closest('section').querySelectorAll('.text-result')[previous]?.focus({preventScroll:true});
  });
 }
 let searchTimer;
 cleanupReader=()=>{clearTimeout(searchTimer);homeActive=false;searchSequence++;};
 document.querySelector('#library-search').addEventListener('input',()=>{clearTimeout(searchTimer);libraryQuery=document.querySelector('#library-search').value;if(searchLibraryReferences(document.querySelector('#library-search').value)!==null)draw();else searchTimer=setTimeout(draw,150);});
 document.querySelector('#library-search').addEventListener('keydown',async event=>{if(event.key==='Enter'){clearTimeout(searchTimer);const submitted=event.target.value;await draw();if(!homeActive||event.target.value!==submitted)return;const results=findReferences(submitted);if(results?.length===1){location.hash=codeHref(results[0].code,results[0].article.id);}else if(results===null){const heading=document.querySelector('.text-search-heading h2');if(heading){heading.tabIndex=-1;heading.scrollIntoView({block:'start'});heading.focus({preventScroll:true});}}}});
 document.querySelectorAll('[data-example]').forEach(button=>button.onclick=()=>{clearTimeout(searchTimer);const input=document.querySelector('#library-search');input.value=button.dataset.example;libraryQuery=input.value;draw();input.focus({preventScroll:true});});
 document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>{category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});draw();});
 draw();
 if(resume&&!resume.code.loaded)loadSearchIndex(resume.code).then(()=>{
  if(homeActive&&!articleById(resume.code,resume.article.id))document.querySelector('.resume-reading')?.remove();
 }).catch(()=>{});
}

function updatesPage(params) {
 document.title='Atualizações da legislação — Lexa';
 let renderedCount=0;
 let codeId=params.get('codigo')||'',articleId=params.get('artigo')||'',limit=12;
 if(!collections.some(c=>c.id===codeId))codeId='';
 const order=recordedUpdates.map((event,index)=>({event,index})).sort((a,b)=>Date.parse(b.event.capturedAt)-Date.parse(a.event.capturedAt)||b.index-a.index).map(item=>item.event);
 const summary=historySummary(recordedUpdates);
 const kindLabels={baseline:'Referência inicial',text:'Mudanças no texto',source:'Atualização da fonte',processing:'Reprocessamento'};
 const changeLabels={added:'Adicionado ao texto',changed:'Texto alterado',removed:'Ausente nesta versão'};
 app.innerHTML=`<section class="updates-hero"><a class="back" href="#">← Voltar à biblioteca</a><div class="eyebrow">Biblioteca / atualizações / versões coletadas</div><h1>Histórico de versões</h1><p>Compare as versões dos textos incorporados ao Lexa. As datas de coleta não certificam vigência.</p><div class="history-stats">${summary.since?`<span>Acompanhando desde <strong>${collectionDate({capturedAt:summary.since})}</strong></span>`:''}<span><strong>${number(summary.norms)}</strong> ${summary.norms===1?'norma em acompanhamento':'normas em acompanhamento'}</span>${summary.versions?`<span><strong>${number(summary.versions)}</strong> ${summary.versions===1?'nova versão registrada':'novas versões registradas'}</span>`:''}${summary.changes?`<span><strong>${number(summary.changes)}</strong> ${summary.changes===1?'alteração de entrada registrada':'alterações de entradas registradas'}</span>`:''}</div></section><section class="updates-content"><div class="updates-toolbar"><label>Legislação<select id="history-code"><option value="">Todas as legislações</option>${collections.map(c=>`<option value="${escape(c.id)}">${escape(c.name)}</option>`).join('')}</select></label><label>Artigo ou súmula<input id="history-article" placeholder="Ex.: 186, ADCT-1 ou SV 13" value="${escape(articleId)}"></label><button id="history-clear">Limpar filtros</button></div><p class="history-help">Este Histórico de versões compara edições incorporadas ao Lexa; é diferente de Redações anteriores. As datas indicam a coleta da fonte. Os destaques mostram diferenças no texto, sem classificar juridicamente as alterações ou certificar sua vigência.</p><div id="history-results" role="status"></div><div id="history-events"></div><button id="history-more" class="history-more" hidden>Carregar mais versões</button></section>`;
 document.querySelector('#history-code').value=codeId;
 function draw(append=false){
  const events=filterUpdates(order,codeId,articleId);
  document.querySelector('#history-results').textContent=`${events.length} ${events.length===1?'registro encontrado':'registros encontrados'}`;
  const container=document.querySelector('#history-events');
  const markup=events.slice(append?renderedCount:0,limit).map(event=>{
   const code=collections.find(c=>c.id===event.codeId);
   const counts=event.changes.reduce((v,c)=>(v[c.type]++,v),{added:0,changed:0,removed:0});
   return `<details class="update-event" data-history-event="${escape(event.id)}" ${articleId?'open':''}><summary><span class="timeline-dot"></span><div class="event-heading"><div class="event-meta"><time datetime="${escape(event.capturedAt)}">Coleta · ${collectionDate(event)}</time><span class="event-kind kind-${event.kind}">${kindLabels[event.kind]||'Registro de versão'}</span></div><h2>${escape(code.name)}</h2><p>${event.kind==='baseline'?'Ponto de partida para acompanhar as próximas versões.':`${event.changes.length} ${event.changes.length===1?'entrada com diferença':'entradas com diferenças'}${counts.added?' · '+counts.added+' adicionado(s)':''}${counts.removed?' · '+counts.removed+' ausente(s)':''}`}</p></div><span class="event-expand" aria-hidden="true">+</span></summary><div class="event-body">${event.kind==='baseline'?'<div class="baseline-note">Esta é a referência inicial do histórico. A migração entre formatos não é apresentada como mudança na legislação. As próximas versões podem ser comparadas a partir deste registro.</div>':event.changes.length?'':'<p>Foi registrada uma nova versão da fonte, sem diferenças identificadas nos textos das entradas pelo comparador.</p>'}${event.kind==='processing'?'<p class="history-help">Este registro decorre de um ajuste no processamento do mesmo documento, sem indicar uma nova publicação legal.</p>':''}${event.changes.map((change,index)=>`<details class="article-change" data-revision-event="${event.id}" data-revision-index="${index}"><summary><strong>${articleLabel(change)}</strong><span class="change-tag tag-${change.type}">${changeLabels[change.type]}</span><span aria-hidden="true">⌄</span></summary><div class="comparison-container"></div><div class="comparison-footer"><a href="${codeHref(code,change.articleId)}">Abrir entrada na versão atual do Lexa →</a></div></details>`).join('')}<div class="event-footer"><a href="${codeHref(code)}">Consultar edição atual de ${escape(code.short)} →</a><a href="${escape(event.sourceUrl)}" target="_blank" rel="noopener noreferrer">Fonte oficial ↗</a></div></div></details>`;
  }).join('')||`<div class="history-empty"><span>↺</span><h2>${recordedUpdates.length?'Nenhum registro para estes filtros':'O histórico começa aqui.'}</h2><p>${recordedUpdates.length?'Escolha outra legislação ou outro artigo.':'As primeiras versões incorporadas estabelecerão a referência inicial. As mudanças seguintes aparecerão aqui, com comparação entre os textos.'}</p><a href="#">Voltar à biblioteca</a></div>`;
  if(append)container.insertAdjacentHTML('beforeend',markup);else container.innerHTML=markup;
  renderedCount=Math.min(limit,events.length);
  document.querySelector('#history-more').hidden=events.length<=limit;
  document.querySelectorAll('[data-revision-event]:not([data-bound])').forEach(details=>{details.dataset.bound='true';details.addEventListener('toggle',()=>{
   if(!details.open||details.dataset.loaded)return;
   const event=events.find(e=>e.id===details.dataset.revisionEvent);
   const change=event.changes[Number(details.dataset.revisionIndex)];
   const comparison=compareVersions(change.before,change.after);
   details.querySelector('.comparison-container').innerHTML=`<div class="diff-legend"><span class="legend-before">Diferente na versão anterior</span><span class="legend-after">Diferente na versão coletada</span></div><div class="comparison-grid"><section><h3>Versão anterior</h3><p class="comparison-edition">Edição ${escape(event.fromVersion?.slice(0,12)||'não identificada')}</p>${diffColumn(comparison.before,'before')}</section><section><h3>Versão coletada</h3><p class="comparison-edition">Coleta ${collectionDate(event)} · edição ${escape(event.toVersion?.slice(0,12)||'não identificada')}</p>${diffColumn(comparison.after,'after')}</section></div><p class="comparison-caution">Riscados já presentes na fonte são preservados. A ausência de um trecho não determina, por si só, revogação ou início de vigência.</p>`;
   details.dataset.loaded='true';
  });});
 }
 function sync(){
  limit=12;
  const query=new URLSearchParams();if(codeId)query.set('codigo',codeId);if(articleId)query.set('artigo',articleId);
  history.replaceState(history.state,'','#/atualizacoes'+(query.size?'?'+query:''));draw();
 }
 document.querySelector('#history-code').onchange=e=>{codeId=e.target.value;sync();};
 document.querySelector('#history-article').oninput=e=>{articleId=e.target.value;sync();};
 document.querySelector('#history-clear').onclick=()=>{codeId='';articleId='';document.querySelector('#history-code').value='';document.querySelector('#history-article').value='';sync();};
 document.querySelector('#history-more').onclick=event=>{const top=scrollY,previous=renderedCount;limit+=12;draw(true);window.scrollTo({top,behavior:'instant'});if(event.currentTarget.hidden)document.querySelectorAll('.update-event>summary')[previous]?.focus({preventScroll:true});};
 draw();
}

function readerServices(){
 return {app,readingPreferences,storageWrite,historyArticleIds,toast,
  copyContent:(text,button,message)=>copyContent(text,button,message,toast),
  state:{get saved(){return saved;},set saved(value){saved=value;},
   get cleanupReader(){return cleanupReader;},set cleanupReader(value){cleanupReader=value;}}
 };
}

let routeGeneration=0;
async function route(){
 const generation=++routeGeneration;
 const copyDialog=document.querySelector('#copy-dialog');if(copyDialog.open)copyDialog.close();
 cleanupReader();cleanupReader=()=>{};app.classList.remove('amendment-reader','amendment-full');
 const [path,query='']=location.hash.slice(1).split('?');
 const [,id,article]=path.split('/');
 const leavingSettings=!document.querySelector('#settings-page').hidden;
 const settings=id==='sobre-e-ajustes'||id==='sobre-lexa'||path==='sobre-lexa';
 document.querySelector('#settings-page').hidden=!settings;app.hidden=settings;
 document.body.classList.toggle('settings-view',settings);
 const activeNav=settings?'#/sobre-e-ajustes':id==='favoritos'?'#/favoritos':id==='atualizacoes'?'#/atualizacoes':'#';
 document.querySelectorAll('header nav>a').forEach(link=>{
  if(link.getAttribute('href')===activeNav)link.setAttribute('aria-current','page');
  else link.removeAttribute('aria-current');
 });
 const code=collections.find(c=>c.id===id);
 activateCollection(code?.id||null);
 const needsData=code&&!code.loaded||id==='favoritos'||id==='atualizacoes';
 if(needsData)app.innerHTML=`<section class="loading-panel"><p role="status">${code?'Carregando '+escape(code.name)+'…':id==='favoritos'?'Carregando favoritos…':'Carregando histórico…'}</p></section>`;
 try{
  if(id==='emendas'){
   if(!initialCatalog.amendments)throw new Error('Biblioteca de Emendas não habilitada nesta edição.');
   app.innerHTML='<p class="loading-panel" role="status">Carregando Emendas Constitucionais…</p>';
   const amendments=await import('./amendments.js');
   if(!article){await amendments.amendmentLibrary(app,new URLSearchParams(query),()=>generation===routeGeneration);return;}
   const {document,entry}=await amendments.loadAmendment(article),links=await amendments.loadAmendmentLinks();if(generation!==routeGeneration)return;
   const collection=amendments.amendmentCollection(document,entry),services=readerServices();services.renderParagraphs=amendments.amendmentParagraphs;services.storageWrite=(key,value)=>key==='lexa-last-reading'?true:storageWrite(key,value);
   reader(collection,path.split('/')[3],new URLSearchParams(query),services);amendments.enhanceAmendmentReader(app,document,links,new URLSearchParams(query));return;
  }
  if(settings){document.title='Sobre e ajustes — Lexa';app.innerHTML='';document.querySelector('#settings-title').focus({preventScroll:true});window.scrollTo(0,0);return;}
  if(id==='favoritos'){
   await loadSearchIndexes(collections.filter(code=>saved.some(key=>key.startsWith(code.id+'/'))));
   if(generation!==routeGeneration)return;
   favoritesPage(new URLSearchParams(query));return;
  }
  if(id==='atualizacoes'){
   const history=await loadHistory();if(generation!==routeGeneration)return;
   recordedUpdates.splice(0,recordedUpdates.length,...history);
   updatesPage(new URLSearchParams(query));window.scrollTo(0,0);return;
  }
  if(code){await loadCollection(code);const services=readerServices();let amendments,links;
   if(code.id==='cf'&&initialCatalog.amendments){amendments=await import('./amendments.js');links=await amendments.loadAmendmentLinks();services.amendmentNotes={records:links.records,decorate:amendments.decorateAmendmentNotes};}
   if(generation!==routeGeneration)return;reader(code,article,new URLSearchParams(query),services);
   const ec=new URLSearchParams(query).get('emenda');if(ec&&links?.records.some(x=>String(x.ec)===ec&&x.articleId===article)){const back=document.createElement('a');back.className='back';back.href='#/emendas/'+ec;back.textContent='← Voltar à EC '+ec;app.querySelector('.reader-top').prepend(back);}
  }
  else{home();if(leavingSettings)app.focus({preventScroll:true});}
  if(!article)window.scrollTo(0,0);
 }catch(error){
  if(generation!==routeGeneration)return;
  app.innerHTML=`<section class="loading-panel"><h1>Não foi possível abrir esta edição</h1><p role="status">${escape(loadFailureText(error))}</p><button id="retry-load">Tentar novamente</button><a href="#">Voltar à biblioteca</a></section>`;
  document.querySelector('#retry-load').onclick=route;
 }
}
let dark=false;try{dark=localStorage.getItem('lexa-theme')==='dark';}catch{}
document.documentElement.classList.toggle('dark',dark);
function setTheme(value){
 dark=value;document.documentElement.classList.toggle('dark',dark);
 document.querySelectorAll('[data-theme]').forEach(button=>button.setAttribute('aria-pressed',String((button.dataset.theme==='dark')===dark)));
 try{localStorage.setItem('lexa-theme',dark?'dark':'light');}catch{}
}
document.querySelector('#theme').onclick=()=>setTheme(!dark);
document.querySelectorAll('[data-theme]').forEach(button=>button.onclick=()=>setTheme(button.dataset.theme==='dark'));
setTheme(dark);
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'&&!document.querySelector('#copy-dialog').open){const menu=document.querySelector('.article-copy[open]');if(menu){menu.open=false;menu.querySelector('summary').focus({preventScroll:true});e.stopImmediatePropagation();return;}}
 if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();document.querySelector('input')?.focus();}});
document.addEventListener('pointerdown',event=>{if(!document.querySelector('#copy-dialog').open&&!event.target.closest('.article-copy'))document.querySelectorAll('.article-copy[open]').forEach(menu=>menu.open=false);});
document.querySelector('#copy-select').onclick=()=>{const field=document.querySelector('#copy-content');field.focus();field.select();};
window.addEventListener('hashchange',route);route();

setupPwa();
