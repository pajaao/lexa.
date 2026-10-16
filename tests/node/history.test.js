import test from 'node:test';
import assert from 'node:assert/strict';
import {compareVersions,filterUpdates} from '../../src/history.js';
const version=(text,deleted=false)=>({title:null,paragraphs:[{runs:[{text,deleted}]}]});
const text=tokens=>tokens.map(t=>t.text).join('');

test('comparação destaca palavras alteradas e preserva os dois textos completos',()=>{
 const result=compareVersions(version('O prazo é de dez dias.'),version('O prazo é de quinze dias.'));
 assert.equal(text(result.before),'O prazo é de dez dias.');
 assert.equal(text(result.after),'O prazo é de quinze dias.');
 assert.equal(result.before.filter(t=>t.changed).map(t=>t.text).join(''),'dez');
 assert.equal(result.after.filter(t=>t.changed).map(t=>t.text).join(''),'quinze');
 assert.ok(result.after.filter(t=>!t.changed).some(t=>t.text==='prazo'));
});
test('adição, ausência e alterações nos riscados permanecem distinguíveis',()=>{
 const added=compareVersions(null,version('Texto adicionado.'));
 assert.equal(added.before.length,0);assert.ok(added.after.every(t=>t.changed));
 const removed=compareVersions(version('Texto anterior.'),null);
 assert.equal(removed.after.length,0);assert.ok(removed.before.every(t=>t.changed));
 const deleted=compareVersions(version('Texto.'),version('Texto.',true));
 assert.ok(deleted.after[0].deleted&&deleted.after[0].changed);
});
test('comparação limitada para artigos extensos retém tudo e as bordas comuns',()=>{
 const result=compareVersions(version('começo antigo final'),version('começo novo final'),0);
 assert.equal(text(result.before),'começo antigo final');
 assert.equal(text(result.after),'começo novo final');
 assert.equal(result.before[0].changed,false);assert.equal(result.after.at(-1).changed,false);
 assert.ok(result.after.some(t=>t.text==='novo'&&t.changed));
});
test('filtros de código e artigo preservam o contexto de Constituição e ADCT',()=>{
 const events=[{codeId:'cf',kind:'text',changes:[{articleId:'1',number:'1'},{articleId:'adct-1',number:'1'}]},
  {codeId:'civil',kind:'text',changes:[{articleId:'1022',number:'1022'}]},
  {codeId:'civil',kind:'baseline',changes:[]}];
 assert.equal(filterUpdates(events,'cf','ADCT-1')[0].changes[0].articleId,'adct-1');
 assert.equal(filterUpdates(events,'civil','Art. 1.022')[0].changes.length,1);
 assert.equal(filterUpdates(events,'civil','99999').length,0);
 assert.equal(filterUpdates(events,'civil').length,2);
 assert.equal(events[0].changes.length,2);
});

test('histórico das súmulas filtra referência por sigla, nome e número',()=>{
 const events=[{codeId:'sv',changes:[{articleId:'13',number:'13',kind:'vinculante'},{articleId:'14',number:'14',kind:'vinculante'}]}, {codeId:'civil',changes:[{articleId:'13',number:'13'}]}];
 for(const query of ['13','SV 13','Súmula Vinculante 13','Sumula nº 13']){
  const result=filterUpdates(events,'sv',query);
  assert.equal(result.length,1);
  assert.equal(result[0].changes.length,1);
  assert.equal(result[0].changes[0].articleId,'13');
 }
 assert.equal(events[0].changes.length,2);
});
