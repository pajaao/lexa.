import test from 'node:test';
import assert from 'node:assert/strict';
import {parseReference,searchLibraryReferences} from '../data.js';

test('biblioteca resolve referências, artigos agrupados e identidades CF/ADCT/SV',()=>{
 const cases=[['Art. 60 CF','cf','60'],['Art. 186 CC','civil','186'],['artigo 186 do Código Civil','civil','186'],['Art. 1.022 CPC','cpc','1022'],['ADCT art. 1','cf','adct-1'],['CF ADCT 1','cf','adct-1'],['Art. 1 CF','cf','1'],['SV13','sv','13'],['Súmula Vinculante nº 13 STF','sv','13'],['Art. 55 CTN','ctn','52']];
 for(const [query,id,article] of cases){
  const result=searchLibraryReferences(query);
  assert.equal(result.length,1,query);
  assert.equal(result[0].code.id,id,query);
  assert.equal(result[0].article.id,article,query);
 }
});
test('texto comum continua sendo texto e referência inexistente não vira outro artigo',()=>{
 for(const query of ['consumidor','CPC','ação ou omissão','Art. 60 XYZ','CF 60 CC'])assert.equal(parseReference(query),null,query);
 assert.deepEqual(searchLibraryReferences('Art. 99999 CF'),[]);
 const results=searchLibraryReferences('Art. 60');
 assert.ok(results.length>1);
 assert.ok(results.every(result=>result.code.id!=='sv'&&(result.article.number==='60'||Number(result.article.number)<=60&&result.article.rangeEnd>=60)));
});
