import test from 'node:test';
import assert from 'node:assert/strict';
import {historyRecords,sourceLink} from '../../src/legislative-history-model.js';
import {historyContent} from '../../src/legislative-history.js';
import {legislativeHistoryData as fixture} from '../fixtures/legislative-history-demo.js';
import {buildPackage} from '../../scripts/build.mjs';
import {stagePages} from '../../scripts/build-pages.mjs';
import {legislativeHistoryData as approvedData} from '../../src/legislative-history-data.js';

test('piloto humano aprovado mantém exatamente os três caputs e notas do art. 215',()=>{
 const records=historyRecords(approvedData,'penal','215');
 assert.deepEqual(records.map(r=>r.id),['penal-215-caput-01','penal-215-caput-02','penal-215-caput-03']);
 assert.deepEqual(records.map(r=>r.text),[
  'Art. 215 - Ter conjunção carnal com mulher honesta, mediante fraude:',
  'Art. 215. Ter conjunção carnal com mulher, mediante fraude:',
  'Art. 215. Ter conjunção carnal ou praticar outro ato libidinoso com alguém, mediante fraude ou outro meio que impeça ou dificulte a livre manifestação de vontade da vítima:'
 ]);
 assert.deepEqual(records.map(r=>r.notes),[[],['(Redação dada pela Lei nº 11.106, de 2005)'],['(Redação dada pela Lei nº 12.015, de 2009)']]);
 assert.ok(records.every(r=>r.part==='caput'&&r.review.evidence&&r.source.sha256==='2655efc6112d4601204208f3f4eb2e911957187fe7ce6727c4d681f6bb77ec19'));
 assert.deepEqual(historyRecords(approvedData,'civil','215'),[]);
 assert.deepEqual(historyRecords(approvedData,'penal','214'),[]);
});

test('histórico exige homologação e ordem fundamentada, sem exigir data',()=>{
 const approved={...fixture.records[0],review:{status:'approved'}};
 const records=[fixture.records[0],{...approved,id:'pending',review:{status:'pending'}},approved,
  {...approved,id:'no-basis',sequence:{order:2,basis:''}},
  {...approved,id:'other',articleId:'2'}];
 assert.deepEqual(historyRecords({demo:false,records},'penal','1'),[approved]);
 assert.equal(historyRecords({demo:true,records},'penal','1').length,1);
 assert.deepEqual(historyRecords(fixture,'penal','2'),[]);
 const reverse={...fixture,records:[...fixture.records].reverse()};
 assert.deepEqual(historyRecords(reverse,'penal','1').map(r=>r.sequence.order),[1,2]);
});

test('textos, notas e fontes são escapados; esquemas perigosos nunca viram links',()=>{
 const payload='<img src=x onerror=alert(1)>';
 const record={...fixture.records[0],text:payload,notes:[payload],reference:payload,source:{label:payload,location:payload,url:'javascript:alert(1)'}};
 const html=historyContent({demo:true,records:[record]},'penal','1');
 assert.ok(html.includes('&lt;img'));assert.ok(!html.includes('<img'));assert.ok(!html.includes('href="javascript:'));
 assert.equal(sourceLink('data:text/html,x'),null);
 assert.equal(sourceLink('https://name:secret@example.org'),null);
 assert.equal(sourceLink('https://example.org/source#page=1'),'https://example.org/source#page=1');
 const withLink=historyContent({demo:true,records:[{...record,source:{url:'https://example.org',label:'Fonte',location:'Página 1'}}]},'penal','1');
 assert.ok(withLink.includes('rel="noopener noreferrer"'));
});

test('ausências são explícitas e notas editoriais ficam separadas',()=>{
 const html=historyContent(fixture,'penal','1');
 for(const record of fixture.records)assert.ok(html.includes(record.text));
 assert.ok(html.includes('Fonte não informada.'));assert.ok(html.includes('Referência legislativa não informada.'));
 assert.equal((html.match(/<summary>Notas editoriais<\/summary>/g)||[]).length,1);
 assert.ok(historyContent({demo:false,records:[]},'penal','1').includes('Isso não significa que ele nunca tenha sido alterado.'));
});

test('pacote normal exclui fixtures; demonstração exige build explícito e não substitui dist',async()=>{
 const production=await buildPackage();
 for(const bytes of production.files.values())assert.ok(!String(bytes).includes('EXEMPLO FICTÍCIO'));
 const demo=await buildPackage({legislativeHistoryDemo:true});
 assert.ok([...demo.files.values()].some(bytes=>String(bytes).includes('EXEMPLO FICTÍCIO')));
 assert.ok([...demo.files.entries()].some(([name,bytes])=>name.endsWith('/pwa.js')&&bytes==='export function setupPwa(){}'));
 assert.deepEqual(production.manifest.collections,demo.manifest.collections);
 await assert.rejects(stagePages(undefined,{legislativeHistoryDemo:true}),/Demonstração não pode/);
});
