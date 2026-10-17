import test from 'node:test';
import assert from 'node:assert/strict';
import {collections,normalize} from '../../src/data.js';
import {createSearchIndex,fieldRuns,searchArticle} from '../../src/search-index.js';
import {searchLibraryText} from '../../src/library-search.js';
test('índices compactos preservam cada campo, ordem, notas e riscos de todas as coleções',()=>{
 for(const code of collections){
  const index=createSearchIndex(code);
  assert.equal(index.articles.length,code.articles.length);
  for(const [i,entry] of index.articles.entries()){
   const original=code.articles[i];
   assert.equal(entry.id,original.id);assert.equal(entry.scope,original.scope);assert.equal(entry.status,original.status);
   const expected=[...original.paragraphs.map(p=>p.runs),...(original.title?[[{text:original.title}]]:[]),...(original.notes||[]).map(p=>p.runs)];
   for(const [n,field] of entry.fields.entries()){
    const actual=fieldRuns(field),runs=expected[n];
    assert.equal(actual.map(r=>r.text).join(''),runs.map(r=>r.text).join(''));
    const mask=list=>list.flatMap(r=>Array(r.text.length).fill(Boolean(r.deleted)));
    assert.deepEqual(mask(actual),mask(runs));
   }
   assert.equal(searchArticle(entry,index).paragraphs.length,original.paragraphs.length);
  }
 }
});
test('busca no índice compacto tem os mesmos IDs e primeiro campo que a pesquisa completa',()=>{
 for(const query of ['dignidade','educação','tributo','liberdade','art.','§ 1','responsabilidade','é vedado']){
  const actual=searchLibraryText(query);
  for(const code of collections){
   const expected=code.articles.filter(a=>[...a.paragraphs,...(a.title?[{runs:[{text:a.title}]}]:[]),...(a.notes||[])].some(p=>normalize(p.runs.map(r=>r.text).join('')).includes(normalize(query))));
   assert.deepEqual(actual.find(g=>g.code.id===code.id)?.matches.map(m=>m.article.id)||[],expected.map(a=>a.id));
  }
 }
});
