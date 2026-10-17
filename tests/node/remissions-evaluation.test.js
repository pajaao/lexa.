import test from 'node:test';import assert from 'node:assert/strict';
import {evaluateSample} from '../../scripts/remissions/evaluate.mjs';
const sample=[{code:'civil',article:'927',paragraph:0,text:'arts. 186 e 187',expected:[{literal:'arts. 186 e 187',status:'A',targets:['civil:186','civil:187']}]}];
function occurrence(classification,ids,start=0){return {source:{codeId:'civil',articleId:'927'},location:{paragraph:0,start,end:start+14,text:sample[0].text},classification,resolution:{targets:ids.map(articleId=>({codeId:'civil',articleId}))}};}
test('avaliação conta destino errado, omissão e candidato não correspondente sem favorecer o extrator',()=>{
 const result=evaluateSample(sample,[occurrence('A',['186','188'])]);assert.equal(result.correctDestinations,1);assert.equal(result.incorrectDestinations,1);assert.equal(result.connectionPrecision,.5);assert.equal(result.destinationRecall,.5);assert.equal(result.correctClassifications,0);
 const omitted=evaluateSample(sample,[occurrence('C',[])]);assert.equal(omitted.safetyOmissions,2);assert.equal(omitted.connectionPrecision,null);assert.equal(omitted.destinationRecall,0);
 const wrongSpan=evaluateSample(sample,[occurrence('A',['186'],100)]);assert.equal(wrongSpan.missedExpressions,1);assert.equal(wrongSpan.spuriousExpressions,1);assert.equal(wrongSpan.incorrectDestinations,1);
});
test('ocorrências repetidas e conexões únicas têm denominadores distintos',()=>{
 const repeated=[sample[0],{...sample[0],paragraph:1}],refs=[occurrence('A',['186','187']),{...occurrence('A',['186','187']),location:{...occurrence('A',[]).location,paragraph:1}}];
 const result=evaluateSample(repeated,refs);assert.equal(result.correctDestinations,4);assert.equal(result.correctUniqueConnections,2);
});
test('seleção de fontes da avaliação é reproduzível sem usar o extrator nem suas saídas',async()=>{
 const {readFile}=await import('node:fs/promises');
 const {loadCorpus}=await import('../../scripts/remissions/corpus.mjs');
 const {selectEvaluationSources}=await import('../../scripts/remissions/select-sample.mjs');
 const root=new URL('../fixtures/remissions/',import.meta.url);
 const development=JSON.parse(await readFile(new URL('phase0.json',root))),holdout=JSON.parse(await readFile(new URL('holdout.json',root)));
 assert.deepEqual(selectEvaluationSources(await loadCorpus(),development),holdout.map(g=>[g.code,g.article,g.paragraph]));
});
