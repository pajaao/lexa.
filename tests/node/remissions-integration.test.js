import test from 'node:test';import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {buildPackage,sha256} from '../../scripts/build.mjs';
import {buildRemissions} from '../../scripts/remissions/build-resource.mjs';
import {applyEligibility,POLICY} from '../../scripts/remissions/eligibility.mjs';
import {extractRemissions} from '../../scripts/remissions/extract.mjs';
import {validateRemissions,relationStore} from '../../src/optional/remissions-contract.js';
import {createRemissionsLoader} from '../../src/optional/remissions.js';
const plain=await buildPackage(),corpus={collections:plain.manifest.collections.map(spec=>({code:JSON.parse(plain.files.get(spec.file)),sha256:spec.sha256}))},built=buildRemissions(corpus);
const metadata=plain.manifest.collections,spec={...built.descriptor,sha256:sha256(built.bytes)};
const outgoing=(index,code,id)=>{const s=relationStore(index);return s.outgoing(code,id).map(e=>s.norm(e[2])+'/'+e[3]).sort();};
function mutate(code,callback){const c=structuredClone(corpus);const entry=c.collections.find(v=>v.code.id===code);callback(entry.code);entry.sha256=sha256(JSON.stringify(entry.code));return c;}
function source(text,runs){return mutate('civil',c=>{c.articles.find(a=>a.id==='927').paragraphs=[{runs:runs||[{text,deleted:false}]}];});}
test('build padrão não importa índice, não inclui módulos opcionais e não inclui diagnóstico',()=>{
 assert.ok(!plain.manifest.remissions);assert.ok(!plain.remissionsAudit);assert.ok([...plain.files.keys()].every(k=>!k.includes('/optional/')&&!k.includes('data/remissions.')));
});
test('build experimental tem JSON imutável verificado, loader sem preload e textos jurídicos idênticos',async()=>{
 const p=await buildPackage({remissions:true}),d=p.manifest.remissions;assert.equal(sha256(p.files.get(d.file)),d.sha256);assert.ok(d.file.includes(d.sha256));
 assert.ok(!p.html.includes('modulepreload" href="./'+[...p.files.keys()].find(k=>k.endsWith('/optional/remissions.js'))));
 for(const c of plain.manifest.collections)assert.equal(p.files.get(c.file),plain.files.get(c.file));
 await validateRemissions(JSON.parse(p.files.get(d.file)),d,p.manifest.collections);
 assert.equal(p.manifest.offlineBytes,plain.manifest.offlineBytes+d.bytes);
});
test('classes autorizadas incluem os exemplos precisos; remissão editorial CF18 permanece excluída',()=>{
 const cases=[['civil','927',['civil/186','civil/187']],['cpc','240',['civil/397','civil/398']],['cpc','609',['civil/1031']],['cf','adct-54-A',['cf/adct-54']],['cdc','104-A',['cdc/54-A']]];
 for(const [code,id,expected] of cases)assert.deepEqual(outgoing(built.index,code,id),expected);
 assert.deepEqual(outgoing(built.index,'cf','18'),[]);
 assert.ok(built.audit.decisions.some(d=>!d.eligible&&d.reason==='editorial-or-implicit-not-authorized'));
});
test('índice determinístico, sem textos jurídicos/diagnósticos e sem mutação da edição',()=>{
 const before=JSON.stringify(corpus),again=buildRemissions(corpus);assert.equal(again.bytes,built.bytes);assert.equal(JSON.stringify(corpus),before);
 assert.ok(!built.bytes.includes('Aquele que'));assert.ok(!built.bytes.includes('classification-C'));assert.ok(built.audit.eligibleOccurrences<built.audit.candidates);
 assert.equal(POLICY.mode,'experimental-only');assert.equal(POLICY.independentReview,'pending');
});
test('mesma aresta preserva múltiplas ocorrências e inversa é derivada da tabela canônica',()=>{
 const b=buildRemissions(source('Nos casos (art. 186), inclusive (art. 186).'));const ci=b.index.editions.findIndex(([id])=>id==='civil');
 const edges=b.index.edges.filter(e=>e[0]===ci&&e[1]==='927');assert.equal(edges.length,1);assert.equal(edges[0][4].length,2);
 const inverse=relationStore(b.index).incoming('civil','186');assert.equal(inverse.filter(e=>e[0]===ci&&e[1]==='927').length,1);
});
test('A forjado não supera evidência, tachado ou o número literal da classe autorizada',()=>{
 const extraction=extractRemissions(corpus);const o=extraction.occurrences.find(o=>o.source.codeId==='civil'&&o.source.articleId==='927');
 for(const transform of [v=>v.location.field='notes',v=>v.location.offsetUnit='codepoints',v=>v.location.start++,v=>v.historical.qualifiers='deleted',v=>v.resolution.targets[0].articleId='188']){
  const copy=structuredClone(o);transform(copy);const gate=applyEligibility(corpus,{occurrences:[copy]});assert.equal(gate.accepted.length,0);
 }
 const del=buildRemissions(source('',[{text:'Referência (arts. 186 e 187)',deleted:true}]));assert.deepEqual(outgoing(del.index,'civil','927'),[]);
 const qualifier=buildRemissions(source('',[{text:'Aplica-se o art. 186 ',deleted:false},{text:'da Lei nº 10.406/2002',deleted:true}]));assert.deepEqual(outgoing(qualifier.index,'civil','927'),[]);
});
test('externas, ambíguas, intervalos agrupados, listas complexas e reproduções não geram arestas',()=>{
 const cases=['Conforme art. 186 da Lei nº 99.999/2000.','Conforme art. 186 da mesma lei.','Conforme art. 1.620 deste Código.','Conforme arts. 186 a 187 deste Código.','Passa a vigorar a seguinte redação: Art. 186. ...'];
 for(const text of cases)assert.deepEqual(outgoing(buildRemissions(source(text)).index,'civil','927'),[],text);
 assert.deepEqual(outgoing(built.index,'eca','263'),[]);
});
test('mudanças jurídicas, só no destino, nas regras e na política invalidam o índice',()=>{
 for(const edit of [c=>{c.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text=c.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text.replace('186 e 187','186 e 188');},c=>{c.articles=c.articles.filter(a=>a.id!=='397');},c=>{c.articles.find(a=>a.id==='187').id='187-X';}]){
  const next=buildRemissions(mutate('civil',edit));assert.notEqual(next.bytes,built.bytes);assert.notEqual(next.index.legalEditionSetSha256,built.index.legalEditionSetSha256);
 }
 const changed=buildRemissions(corpus,{policy:{...POLICY,version:'test',classes:[]}});assert.notEqual(changed.index.generationSha256,built.index.generationSha256);assert.equal(changed.index.edges.length,0);
 assert.throws(()=>buildRemissions(corpus,{policy:{...POLICY,mode:'production'}}),/approval/);
});
test('contrato falha fechado: edição, regras, política, hash lógico, proveniência e inversa inconsistentes',async()=>{
 const good=JSON.parse(built.bytes);await validateRemissions(good,spec,metadata);
 for(const edit of [i=>i.editions[0][1]='0'.repeat(64),i=>i.extractor.sha256='0'.repeat(64),i=>i.policy.version='wrong',i=>i.generationSha256='0'.repeat(64),i=>i.occurrences[0][4]=-1,i=>i.incoming={},i=>i.edges.push(i.edges[0])]){
  const c=JSON.parse(built.bytes);edit(c);await assert.rejects(()=>validateRemissions(c,spec,metadata));
 }
});
test('loader só carrega quando chamado, deduplica e não baixa normas; ausente retorna null',async()=>{
 let calls=0;const loader=createRemissionsLoader({catalog:{...plain.manifest,remissions:spec},fetchJSON:async requested=>{calls++;assert.equal(requested,spec);return JSON.parse(built.bytes);}});
 assert.equal(calls,0);const [a,b]=await Promise.all([loader(),loader()]);assert.equal(calls,1);assert.equal(a,b);assert.deepEqual(outgoing(built.index,'civil','927'),a.outgoing('civil','927').map(e=>a.norm(e[2])+'/'+e[3]).sort());assert.equal(a.hasConnections('civil','999999'),false);
 assert.equal(await createRemissionsLoader({catalog:plain.manifest,fetchJSON:()=>{throw Error('must not fetch');}})(),null);
});
test('falha de rede/contrato não deixa grafo parcial e permite tentativa posterior',async()=>{
 let attempt=0;const loader=createRemissionsLoader({catalog:{...plain.manifest,remissions:spec},fetchJSON:async()=>{if(++attempt===1)throw Error('offline');if(attempt===2)return {};return JSON.parse(built.bytes);}});
 await assert.rejects(loader,/offline/);await assert.rejects(loader);assert.ok((await loader()).hasConnections('civil','927'));assert.equal(attempt,3);
});
test('fontes adicionais não repetem artigos das amostras anteriores e conferem com runs reais',async()=>{
 const root=new URL('../fixtures/',import.meta.url),old=(await Promise.all(['phase0','holdout'].map(async n=>JSON.parse(await readFile(new URL('remissions/'+n+'.json',root)))))).flat(),used=new Set(old.map(g=>g.code+'/'+g.article));
 const rows=JSON.parse(await readFile(new URL('remissions-1a/additional.json',root)));for(const g of rows){assert.ok(!used.has(g.code+'/'+g.article));const a=corpus.collections.find(c=>c.code.id===g.code).code.articles.find(a=>a.id===g.article);assert.deepEqual(a.paragraphs[g.paragraph].runs,g.runs);for(const e of g.expected)assert.equal(g.text.slice(...e.span),e.literal);}
});
test('versão/hash de regras e hash da política participam da identidade mesmo com arestas iguais',()=>{
 const version=buildRemissions(corpus,{extract:c=>extractRemissions(c,{rulesVersion:'future-test'})});assert.notEqual(version.index.generationSha256,built.index.generationSha256);
 const hash=buildRemissions(corpus,{extract:c=>{const e=extractRemissions(c);e.rules.sha256='f'.repeat(64);return e;}});assert.notEqual(hash.index.generationSha256,built.index.generationSha256);
 const policy=buildRemissions(corpus,{policy:{...POLICY,sha256:'e'.repeat(64)}});assert.notEqual(policy.index.generationSha256,built.index.generationSha256);
});
test('reconstrução após oito alterações remove arestas obsoletas e respeita classes ainda desabilitadas',()=>{
 const cases=[
  ['incluir',source('Nos casos (arts. 186, 187 e 188).'),['civil/186','civil/187','civil/188']],
  ['excluir',source('Sem remissão numerada.'),[]],
  ['trocar',source('Nos casos (arts. 186 e 188).'),['civil/186','civil/188']],
  ['remover',mutate('civil',c=>{c.articles=c.articles.filter(a=>a.id!=='187');}),[]],
  ['identificador',mutate('civil',c=>{c.articles.find(a=>a.id==='187').id='187-X';}),[]],
  ['norma',source('Conforme art. 186 da Lei nº 13.105/2015.'),['cpc/186']],
  ['riscado',source('',[{text:'Nos casos (arts. 186 e 187).',deleted:true}]),[]],
 ];
 for(const [name,c,expected] of cases){const next=buildRemissions(c);assert.deepEqual(outgoing(next.index,'civil','927'),expected,name);assert.notEqual(next.index.generationSha256,built.index.generationSha256);}
 const scope=buildRemissions(mutate('cf',c=>{const a=c.articles.find(a=>a.id==='adct-54-A');a.paragraphs[0].runs[0].text=a.paragraphs[0].runs[0].text.replace('deste Ato das Disposições Constitucionais Transitórias','desta Constituição Federal');}));
 assert.deepEqual(outgoing(scope.index,'cf','adct-54-A'),[]); // explicit Constitution class is deliberately not enabled
 const destOnly=buildRemissions(mutate('civil',c=>{c.articles.find(a=>a.id==='397').paragraphs[0].runs[0].text+=' (fixture edit)';}));
 assert.notEqual(destOnly.index.generationSha256,built.index.generationSha256);assert.deepEqual(outgoing(destOnly.index,'cpc','240'),['civil/397','civil/398']);
});
test('CPP13-A abstém-se de escopo compartilhado não suportado e não publica CPP158',()=>{
 const audit=built.audit,raw=audit.occurrences.find(o=>o.source.codeId==='cpp'&&o.source.articleId==='13-A'&&o.location.text==='art. 158');
 assert.ok(raw&&raw.classification==='C');assert.equal(raw.resolution.reason,'coordinated-norm-scope-not-supported');assert.deepEqual(raw.resolution.targets,[]);
 assert.ok(audit.decisions.some(d=>d.occurrenceId===raw.id&&!d.eligible));
 assert.ok(!outgoing(built.index,'cpp','13-A').includes('cpp/158'));assert.ok(outgoing(built.index,'cpp','13-A').includes('penal/159'));
});
test('classe parentética não presume norma local se outra norma foi mencionada antes ou qualifica após o parêntese',()=>{
 for(const text of ['Conforme o Código Penal, consulte (art. 186).','Conforme (art. 186), da Lei nº 13.105/2015.'])assert.deepEqual(outgoing(buildRemissions(source(text)).index,'civil','927'),[]);
});
