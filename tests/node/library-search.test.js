import test from 'node:test';
import assert from 'node:assert/strict';
import {collections,normalize,searchLibraryReferences} from '../../src/data.js';
import {searchLibraryText,libraryExcerpt} from '../../src/library-search.js';

test('busca textual cobre as coleções e os escopos, sem duplicar entradas',()=>{
 for(const query of ['dignidade','educação','tributo','liberdade']){
  const groups=searchLibraryText(query);
  for(const code of collections){
   const expected=code.articles.filter(a=>[...a.paragraphs,...(a.notes||[]),...(a.title?[{runs:[{text:a.title}]}]:[])].some(p=>normalize(p.runs.map(r=>r.text).join('')).includes(normalize(query))));
   assert.deepEqual(groups.find(g=>g.code.id===code.id)?.matches.map(m=>m.article.id)||[],expected.map(a=>a.id));
  }
 }
 const all=searchLibraryText('constitui');
 const cf=all.find(group=>group.code.id==='cf');
 assert.ok(cf.matches.some(m=>m.article.scope==='adct'));assert.ok(cf.matches.some(m=>m.article.scope==='main'));
});

test('acentos, áreas e referências diretas mantêm seus significados',()=>{
 assert.deepEqual(searchLibraryText('EDUCACAO').map(g=>g.matches.map(m=>m.article.id)),searchLibraryText('educação').map(g=>g.matches.map(m=>m.article.id)));
 assert.ok(searchLibraryText('dignidade').length>1);
 assert.ok(searchLibraryText('dignidade','Penal').every(group=>group.code.id==='penal'));
 for(const query of ['','a','Art. 60 CF','SV 13','ADCT art. 1','Art. 99999 CF'])assert.deepEqual(searchLibraryText(query),[]);
 assert.equal(searchLibraryReferences('Art. 60 CF')[0].article.id,'60');
 assert.deepEqual(searchLibraryText('umaexpressaoquenuncaexistenabasedolexa'),[]);
});

test('trecho mostra a ocorrência original, com acento e riscados preservados',()=>{
 const text='Antes '.repeat(70)+'Educação e liberdade '+'depois '.repeat(60);
 const match={text,runs:[{text,deleted:true}],query:'educacao',index:normalize(text).indexOf('educacao')};
 const excerpt=libraryExcerpt(match);
 assert.ok(excerpt.leading&&excerpt.trailing);assert.ok(excerpt.runs.every(r=>r.deleted));
 assert.match(excerpt.runs.map(r=>r.text).join(''),/Educação/);
 assert.ok(excerpt.runs.map(r=>r.text).join('').length<=220);
});

test('notas de aplicação das súmulas são identificadas separadamente do enunciado',()=>{
 const sv=collections.find(code=>code.id==='sv');
 const candidate=sv.articles.find(a=>a.notes?.some(p=>p.runs.map(r=>r.text).join('').length>100));
 const phrase=candidate.notes.map(p=>p.runs.map(r=>r.text).join('')).find(text=>text.length>100).slice(0,90);
 const match=searchLibraryText(phrase).find(g=>g.code.id==='sv')?.matches.find(m=>m.article.id===candidate.id);
 assert.ok(match);assert.equal(match.match.kind,'notes');
});
