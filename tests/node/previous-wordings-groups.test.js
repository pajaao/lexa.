import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {historyContent} from '../../src/legislative-history.js';
import {previousRecords} from '../../src/legislative-history-model.js';

test('art. 215 destaca caputs e recolhe complementos sem modificar registros ou sua ordem interna',async()=>{
 const data=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-simple.json',import.meta.url),'utf8'));
 const snapshot=JSON.stringify(data);
 const records=previousRecords(data,'penal','215');
 const caputs=records.filter(r=>r.part==='caput'),others=records.filter(r=>r.part!=='caput');
 const html=historyContent(data,'penal','215');
 const cut=html.indexOf('<details class="legislative-other">');
 assert.ok(cut>0);
 assert.ok(html.includes(`Outras redações anteriores (${others.length})`));
 for(const row of caputs)assert.ok(html.indexOf(row.text)<cut);
 let last=cut;
 for(const row of others){const at=html.indexOf(row.text,last);assert.ok(at>last);last=at;}
 assert.ok(!html.includes('<details class="legislative-other" open'));
 assert.equal(JSON.stringify(data),snapshot);
});

test('caput isolado, complementos isolados e ausência de registros não produzem seção vazia',async()=>{
 const data=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-simple.json',import.meta.url),'utf8'));
 const groups=Map.groupBy(data.records,r=>r.codeId+'|'+r.articleId);
 for(const predicate of [rows=>rows.every(r=>r.part==='caput'),rows=>rows.every(r=>['paragraph','penalty'].includes(r.part))]){
  const rows=[...groups.values()].find(predicate);assert.ok(rows);
  const html=historyContent(data,rows[0].codeId,rows[0].articleId);
  assert.ok(!html.includes('legislative-other'));
  assert.ok(html.includes('legislative-text'));
 }
 const empty=historyContent({preview:true,records:[]},'penal','215');
 assert.ok(empty.includes('legislative-empty'));
 assert.ok(!empty.includes('legislative-timeline'));
 assert.ok(!empty.includes('legislative-other'));
});

test('contagem considera deduplicação existente e trechos conjuntos não viram caputs artificiais',async()=>{
 const data=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-simple.json',import.meta.url),'utf8'));
 const sample=data.records.find(r=>r.part==='caput');
 const caput={...sample,id:'caput',text:'Art. 1. Texto antigo.',articleId:'1'};
 const composite={...caput,id:'composite',part:'article',unitLabel:'Trecho da fonte: caput e pena',text:'Art. 1. Texto antigo. Pena - multa.'};
 const isolated={...caput,id:'isolated',text:'Art. 1. Outro caput anterior.'};
 const html=historyContent({preview:true,records:[caput,composite,isolated]},sample.codeId,'1');
 assert.ok(html.includes('Outras redações anteriores (1)'));
 assert.ok(html.includes(composite.unitLabel));
 assert.equal((html.match(/class="legislative-text"/g)||[]).length,2);
});
