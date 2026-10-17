import test from 'node:test';
import assert from 'node:assert/strict';
import {recentTextUpdates} from '../../scripts/recent-updates.mjs';
import {buildPackage} from '../../scripts/build.mjs';

const version=(text,deleted=false)=>({title:null,paragraphs:[{runs:[{text,deleted}]}]});
const change=(articleId='7',before='Texto anterior.',after='Texto diferente.')=>({articleId,number:articleId,scope:'main',type:'changed',before:version(before),after:version(after)});
const event=(id,kind='text',changes=[change()],capturedAt='2026-10-17T12:00:00Z')=>({id,codeId:'cf',kind,capturedAt,changes});

test('resumo exclui baseline, fonte e reprocessamento mesmo se contiverem diferenças',()=>{
 assert.deepEqual(recentTextUpdates([]),[]);
 assert.deepEqual(recentTextUpdates(['baseline','source','processing'].map(kind=>event(kind,kind))),[]);
 assert.deepEqual(recentTextUpdates([event('empty','text',[])]),[]);
 assert.deepEqual(recentTextUpdates([event('same','text',[change('7','Igual.','Igual.')])]),[]);
 assert.deepEqual(recentTextUpdates([event('invalid','text',[change()],'data inválida')]),[]);
});

test('diferenças só de espaços, parágrafos ou metadados não são alterações textuais',()=>{
 const before={title:'Título',paragraphs:[{runs:[{text:'Primeiro   texto.',deleted:false}]},{runs:[{text:'Segundo texto.',deleted:false}]}]};
 const after={title:'Título',paragraphs:[{runs:[{text:'Primeiro texto. Segundo\ntexto.',deleted:false}]}],page:99};
 assert.deepEqual(recentTextUpdates([event('format','text',[{...change(),before,after}])]),[]);
 assert.deepEqual(recentTextUpdates([event('empty-entry','text',[{...change(),before:null,after:version('')}])]),[]);
});

test('resumo inclui adição, remoção e mudança de riscos registradas como textuais',()=>{
 const changes=[{...change('7'),type:'added',before:null},
  {...change('40'),type:'removed',after:null},
  {...change('198'),before:version('Texto.',false),after:version('Texto.',true)}];
 const [summary]=recentTextUpdates([event('real','text',changes)]);
 assert.deepEqual(summary.articles.map(article=>article.articleId),['7','40','198']);
 assert.equal(summary.totalChanges,3);
 assert.ok(!JSON.stringify(summary).includes('Texto.'));
 assert.ok(!JSON.stringify(summary).includes('before'));
});

test('ordena eventos por data, limita volume e preserva ordem/IDs das entradas sem mutar histórico',()=>{
 const events=[event('old','text',[change()],'2026-10-15T12:00:00Z'),
  event('new','text',[change('adct-1'),change('40'),change('40'),change('198')]),
  event('middle','text',[change()],'2026-10-16T12:00:00Z')];
 events[1].changes[0].number='1';events[1].changes[0].scope='adct';
 const original=JSON.stringify(events),summary=recentTextUpdates(events,2,2);
 assert.deepEqual(summary.map(item=>item.id),['new','middle']);
 assert.deepEqual(summary[0].articles.map(article=>article.articleId),['adct-1','40']);
 assert.equal(summary[0].articles[0].scope,'adct');assert.equal(summary[0].totalChanges,3);
 assert.equal(JSON.stringify(events),original);
 assert.deepEqual(recentTextUpdates(events,0),[]);
});

test('mesma data segue ordem do histórico existente e preserva metadados de súmula/intervalo',()=>{
 const a=event('a'),b=event('b');b.codeId='sv';b.changes=[{...change('13'),kind:'vinculante',rangeEnd:'14'}];
 const summary=recentTextUpdates([a,b]);assert.deepEqual(summary.map(e=>e.id),['b','a']);
 assert.equal(summary[0].articles[0].kind,'vinculante');assert.equal(summary[0].articles[0].rangeEnd,'14');
});

test('build deriva resumo da mesma edição sem copiar versões completas para o shell',async()=>{
 const history=[event('text-real'),event('processing','processing'),event('baseline','baseline')];
 const built=await buildPackage({history});
 assert.deepEqual(built.manifest.recentUpdates,recentTextUpdates(history));
 assert.deepEqual(JSON.parse(built.files.get(built.manifest.history.file)),history);
 assert.deepEqual(JSON.parse(built.files.get('catalog.json')).recentUpdates,built.manifest.recentUpdates);
 const adapter=[...built.files].find(([file])=>file.endsWith('/collections.js'))[1];
 assert.ok(adapter.includes('text-real'));assert.ok(!adapter.includes('Texto anterior.'));
 assert.ok(!adapter.includes('"before"'));assert.ok(!adapter.includes('"after"'));
 const neutral=await buildPackage({history:history.filter(event=>event.kind!=='text')});
 assert.deepEqual(neutral.manifest.recentUpdates,[]);
 assert.deepEqual((await buildPackage({history:[]})).manifest.recentUpdates,[]);
 const unknown={...event('unknown'),codeId:'not-in-catalog'};
 assert.deepEqual((await buildPackage({history:[unknown]})).manifest.recentUpdates,[]);
 const oldNorms=[...built.files].filter(([file])=>file.startsWith('data/')&&!file.startsWith('data/history.'));
 assert.deepEqual([...neutral.files].filter(([file])=>file.startsWith('data/')&&!file.startsWith('data/history.')),oldNorms);
});
