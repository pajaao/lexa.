export {amendmentParagraphs} from './amendment-reading.js';
import {initialCatalog} from './collections.js';
import {fetchVerifiedJson} from './loading.js';
import {escape,collectionDate} from './presentation.js';
import {prepareCollection} from './collection-model.js';
let indexTask,linksTask;
const documents=new Map();
const candidate=initialCatalog?.amendments?.candidate!==false;
export const amendmentsAvailable=()=>Boolean(initialCatalog?.amendments);
export const loadAmendmentIndex=()=>indexTask??=(initialCatalog?.amendments?fetchVerifiedJson(initialCatalog?.amendments.index).catch(e=>{indexTask=null;throw e;}):Promise.reject(new Error('Biblioteca candidata não habilitada nesta edição.')));
export const loadAmendmentLinks=()=>linksTask??=(initialCatalog?.amendments?fetchVerifiedJson(initialCatalog?.amendments.links).catch(e=>{linksTask=null;throw e;}):Promise.resolve({records:[]}));
export async function loadAmendment(number){
 const index=await loadAmendmentIndex(),entry=index.entries.find(x=>String(x.number)===String(number));
 if(!entry)throw new Error('Emenda não encontrada nesta edição.');
 if(!documents.has(entry.number)){const document=await fetchVerifiedJson(entry.document);if(document.number!==entry.number||document.blocks.length===0)throw new Error('Emenda incompleta.');documents.set(entry.number,document);if(documents.size>2)documents.delete(documents.keys().next().value);}
 return {entry,document:documents.get(entry.number)};
}
export function amendmentCollection(document,entry){
 const own=document.blocks.filter(b=>b.kind==='artigo_proprio');
 return prepareCollection({id:'ec-'+document.number,kind:'amendment',number:document.number,name:'Emenda Constitucional nº '+document.number,short:'EC '+document.number,area:'Emendas Constitucionais',law:(document.dateKind||'Data documental')+': '+formatDate(document.date),url:document.source.url,
 source:{kind:'official_html',url:document.source.url,capturedAt:document.collection.coleta_utc,edition:'Publicação original · Câmara dos Deputados'+(candidate?' · base candidata':''),sha256:entry.document.sha256,rawSha256:document.source.sha256,coverage:'Texto originalmente publicado, com transcrições constitucionais e ressalvas documentais preservadas.',reviewStatus:candidate?'Validação técnica não equivale a homologação jurídica humana. Publicação ainda não autorizada.':'Publicação autorizada conforme o registro de liberação desta edição.'},
 preamble:document.preamble?.text||'',sections:own.map(b=>({id:b.ownArticle,scope:'main',title:'Art. '+b.ownArticle})),introductions:[],
 articles:own.map(b=>({id:b.ownArticle,number:b.ownArticle,scope:'main',sectionId:b.ownArticle,paragraphs:document.blocks.filter(x=>x.ownArticle===b.ownArticle).map(x=>({runs:x.runs,sourceBlock:x.id,documentaryKind:x.kind,sourceLocation:x.source}))}))});
}
export const formatDate=value=>value?new Intl.DateTimeFormat('pt-BR',{dateStyle:'long',timeZone:'UTC'}).format(new Date(value+'T12:00:00Z')):'Data não estabelecida';
// Preserve existing text nodes and highlights: only wrap literal verified notes.
export function decorateAmendmentNotes(container,articleId,records,{historical=false}={}){
 const matches=records.filter(x=>x.articleId===articleId&&x.previous===historical);
 for(const record of matches){
  const walker=document.createTreeWalker(container,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.parentElement.closest('a,button,summary')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});let nodes=[],node;while(node=walker.nextNode())nodes.push(node);
  const full=nodes.map(n=>n.textContent).join(''),start=full.indexOf(record.note);if(start<0)continue;const end=start+record.note.length;let at=0,first,last;
  for(const node of nodes){const next=at+node.textContent.length;if(start>=at&&start<next)first={node,offset:start-at};if(end>at&&end<=next)last={node,offset:end-at};at=next;}
  if(!first||!last)continue;
  const range=document.createRange();range.setStart(first.node,first.offset);range.setEnd(last.node,last.offset);
  const a=document.createElement('a');a.href='#/emendas/'+record.ec+'?origem='+encodeURIComponent(articleId);a.className='amendment-note';a.dataset.previous=String(record.previous);a.title='Consultar EC '+record.ec+'/'+record.year+(record.previous?' · referência em redação anterior':'');a.append(range.extractContents());range.insertNode(a);
 }
}
export async function amendmentLibrary(app,params,isCurrent){
 const {entries}=await loadAmendmentIndex();if(!isCurrent())return;
 let query=params.get('q')||'',order=params.get('ordem')||'recentes',limit=5;
 document.title='Emendas Constitucionais — Lexa';
 app.innerHTML=`<section class="amendments-library"><a class="back" href="#">← Biblioteca principal</a><div class="eyebrow">Biblioteca / Emendas Constitucionais</div><h1>Emendas Constitucionais</h1><p>Consulte individualmente as emendas à Constituição, preservando a redação e a fonte de cada documento.</p>${candidate?'<p class="candidate-notice" role="note">Base candidata local · publicação não autorizada · homologação jurídica pendente.</p>':''}<p>${entries.length} emendas no acervo${candidate?' candidato':''}</p><div class="amendment-filters"><label for="amendment-search">Localizar emenda<input id="amendment-search" type="search" placeholder="Número, ano ou palavra-chave" value="${escape(query)}"></label><label for="amendment-order">Ordenar por data documental<select id="amendment-order"><option value="recentes">Mais recentes</option><option value="antigas">Mais antigas</option></select></label></div><p class="amendment-search-help">Busca por nº, ano ou termos dos metadados.</p><p id="amendment-count" role="status"></p><div id="amendment-list"></div><button id="amendment-more">Carregar mais emendas ↓</button></section>`;
 const normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 function draw(){
  const q=normalize(query).replace(/^ec\s*(?:n[ºo°.]?\s*)?/,'').trim(),exact=/^(\d+)(?:\/(\d{4}))?$/.exec(q);const selected=entries.filter(x=>!q||(exact?(exact[1].length===4?x.year===Number(exact[1]):x.number===Number(exact[1]))&&(!exact[2]||x.year===Number(exact[2])):normalize(`${x.number} ${x.year} ${x.ementa}`).includes(q))).sort((a,b)=>(order==='antigas'?1:-1)*((a.year-b.year)||(a.number-b.number)));
  app.querySelector('#amendment-list').innerHTML=selected.slice(0,limit).map(x=>`<a class="amendment-entry" href="#/emendas/${x.number}"><strong>${x.number}</strong><div><span>Emenda Constitucional · ${x.year}</span><p>${escape(x.ementa)}</p><small>${escape(x.dateKind||'Data documental')} · ${formatDate(x.date)}</small></div><span class="amendment-open">Abrir ↗</span></a>`).join('')||'<div class="empty"><h2>Nenhuma emenda encontrada</h2><p>Tente outro número, ano ou termo da ementa.</p></div>';
  app.querySelector('#amendment-count').textContent=`Exibindo ${Math.min(limit,selected.length)} de ${selected.length} emendas`;
  app.querySelector('#amendment-more').hidden=limit>=selected.length;
 }
 const sync=()=>{const p=new URLSearchParams();if(query)p.set('q',query);if(order!=='recentes')p.set('ordem',order);history.replaceState(history.state,'','#/emendas'+(p.size?'?'+p:''));};
 app.querySelector('#amendment-search').oninput=e=>{query=e.target.value;limit=5;sync();draw();};app.querySelector('#amendment-order').value=order;app.querySelector('#amendment-order').onchange=e=>{order=e.target.value;limit=5;sync();draw();};app.querySelector('#amendment-more').onclick=e=>{const old=limit;limit+=5;draw();if(e.currentTarget.hidden)app.querySelectorAll('.amendment-entry')[old]?.focus({preventScroll:true});};draw();
}
export function enhanceAmendmentReader(app,document,links,params){
 const page=app.querySelector('.reader-top');page.classList.add('amendment-heading');
 app.classList.add('amendment-reader');page.querySelector('h1').textContent='Emenda Constitucional nº '+document.number;page.querySelector(':scope>p').innerHTML=escape(document.dateKind+': '+formatDate(document.date))+' · <a href="'+escape(document.source.url)+'" target="_blank" rel="noopener noreferrer">Fonte oficial · Câmara dos Deputados ↗</a>';
 page.querySelector('.back').href='#/emendas';page.querySelector('.back').textContent='← Emendas Constitucionais';
 const heading=window.document.createElement('section');heading.className='amendment-ementa';heading.innerHTML='<div class="eyebrow">Ementa</div>'+document.ementas.map(x=>'<p>'+escape(x.text)+'</p>').join('')+(candidate?'<p class="candidate-notice">Base candidata local · publicação não autorizada.</p>':'');page.append(heading);
 const details=window.document.createElement('details');details.className='amendment-caveats';details.innerHTML='<summary>Ressalvas e identidade documental</summary>'+document.caveats.map(x=>'<p>'+escape(x)+'</p>').join('')+'<p>SHA-256 do HTML original: '+escape(document.source.sha256)+'</p>';page.append(details);
 const toggle=window.document.createElement('button');toggle.type='button';toggle.className='amendment-transcription-toggle';toggle.setAttribute('aria-pressed','false');toggle.setAttribute('aria-controls','articles');toggle.textContent='Exibir transcrição oficial integral';
 toggle.onclick=()=>{const full=app.classList.toggle('amendment-full');toggle.setAttribute('aria-pressed',String(full));toggle.textContent=full?'Voltar à leitura simplificada':'Exibir transcrição oficial integral';};
 const help=window.document.createElement('p');help.className='amendment-reading-help';help.textContent='Leitura simplificada: pontilhados de continuidade podem estar ocultos. Identificações, notas e texto normativo são preservados.';
 app.querySelector('#articles').before(toggle,help);
 app.querySelector('#saved-filter').hidden=true;app.querySelectorAll('[data-save]').forEach(x=>x.remove());
 const introduction=app.querySelector('#introduction');if(document.preamble)introduction.innerHTML='<p class="amendment-preamble">'+escape(document.preamble.text)+'</p>';
 const related=links.records.filter(x=>x.ec===document.number),unique=[...new Map(related.map(x=>[x.articleId+'|'+x.previous,x])).values()];
 const footer=window.document.createElement('section');footer.className='amendment-related';footer.innerHTML='<h2>Dispositivos relacionados na Constituição</h2><p>Referências associadas às notas oficiais da edição consultada. Esta relação não é um histórico completo de alterações.</p><div>'+unique.map(x=>`<a href="#/cf/${escape(x.articleId)}?emenda=${document.number}">${x.articleId.startsWith('adct-')?'ADCT · ':''}Art. ${escape(x.articleId.replace('adct-',''))}${x.previous?' · redação anterior na fonte':''}</a>`).join('')+'</div>'+(unique.length?'':'<p>Nenhum vínculo confirmado nas notas desta edição. Isso não significa ausência de alterações constitucionais.</p>')+'<details><summary>Fecho, assinaturas e informações de publicação</summary>'+document.closing.map(x=>'<p>'+escape(x.text)+'</p>').join('')+'</details><a class="back" href="#/emendas">← Voltar à biblioteca de Emendas</a>';
 const origin=params.get('origem');if(origin&&/^(adct-)?\d+(?:-[A-Z])?$/.test(origin)){const a=window.document.createElement('a');a.href='#/cf/'+origin;a.className='back';a.textContent='↶ Voltar à consulta do art. '+origin;footer.append(a);}
 app.querySelector('.reading').append(footer);
}
