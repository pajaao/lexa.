import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {continuityPresentation,amendmentParagraphs} from '../../src/amendment-reading.js';
const paragraph=(text,kind='dispositivo_citado')=>({runs:[{text,deleted:false}],documentaryKind:kind});
test('continuidade estrita: oculta só pontos, preserva identidade, notas e casos ambíguos',()=>{
 assert.deepEqual(continuityPresentation(paragraph('............. ')),{safe:true,pure:true});
 for(const value of ['"Art. 225. ..........','§ 1º ..........','..........." (NR)','………'])assert.equal(continuityPresentation(paragraph(value)).safe,true,value);
 for(const value of ['Art. 2º Revogam-se os arts. 3º e 4º.','VIII - Texto normativo ........ e sua continuação.','...','[..................]','...... (VETADO)','§ 1º Texto relevante.'])assert.equal(continuityPresentation(paragraph(value)).safe,false,value);
 assert.equal(continuityPresentation(paragraph('........','artigo_proprio')).safe,false);
 const html=amendmentParagraphs([paragraph('"Art. 225. ..........'),paragraph('......" (NR)'),paragraph('VIII - Texto integral.')]);
 assert.match(html,/Art\. 225\./);assert.match(html,/\(NR\)/);assert.match(html,/VIII - Texto integral\./);assert.match(html,/ec-continuity-dots/);
});
test('EC123 e EC115: somente marcadores documentais; nenhum dado ou run é alterado',async()=>{
 for(const n of [123,115,103,19,29,132]){
  const doc=JSON.parse(await readFile(new URL(`../../data/amendments/candidate/documents/ec-${n}.json`,import.meta.url),'utf8'));
  const paragraphs=doc.blocks.map(b=>({runs:b.runs,documentaryKind:b.kind,sourceBlock:b.id}));const before=JSON.stringify(paragraphs);
  amendmentParagraphs(paragraphs);assert.equal(JSON.stringify(paragraphs),before);
  for(const p of paragraphs.filter(p=>continuityPresentation(p).pure))assert.match(p.runs.map(r=>r.text).join(''),/^[\s.…]+$/u);
 }
});
