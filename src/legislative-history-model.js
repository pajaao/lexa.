export const historicalParts={caput:'Caput',rubric:'Rubrica',penalty:'Pena',paragraph:'Parágrafo',article:'Artigo completo'};

// A record identifies one complete documented part, not necessarily an entire
// article. No date or inferred period of legal validity is required.
export function historyRecords(data,codeId,articleId){
 const ids=new Set();
 return data.records.filter(record=>{
  const valid=typeof record.id==='string'&&!ids.has(record.id)&&record.codeId===codeId&&record.articleId===articleId&&
   Object.hasOwn(historicalParts,record.part)&&typeof record.text==='string'&&record.text.trim()&&
   Number.isSafeInteger(record.sequence?.order)&&typeof record.sequence?.basis==='string'&&record.sequence.basis.trim()&&
   Array.isArray(record.notes)&&record.notes.every(note=>typeof note==='string')&&
   (data.demo?record.review?.status==='demonstration':record.review?.status==='approved');
  if(valid)ids.add(record.id);
  return valid;
 }).sort((a,b)=>a.sequence.order-b.sequence.order||a.id.localeCompare(b.id));
}

export function sourceLink(url){
 if(typeof url!=='string')return null;
 try{const parsed=new URL(url);return ['https:','http:'].includes(parsed.protocol)&&!parsed.username&&!parsed.password?parsed.href:null;}catch{return null;}
}
