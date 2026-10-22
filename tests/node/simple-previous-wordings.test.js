import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {buildPackage} from '../../scripts/build.mjs';
import {stagePages} from '../../scripts/build-pages.mjs';

test('prévia HTML simples contém somente a nova fixture pending e produção permanece vazia',async()=>{
 const fixture=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-simple.json',import.meta.url),'utf8'));
 assert.ok(fixture.records.length>0);
 assert.ok(fixture.records.every(r=>r.review.status==='pending'&&r.wording.status==='previous'));
 const experimental=await buildPackage({legislativeHistorySimple:true});
 const normal=await buildPackage();
 const moduleFor=result=>[...result.files].find(([name])=>name.endsWith('/legislative-history-data.js'))[1];
 assert.ok(moduleFor(experimental).includes(fixture.records[0].id));
 const release=JSON.parse(await readFile(new URL('../../data/previous-wordings/release.json',import.meta.url),'utf8'));
 assert.equal(moduleFor(normal).includes(fixture.records[0].id),release.publicationAuthorized);
 assert.ok(!moduleFor(experimental).includes('penal-215-caput-01'));
 assert.match([...experimental.files].find(([name])=>name.endsWith('/pwa.js'))[1],/setupPwa\(\)\{\}/);
});

test('prévia HTML simples não pode substituir dist nem misturar os pilotos anteriores',async()=>{
 await assert.rejects(stagePages(undefined,{legislativeHistorySimple:true}),/não pode substituir/);
 await assert.rejects(buildPackage({legislativeHistorySimple:true,legislativeHistoryPilot:true}),/apenas uma/);
});


test('separação cobre todos os runs riscados das 13 fontes sem alterar os dados originais',async()=>{
 const {officialImported}=await import('../../data/official/legislation.js');
 const {readingArticle}=await import('../../src/legislative-history-model.js');
 for(const [code,collection] of Object.entries(officialImported)){
  const snapshot=JSON.stringify(collection);
  for(const article of collection.articles){
   const visible=readingArticle({records:[]},code,article);
   assert.ok(visible.paragraphs.every(p=>p.runs.every(r=>!r.deleted)),`${code}/${article.id}`);
  }
  assert.equal(JSON.stringify(collection),snapshot);
 }
});

test('CP 215 e CF 7 preservam todos os trechos anteriores identificados e o texto não riscado',async()=>{
 const {officialImported}=await import('../../data/official/legislation.js');
 const {readingArticle}=await import('../../src/legislative-history-model.js');
 const fixture=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-simple.json',import.meta.url),'utf8'));
 for(const [code,id,count] of [['penal','215',6],['cf','7',8]]){
  const article=officialImported[code].articles.find(a=>a.id===id);
  const visible=readingArticle(fixture,code,article);
  const texts=visible.paragraphs.flatMap(p=>p.runs.map(r=>r.text)).join(' ');
  assert.equal(fixture.records.filter(r=>r.codeId===code&&r.articleId===id).length,count);
  for(const paragraph of visible.paragraphs)for(const run of paragraph.runs)assert.ok(article.paragraphs.some(p=>p.runs.includes(run)));
  assert.ok(texts.includes(code==='penal'?'outro ato libidinoso':'São direitos dos trabalhadores'));
 }
});


test('novas associações mantêm o contexto antigo explícito e escapado no painel',async()=>{
 const {historyContent}=await import('../../src/legislative-history.js');
 const fixture=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-simple.json',import.meta.url),'utf8'));
 const old=fixture.records.find(r=>r.codeId==='penal'&&r.articleId==='65'&&r.documentaryContext);
 assert.ok(old);
 const html=historyContent(fixture,'penal','65');
 assert.ok(html.includes('Correspondência com o conteúdo do dispositivo atual não estabelecida.'));
 const injected={...old,documentaryContext:'<img src=x onerror=alert(1)>'};
 assert.ok(!historyContent({...fixture,records:[injected]},'penal','65').includes('<img'));
});
