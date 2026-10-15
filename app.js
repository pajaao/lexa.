import { codes, normalize, searchArticles, articleById, articleLabel } from './data.js';

const app = document.querySelector('#app');
const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const total = codes.reduce((n,c)=>n+c.articles.length,0);
const number = n => n.toLocaleString('pt-BR');
let category = 'Todas as áreas';
let saved = [];
try { const value=JSON.parse(localStorage.getItem('lexa-saved') || '[]'); if(Array.isArray(value))saved=value.filter(x=>typeof x==='string'); } catch {}
function toast(message) { const el=document.querySelector('#toast'); el.textContent=message; el.classList.add('visible'); setTimeout(()=>el.classList.remove('visible'),2500); }
const codeHref = (code,article='') => `#/${code.id}${article?'/'+article:''}`;

function home() {
 document.title='Lexa — Legislação, com clareza';
 app.innerHTML=`<section class="hero"><div class="eyebrow"><span></span> SEU PONTO DE PARTIDA NO DIREITO</div><h1>A lei, mais perto.<br><em>A consulta, mais simples.</em></h1><p>Os principais códigos brasileiros e a Constituição em um só lugar.<br>Encontre o que precisa. Leia com tranquilidade.</p><label class="search hero-search"><span>⌕</span><input id="library-search" placeholder="Busque uma legislação, área ou sigla…" aria-label="Buscar na biblioteca"><kbd>/</kbd></label><div class="hero-note">§ <span>6 legislações · ${number(total)} entradas de artigos · Acesso livre</span></div><div class="hero-art" aria-hidden="true"><div class="orbit"></div><div class="book book-back"></div><div class="book book-front"><span>LEXA / BIBLIOTECA JURÍDICA</span><b>O direito<br>ao seu<br>alcance.</b><i>§</i><small>LEGISLAÇÃO FEDERAL BRASILEIRA</small></div><div class="art-tag">↗ Clareza em cada artigo</div></div></section><section class="library"><div class="section-heading"><div class="eyebrow">EXPLORE A BIBLIOTECA</div><h2>Qual legislação você procura?</h2><p>Abra um texto para buscar por assunto ou ir direto ao artigo.</p></div><div class="filters" aria-label="Filtrar por área">${['Todas as áreas','Constitucional','Civil','Penal','Processual','Consumidor','Tributário'].map(x=>`<button class="${x===category?'active':''}" data-category="${x}" aria-pressed="${x===category}">${x}</button>`).join('')}</div><div class="cards" id="cards"></div><div class="notice"><span>ⓘ</span><div><strong>Textos importados dos PDFs fornecidos</strong><p>Os cinco códigos foram extraídos dos PDFs do Planalto. A Constituição segue a 69ª edição da Câmara (2026), até a EC 138/2025, incluindo o ADCT. A extração é automatizada; não houve conferência jurídica integral nem verificação de alterações posteriores. A atualização automática ainda não está ativa.</p></div></div></section><section class="features"><div><span>01 / ENCONTRE</span><h3>Menos caminhos.<br>Mais respostas.</h3><p>Legislações organizadas por área, com indicação da edição consultada.</p></div><div><span>02 / NAVEGUE</span><h3>Direto ao artigo<br>que você precisa.</h3><p>Busque por palavras, artigos com letras ou números como 1.022. Constituição e ADCT têm navegação separada.</p></div><div><span>03 / LEIA</span><h3>Espaço para<br>se concentrar.</h3><p>Fonte ajustável, tema escuro e marcações salvas no seu dispositivo.</p></div></section>`;
 const draw=()=>{
  const q=normalize(document.querySelector('#library-search').value);
  const filtered=codes.filter(c=>(category==='Todas as áreas'||c.area.includes(category))&&normalize(c.name+' '+c.short+' '+c.area+' '+c.description).includes(q));
  document.querySelector('#cards').innerHTML=filtered.length?filtered.map(c=>`<a class="code-card" href="${codeHref(c)}"><div class="card-top"><span class="code-icon">${c.icon}</span><span class="code-short">${c.short}</span></div><span class="area">${c.area}</span><h3>${c.name}</h3><p>${c.description}</p><span class="card-count">${number(c.articles.length)} entradas${c.id==='cf'?' · inclui ADCT':''}</span><div class="card-bottom"><small>${c.law}</small><span>Consultar <b>↗</b></span></div></a>`).join(''):'<p class="empty">Nenhuma legislação encontrada. Tente outra palavra ou área.</p>';
 };
 document.querySelector('#library-search').addEventListener('input',draw);
 document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>{category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});draw();});
 draw();
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

function reader(code, requested, params) {
 const target=requested?articleById(code,requested):null;
 let scope=target?.scope || (params.get('scope')==='adct'?'adct':'main');
 let query=params.get('q') || (requested&&!target?requested:'');
 let onlySaved=params.get('saved')==='1';
 let page=0, size=19, sectionId=null;
 const pageSize=15;
 document.title=`${code.short} · ${code.name} — Lexa`;
 const source=code.source;
 app.innerHTML=`<section class="reader-top"><a class="back" href="#">← Voltar à biblioteca</a><div class="eyebrow">${code.area}</div><h1>${code.name}</h1><p>${code.law} <span>·</span> <a href="${code.url}" target="_blank" rel="noopener noreferrer">Fonte oficial ↗</a></p><div class="reading-notice"><strong>${escape(source.edition)}</strong><br>Importação dos PDFs · 15/10/2026 · Atualização posterior não verificada.</div><details class="source-details"><summary>Sobre esta versão e o PDF de origem</summary><p>${escape(source.coverage)} Redações riscadas no PDF são exibidas riscadas e identificadas abaixo.</p><p>${escape(source.reviewStatus)} Não há monitoramento automático ativo.</p><p><strong>Arquivo:</strong> ${escape(source.filename)} · ${source.pages} páginas.</p><p><a href="./${source.pdf}" target="_blank" rel="noopener">Abrir PDF fornecido ↗</a> <small>(disponível ao executar o site completo; a prévia isolada inclui apenas os textos)</small></p><p class="source-hash">SHA-256: ${source.sha256}</p></details></section><div class="reader-layout"><aside><details class="reader-index" ${window.innerWidth>700?'open':''}><summary>Índice da legislação</summary><p class="index-note">Escolha um capítulo para navegar pelos artigos.</p><div id="index-list"></div></details></aside><section class="reading">${code.id==='cf'?'<div class="scope-tabs" role="group" aria-label="Parte da Constituição"><button data-scope="main">Constituição</button><button data-scope="adct">ADCT</button></div>':''}<div class="reading-toolbar"><label class="search"><span>⌕</span><input id="article-search" placeholder="Buscar expressão ou artigo (ex.: 5 ou 54-A)" aria-label="Buscar nesta legislação"></label><button id="font-down" aria-label="Diminuir fonte">A−</button><button id="font-up" aria-label="Aumentar fonte">A+</button></div><div class="reader-options"><button id="saved-filter" aria-pressed="${onlySaved}">☆ Meus favoritos</button><button id="clear-section" hidden>Limpar filtro de capítulo ×</button><span id="results-label" role="status"></span></div><div id="introduction"></div><div id="articles"></div><nav class="pagination" aria-label="Páginas de artigos"><button id="previous-page">← Anteriores</button><span id="page-label"></span><button id="next-page">Próximos →</button></nav></section></div>`;
 const input=document.querySelector('#article-search');input.value=query;
 function selectedArticles(){return searchArticles(code,query,scope).filter(a=>(!sectionId||a.sectionId===sectionId)&&(!onlySaved||saved.includes(code.id+'/'+a.id)));}
 const sectionMap=new Map(code.sections.map(s=>[s.id,s]));
 function drawIndex(){
  const sections=code.sections.filter(s=>s.scope===scope);
  document.querySelector('#index-list').innerHTML=sections.map(s=>{
   const list=code.articles.filter(a=>a.sectionId===s.id);
   const parts=s.title.split(' › ');
   return `<button class="index-entry ${sectionId===s.id?'selected':''}" data-section="${s.id}" title="${escape(s.title)}"><span>${escape(parts.at(-1))}</span><small>${list[0]?.number || ''}${list.length>1?' – '+(list.at(-1).rangeEnd||list.at(-1).number):''} · ${list.length} ${list.length===1?'entrada':'entradas'}</small></button>`;
  }).join('');
  document.querySelectorAll('[data-section]').forEach(b=>b.onclick=()=>{sectionId=b.dataset.section;query='';input.value='';page=0;draw();if(window.innerWidth<=700)document.querySelector('.reader-index').open=false;scrollReading();});
 }
 function scrollReading(){document.querySelector('.reading-toolbar').scrollIntoView({block:'start',behavior:'smooth'});}
 function draw(){
  const list=selectedArticles();
  const pages=Math.max(1,Math.ceil(list.length/pageSize));page=Math.min(page,pages-1);
  const visible=list.slice(page*pageSize,(page+1)*pageSize);
  document.querySelector('#results-label').textContent=`${number(list.length)} ${list.length===1?'entrada':'entradas'}${query?' encontradas':''}`;
  document.querySelector('#saved-filter').setAttribute('aria-pressed',String(onlySaved));
  document.querySelector('#clear-section').hidden=!sectionId;
  document.querySelectorAll('[data-scope]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.scope===scope)));
  document.querySelector('#introduction').innerHTML=code.id==='cf'&&scope==='main'&&!query&&!onlySaved&&!sectionId&&page===0?code.introductions.map(intro=>`<details class="preamble"><summary>${escape(intro.title)}</summary><p>${escape(intro.text)}</p></details>`).join(''):'';
  let last='';
  document.querySelector('#articles').innerHTML=visible.map(a=>{
   const heading=last!==a.sectionId?`<h2 class="chapter">${escape(sectionMap.get(a.sectionId).title.split(' › ').at(-1))}</h2>`:'';
   last=a.sectionId;
   const hasDeleted=a.paragraphs.some(p=>p.runs.some(r=>r.deleted));
   return `${heading}<article id="art-${a.id}" class="article ${target?.id===a.id?'focused-article':''}"><div class="article-heading"><a href="${codeHref(code,a.id)}">${articleLabel(a)}</a><div><button data-save="${a.id}" aria-label="Favoritar ${articleLabel(a)}" aria-pressed="${saved.includes(code.id+'/'+a.id)}">${saved.includes(code.id+'/'+a.id)?'★':'☆'}</button><button data-copy="${a.id}" aria-label="Copiar link de ${articleLabel(a)}">↗</button></div></div>${a.title?`<h3 class="article-title">${highlight(a.title,query)}</h3>`:''}${hasDeleted?'<p class="deleted-note">Trechos riscados no PDF original estão preservados como redações anteriores ou suprimidas.</p>':''}${a.paragraphs.map(p=>`<p${p.runs.every(r=>r.deleted||!r.text.trim())?' class="deleted-paragraph"':''}>${p.runs.map(r=>r.deleted?`<del>${highlight(r.text,query)}</del>`:highlight(r.text,query)).join('')}</p>`).join('')}<div class="article-source">${escape(source.filename)} · página ${a.page}${a.rangeEnd?' · revogação agrupada no documento':''}</div></article>`;
  }).join('')||`<div class="empty"><h3>${onlySaved?'Nenhum favorito nesta seleção':'Nenhum artigo encontrado'}</h3><p>${onlySaved?'Use a estrela ao lado de um artigo para guardá-lo neste navegador.':'Tente outra expressão, limpe o filtro de capítulo ou confira a parte selecionada.'}</p><button id="reset-search">Limpar filtros</button></div>`;
  document.querySelector('#reset-search')?.addEventListener('click',()=>{query='';sectionId=null;onlySaved=false;input.value='';page=0;draw();});
  document.querySelector('#page-label').textContent=list.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,list.length)} de ${number(list.length)}`:'Sem resultados';
  document.querySelector('#previous-page').disabled=page===0;
  document.querySelector('#next-page').disabled=page>=pages-1;
  document.querySelectorAll('[data-save]').forEach(b=>b.onclick=()=>{const key=code.id+'/'+b.dataset.save;saved=saved.includes(key)?saved.filter(x=>x!==key):[...saved,key];try{localStorage.setItem('lexa-saved',JSON.stringify(saved));toast(saved.includes(key)?'Artigo salvo neste dispositivo':'Marcação removida');}catch{toast('Marcação temporária: armazenamento indisponível');}draw();});
  document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=async()=>{const link=location.href.split('#')[0]+codeHref(code,b.dataset.copy);try{await navigator.clipboard.writeText(link);toast('Link do artigo copiado');}catch{location.hash=codeHref(code,b.dataset.copy);toast('Artigo aberto. Copie o endereço da página.');}});
  drawIndex();
 }
 if(target){const index=selectedArticles().findIndex(a=>a.id===target.id);page=Math.max(0,Math.floor(index/pageSize));}
 let debounce;
 input.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(()=>{query=input.value;page=0;draw();},120);});
 document.querySelector('#font-down').onclick=()=>{size=Math.max(16,size-1);document.querySelector('#articles').style.fontSize=size+'px';};
 document.querySelector('#font-up').onclick=()=>{size=Math.min(26,size+1);document.querySelector('#articles').style.fontSize=size+'px';};
 document.querySelector('#saved-filter').onclick=()=>{onlySaved=!onlySaved;page=0;draw();};
 document.querySelector('#clear-section').onclick=()=>{sectionId=null;page=0;draw();};
 document.querySelectorAll('[data-scope]').forEach(b=>b.onclick=()=>{scope=b.dataset.scope;query='';input.value='';sectionId=null;page=0;draw();});
 document.querySelector('#previous-page').onclick=()=>{page--;draw();scrollReading();};
 document.querySelector('#next-page').onclick=()=>{page++;draw();scrollReading();};
 draw();
 if(target)requestAnimationFrame(()=>document.getElementById('art-'+target.id)?.scrollIntoView({block:'start'}));
}

function route(){
 const [path,query='']=location.hash.slice(1).split('?');
 const [,id,article]=path.split('/');
 const code=codes.find(c=>c.id===id);
 if(code)reader(code,article,new URLSearchParams(query));else home();
 if(!article)window.scrollTo(0,0);
}
let dark=false;try{dark=localStorage.getItem('lexa-theme')==='dark';}catch{}
document.documentElement.classList.toggle('dark',dark);
document.querySelector('#theme').onclick=()=>{dark=!dark;document.documentElement.classList.toggle('dark',dark);try{localStorage.setItem('lexa-theme',dark?'dark':'light');}catch{}};
document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();document.querySelector('input')?.focus();}});
window.addEventListener('hashchange',route);route();
