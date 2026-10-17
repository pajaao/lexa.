import {readerModel} from './reader-model.js';
import {loadCollection,loadCollections,loadHistory,loadSearchIndexes,loadSearchIndex} from './loading.js';
import { searchLibraryText, libraryExcerpt } from './library-search.js';
import { articleCopyText } from './copy.js';
import { sectionPath, headingKind, unitKind, buildSectionTree } from './structure.js';
import { setupPwa } from './pwa.js';
import { collections, normalize, searchArticles, articleById, articleLabel, parseReference, searchLibraryReferences } from './data.js';
import { updateHistory } from '../data/history/legislation.js';
import { sumulaUpdates } from '../data/history/sumulas.js';
import { filterUpdates, compareVersions, historySummary } from './history.js';

const recordedUpdates=[...updateHistory,...sumulaUpdates];
const app = document.querySelector('#app');
const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const total = collections.filter(c=>c.kind!=='sumulas').reduce((n,c)=>n+c.articleCount,0);
const number = n => n.toLocaleString('pt-BR');
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
function toast(message) { const el=document.querySelector('#toast'); el.textContent=message; el.classList.add('visible'); setTimeout(()=>el.classList.remove('visible'),2500); }
document.querySelector('.skip-link').addEventListener('click',event=>{event.preventDefault();app.focus();app.scrollIntoView({block:'start'});});
const codeHref = (code,article='') => `#/${encodeURIComponent(code.id)}${article?'/'+article:''}`;
const historyArticleIds=new Set([...recordedUpdates.flatMap(event=>event.changes.map(change=>event.codeId+'/'+change.articleId)),...collections.flatMap(code=>(code.changedArticleIds||[]).map(id=>code.id+'/'+id))]);

const collectionDate = source => new Intl.DateTimeFormat('pt-BR',{timeZone:'America/Sao_Paulo',dateStyle:'short'}).format(new Date(source.capturedAt));
function sourcePanel(source) {
 if(['official_html','official_stf'].includes(source.kind))return `<p>${escape(source.coverage)}</p><p>${escape(source.reviewStatus)}</p><p>Coleta da fonte oficial: ${collectionDate(source)}. Novas versões são propostas para revisão no GitHub.</p><p><a href="${escape(source.url)}" target="_blank" rel="noopener noreferrer">Consultar página oficial ↗</a></p><p class="source-hash">SHA-256 do texto extraído: ${escape(source.sha256)}</p>`;
 return `<p>${escape(source.coverage)}</p><p>${escape(source.reviewStatus)}</p><p>Arquivo: ${escape(source.filename)} · ${escape(source.pages)} páginas.</p><p><a href="./${escape(source.pdf)}" target="_blank" rel="noopener">Abrir PDF fornecido ↗</a> <small>(disponível ao executar o site completo)</small></p><p class="source-hash">SHA-256: ${escape(source.sha256)}</p>`;
}
function favoritesPage(){
 document.title='Meus favoritos — Lexa';
 app.innerHTML=`<section class="favorites-page"><a class="back" href="#">← Voltar à biblioteca</a><div class="eyebrow">SUA SELEÇÃO</div><h1>Meus favoritos</h1><p class="favorites-intro">Artigos e súmulas que você guardou, reunidos por norma. <br>As marcações ficam somente neste navegador.</p><label class="search favorites-search"><span>⌕</span><input id="favorites-search" placeholder="Buscar nos favoritos…" aria-label="Buscar nos favoritos"></label><p id="favorites-count" role="status"></p><div id="favorites-list"></div></section>`;
 const input=document.querySelector('#favorites-search');
 const entries=()=>[...new Set(saved)].map(key=>{
  const separator=key.indexOf('/'),code=collections.find(c=>c.id===key.slice(0,separator));
  const article=code&&articleById(code,key.slice(separator+1));
  return {key,code,article};
 });
 function draw(){
  const q=normalize(input.value).trim();
  const all=entries();
  const references=searchLibraryReferences(input.value);
  const matches=all.filter(({key,code,article})=>!q||(references!==null?references.some(result=>result.code.id===code?.id&&result.article.id===article?.id):normalize(code?code.name+' '+code.short+' '+(article?articleLabel(article)+' '+article.text:key):key).includes(q)));
  const groups=collections.map(code=>({code,items:matches.filter(item=>item.code?.id===code.id)}));
  const unknown=matches.filter(item=>!item.code);if(unknown.length)groups.push({code:null,items:unknown});
  document.querySelector('#favorites-count').textContent=`${matches.length} ${matches.length===1?'favorito':'favoritos'}${q?(matches.length===1?' encontrado':' encontrados'):''}`;
  document.querySelector('#favorites-list').innerHTML=matches.length?groups.filter(group=>group.items.length).map(({code,items})=>`<section class="favorite-group"><h2>${code?escape(code.name):'Marcações indisponíveis'} <span>${items.length}</span></h2><ul>${items.map(({key,article})=>{
   const label=article?articleLabel(article):key;
   const paragraph=article?.paragraphs.find(p=>p.runs.some(run=>!run.deleted&&run.text.trim()));
   const preview=paragraph?.runs.filter(run=>!run.deleted).map(run=>run.text).join('')||article?.text||'';
   return `<li class="favorite-entry"><div>${article?`<a class="favorite-link" href="${codeHref(code,article.id)}"><strong>${escape(label)}</strong><span aria-hidden="true">→</span></a>${['cancelled','pending','suspended'].includes(article.status)?`<small class="favorite-status">${{cancelled:'Cancelada',pending:'Pendente de publicação',suspended:'Suspensa'}[article.status]} — conforme indicado na edição</small>`:''}<p>${escape(preview.slice(0,220))}${preview.length>220?'…':''}</p>`:`<strong>${escape(label)}</strong><p>Esta referência não foi encontrada na edição atual. A marcação foi mantida para sua conferência.</p>`}</div><button data-remove-favorite="${escape(key)}" aria-label="Remover favorito ${escape(label)}${code?' de '+escape(code.short):''}">Remover</button></li>`;
  }).join('')}</ul></section>`).join(''):`<div class="favorites-empty"><span aria-hidden="true">☆</span><h2>${all.length?'Nenhum favorito encontrado':'Sua seleção começa aqui'}</h2><p>${all.length?'Tente o nome da norma, o número ou uma palavra do texto.':'Use a estrela ao lado de um artigo ou súmula para encontrá-lo aqui depois.'}</p><a href="#">Explorar a biblioteca →</a></div>`;
  document.querySelectorAll('[data-remove-favorite]').forEach(button=>button.onclick=()=>{
   const key=button.dataset.removeFavorite;
   const buttons=[...document.querySelectorAll('[data-remove-favorite]')],index=buttons.indexOf(button);
   saved=saved.filter(item=>item!==key);
   toast(storageWrite('lexa-saved',saved)?'Favorito removido':'Remoção temporária: armazenamento indisponível');
   draw();const remaining=document.querySelectorAll('[data-remove-favorite]');(remaining[Math.min(index,remaining.length-1)]||input).focus();
  });
 }
 input.addEventListener('input',draw);draw();
}

async function copyContent(text,button,message){
 try{
  await navigator.clipboard.writeText(text);toast(message);
  const menu=button.closest('.article-copy');menu.open=false;menu.querySelector('summary').focus({preventScroll:true});
 }catch{
  const dialog=document.querySelector('#copy-dialog');
  const content=document.querySelector('#copy-content');content.value=text;
  dialog.showModal();content.focus();content.select();
 }
}
function home() {
 const resume=lastReading();
 let homeActive=true,searchSequence=0;
 document.title='Lexa — Legislação, com clareza';
 app.innerHTML=`<section class="hero"><div class="eyebrow"><span></span> SEU PONTO DE PARTIDA NO DIREITO</div><h1>A lei, mais perto. <br><em>A consulta, mais simples.</em></h1><p>Busque por referência, palavra ou súmula. <br>Compare as versões registradas e leia offline após preparar o acesso neste navegador.</p><label class="search hero-search"><span>⌕</span><input id="library-search" placeholder="Ex.: Art. 60 CF, CPC ou dignidade…" aria-label="Buscar na biblioteca"><kbd>/</kbd></label><div class="search-examples" role="group" aria-label="Exemplos de busca"><span>Experimente</span>${['Art. 5 CF','SV 13','dignidade'].map(query=>`<button type="button" data-example="${escape(query)}">${escape(query)}</button>`).join('')}</div><div class="quick-reference" id="quick-reference" aria-label="Resultados por referência" hidden></div><div class="hero-note">§ <span>${collections.filter(c=>c.kind!=='sumulas').length} legislações · ${number(total)} entradas de artigos · ${collections.find(c=>c.id==='sv').articleCount} súmulas vinculantes</span></div><div class="hero-art" aria-hidden="true"><div class="orbit"></div><div class="book book-back"></div><div class="book book-front"><span>LEXA / BIBLIOTECA JURÍDICA</span><b>O direito <br>ao seu <br>alcance.</b><i>§</i><small>LEGISLAÇÃO FEDERAL BRASILEIRA</small></div><div class="art-tag">↗ Clareza em cada artigo</div></div></section>${resume?`<section class="resume-reading" aria-label="Retomar leitura"><div><span class="eyebrow">SUA ÚLTIMA LEITURA</span><p><strong>${escape(resume.code.name)}</strong> · ${articleLabel(resume.article)}</p><small>Salva somente neste navegador.</small></div><a href="${codeHref(resume.code,resume.article.id)}">Continuar leitura →</a><button id="forget-reading" aria-label="Esquecer última leitura">×</button></section>`:''}<section class="library"><div class="section-heading"><div class="eyebrow">EXPLORE A BIBLIOTECA</div><h2>O que você quer consultar?</h2><p>Busque uma coleção, uma referência ou palavras nos textos de toda a biblioteca.</p></div><div class="filters" aria-label="Filtrar por área">${['Todas as áreas','Constitucional','Civil','Penal','Processual','Consumidor','Tributário','Trabalho','Infância e Juventude','Mulher','Administrativo','Súmulas'].map(x=>`<button class="${x===category?'active':''}" data-category="${x}" aria-pressed="${x===category}">${x}</button>`).join('')}</div><p id="library-results" class="library-results" role="status"></p><div class="cards" id="cards"></div><div id="text-results" class="text-results"></div><div class="notice"><span>ⓘ</span><div><strong>${collections.filter(c=>c.kind!=='sumulas').every(c=>c.source.kind==='official_html')?'Textos extraídos das fontes oficiais':'Base de leitura e atualização'}</strong><p>${collections.filter(c=>c.kind!=='sumulas').every(c=>c.source.kind==='official_html')?'As legislações foram extraídas das páginas oficiais do Planalto. A data de coleta aparece em cada legislação.':'Esta edição usa os PDFs fornecidos. A Constituição segue a 69ª edição da Câmara (2026), até a EC 138/2025.'} Novas coletas são propostas para revisão antes de incorporar os textos ao site. A data de coleta não certifica o início de vigência de cada alteração. ${collections.find(c=>c.id==='sv').source.kind==='official_stf'?'As súmulas vinculantes usam a edição das páginas oficiais do STF incorporada após revisão.':'As súmulas vinculantes usam o PDF fornecido, com consulta declarada em 16/10/2026.'} As situações constam em cada entrada.</p></div></div></section><section class="history-invite"><div><div class="eyebrow">DE OLHO NAS VERSÕES</div><h2>Entenda o que mudou.</h2><p>Acompanhe os registros e compare os textos das atualizações.</p></div><a href="#/atualizacoes">Ver atualizações →</a></section><section class="features"><div><span>01 / ENCONTRE</span><h3>Menos caminhos. <br>Mais respostas.</h3><p>Legislações e súmulas organizadas, com indicação da edição consultada.</p></div><div><span>02 / NAVEGUE</span><h3>Direto ao artigo <br>que você precisa.</h3><p>Busque por palavras, artigos com letras ou números como 1.022. Constituição e ADCT têm navegação separada.</p></div><div><span>03 / LEIA</span><h3>Espaço para <br>se concentrar.</h3><p>Fonte ajustável, tema escuro e marcações salvas no seu dispositivo.</p></div></section>`;
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
   try{await loadSearchIndexes(selected);}catch{
    if(homeActive&&sequence===searchSequence){status.textContent='Não foi possível carregar a busca. Verifique a conexão e tente novamente.';document.querySelector('#text-results').innerHTML='<button class="text-more" id="retry-search">Tentar novamente</button>';document.querySelector('#retry-search').onclick=draw;}
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
   document.querySelector('#cards').innerHTML=references.length?references.map(({code,article})=>{
    const paragraph=article.paragraphs.find(p=>p.runs.some(r=>!r.deleted&&r.text.trim()));
    const preview=paragraph?.runs.filter(r=>!r.deleted).map(r=>r.text).join('')||article.text;
    return `<a class="code-card reference-result" href="${codeHref(code,article.id)}"><span class="area">${escape(code.name)}</span><h3>${articleLabel(article)}</h3><p>${escape(preview.slice(0,220))}${preview.length>220?'…':''}</p><div class="card-bottom"><small>${escape(code.short)}</small><span>Abrir no leitor →</span></div></a>`;
   }).join(''):'<p class="empty">Referência não encontrada. Confira o número e a sigla da coleção.</p>';
   return;
  }
  document.querySelector('#library-results').textContent='';
  const filtered=collections.filter(c=>(category==='Todas as áreas'||c.area.includes(category))&&normalize(c.name+' '+c.short+' '+c.area+' '+c.description).includes(q));
  document.querySelector('#cards').innerHTML=filtered.length?filtered.map(c=>`<a class="code-card" href="${codeHref(c)}"><div class="card-top"><span class="code-icon">${escape(c.icon)}</span><span class="code-short">${escape(c.short)}</span></div><span class="area">${escape(c.area)}</span><h3>${escape(c.name)}</h3><p>${escape(c.description)}</p><span class="card-count">${number(c.articleCount)} ${c.kind==='sumulas'?'súmulas':'entradas'}${c.id==='cf'?' · inclui ADCT':''}</span><div class="card-bottom"><small>${escape(c.law)}</small><span>Consultar <b>↗</b></span></div></a>`).join(''):'';
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
    return `<li><a class="text-result" href="${codeHref(code,article.id)}?q=${encodeURIComponent(currentQuery)}"><div class="text-result-title"><strong>${articleLabel(article)}</strong><span aria-hidden="true">→</span></div>${status?`<span class="search-badge">${status} — conforme a edição</span>`:''}${match.kind==='notes'?'<span class="search-badge">Ocorrência em precedentes, jurisprudência ou observações</span>':match.kind==='title'?'<span class="search-badge">Ocorrência no título do artigo</span>':''}${riscado?'<span class="search-badge">Contém trecho riscado na fonte</span>':''}<p>${excerpt.leading?'…':''}${excerpt.runs.map(run=>run.deleted?`<del>${highlight(run.text,currentQuery)}</del>`:highlight(run.text,currentQuery)).join('')}${excerpt.trailing?'…':''}</p><small>${escape(article.section||'')}</small></a></li>`;
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

function highlight(text, query) {
 const q=normalize(query.trim());
 if(!q || !/[a-z]/.test(q) || /^(?:adct\s*)?art\.?\s*\d/.test(q))return escape(text);
 const chars=Array.from(text), positions=[];
 let normalized='';
 chars.forEach((c,index)=>{const part=normalize(c);for(let i=0;i<part.length;i++)positions.push(index);normalized+=part;});
 let html='',cursor=0,search=0,found;
 while((found=normalized.indexOf(q,search))>=0){
  const start=positions[found],end=positions[found+q.length-1]+1;
  html+=escape(chars.slice(cursor,start).join(''))+'<mark>'+escape(chars.slice(start,end).join(''))+'</mark>';
  cursor=end;search=found+q.length;
 }
 return html+escape(chars.slice(cursor).join(''));
}

function diffColumn(tokens, side) {
 if(!tokens.length)return '<p class="comparison-empty">Não constava nesta versão.</p>';
 let html='',paragraph=-1;
 for(const token of tokens){
  if(token.paragraph!==paragraph){if(paragraph>=0)html+='</p>';html+='<p>';paragraph=token.paragraph;}
  let text=escape(token.text);
  if(token.deleted)text=`<del title="Riscado na fonte original">${text}</del>`;
  if(token.changed)text=`<mark class="diff-${side}">${text}</mark>`;
  html+=text;
 }
 return html+'</p>';
}

function updatesPage(params) {
 document.title='Atualizações da legislação — Lexa';
 let codeId=params.get('codigo')||'',articleId=params.get('artigo')||'',limit=12;
 if(!collections.some(c=>c.id===codeId))codeId='';
 const order=recordedUpdates.map((event,index)=>({event,index})).sort((a,b)=>Date.parse(b.event.capturedAt)-Date.parse(a.event.capturedAt)||b.index-a.index).map(item=>item.event);
 const summary=historySummary(recordedUpdates);
 const kindLabels={baseline:'Referência inicial',text:'Mudanças no texto',source:'Atualização da fonte',processing:'Reprocessamento'};
 const changeLabels={added:'Adicionado ao texto',changed:'Texto alterado',removed:'Ausente nesta versão'};
 app.innerHTML=`<section class="updates-hero"><a class="back" href="#">← Voltar à biblioteca</a><div class="eyebrow"><span></span> ACOMPANHE AS VERSÕES</div><h1>O que mudou <br><em>na sua leitura.</em></h1><p>Veja as diferenças entre as versões consultadas dos códigos e das súmulas. <br>Mais contexto para acompanhar cada atualização.</p><div class="history-stats">${summary.since?`<span>Acompanhando desde <strong>${collectionDate({capturedAt:summary.since})}</strong></span>`:''}<span><strong>${number(summary.norms)}</strong> ${summary.norms===1?'norma em acompanhamento':'normas em acompanhamento'}</span>${summary.versions?`<span><strong>${number(summary.versions)}</strong> ${summary.versions===1?'nova versão registrada':'novas versões registradas'}</span>`:''}${summary.changes?`<span><strong>${number(summary.changes)}</strong> ${summary.changes===1?'alteração de entrada registrada':'alterações de entradas registradas'}</span>`:''}</div></section><section class="updates-content"><div class="updates-toolbar"><label>Legislação<select id="history-code"><option value="">Todas as legislações</option>${collections.map(c=>`<option value="${escape(c.id)}">${escape(c.name)}</option>`).join('')}</select></label><label>Artigo ou súmula<input id="history-article" placeholder="Ex.: 186, ADCT-1 ou SV 13" value="${escape(articleId)}"></label><button id="history-clear">Limpar filtros</button></div><p class="history-help">As datas indicam a coleta da fonte. Os destaques mostram diferenças no texto, sem classificar juridicamente as alterações ou certificar sua vigência.</p><div id="history-results" role="status"></div><div id="history-events"></div><button id="history-more" class="history-more" hidden>Carregar mais versões</button></section>`;
 document.querySelector('#history-code').value=codeId;
 function draw(){
  const events=filterUpdates(order,codeId,articleId);
  document.querySelector('#history-results').textContent=`${events.length} ${events.length===1?'registro encontrado':'registros encontrados'}`;
  document.querySelector('#history-events').innerHTML=events.slice(0,limit).map(event=>{
   const code=collections.find(c=>c.id===event.codeId);
   const counts=event.changes.reduce((v,c)=>(v[c.type]++,v),{added:0,changed:0,removed:0});
   return `<details class="update-event" ${articleId?'open':''}><summary><span class="timeline-dot"></span><div class="event-heading"><div class="event-meta"><time datetime="${escape(event.capturedAt)}">${collectionDate(event)}</time><span class="event-kind kind-${event.kind}">${kindLabels[event.kind]||'Registro de versão'}</span></div><h2>${escape(code.name)}</h2><p>${event.kind==='baseline'?'Ponto de partida para acompanhar as próximas versões.':`${event.changes.length} ${event.changes.length===1?'entrada com diferença':'entradas com diferenças'}${counts.added?' · '+counts.added+' adicionado(s)':''}${counts.removed?' · '+counts.removed+' ausente(s)':''}`}</p></div><span class="event-expand" aria-hidden="true">+</span></summary><div class="event-body">${event.kind==='baseline'?'<div class="baseline-note">Esta é a referência inicial do histórico. A migração entre formatos não é apresentada como mudança na legislação. As próximas versões podem ser comparadas a partir deste registro.</div>':event.changes.length?'':'<p>Foi registrada uma nova versão da fonte, sem diferenças identificadas nos textos das entradas pelo comparador.</p>'}${event.kind==='processing'?'<p class="history-help">Este registro decorre de um ajuste no processamento do mesmo documento, sem indicar uma nova publicação legal.</p>':''}${event.changes.map((change,index)=>`<details class="article-change" data-revision-event="${event.id}" data-revision-index="${index}"><summary><strong>${articleLabel(change)}</strong><span class="change-tag tag-${change.type}">${changeLabels[change.type]}</span><span aria-hidden="true">⌄</span></summary><div class="comparison-container"></div><div class="comparison-footer"><a href="${codeHref(code,change.articleId)}">Abrir entrada na versão do site →</a></div></details>`).join('')}<div class="event-footer"><a href="${codeHref(code)}">Consultar ${escape(code.short)} →</a><a href="${escape(event.sourceUrl)}" target="_blank" rel="noopener noreferrer">Fonte oficial ↗</a></div></div></details>`;
  }).join('')||`<div class="history-empty"><span>↺</span><h2>${recordedUpdates.length?'Nenhum registro para estes filtros':'O histórico começa aqui.'}</h2><p>${recordedUpdates.length?'Escolha outra legislação ou outro artigo.':'As primeiras versões incorporadas estabelecerão a referência inicial. As mudanças seguintes aparecerão aqui, com comparação entre os textos.'}</p><a href="#">Explorar a biblioteca →</a></div>`;
  document.querySelector('#history-more').hidden=events.length<=limit;
  document.querySelectorAll('[data-revision-event]').forEach(details=>details.addEventListener('toggle',()=>{
   if(!details.open||details.dataset.loaded)return;
   const event=events.find(e=>e.id===details.dataset.revisionEvent);
   const change=event.changes[Number(details.dataset.revisionIndex)];
   const comparison=compareVersions(change.before,change.after);
   details.querySelector('.comparison-container').innerHTML=`<div class="diff-legend"><span class="legend-before">Diferente na versão anterior</span><span class="legend-after">Diferente na versão coletada</span></div><div class="comparison-grid"><section><h3>Versão anterior</h3>${diffColumn(comparison.before,'before')}</section><section><h3>Versão coletada</h3>${diffColumn(comparison.after,'after')}</section></div><p class="comparison-caution">Riscados já presentes na fonte são preservados. A ausência de um trecho não determina, por si só, revogação ou início de vigência.</p>`;
   details.dataset.loaded='true';
  }));
 }
 function sync(){
  limit=12;
  const query=new URLSearchParams();if(codeId)query.set('codigo',codeId);if(articleId)query.set('artigo',articleId);
  history.replaceState(null,'','#/atualizacoes'+(query.size?'?'+query:''));draw();
 }
 document.querySelector('#history-code').onchange=e=>{codeId=e.target.value;sync();};
 document.querySelector('#history-article').oninput=e=>{articleId=e.target.value;sync();};
 document.querySelector('#history-clear').onclick=()=>{codeId='';articleId='';document.querySelector('#history-code').value='';document.querySelector('#history-article').value='';sync();};
 document.querySelector('#history-more').onclick=()=>{limit+=12;draw();};
 draw();
}

function reader(code, requested, params) {
 const target=requested?articleById(code,requested):null;
 let scope=target?.scope || (params.get('scope')==='adct'?'adct':'main');
 let query=params.get('q') || (requested&&!target?requested:'');
 let onlySaved=params.get('saved')==='1';
 let page=0, sectionId=null;
 const pageSize=15;
 document.title=`${escape(code.short)} · ${escape(code.name)} — Lexa`;
 const source=code.source;
 const isSumula=code.kind==='sumulas';
 app.innerHTML=`<section class="reader-top"><a class="back" href="#">← Voltar à biblioteca</a><div class="eyebrow">${escape(code.area)}</div><h1>${escape(code.name)}</h1><p>${escape(code.law)} <span>·</span> <a href="#/atualizacoes?codigo=${escape(code.id)}">Histórico de versões</a> <span>·</span> <a href="${escape(code.url)}" target="_blank" rel="noopener noreferrer">Fonte oficial ↗</a></p><div class="reading-notice"><strong>${escape(source.edition)}</strong> <br>${['official_html','official_stf'].includes(source.kind)?'Coleta da fonte oficial · '+collectionDate(source):isSumula?'Data de consulta declarada no PDF · 16/10/2026':'Importação do PDF fornecido · '+source.importedAt.split('-').reverse().join('/')} · Confira as notas de vigência.</div><details class="source-details"><summary>Sobre esta versão e a fonte de origem</summary>${sourcePanel(source)}</details></section><div class="reader-layout"><aside><details class="reader-index" ${window.innerWidth>700?'open':''}><summary>${isSumula?'Índice das súmulas':'Índice da legislação'}</summary><p class="index-note">${isSumula?'Escolha um intervalo para navegar pelas súmulas.':'Expanda as divisões e escolha o trecho que deseja ler.'}</p><div id="index-list"></div></details></aside><section class="reading">${code.id==='cf'?'<div class="scope-tabs" role="group" aria-label="Parte da Constituição"><button data-scope="main">Constituição</button><button data-scope="adct">ADCT</button></div>':''}<div class="reading-controls"><div class="reading-context"><span class="reading-position"><strong>${escape(code.short)}</strong><span id="reading-location">Leitura</span></span><button id="focus-mode" aria-pressed="false">Modo de foco</button></div><div class="reading-toolbar"><label class="search"><span>⌕</span><input id="article-search" placeholder="${isSumula?'Buscar expressão ou súmula (ex.: SV 13)':'Buscar expressão ou artigo (ex.: 5 ou 54-A)'}" aria-label="${isSumula?'Buscar nas súmulas vinculantes':'Buscar nesta legislação'}"></label></div><details class="reading-settings" ${window.innerWidth>700?'open':''}><summary>Ajustes de leitura <span id="font-size" role="status"></span></summary><div class="reading-adjustments"><div class="font-controls" role="group" aria-label="Tamanho da fonte"><button id="font-down" aria-label="Diminuir fonte">A−</button><button id="font-up" aria-label="Aumentar fonte">A+</button></div><label for="reading-spacing">Espaçamento</label><select id="reading-spacing"><option value="standard">Padrão</option><option value="comfortable">Confortável</option><option value="wide">Amplo</option></select><button id="reset-reading">Restaurar leitura</button></div></details></div><div class="reader-options"><button id="saved-filter" aria-pressed="${onlySaved}">☆ Meus favoritos</button><button id="clear-section" hidden>Limpar divisão selecionada ×</button><span id="results-label" role="status"></span></div><div id="introduction"></div><div id="articles"></div><nav class="pagination" aria-label="Páginas de leitura"><button id="previous-page">← Anteriores</button><span id="page-label"></span><button id="next-page">Próximos →</button></nav></section></div>`;
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
 cleanupReader=()=>{rememberPosition();controlsObserver?.disconnect();active=false;clearTimeout(positionTimer);window.removeEventListener('scroll',onScroll);document.body.classList.remove('reading-focus');};
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
 const previousCleanup=cleanupReader;cleanupReader=()=>{document.removeEventListener('keydown',onEscape);previousCleanup();};
 applyPreferences();
 const {sectionMap,trees,bySection}=readerModel(code);
 let expanded=new Set(),indexInitialized=false,indexMarkupKey=null,selectionCache=null;
 function selectedArticles(){
  if(selectionCache&&selectionCache.query===query&&selectionCache.scope===scope&&selectionCache.sectionId===sectionId&&selectionCache.onlySaved===onlySaved&&selectionCache.saved===saved)return selectionCache.articles;
  const ids=sectionId?.startsWith('branch:')?trees.get(scope).nodes.get(sectionId.slice(7))?.sectionIds:null;
  const articles=searchArticles(code,query,scope).filter(a=>(!sectionId||(ids?ids.includes(a.sectionId):a.sectionId===sectionId))&&(!onlySaved||saved.includes(code.id+'/'+a.id)));
  selectionCache={query,scope,sectionId,onlySaved,saved,articles};return articles;
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
  document.querySelectorAll('#index-list [data-section],#index-list [data-branch]').forEach(button=>button.onclick=()=>{
   sectionId=button.dataset.branch?'branch:'+button.dataset.branch:button.dataset.section;
   query='';input.value='';page=0;draw();if(window.innerWidth<=700)document.querySelector('.reader-index').open=false;scrollReading();
  });
  updateLocation(currentSection);
 }
 function sectionHeadings(section,previous){
  const path=sectionPath(section),before=previous?sectionPath(previous):[];
  let shared=0;while(shared<path.length&&path[shared]===before[shared])shared++;
  return `<div class="legal-divisions">${path.slice(shared).map((text,offset)=>{
   const depth=shared+offset,level=Math.min(6,depth+2),[label,...description]=text.split(' — ');
   return `<h${level} class="legal-heading legal-${headingKind(text)}"><span>${escape(label)}</span>${description.length?`<strong>${escape(description.join(' — '))}</strong>`:''}</h${level}>`;
  }).join('')}</div>`;
 }
 function scrollReading(){document.querySelector('.reading-toolbar').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}
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
   return `${heading}<article id="art-${a.id}" data-section-id="${a.sectionId}" class="article ${target?.id===a.id?'focused-article':''}"><div class="article-heading"><a href="${codeHref(code,a.id)}">${articleLabel(a)}</a><div><button data-save="${a.id}" aria-label="Favoritar ${articleLabel(a)}" aria-pressed="${saved.includes(code.id+'/'+a.id)}">${saved.includes(code.id+'/'+a.id)?'★':'☆'}</button><details class="article-copy"><summary aria-label="Opções de cópia de ${articleLabel(a)}">Copiar <span aria-hidden="true">⌄</span></summary><div class="copy-menu"><button data-copy-text="${a.id}">${isSumula?'Enunciado e referência':'Texto e referência'}</button><button data-copy="${a.id}">Copiar link</button></div></details></div></div>${a.status==='cancelled'?`<p class="sumula-status">Cancelada — conforme indicado ${source.kind==='official_stf'?'na fonte consultada':'no PDF'}</p>`:a.status==='pending'?`<p class="sumula-status">Pendente de publicação — conforme indicado ${source.kind==='official_stf'?'na fonte consultada':'no PDF'}</p>`:a.status==='suspended'?'<p class="sumula-status">Suspensa — conforme indicado na fonte consultada</p>':''}${a.title?`<h3 class="article-title">${highlight(a.title,query)}</h3>`:''}${hasDeleted?'<p class="deleted-note">Trechos riscados na fonte original estão preservados como redações anteriores ou suprimidas.</p>':''}${a.paragraphs.map((p,index)=>`<p class="legal-unit unit-${unitKind(p,index)}${p.runs.every(r=>r.deleted||!r.text.trim())?' deleted-paragraph':''}">${p.runs.map(r=>r.deleted?`<del>${highlight(r.text,query)}</del>`:highlight(r.text,query)).join('')}</p>`).join('')}${a.notes?.length?`<details class="sumula-notes" ${searchNotes&&a.notes.some(p=>normalize(p.runs.map(r=>r.text).join('')).includes(normalize(query)))?'open':''}><summary>Precedentes, jurisprudência e observações</summary><div>${a.notes.map(p=>`<${p.heading?'h4':'p'}>${p.runs.map(r=>highlight(r.text,query)).join('')}</${p.heading?'h4':'p'}>`).join('')}</div></details>`:''}<div class="article-source">${['official_html','official_stf'].includes(source.kind)?'Fonte: '+(isSumula?'STF':'Planalto')+' · coleta em '+collectionDate(source):escape(source.filename)+' · página '+a.page+(a.endPage&&a.endPage!==a.page?' a '+a.endPage:'')}${a.url?` · <a href="${escape(a.url)}" target="_blank" rel="noopener noreferrer">Página desta súmula no STF ↗</a>`:''}${a.rangeEnd?' · revogação agrupada no documento':''}${historyArticleIds.has(code.id+'/'+a.id)?` · <a href="#/atualizacoes?codigo=${escape(code.id)}&artigo=${a.id}">${isSumula?'Ver alterações desta súmula':'Ver alterações deste artigo'} →</a>`:''}</div></article>`;
  }).join('')||`<div class="empty"><h3>${onlySaved?'Nenhum favorito nesta seleção':isSumula?'Nenhuma súmula encontrada':'Nenhum artigo encontrado'}</h3><p>${onlySaved?'Use a estrela ao lado de uma entrada para guardá-la neste navegador.':'Tente outra expressão, limpe o filtro de divisão ou confira a parte selecionada.'}</p>${otherReference?`<p><a href="${codeHref(otherReference.code,otherReference.article.id)}">Abrir ${articleLabel(otherReference.article)} · ${escape(otherReference.code.name)} →</a></p>`:''}<button id="reset-search">Limpar filtros</button></div>`;
  document.querySelector('#reset-search')?.addEventListener('click',()=>{query='';sectionId=null;onlySaved=false;input.value='';page=0;draw();});
  document.querySelector('#page-label').textContent=list.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,list.length)} de ${number(list.length)}`:'Sem resultados';
  document.querySelector('#previous-page').disabled=page===0;
  document.querySelector('#next-page').disabled=page>=pages-1;
  document.querySelectorAll('[data-save]').forEach(b=>b.onclick=()=>{const key=code.id+'/'+b.dataset.save;saved=saved.includes(key)?saved.filter(x=>x!==key):[...saved,key];try{localStorage.setItem('lexa-saved',JSON.stringify(saved));toast(saved.includes(key)?(isSumula?'Súmula salva neste dispositivo':'Artigo salvo neste dispositivo'):'Marcação removida');}catch{toast('Marcação temporária: armazenamento indisponível');}draw();});
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
 document.querySelector('#previous-page').onclick=()=>{page--;draw();scrollReading();};
 document.querySelector('#next-page').onclick=()=>{page++;draw();scrollReading();};
 draw();
 if(target)requestAnimationFrame(()=>{if(active){document.getElementById('art-'+target.id)?.scrollIntoView({block:'start'});rememberPosition();}});
}

let routeGeneration=0;
async function route(){
 const generation=++routeGeneration;
 const copyDialog=document.querySelector('#copy-dialog');if(copyDialog.open)copyDialog.close();
 cleanupReader();cleanupReader=()=>{};
 const [path,query='']=location.hash.slice(1).split('?');
 const [,id,article]=path.split('/');
 const activeNav=id==='favoritos'?'#/favoritos':id==='atualizacoes'?'#/atualizacoes':'#';
 document.querySelectorAll('header nav>a').forEach(link=>{
  if(link.getAttribute('href')===activeNav)link.setAttribute('aria-current','page');
  else link.removeAttribute('aria-current');
 });
 const code=collections.find(c=>c.id===id);
 const needsData=code&&!code.loaded||id==='favoritos'||id==='atualizacoes';
 if(needsData)app.innerHTML=`<section class="loading-panel"><p role="status">${code?'Carregando '+escape(code.name)+'…':id==='favoritos'?'Carregando favoritos…':'Carregando histórico…'}</p></section>`;
 try{
  if(id==='favoritos'){
   await loadCollections(collections.filter(code=>saved.some(key=>key.startsWith(code.id+'/'))));
   if(generation!==routeGeneration)return;
   favoritesPage();window.scrollTo(0,0);return;
  }
  if(id==='atualizacoes'){
   const history=await loadHistory();if(generation!==routeGeneration)return;
   recordedUpdates.splice(0,recordedUpdates.length,...history);
   updatesPage(new URLSearchParams(query));window.scrollTo(0,0);return;
  }
  if(code){await loadCollection(code);if(generation!==routeGeneration)return;reader(code,article,new URLSearchParams(query));}
  else home();
  if(!article)window.scrollTo(0,0);
 }catch{
  if(generation!==routeGeneration)return;
  app.innerHTML='<section class="loading-panel"><h1>Não foi possível abrir esta edição</h1><p role="status">Verifique a conexão e tente novamente. Para ler offline, aguarde a preparação completa do acesso neste navegador.</p><button id="retry-load">Tentar novamente</button><a href="#">Voltar à biblioteca</a></section>';
  document.querySelector('#retry-load').onclick=route;
 }
}
let dark=false;try{dark=localStorage.getItem('lexa-theme')==='dark';}catch{}
document.documentElement.classList.toggle('dark',dark);
document.querySelector('#theme').onclick=()=>{dark=!dark;document.documentElement.classList.toggle('dark',dark);try{localStorage.setItem('lexa-theme',dark?'dark':'light');}catch{}};
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'&&!document.querySelector('#copy-dialog').open){const menu=document.querySelector('.article-copy[open]');if(menu){menu.open=false;menu.querySelector('summary').focus({preventScroll:true});e.stopImmediatePropagation();return;}}
 if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();document.querySelector('input')?.focus();}});
document.addEventListener('pointerdown',event=>{if(!document.querySelector('#copy-dialog').open&&!event.target.closest('.article-copy'))document.querySelectorAll('.article-copy[open]').forEach(menu=>menu.open=false);});
document.querySelector('#copy-select').onclick=()=>{const field=document.querySelector('#copy-content');field.focus();field.select();};
window.addEventListener('hashchange',route);route();

setupPwa();
