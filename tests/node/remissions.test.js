import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {loadCorpus} from '../../scripts/remissions/corpus.mjs';
import {extractRemissions,sha256,RULES_SHA256} from '../../scripts/remissions/extract.mjs';
import {relationGraph,compactBundle} from '../../scripts/remissions/graph.mjs';
import {buildPackage} from '../../scripts/build.mjs';
const corpus=await loadCorpus(),extraction=extractRemissions(corpus);
const find=(data,code,article,paragraph)=>data.occurrences.filter(o=>o.source.codeId===code&&o.source.articleId===article&&(paragraph===undefined||o.location.paragraph===paragraph));
const targets=occurrences=>[...new Set(occurrences.filter(o=>o.classification==='A').flatMap(o=>o.resolution.targets.map(t=>t.codeId+':'+t.articleId)))].sort();
const raw=p=>p.runs.map(r=>r.text).join('');
function change(source,transform){
 const copy=structuredClone(corpus),entry=copy.collections.find(c=>c.code.id===source);transform(entry.code);entry.sha256=sha256(JSON.stringify(entry.code));return copy;
}
function paragraphFixture(text,runs){
 return change('civil',code=>{const a=code.articles.find(a=>a.id==='927');a.paragraphs=[{runs:runs||[{text,deleted:false}]}];});
}
const variants=[
 ['CC927','civil','927',0,['civil:186','civil:187']],
 ['CPC240 explicitamente Lei10406','cpc','240',0,['civil:397','civil:398']],
 ['CPC609 §2 de CC1031','cpc','609',0,['civil:1031']],
 ['ADCT54-A deste Ato','cf','adct-54-A',0,['cf:adct-54']],
 ['CDC104-A artigo letrado','cdc','104-A',0,['cdc:54-A']],
 ['CF18 art96 - ADCT','cf','18',5,['cf:adct-96']],
 ['lista intercalada CF28','cf','28',5,['cf:150','cf:153','cf:37','cf:39']],
 ['lista intercalada ADCT72 qualificada Constituição','cf','adct-72',20,['cf:153','cf:157','cf:212','cf:239']],
 ['intervalo com milhar CC28','civil','28',2,['civil:1819','civil:1820','civil:1821','civil:1822','civil:1823']],
 ['artigos por extenso CPC910','cpc','910',3,['cpc:534','cpc:535']],
 ['lista com letras CF49','cf','49',20,['cf:167-B','cf:167-C','cf:167-D','cf:167-E','cf:167-F','cf:167-G']]
];
for(const [name,code,article,pi,expected] of variants)test('remissões reais: '+name,()=>assert.deepEqual(targets(find(extraction,code,article,pi)),expected));

test('CódigoCivil1916 é externo, não o mesmo número no código atual',()=>{
 const refs=find(extraction,'civil','2040',0);
 assert.equal(refs[0].classification,'B');assert.equal(refs[0].norm.identity.year,'1916');
 assert.deepEqual(targets(refs),['civil:1745']);
});
test('ambos deste Ato propaga somente para o par coordenado, não para a remissão CC1275',()=>{
 const refs=find(extraction,'cf','adct-121',1).filter(o=>o.classification==='A');
 assert.deepEqual(refs.map(o=>targets([o])),[['civil:1275'],['cf:adct-107'],['cf:adct-107']]);
});
test('históricas são separadas de resolução e não criam arestas ativas',()=>{
 const old=find(extraction,'cpc','521',3)[0],current=find(extraction,'cpc','521',4)[0];
 assert.equal(old.classification,'D');assert.equal(old.resolution.status,'resolved');assert.equal(old.historical.core,'deleted');assert.equal(current.classification,'A');
 const graph=relationGraph(extraction);const edge=graph.edges.find(e=>e.source.join('/')==='cpc/521'&&e.target.join('/')==='cpc/1042');
 assert.ok(edge);assert.ok(edge.occurrences.every(i=>extraction.occurrences[i].historical.state==='clear'));
});
test('notas de decretos riscadas não contaminam a remissão não riscada de Licitações37',()=>{
 const ref=find(extraction,'licitacoes','37',8)[0];assert.equal(ref.classification,'A');assert.deepEqual(targets([ref]),['licitacoes:6']);
});
test('preserva qualificadores com offsets reais, sem prometer âncora do §2',()=>{
 const ref=find(extraction,'cpc','609',0)[0];assert.ok(ref.qualifiers.some(q=>q.text.includes('§ 2º')));
 assert.ok(ref.resolution.targets.every(t=>t.resolutionLevel==='article'&&!Object.hasOwn(t,'paragraphId')));
});
test('qualificador necessário riscado bloqueia conexão; parágrafo parcialmente riscado não é todo D',()=>{
 const data=extractRemissions(paragraphFixture('',[{text:'Nos termos do art. 186 ',deleted:false},{text:'da Lei nº 10.406/2002',deleted:true},{text:'.',deleted:false}]));
 const ref=find(data,'civil','927',0)[0];assert.notEqual(ref.classification,'A');assert.equal(ref.resolution.status,'resolved');assert.equal(ref.historical.qualifiers,'deleted');
 assert.deepEqual(targets([ref]),[]);
});
test('qualificador de § riscado também impede publicar a referência composta',()=>{
 const data=extractRemissions(paragraphFixture('',[{text:'Ver art. 186, ',deleted:false},{text:'§ 1º',deleted:true},{text:' deste Código.',deleted:false}]));
 const ref=find(data,'civil','927',0)[0];assert.equal(ref.classification,'C');assert.equal(ref.reason,'historical-required-evidence');
});
test('não associa lei distante ao artigo anterior',()=>{
 const data=extractRemissions(paragraphFixture('Aplica-se o art. 186. Uma outra matéria é disciplinada pela Lei nº 13.105/2015.'));
 assert.deepEqual(targets(find(data,'civil','927',0)),['civil:186']);
});
test('norma externa exata não vira o mesmo artigo interno',()=>{
 const data=extractRemissions(paragraphFixture('Nos termos do art. 186 da Lei nº 99.999/2001.'));
 const ref=find(data,'civil','927',0)[0];assert.equal(ref.classification,'B');assert.equal(ref.norm.identity.number,'99999');assert.deepEqual(targets([ref]),[]);
});
test('escopo ADCT não explícito não recebe destino pela coincidência numérica',()=>{
 const copy=change('cf',code=>{code.articles.find(a=>a.id==='adct-54-A').paragraphs=[{runs:[{text:'Conforme art. 54.',deleted:false}]}];});
 const ref=find(extractRemissions(copy),'cf','adct-54-A',0)[0];assert.equal(ref.classification,'C');assert.equal(ref.reason,'adct-scope-not-explicit');
});
test('intervalo alfanumérico é uma expressão não resolvida, nunca expandida aritmeticamente',()=>{
 const data=extractRemissions(paragraphFixture('Aplicam-se os arts. 186 a 187-A deste Código.'));
 const refs=find(data,'civil','927',0);assert.equal(refs.length,1);assert.equal(refs[0].classification,'C');assert.equal(refs[0].reason,'alphanumeric-range-not-supported');
 const historical=find(extraction,'licitacoes','193',6);assert.equal(historical.length,1);assert.equal(historical[0].location.text,'art. 1º a art. 47-A');assert.equal(historical[0].classification,'D');
});
test('referências repetidas mantêm duas ocorrências, uma conexão e uma inversa',()=>{
 const data=extractRemissions(paragraphFixture('Aplicam-se o art. 186 e o art. 186.'));const refs=find(data,'civil','927',0);assert.equal(refs.length,2);
 const graph=relationGraph(data),edges=graph.edges.filter(e=>e.source.join('/')==='civil/927');assert.equal(edges.length,1);assert.equal(edges[0].occurrences.length,2);
 assert.equal(graph.incoming['civil/186'].filter(i=>graph.edges[i].source.join('/')==='civil/927').length,1);
});
test('UTF16, todos os spans e qualificadores correspondem aos runs originais',()=>{
 const modified=paragraphFixture('🧭 Conforme § 2º do art. 186 deste Código.'),data=extractRemissions(modified);
 for(const result of [extraction,data])for(const ref of result.occurrences){
  const source=(result===data?modified:corpus).collections.find(c=>c.code.id===ref.source.codeId).code;
  const article=source.articles.find(a=>a.id===ref.source.articleId),text=raw(article.paragraphs[ref.location.paragraph]);
  for(const span of [ref.location,...ref.qualifiers,...(ref.normEvidence?[ref.normEvidence]:[])])assert.equal(text.slice(span.start,span.end),span.text);
 }
 const ref=find(data,'civil','927',0)[0];assert.equal(ref.location.start,'🧭 Conforme § 2º do '.length);
});
test('IDs agrupados não são certificados como dispositivos individuais',()=>{
 const data=extractRemissions(paragraphFixture('Aplica-se o art. 1.620 deste Código.'));
 const ref=find(data,'civil','927',0)[0];assert.equal(ref.classification,'C');assert.equal(ref.reason,'grouped-target-not-supported');
});
test('datas, dinheiro, ADIs e cabeçalhos próprios não viram remissões',()=>{
 const data=extractRemissions(paragraphFixture('Art. 927. Valor de R$ 186,00, em 18/06/2026. Vide ADI nº 7055.'));
 assert.deepEqual(find(data,'civil','927',0),[]);
});
test('rebuild determinístico depende também do destino e das regras; hashes incorretos falham',()=>{
 assert.deepEqual(extractRemissions(corpus),extraction);
 const copy=change('civil',code=>{code.articles=code.articles.filter(a=>a.id!=='397');}),changed=extractRemissions(copy);
 assert.equal(changed.editions.cpc,extraction.editions.cpc);assert.notEqual(changed.editionSetSha256,extraction.editionSetSha256);assert.deepEqual(targets(find(changed,'cpc','240',0)),[]);
 assert.notEqual(extractRemissions(corpus,{rulesVersion:'test-policy'}).editionSetSha256,extraction.editionSetSha256);
 const bad=structuredClone(corpus);bad.collections.find(c=>c.code.id==='civil').code.articles[0].number='999';assert.throws(()=>extractRemissions(bad),/checksum mismatch/);
 assert.equal(RULES_SHA256.length,64);
});
test('grafo compacto preserva origem, proveniência e inversas derivadas; não entra no pacote publicado',async()=>{
 const graph=relationGraph(extraction),compact=compactBundle(extraction);
 assert.equal(compact.edges.length,graph.edges.length);
 for(const [target,indices] of Object.entries(graph.incoming))for(const i of indices)assert.equal(graph.edges[i].target.join('/'),target);
 const {manifest,files,html}=await buildPackage();assert.ok(!Object.hasOwn(manifest,'references'));
 assert.ok([...files.keys()].every(path=>!path.includes('remissions')&&!path.includes('references.')));assert.ok(!html.includes('remissions/'));
});
test('amostras estão congeladas, com origens disjuntas e expectativas presentes no texto real',async()=>{
 const root=new URL('../fixtures/remissions/',import.meta.url),sampling=JSON.parse(await readFile(new URL('sampling.json',root))),phase0=await readFile(new URL('phase0.json',root)),holdout=await readFile(new URL('holdout.json',root));
 assert.equal(sha256(phase0),sampling.trainingSha256);assert.equal(sha256(holdout),sampling.evaluationSha256);
 const train=new Set(JSON.parse(phase0).map(g=>g.code+'/'+g.article));
 for(const g of JSON.parse(holdout)){
  assert.ok(!train.has(g.code+'/'+g.article));const a=corpus.collections.find(c=>c.code.id===g.code).code.articles.find(a=>a.id===g.article);
  assert.equal(raw(a.paragraphs[g.paragraph]),g.text);assert.deepEqual(a.paragraphs[g.paragraph].runs,g.runs);
  for(const e of g.expected)assert.equal(g.text.slice(...e.span),e.literal);
 }
});
test('nove mudanças de edição removem conexões obsoletas, inclusive escopo e qualificador',async()=>{
 const {simulateEditions}=await import('../../scripts/remissions/simulate.mjs');
 const results=simulateEditions(corpus);assert.equal(results.length,9);assert.ok(results.every(r=>r.passed&&r.editionSetChanged));
 assert.equal(results.find(r=>r.scenario==='target-only-other-norm').sourceEditionChanged,false);
});
test('identidades normativas explícitas contraditórias não produzem destino presumido',()=>{
 const data=extractRemissions(paragraphFixture('Aplica-se o art. 186 da Lei nº 13.105/2015 (Código Civil).'));
 const ref=find(data,'civil','927',0)[0];assert.equal(ref.classification,'C');assert.equal(ref.reason,'conflicting-norm-identities');
});
test('ponto final delimita norma posterior e norma anterior sem ligação sintática provoca abstenção',()=>{
 const first=extractRemissions(paragraphFixture('Aplica-se o art. 186. Constituição Federal será objeto de outra consulta.'));
 assert.deepEqual(targets(find(first,'civil','927',0)),['civil:186']);
 const second=extractRemissions(paragraphFixture('Conforme o Código Penal, o art. 186 trata da questão.'));
 assert.equal(find(second,'civil','927',0)[0].classification,'C');
});
