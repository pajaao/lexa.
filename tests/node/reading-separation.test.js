import test from 'node:test';
import assert from 'node:assert/strict';
import {officialImported} from '../../data/official/legislation.js';
import {readingArticle} from '../../src/legislative-history-model.js';

test('leitor separa todos os runs riscados das 13 fontes sem modificar as fontes',()=>{
 assert.equal(Object.keys(officialImported).length,13);
 for(const [code,collection] of Object.entries(officialImported)){
  const snapshot=JSON.stringify(collection);
  for(const article of collection.articles){
   const visible=readingArticle({records:[]},code,article);
   assert.ok(visible.paragraphs.every(p=>p.runs.every(r=>!r.deleted)),`${code}/${article.id}`);
   for(const paragraph of article.paragraphs)if(paragraph.runs.every(r=>!r.deleted))assert.ok(visible.paragraphs.includes(paragraph));
   for(const paragraph of visible.paragraphs)for(const run of paragraph.runs)assert.ok(article.paragraphs.some(p=>p.runs.includes(run)));
  }
  assert.equal(JSON.stringify(collection),snapshot);
 }
});

test('marcadores e notas órfãos somem; texto não riscado permanece literal',()=>{
 const paragraph=runs=>({runs:runs.map(([text,deleted])=>({text,deleted}))});
 const old=paragraph([['a) ',false],['Corpo antigo;',true],[' b) ',false],['Outro antigo;',true]]);
 const note=paragraph([['Art. 1. Antiga.',true],[' (Redação dada pela Lei nº 1)',false]]);
 const mixed=paragraph([['Art. 1. ',false],['trecho antigo ',true],['texto da fonte. (Revogado pela Lei nº 2)',false]]);
 const article={id:'1',paragraphs:[old,note,mixed]};
 const snapshot=JSON.stringify(article);
 const visible=readingArticle({records:[]},'civil',article);
 assert.equal(visible.paragraphs.length,1);
 assert.equal(visible.paragraphs[0].runs.map(r=>r.text).join(''),'Art. 1. texto da fonte. (Revogado pela Lei nº 2)');
 assert.equal(JSON.stringify(article),snapshot);
});

test('CP 215 e CF 7 conservam texto não riscado e excluem todas as redações riscadas',()=>{
 for(const [code,id,word] of [['penal','215','outro ato libidinoso'],['cf','7','São direitos dos trabalhadores']]){
  const article=officialImported[code].articles.find(a=>a.id===id);
  const visible=readingArticle({records:[]},code,article);
  if(article.paragraphs.some(p=>p.runs.some(r=>r.deleted)))assert.ok(visible.paragraphs.length<article.paragraphs.length);
  else assert.equal(visible,article);
  assert.ok(visible.paragraphs.flatMap(p=>p.runs).map(r=>r.text).join(' ').includes(word));
  assert.ok(visible.paragraphs.every(p=>p.runs.every(r=>!r.deleted)));
 }
});
