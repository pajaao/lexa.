import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {collections,codes,normalize,articleLabel,searchArticles,articleById} from '../data.js';
import {sumulas} from '../sumulas-content.js';
const sv={...sumulas[0],articles:sumulas[0].articles.map(a=>({...a,text:a.paragraphs.map(p=>p.runs.map(r=>r.text).join('')).join('\n'),searchText:normalize([...a.paragraphs,...a.notes].map(p=>p.runs.map(r=>r.text).join('')).join('\n'))}))};

test('PDF novo preservado, 63 identidades próprias, sem modificar os seis códigos',()=>{
 assert.equal(codes.length,6);
 assert.equal(collections.length,7);
 assert.equal(sv.articles.length,63);
 assert.deepEqual(sv.articles.map(a=>a.id),Array.from({length:63},(_,i)=>String(i+1)));
 const manifest=JSON.parse(readFileSync(new URL('../sources/sumulas-manifest.json',import.meta.url)));
 assert.equal(createHash('sha256').update(readFileSync(new URL('../'+manifest.pdf,import.meta.url))).digest('hex'),manifest.sha256);
 assert.equal(manifest.declaredConsultationDate,'2026-10-16');
 for(const a of sv.articles){
  assert.equal(articleLabel(a),'Súmula Vinculante '+a.number);
  assert.ok(a.page>=1&&a.endPage>=a.page&&a.endPage<=236);
  assert.ok(sv.sections.some(s=>s.id===a.sectionId));
  assert.equal(new URL(a.url).hostname,'portal.stf.jus.br');
  for(const p of [...a.paragraphs,...a.notes])assert.ok(p.page>=a.page&&p.page<=a.endPage);
 }
});
test('busca por número, nome, sigla e texto do enunciado ou dos precedentes',()=>{
 for(const q of ['13','SV 13','sv13','Súmula 13','Súmula Vinculante nº 13'])assert.deepEqual(searchArticles(sv,q).map(a=>a.id),['13']);
 assert.equal(searchArticles(sv,'SV 999').length,0);
 assert.ok(searchArticles(sv,'cônjuge').some(a=>a.id==='13'));
 assert.ok(searchArticles(sv,'Rcl 87.875').some(a=>a.id==='63'));
 assert.match(articleById(sv,'63').text,/não configura crime hediondo/);
 assert.match(articleById(codes.find(c=>c.id==='civil'),'13').text,/Salvo por exigência médica/);
});
test('situações do documento preservadas sem confundir precedentes com enunciado',()=>{
 assert.equal(articleById(sv,'9').status,'cancelled');
 assert.equal(articleById(sv,'30').status,'pending');
 assert.equal(articleById(sv,'30').text,'A Súmula Vinculante 30 está pendente de publicação.');
 assert.equal(articleById(sv,'13').status,'as_provided');
 assert.doesNotMatch(articleById(sv,'13').text,/Precedente|Jurisprudência selecionada|RE 579/);
 assert.ok(articleById(sv,'13').notes.some(p=>p.heading&&p.runs[0].text==='Precedentes Representativos'));
 assert.ok(articleById(sv,'63').notes.some(p=>p.runs[0].text.includes('Rcl 87.875')));
});

 test('coleção ativa das súmulas mantém cobertura e procedência válidas',()=>{
 const active=collections.find(c=>c.id==='sv');
 assert.ok(active.articles.length>=63);
 for(let n=1;n<=active.articles.length;n++)assert.ok(articleById(active,String(n)));
 if(active.source.kind==='official_stf'){
  const snapshot=JSON.parse(readFileSync(new URL('../'+active.source.snapshot,import.meta.url)));
  assert.equal(snapshot.semantic_sha256,active.source.sha256);
  assert.equal(snapshot.captured_at,active.source.capturedAt);
  for(const article of active.articles){
   const item=JSON.parse(readFileSync(new URL('../monitor/stf/items/'+article.number+'.json',import.meta.url)));
   assert.deepEqual(item.article.paragraphs,article.paragraphs);
   assert.equal(item.source_url,article.url);
  }
 }else assert.equal(active.source.kind,'supplied_pdf');
 });
