import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdtemp,cp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {buildPackage,sha256} from '../../scripts/build.mjs';
import {stagePages} from '../../scripts/build-pages.mjs';
import {amendmentCollection} from '../../src/amendments.js';
const folder=new URL('../../data/amendments/candidate/',import.meta.url);
const json=async path=>JSON.parse(await readFile(path,'utf8'));

test('141 originais e textos candidatos preservam hashes, ordem, unidades e pending',async()=>{
 const catalog=await json(new URL('catalog.json',folder));
 assert.equal(catalog.entries.length,141);assert.equal(new Set(catalog.entries.map(x=>x.number)).size,141);
 for(const entry of catalog.entries){
  const bytes=await readFile(new URL(entry.document,folder)),doc=JSON.parse(bytes);
  assert.equal(sha256(bytes),entry.sha256);assert.equal(sha256(await readFile(new URL(entry.original,folder))),entry.originalSha256);
  assert.equal(doc.source.sha256,entry.originalSha256);assert.equal(doc.review.status,'pending');assert.equal(doc.review.publicationAuthorized,false);
  for(const block of doc.blocks)assert.equal(block.runs.map(x=>x.text).join(''),block.text);
  const code=amendmentCollection(doc,{...entry,document:{sha256:entry.sha256}});
  assert.deepEqual(code.articles.flatMap(x=>x.paragraphs.map(p=>p.runs.map(r=>r.text).join(''))),doc.blocks.map(x=>x.text),'Nenhum bloco pode desaparecer na adaptação ao leitor: EC '+entry.number);
  assert.equal(code.articles.length,doc.ownArticles.length);
 }
});

test('build comum não incorpora ECs; candidata lazy gera vínculos verificáveis no build',async()=>{
 const normal=await buildPackage();assert.equal(normal.manifest.amendments,undefined);assert.ok(![...normal.files.keys()].some(x=>/^data\/ec-/.test(x)));
 const candidate=await buildPackage({amendmentsCandidate:true});const ec=candidate.manifest.amendments;
 assert.equal(ec.count,141);assert.equal(ec.publicationAuthorized,false);assert.equal(ec.auditSummary.amendments,141);
 const index=JSON.parse(candidate.files.get(ec.index.file));const links=JSON.parse(candidate.files.get(ec.links.file));
 assert.equal(index.entries.length,141);
 assert.deepEqual([58,103,115].map(n=>links.records.filter(x=>x.ec===n).length),[31,79,3]);
 assert.equal(links.records.filter(x=>x.ec===115).map(x=>x.articleId).sort().join(','),'21,22,5');
 assert.ok(links.records.every(x=>x.note&&!/^\(Vide/i.test(x.note)&&typeof x.previous==='boolean'));
 assert.ok(links.records.some(x=>x.previous));
 const builtIndex=JSON.parse(candidate.files.get(ec.index.file));
 for(const entry of builtIndex.entries){
  assert.equal(entry.original.sha256,entry.originalSha256);assert.match(entry.original.url,/^https:\/\/www2\.camara\.leg\.br\//);
 }
 await assert.rejects(stagePages('dist',{amendmentsCandidate:true}),/Demonstração/);
});

test('mutação de um original impede o build candidato em vez de publicar silenciosamente',async()=>{
 const temp=await mkdtemp(join(tmpdir(),'lexa-ec-integrity-'));
 try{
  await cp(folder,temp,{recursive:true});const catalog=await json(join(temp,'catalog.json'));
  await writeFile(join(temp,catalog.entries[0].original),'alterado');
  await assert.rejects(buildPackage({amendmentsCandidate:true,amendmentsDirectory:temp}),/Original de EC alterado/);
 }finally{await rm(temp,{recursive:true,force:true});}
});
