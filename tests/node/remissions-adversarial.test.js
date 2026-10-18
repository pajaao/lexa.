import test from 'node:test';
import assert from 'node:assert/strict';
import {cases,corpusFromBuild,caseCorpus,runCase} from '../../scripts/remissions/adversarial.mjs';
import {extractRemissions} from '../../scripts/remissions/extract.mjs';
import {applyEligibility,POLICY} from '../../scripts/remissions/eligibility.mjs';
import {buildRemissions} from '../../scripts/remissions/build-resource.mjs';
const corpus=await corpusFromBuild();
for(const c of cases)test('adversarial '+c.id+': '+c.justification,()=>{
 const before=JSON.stringify(corpus),row=runCase(corpus,c);
 assert.deepEqual(row.eligibleTargets,c.expected);
 assert.equal(JSON.stringify(corpus),before);
 for(const o of row.occurrences){
  const text=row.paragraphs[o.location.paragraph].runs.map(r=>r.text).join('');
  for(const span of [o.location,...o.qualifiers,...(o.normEvidence?[o.normEvidence]:[])])assert.equal(text.slice(span.start,span.end),span.text);
 }
 if(c.expected.length)assert.deepEqual(row.rawTargets,c.expected);
 if(c.expectedRaw)assert.deepEqual(row.rawTargets,c.expectedRaw);
 if(['A01','A02','B01','B02','C01','CPP13A'].includes(c.id))assert.deepEqual(row.rawTargets,[]);
 if(c.id==='A01')assert.equal(row.occurrences[0].norm.identity.year,'1993');
 if(c.id==='B01')assert.equal(row.occurrences[0].norm.identity.year,'1967');
 if(c.id==='B02')assert.equal(row.occurrences[0].historical.context,'mixed');
 if(c.id==='B04')assert.equal(row.occurrences[0].classification,'D');
});
test('reprodução tardia: bloqueia núcleo explícito e referências nos parágrafos posteriores sem presumir fim da transcrição',()=>{
 const base=cases.find(c=>c.id==='C01');
 for(const paragraphs of [
  [...base.paragraphs,'Consultar o art. 148 desta Lei.'],
  ['Texto sem referência.','Outro parágrafo.','Passa a vigorar a seguinte redação:','Consultar o art. 147 desta Lei.'],
  ['No trecho reproduzido de um diploma não identificado: (art. 147).']
 ])assert.deepEqual(runCase(corpus,{...base,paragraphs}).eligibleTargets,[]);
 // Do not relax the existing article-wide publication exclusion.
 assert.deepEqual(runCase(corpus,{...base,paragraphs:['Consultar o art. 147 desta Lei.','Passa a vigorar a seguinte redação: sem referência.']}).eligibleTargets,[]);
});
test('histórico necessário misto bloqueia mesmo sem a palavra editorial Ver',()=>{
 const c=cases.find(c=>c.id==='B02');
 for(const verb of ['consultar','aplicar','considerar']){
  const paragraphs=structuredClone(c.paragraphs);paragraphs[0][1].text=verb+' art. 147 desta Lei.';
  const row=runCase(corpus,{...c,paragraphs});assert.deepEqual(row.rawTargets,[]);assert.deepEqual(row.eligibleTargets,[]);
 }
});
test('gate revalida identidade normativa mesmo se classificação e spans da saída antiga forem forjados',()=>{
 const c=caseCorpus(corpus,cases.find(c=>c.id==='A01')),e=extractRemissions(c,{selected:['licitacoes']});
 const o=e.occurrences.find(o=>o.source.articleId==='100'),entry=c.collections.find(v=>v.code.id==='licitacoes');
 o.classification='A';o.resolution={status:'resolved',reason:'explicit-self',targets:[{codeId:'licitacoes',articleId:'147',scope:'main',editionSha256:entry.sha256}]};
 o.norm={status:'resolved',codeId:'licitacoes',scope:'main',identity:null};o.normEvidence.end=o.normEvidence.start+' desta Lei'.length;o.normEvidence.text=' desta Lei';
 assert.equal(applyEligibility(c,{occurrences:[o]}).accepted.length,0);
});
test('classes e publicação continuam restritas; guardas novas participam da geração determinística',()=>{
 assert.equal(POLICY.mode,'experimental-only');assert.deepEqual([...POLICY.classes],['parenthetical-article-list','self-qualified-article-list','adct-self-article','numbered-law-article-list']);
 const c=caseCorpus(corpus,cases.find(c=>c.id==='C03')),first=buildRemissions(c),again=buildRemissions(c);
 assert.equal(first.bytes,again.bytes);
 const next=buildRemissions(c,{policy:{...POLICY,version:POLICY.version+'-test'}});assert.notEqual(first.index.generationSha256,next.index.generationSha256);
});
