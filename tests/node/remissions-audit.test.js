import test from 'node:test';import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {hash,identity,literalNumbers,inspectOccurrence,sampleRejected,csv} from '../../scripts/audit-remissions/checks.mjs';
function fixture(text='Conforme art. 186 deste Código.'){
 const code={id:'civil',name:'Código Civil',law:'Lei nº 10.406/2002',articles:[{id:'927',number:'927',scope:'main',paragraphs:[{runs:[{text,deleted:false}]}]},{id:'186',number:'186',scope:'main',paragraphs:[{runs:[{text:'Art. 186. Texto de teste.',deleted:false}]}]}]},sha=hash(JSON.stringify(code));
 const start=text.indexOf('art. 186'),end=start+'art. 186'.length;
 const o={source:{codeId:'civil',articleId:'927',scope:'main',editionSha256:sha},location:{field:'paragraphs',paragraph:0,offsetUnit:'utf16',start,end,text:'art. 186'},normEvidence:{start:end,end:text.length-1,text:text.slice(end,-1)},qualifiers:[],historical:{core:'clear',qualifiers:'clear',context:'clear',state:'clear'}};
 return {corpus:{collections:[{code,sha256:sha}]},o,target:{codeId:'civil',articleId:'186',scope:'main',editionSha256:sha}};
}
test('auditor independente reconhece números e identidades exatas sem parser de produção',()=>{
 assert.deepEqual(literalNumbers('arts. 186 e 1.022-A'),['186','1022-A']);assert.equal(literalNumbers('arts. 186 a 188'),null);
 assert.equal(identity(' da Lei no 10.406, de 10 de janeiro de 2002 (Código Civil)'),identity('Lei nº 10.406/2002'));
 assert.notEqual(identity('Lei nº 3.071/1916'),identity('Lei nº 10.406/2002'));
});
test('auditor exige spans UTF16, SHA e identidade e não usa a classificação A como atestado',()=>{
 const f=fixture('🧭 Conforme art. 186 deste Código.');
 assert.equal(inspectOccurrence(f.corpus,f.o,'self-qualified-article-list',f.target).status,'Consistente na verificação automatizada');
 for(const edit of [c=>c.o.location.start--,c=>c.target.editionSha256='0'.repeat(64),c=>c.target.scope='adct',c=>c.o.normEvidence.text=' desta Lei nº 3.071/1916']){const copy=structuredClone(f);edit(copy);assert.equal(inspectOccurrence(copy.corpus,copy.o,'self-qualified-article-list',copy.target).status,'Erro confirmado');}
});
test('destino com nota de revogação é alerta documental, não inferência de vigência',()=>{
 const f=fixture();f.corpus.collections[0].code.articles[1].paragraphs[0].runs[0].text='Art. 186. (Revogado pela Lei nº 99.999/2000)';
 const sha=hash(JSON.stringify(f.corpus.collections[0].code));f.corpus.collections[0].sha256=sha;f.o.source.editionSha256=sha;f.target.editionSha256=sha;
 assert.equal(inspectOccurrence(f.corpus,f.o,'self-qualified-article-list',f.target).status,'Suspeita');
});
test('norma ausente no literal parentético permanece inconclusiva',()=>{
 const f=fixture('Conforme (art. 186).');f.o.normEvidence=null;
 assert.equal(inspectOccurrence(f.corpus,f.o,'parenthetical-article-list',f.target).status,'Inconclusiva');
});
test('amostra cobre cada estrato e independe da ordem da população',()=>{
 const rows=Array.from({length:12},(_,i)=>({id:String(i),source:{codeId:i%2?'civil':'cf',scope:i%2?'main':'adct'},classification:'C',exclusionReason:'classification-C',diagnosticReason:'ambiguous',facets:{historical:false,ambiguity:true,reproduction:false,unauthorizedSyntax:false}}));
 assert.deepEqual(sampleRejected(rows),sampleRejected([...rows].reverse()));assert.equal(sampleRejected(rows).records.length,4);
});
function parseCSV(value){const rows=[];let row=[],cell='',quoted=false;for(let i=1;i<value.length;i++){const c=value[i];if(c==='"'){if(quoted&&value[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;}else if(c===','&&!quoted){row.push(cell);cell='';}else if(c==='\r'&&value[i+1]==='\n'&&!quoted){row.push(cell);rows.push(row);row=[];cell='';i++;}else cell+=c;}return rows;}
test('CSV preserva aspas, vírgulas, novas linhas e campos de revisão realmente vazios',()=>{
 const s=csv([{id:'🧭',text:'“artigo”, "Lei"\nseguinte',decision:''}],['id','text','decision']);assert.deepEqual(parseCSV(s),[['id','text','decision'],['🧭','“artigo”, "Lei"\nseguinte','']]);
});
test('artefatos integrais têm 329 arestas, 272 ocorrências e planilha com evidência e revisão em branco',async()=>{
 const root=new URL('../../docs/remissoes/fase-1a-2/',import.meta.url),edges=JSON.parse(await readFile(new URL('arestas.json',root))),sample=JSON.parse(await readFile(new URL('rejeicoes-amostra.json',root)));
 assert.equal(edges.edges.length,329);assert.equal(new Set(edges.edges.flatMap(e=>e.occurrenceIds)).size,272);assert.equal(new Set(edges.edges.map(e=>e.edgeId)).size,329);
 for(const r of [...edges.edges,...sample.sampling.records])assert.ok(Object.values(r.review).every(v=>v===''));
 for(const file of ['arestas.csv','revisao-humana.csv']){const rows=parseCSV(await readFile(new URL(file,root),'utf8')),header=rows.shift();assert.equal(rows.length,file==='arestas.csv'?329:329+sample.sampling.records.length);for(const row of rows){assert.equal(row.length,header.length);for(const k of ['decision','justification','evidenceConsulted','needsAdjudication'])assert.equal(row[header.indexOf(k)],'');}}
 assert.equal(sample.sampling.records.length,new Set(sample.sampling.records.map(r=>r.id)).size);assert.ok(sample.sampling.records.every(r=>r.independentEvidence.sourceHash&&r.independentEvidence.coreSpan.ok));
});
