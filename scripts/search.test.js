import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {codes,searchArticles,articleById,articleLabel} from '../data.js';
const code = id => codes.find(c=>c.id===id);

test('artigos por número, referência e separador de milhar',()=>{
 for(const q of ['186','Art. 186','art 186º']) assert.deepEqual(searchArticles(code('civil'),q).map(a=>a.id),['186']);
 for(const q of ['1022','1.022','Art. 1.022.']) assert.deepEqual(searchArticles(code('cpc'),q).map(a=>a.id),['1022']);
 assert.equal(searchArticles(code('civil'),'99999').length,0);
});
test('busca ignora acentos e encontra artigos com letras',()=>{
 assert.ok(searchArticles(code('civil'),'ACAO OU OMISSAO').some(a=>a.id==='186'));
 for(const q of ['54-A','art. 54-a']) assert.deepEqual(searchArticles(code('cdc'),q).map(a=>a.id),['54-A']);
 assert.equal(searchArticles(code('penal'),'359-M-A')[0].id,'359-M-A');
});
test('Constituição e ADCT mantêm identidades e buscas separadas',()=>{
 assert.match(articleById(code('cf'),'1').text,/A República Federativa do Brasil/);
 assert.match(articleById(code('cf'),'adct-1').text,/O Presidente da República/);
 assert.equal(searchArticles(code('cf'),'1','adct')[0].id,'adct-1');
 assert.equal(searchArticles(code('cf'),'ADCT art. 1')[0].id,'adct-1');
 assert.match(articleLabel(articleById(code('cf'),'adct-1')),/^ADCT/);
 assert.ok(articleById(code('cf'),'adct-138'));
 assert.equal(code('cf').introductions.length,1);
 assert.match(code('cf').introductions[0].text,/Nós, representantes/);
 assert.doesNotMatch(code('cf').introductions[0].text,/Contribuição|recursos|Previdência/);
});
test('incisos e parágrafos continuam presentes em artigos longos e entre páginas',()=>{
 const cf5=articleById(code('cf'),'5');
 assert.match(cf5.text,/LXXIX/);
 assert.match(cf5.text,/proteção dos dados pessoais/);
 assert.match(cf5.text,/§ 4º O Brasil se submete/);
 assert.match(articleById(code('cpc'),'319').text,/VI - as provas/);
 assert.match(articleById(code('cdc'),'54-A').text,/superendividamento/);
 assert.match(articleById(code('penal'),'13').text,/§ 1º - A superveniência/);
 assert.match(articleById(code('penal'),'13').text,/c\) com seu comportamento anterior/);
 assert.match(articleById(code('civil'),'2046').text,/disposições correspondentes deste Código\.$/);
});
test('revogações em bloco mantêm o texto original e resolvem todos os números',()=>{
 const group=articleById(code('ctn'),'52');
 assert.equal(group.rangeEnd,58);
 assert.match(group.text,/Revogados/);
 for(let n=52;n<=58;n++)assert.equal(articleById(code('ctn'),String(n)),group);
 assert.equal(searchArticles(code('ctn'),'55')[0],group);
 assert.equal(articleById(code('civil'),'1625').rangeEnd,1629);
});
test('redação histórica riscada no CPC permanece distinta da substituta',()=>{
 const twelve=articleById(code('cpc'),'12');
 const first=twelve.paragraphs[0],second=twelve.paragraphs[1];
 assert.ok(first.runs.some(r=>r.deleted&&r.text.includes('deverão obedecer')));
 assert.ok(second.runs.some(r=>!r.deleted&&r.text.includes('atenderão, preferencialmente')));
 assert.equal(code('cpc').articles.filter(a=>a.id==='12').length,1);
});
test('todos os números-base até os artigos finais têm entrada ou revogação agrupada',()=>{
 for(const [id,last] of Object.entries({civil:2046,penal:361,cpc:1072,cdc:119,ctn:218,cf:250})){
  for(let n=1;n<=last;n++)assert.ok(articleById(code(id),String(n)),`${id}: artigo ${n} ausente`);
 }
 for(let n=1;n<=138;n++)assert.ok(articleById(code('cf'),'adct-'+n));
});
test('seis fontes preservadas com SHA-256 correspondente e páginas válidas',()=>{
 assert.equal(codes.length,6);
 for(const c of codes){
  const original=readFileSync(new URL('../'+c.source.pdf,import.meta.url));
  assert.equal(createHash('sha256').update(original).digest('hex'),c.source.sha256);
  const sections=new Set(c.sections.map(s=>s.id));
  assert.equal(new Set(c.articles.map(a=>a.id)).size,c.articles.length);
  for(const a of c.articles){
   assert.ok(sections.has(a.sectionId));
   assert.ok(a.text.trim().length>8);
   assert.ok(a.page>=1&&a.page<=c.source.pages);
   for(const p of a.paragraphs)assert.ok(p.page>=a.page&&p.page<=c.source.pages);
  }
 }
});
