import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
import {historyRecords,previousRecords,sourceLink,wordingLabel,readingArticle} from '../../src/legislative-history-model.js';
import {historyContent} from '../../src/legislative-history.js';
import {legislativeHistoryData as fixture} from '../fixtures/legislative-history-demo.js';
import {buildPackage} from '../../scripts/build.mjs';
import {stagePages} from '../../scripts/build-pages.mjs';
import {legislativeHistoryData as approvedData} from '../fixtures/legislative-history-pilot.js';

test('piloto local preserva a confirmação anterior e exatamente os três caputs e notas do art. 215',()=>{
 const records=historyRecords(approvedData,'penal','215');
 assert.deepEqual(records.map(r=>r.id),['penal-215-caput-01','penal-215-caput-02','penal-215-caput-03']);
 assert.deepEqual(records.map(r=>r.text),[
  'Art. 215 - Ter conjunção carnal com mulher honesta, mediante fraude:',
  'Art. 215. Ter conjunção carnal com mulher, mediante fraude:',
  'Art. 215. Ter conjunção carnal ou praticar outro ato libidinoso com alguém, mediante fraude ou outro meio que impeça ou dificulte a livre manifestação de vontade da vítima:'
 ]);
 assert.deepEqual(records.map(r=>r.notes),[[],['(Redação dada pela Lei nº 11.106, de 2005)'],['(Redação dada pela Lei nº 12.015, de 2009)']]);
 assert.ok(records.every(r=>r.part==='caput'&&r.review.evidence&&r.source.sha256==='2655efc6112d4601204208f3f4eb2e911957187fe7ce6727c4d681f6bb77ec19'));
 assert.deepEqual(historyRecords(approvedData,'civil','215'),[]);
 assert.deepEqual(historyRecords(approvedData,'penal','214'),[]);
});

test('histórico exige homologação e ordem fundamentada, sem exigir data',()=>{
 const approved={...fixture.records[0],review:{status:'approved'}};
 const records=[fixture.records[0],{...approved,id:'pending',review:{status:'pending'}},approved,
  {...approved,id:'no-basis',sequence:{order:2,basis:''}},
  {...approved,id:'other',articleId:'2'}];
 assert.deepEqual(historyRecords({demo:false,records},'penal','1'),[approved]);
 assert.equal(historyRecords({demo:true,records},'penal','1').length,1);
 assert.deepEqual(historyRecords(fixture,'penal','2'),[]);
 const reverse={...fixture,records:[...fixture.records].reverse()};
 assert.deepEqual(historyRecords(reverse,'penal','1').map(r=>r.sequence.order),[1,2]);
});

test('textos, notas e fontes são escapados; esquemas perigosos nunca viram links',()=>{
 const payload='<img src=x onerror=alert(1)>';
 const record={...fixture.records[0],text:payload,notes:[payload],reference:payload,source:{label:payload,location:payload,url:'javascript:alert(1)'}};
 const html=historyContent({demo:true,records:[record]},'penal','1');
 assert.ok(html.includes('&lt;img'));assert.ok(!html.includes('<img'));assert.ok(!html.includes('href="javascript:'));
 assert.equal(sourceLink('data:text/html,x'),null);
 assert.equal(sourceLink('https://name:secret@example.org'),null);
 assert.equal(sourceLink('https://example.org/source#page=1'),'https://example.org/source#page=1');
 const withLink=historyContent({demo:true,records:[{...record,source:{url:'https://example.org',label:'Fonte',location:'Página 1'}}]},'penal','1');
 assert.ok(withLink.includes('rel="noopener noreferrer"'));
});

test('ausências são explícitas e notas editoriais ficam separadas',()=>{
 const html=historyContent(fixture,'penal','1');
 for(const record of fixture.records)assert.ok(html.includes(record.text));
 assert.ok(html.includes('Fonte não informada.'));assert.ok(html.includes('Referência legislativa não informada.'));
 assert.equal((html.match(/<summary>Notas editoriais<\/summary>/g)||[]).length,1);
 assert.ok(historyContent({demo:false,records:[]},'penal','1').includes('Isso não significa que ele nunca tenha sido alterado.'));
});

test('pacote normal exclui fixtures; demonstração exige build explícito e não substitui dist',async()=>{
 const production=await buildPackage();
 for(const bytes of production.files.values())assert.ok(!String(bytes).includes('EXEMPLO FICTÍCIO'));
 const demo=await buildPackage({legislativeHistoryDemo:true});
 assert.ok([...demo.files.values()].some(bytes=>String(bytes).includes('EXEMPLO FICTÍCIO')));
 assert.ok([...demo.files.entries()].some(([name,bytes])=>name.endsWith('/pwa.js')&&bytes==='export function setupPwa(){}'));
 assert.deepEqual(production.manifest.collections,demo.manifest.collections);
 await assert.rejects(stagePages(undefined,{legislativeHistoryDemo:true}),/Demonstração não pode/);
});

 test('piloto real fica fora do pacote publicável e exige prévia explícita',async()=>{
 const normal=await buildPackage();
 const pilot=await buildPackage({legislativeHistoryPilot:true});
 const contains=pack=>[...pack.files.values()].some(bytes=>String(bytes).includes('penal-215-caput-01'));
 assert.equal(contains(normal),true);assert.equal(contains(pilot),true);
 assert.ok(![...normal.files.values()].some(bytes=>String(bytes).includes('penal-213-caput-01')));
 assert.ok(historyContent(approvedData,'penal','215').includes('homologação jurídica independente pendente'));
 await assert.rejects(stagePages(undefined,{legislativeHistoryPilot:true}),/Demonstração não pode/);
 });

test('unidades documentadas distinguem inciso de caput',()=>{
 const record={...fixture.records[0],part:'item'};
 assert.ok(historyContent({demo:true,records:[record]},'penal','1').includes('<h3>Inciso</h3>'));
});

 test('amostra limitada a vinte artigos preserva pendências e rótulos sem inferir vigência',async()=>{
 const {officialImported}=await import('../../data/official/legislation.js');
 assert.equal(new Set(approvedData.records.map(r=>r.articleId)).size,20);
 assert.equal(approvedData.records.length,44);
 const extra=approvedData.records.filter(r=>r.articleId!=='215');
 assert.ok(extra.every(r=>r.review.status==='pending'&&r.evidence.rawText&&r.source.sha256));
 assert.equal(historyRecords({...approvedData,preview:false},'penal','44').length,0);
 for(const id of new Set(approvedData.records.map(r=>r.articleId))){
  const records=historyRecords(approvedData,'penal',id);
  const article=officialImported.penal.articles.find(a=>a.id===id);
  assert.equal(wordingLabel(records[0],article),'Redação anterior');
  assert.equal(wordingLabel(records.at(-1),article),id==='339'?'Redação mais recente documentada':'Redação atual na edição consultada');
  assert.equal(wordingLabel(records.at(-1),{paragraphs:[{runs:[{text:'Outra edição'}]}]}),'Redação mais recente documentada');
 }
 const normal=await buildPackage();
 const source=[...normal.files].find(([name])=>name.endsWith('/legislative-history-data.js'))[1];
 assert.match(source,/penal-215-caput-01/);
 assert.ok(!source.includes('"status": "pending"'));
 assert.ok(!source.includes('penal-44-caput'));
 });

 test('ampliação preserva transcrição bruta e associação explícita por dispositivo',()=>{
 const ids=['172','180','206','218','272','282','310','311','339','343'];
 for(const id of ids){
  const rows=historyRecords(approvedData,'penal',id);
  assert.equal(rows.length,['172','311','339'].includes(id)?3:2);
  for(const row of rows){
   assert.equal(row.review.status,'pending');
   assert.equal(row.text,row.evidence.rawText.replace(/\s+/gu,' ').trim());
   assert.ok(!/Pena[ -]|Parágrafo único|\(Redação dada/u.test(row.text));
   assert.equal(historyRecords({...approvedData,preview:false},'penal',id).length,0);
  }
 }
 });

test('fontes ficam em uma única seção final com associação a cada redação',()=>{
 const html=historyContent(approvedData,'penal','215');
 assert.equal((html.match(/<summary>Fonte e contexto documental<\/summary>/g)||[]).length,1);
 assert.ok(html.indexOf('class="legislative-sources"')>html.indexOf('</ol>'));
 for(let i=1;i<=2;i++)assert.ok(html.includes(`Redação ${i} · Caput`));
 assert.equal((html.match(/Consultar fonte ↗/g)||[]).length,2);
});

test('lote adicional é isolado, preserva a base e identifica cada unidade integral',async()=>{
 const batch=JSON.parse(await readFile(new URL('../fixtures/legislative-history-batch.json',import.meta.url),'utf8'));
 const combined={...approvedData,records:[...approvedData.records,...batch.records]};
 const baselineIds=new Set(approvedData.records.map(r=>r.articleId));
 assert.equal(new Set(batch.records.map(r=>r.articleId)).size,22);
 assert.equal(batch.records.length,52);
 assert.equal(new Set(combined.records.map(r=>r.articleId)).size,42);
 assert.equal(combined.records.length,96);
 assert.ok(batch.records.every(r=>r.review.status==='pending'&&!baselineIds.has(r.articleId)));
 for(const id of new Set(batch.records.map(r=>r.articleId))){
  const rows=historyRecords(combined,'penal',id);
  assert.deepEqual(historyRecords({...combined,preview:false},'penal',id),[]);
  const html=historyContent(combined,'penal',id);
  assert.equal((html.match(/<summary>Fonte e contexto documental<\/summary>/g)||[]).length,1);
  for(const row of rows){
   assert.ok(html.includes(row.unitLabel));
   if(row.part!=='caput')assert.notEqual(wordingLabel(row), 'Redação atual na edição consultada');
  }
 }
 const production=await buildPackage();
 const pilot=await buildPackage({legislativeHistoryPilot:true});
 const getData=pack=>[...pack.files].find(([name])=>name.endsWith('/legislative-history-data.js'))[1];
 for(const record of batch.records){assert.ok(!getData(production).includes(record.id));assert.ok(getData(pilot).includes(record.id));}
 const injection={...batch.records[0],unitLabel:'<img src=x onerror=alert(1)>'};
 assert.ok(!historyContent({...combined,records:[injection]},'penal',injection.articleId).includes('<img'));
});

test('HTML fica isolado, mantém os 96 registros e identifica alíneas sem duplicar unidades',async()=>{
 const read=async name=>JSON.parse(await readFile(new URL('../fixtures/'+name,import.meta.url),'utf8')).records;
 const pdf=await read('legislative-history-batch.json');
 const html=await read('legislative-history-html.json');
 const prior=[...approvedData.records,...pdf];
 const combined={...approvedData,records:[...prior,...html]};
 assert.equal(prior.length,96);assert.ok(html.length>0);
 assert.equal(new Set(combined.records.map(r=>r.id)).size,combined.records.length);
 assert.ok(html.every(r=>r.review.status==='pending'));
 for(const code of new Set(html.map(r=>r.codeId))){
  for(const article of new Set(html.filter(r=>r.codeId===code).map(r=>r.articleId))){
   const records=historyRecords(combined,code,article);
   assert.equal(records.length,combined.records.filter(r=>r.codeId===code&&r.articleId===article).length);
   const content=historyContent(combined,code,article);
   for(const row of records)assert.ok(content.includes(row.unitLabel||'Caput'));
   assert.deepEqual(historyRecords({...combined,preview:false,records:html},code,article),[]);
  }
 }
 const letter=html.find(r=>r.part==='letter');assert.ok(letter);
 assert.ok(historyContent({...combined,records:[letter]},letter.codeId,letter.articleId).includes('alínea'));
 const production=await buildPackage();const preview=await buildPackage({legislativeHistoryPilot:true});
 const module=pack=>[...pack.files].find(([name])=>name.endsWith('/legislative-history-data.js'))[1];
 for(const row of html){assert.ok(!module(production).includes(row.id));assert.ok(module(preview).includes(row.id));}
 const exported=JSON.parse(await readFile(new URL('../../experiments/html-history/existing-records.json',import.meta.url),'utf8'));
 assert.deepEqual(prior,exported);
});

test('leitor separa anteriores integrais sem exigir substituta nem alterar a fonte',()=>{
 const old={...fixture.records[0],id:'old',codeId:'penal',articleId:'1',text:'Art. 1. Texto anterior:',review:{status:'pending'},wording:{status:'previous'}};
 const latest={...old,id:'latest',text:'Art. 1. Texto posterior:',wording:{status:'current_candidate'},sequence:{order:2,basis:'Nota de alteração documentada'}};
 const data={preview:true,demo:false,records:[old,latest]};
 const paragraph=(text,deleted)=>({runs:[{text,deleted}]});
 const article={id:'1',paragraphs:[paragraph(old.text+' (Redação dada pela Lei nº 1)',true),paragraph(latest.text,false)]};
 const snapshot=JSON.stringify(article);
 assert.deepEqual(readingArticle(data,'penal',article).paragraphs,[article.paragraphs[1]]);
 assert.equal(JSON.stringify(article),snapshot);
 assert.equal(wordingLabel(latest,article),'Redação atual na edição consultada');
 assert.deepEqual(readingArticle({...data,preview:false},'penal',article).paragraphs,[article.paragraphs[1]]);
 const missing={...article,paragraphs:[article.paragraphs[0]]};
 assert.deepEqual(readingArticle(data,'penal',missing).paragraphs,[]);
 const mixed={...article,paragraphs:[{runs:[{text:'Art. 1. Texto ',deleted:true},{text:'anterior:',deleted:false}]},article.paragraphs[1]]};
 assert.ok(readingArticle(data,'penal',mixed).paragraphs.every(p=>p.runs.every(r=>!r.deleted)));
 const incomplete={...article,paragraphs:[paragraph(old.text+' (Redação dada sem fechamento',true),article.paragraphs[1]]};
 assert.deepEqual(readingArticle(data,'penal',incomplete).paragraphs,[article.paragraphs[1]]);
 const ambiguous={...data,records:[...data.records,{...old,id:'other-unit',part:'paragraph',unitLabel:'§ 1'}]};
 assert.deepEqual(readingArticle(ambiguous,'penal',article).paragraphs,[article.paragraphs[1]]);
});

test('Constituição art. 6 mantém caput e parágrafo atual no leitor e três anteriores no histórico',async()=>{
 const {officialImported}=await import('../../data/official/legislation.js');
 const html=JSON.parse(await readFile(new URL('../fixtures/legislative-history-html.json',import.meta.url),'utf8'));
 const data={...approvedData,records:[...approvedData.records,...html.records]};
 const source=officialImported.cf.articles.find(a=>a.id==='6');const snapshot=JSON.stringify(source);
 const visible=readingArticle(data,'cf',source);
 assert.equal(source.paragraphs.length,5);assert.equal(visible.paragraphs.length,2);
 assert.equal(historyRecords(data,'cf','6').filter(r=>r.wording.status==='previous').length,3);
 assert.ok(visible.paragraphs.every(p=>p.runs.every(r=>!r.deleted)));
 assert.ok(visible.paragraphs[0].runs.map(r=>r.text).join('').includes('transporte'));
 assert.equal(JSON.stringify(source),snapshot);
});


test('CF 16, 18 e 20 separam anteriores com variantes editoriais sem alterar fontes',async()=>{
 const {officialImported}=await import('../../data/official/legislation.js');
 const {records}=JSON.parse(await readFile(new URL('../fixtures/legislative-history-html.json',import.meta.url),'utf8'));
 const data={preview:true,demo:false,records};
 for(const id of ['16','18','20']){
  const source=officialImported.cf.articles.find(a=>a.id===id),snapshot=JSON.stringify(source);
  const visible=readingArticle(data,'cf',source);
  assert.ok(visible.paragraphs.length<source.paragraphs.length,`CF ${id} deve separar anteriores`);
  assert.ok(visible.paragraphs.every(p=>p.runs.every(r=>!r.deleted)),`CF ${id} sem riscados restantes`);
  assert.equal(JSON.stringify(source),snapshot);
  assert.ok(historyRecords(data,'cf',id).some(r=>r.wording.status==='previous'));
 }
});


test('painel mostra somente anteriores: CP 215 tem duas, nunca a redação atual',()=>{
 const records=previousRecords(approvedData,'penal','215');
 assert.equal(records.length,2);
 const html=historyContent(approvedData,'penal','215');
 for(const record of records)assert.ok(html.includes(record.text));
 assert.ok(!html.includes(approvedData.records.find(r=>r.articleId==='215'&&r.wording.status==='current_candidate').text));
 assert.ok(!html.includes('Redação atual na edição consultada'));
});


test('novas anteriores locais são isoladas e CP 216 não recebe texto do 216-A',async()=>{
 const {records}=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-html.json',import.meta.url),'utf8'));
 assert.ok(records.length>0);
 assert.ok(records.every(r=>r.review.status==='pending'&&r.wording.status==='previous'));
 const data={preview:true,demo:false,records};
 const caputs=previousRecords(data,'penal','216').filter(r=>r.part==='caput');
 assert.equal(caputs.length,2);
 assert.ok(caputs.every(r=>!r.text.includes('superior hierárquico')));
 const html=historyContent(data,'penal','216');
 assert.ok(html.includes('Induzir mulher honesta'));
 assert.ok(html.includes('Induzir alguém'));
 const production=await buildPackage();
 const module=[...production.files].find(([name])=>name.endsWith('/legislative-history-data.js'))[1];
 for(const row of records)assert.ok(!module.includes(row.id));
});
