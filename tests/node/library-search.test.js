import test from 'node:test';
import {compactField} from '../../src/search-index.js';
import assert from 'node:assert/strict';
import {collections,normalize,searchLibraryReferences} from '../../src/data.js';
import {searchLibraryText,libraryExcerpt,selectLibraryMatch} from '../../src/library-search.js';

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
 assert.deepEqual(searchLibraryText('dignidade','Penal').map(group=>group.code.id),['penal','cpp','lep','maria-penha']);
 for(const query of ['','a','Art. 60 CF','SV 13','ADCT art. 1','Art. 99999 CF'])assert.deepEqual(searchLibraryText(query),[]);
 assert.equal(searchLibraryReferences('Art. 60 CF')[0].article.id,'60');
 assert.deepEqual(searchLibraryText('umaexpressaoquenuncaexistenabasedolexa'),[]);
});

test('nome abreviado da legislação após o artigo resolve referência única',()=>{
 for(const [query,codeId,id] of [
  ['art 60 penal','penal','60'],['Art. 60 do Penal','penal','60'],
  ['penal art 60','penal','60'],['ART 359-M-A PENAL','penal','359-M-A'],
  ['art 54 constituição','cf','54'],['art 54 constituicao','cf','54'],
  ['art 54 da Constituição','cf','54']
 ]){
  assert.deepEqual(searchLibraryReferences(query).map(r=>[r.code.id,r.article.id]),[[codeId,id]]);
  assert.deepEqual(searchLibraryText(query),[]);
 }
 assert.deepEqual(searchLibraryReferences('art 99999 penal'),[]);
 assert.equal(searchLibraryReferences('art 60 penal militar'),null);
 assert.equal(searchLibraryReferences('art 60 penal cf'),null);
 assert.equal(searchLibraryReferences('direito penal'),null);
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

test('art. 227 da CF usa a ocorrência não riscada sem mudar a ordem dos resultados',()=>{
 const groups=searchLibraryText('dignidade');
 const cf=groups.find(group=>group.code.id==='cf');
 assert.deepEqual(cf.matches.map(hit=>hit.article.id),['1','226','227','230']);
 const {match}=cf.matches.find(hit=>hit.article.id==='227');
 assert.equal(match.deleted,false);
 assert.ok(match.runs.some(run=>!run.deleted&&run.text.includes('ao jovem')));
 assert.ok(libraryExcerpt(match).runs.every(run=>!run.deleted));
});


test('resumo prefere ocorrência não riscada no mesmo campo, com offsets e acentos preservados',()=>{
 const field=compactField('text',[{text:'Educação antiga; ',deleted:true},{text:'a educação permanece.',deleted:false}]);
 const original=JSON.stringify(field),match=selectLibraryMatch([field],'EDUCAÇÃO');
 assert.equal(match.deleted,false);assert.equal(match.index,normalize(field[1]).lastIndexOf('educacao'));
 assert.equal(JSON.stringify(field),original);
 assert.equal(match.runs.map(run=>run.text).join(''),field[1]);
});

test('resumo conserva ocorrências exclusivamente riscadas e não junta partes separadas',()=>{
 const historical=compactField('text',[{text:'Texto '},{text:'histórico exclusivo',deleted:true},{text:' preservado.'}]);
 const match=selectLibraryMatch([historical,compactField('text',[{text:'Outra redação.'}])],'histórico exclusivo');
 assert.ok(match);assert.equal(match.deleted,true);assert.equal(match.kind,'text');
 assert.ok(libraryExcerpt(match).runs.some(run=>run.deleted&&run.text.includes('histórico exclusivo')));
 const crossing=compactField('text',[{text:'direito '},{text:'anterior',deleted:true}]);
 assert.equal(selectLibraryMatch([crossing],'direito anterior').deleted,true);
 assert.equal(selectLibraryMatch([crossing],'direito').deleted,false);
 assert.equal(selectLibraryMatch([crossing],'anterior').deleted,true);
 assert.equal(selectLibraryMatch([crossing],'inexistente'),null);
 assert.equal(selectLibraryMatch([crossing],''),null);
});

test('ocorrência não riscada pode estar em outro campo; fallback histórico mantém o primeiro',()=>{
 const old=compactField('text',[{text:'termo antigo',deleted:true}]);
 const live=compactField('text',[{text:'termo não riscado'}]);
 assert.equal(selectLibraryMatch([old,live],'termo').text,'termo não riscado');
 const other=compactField('notes',[{text:'termo também anterior',deleted:true}]);
 assert.equal(selectLibraryMatch([old,other],'termo').text,'termo antigo');
});


test('art. 6 da CF continua encontrável por expressão exclusivamente riscada',()=>{
 const {match}=searchLibraryText('a saúde, o trabalho, o lazer').find(group=>group.code.id==='cf').matches.find(hit=>hit.article.id==='6');
 assert.equal(match.deleted,true);
 assert.ok(libraryExcerpt(match).runs.some(run=>run.deleted&&run.text.includes('a saúde, o trabalho, o lazer')));
});
