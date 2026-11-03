import {escape,highlight} from './presentation.js';
import {unitKind} from './structure.js';

// Presentation only. Never infer an amendment operation from the absence of dots.
const dots=/\.{4,}|…{2,}/;
const marker=/^["“«]?\s*(?:(?:Art\.?\s*\d+(?:-[A-Z])?[º°o.]*|§\s*\d+[º°o.]*|Parágrafo\s+único\.?|[IVXLCDM]+\s*[-–—]?)\s*)?(?:\.{4,}|…{2,})[\s.…]*(?:["”»]\s*)?(?:\((?:NR|AC)\))?\s*[.;]?$/iu;
export function continuityPresentation(paragraph){
 const text=paragraph.runs.map(x=>x.text).join('');
 const safe=Boolean(paragraph.documentaryKind?.includes('citado')&&dots.test(text)&&marker.test(text.trim()));
 return {safe,pure:safe&&!text.replace(/[.\s…]/gu,'')};
}
export function amendmentParagraphs(paragraphs,query=''){
 return paragraphs.map((p,index)=>{
  const {safe,pure}=continuityPresentation(p);
  const runs=p.runs.map(r=>{
   const text=safe?r.text.split(/(\.{4,}|…{2,})/u).map(part=>dots.test(part)?`<span class="ec-continuity-dots">${escape(part)}</span>`:highlight(part,query)).join(''):highlight(r.text,query);
   return r.deleted?`<del>${text}</del>`:text;
  }).join('');
  return `<p ${p.sourceBlock!=null?'data-source-block="'+escape(String(p.sourceBlock))+'"':''} class="legal-unit ${p.documentaryKind?.includes('citado')?'ec-citation ':''}${pure?'ec-continuity-only ':''}unit-${unitKind(p,index)}${p.runs.every(r=>r.deleted||!r.text.trim())?' deleted-paragraph':''}">${runs}</p>`;
 }).join('');
}
