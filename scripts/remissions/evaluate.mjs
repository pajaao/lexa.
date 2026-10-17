// Evaluation consumes independently declared expectations, never parser-generated labels.
const key=(code,article,paragraph)=>JSON.stringify([code,article,paragraph]);
const names=targets=>new Set(targets.map(t=>typeof t==='string'?t:t.codeId+':'+t.articleId));
const same=(a,b)=>a.size===b.size&&[...a].every(x=>b.has(x));
const ratio=(a,b)=>b?a/b:null;
export function evaluateSample(sample,occurrences,{legacy=false}={}){
 const actual=new Map();
 for(const o of occurrences){
  if(legacy&&o.status==='E'&&o.reason==='own-heading')continue;
  const k=legacy?key(...o.source,o.paragraph):key(o.source.codeId,o.source.articleId,o.location.paragraph);
  if(!actual.has(k))actual.set(k,[]);actual.get(k).push(o);
 }
 let expectedExpressions=0,detected=0,matched=0,missed=0,spurious=0,correctClassifications=0,expectedDestinations=0,emittedDestinations=0,correctDestinations=0,incorrectDestinations=0,safetyOmissions=0;
 const classifications={A:0,B:0,C:0,D:0,E:0},expectedClassifications={...classifications},errors=[],expectedUnique=new Set(),emittedUnique=new Set(),correctUnique=new Set();
 for(const g of sample){
  const candidates=actual.get(key(g.code,g.article,g.paragraph))||[],used=new Set();let cursor=0;
  detected+=candidates.length;
  for(const p of candidates){const status=legacy?p.status:p.classification;classifications[status]++;if(status==='A'){
   const targets=names(legacy?p.targets.map(v=>v.join(':')):p.resolution.targets);emittedDestinations+=targets.size;for(const t of targets)emittedUnique.add(key(g.code,g.article,t));
  }}
  for(const e of g.expected){
   expectedExpressions++;expectedClassifications[e.status]++;
   const start=e.span?.[0]??g.text.indexOf(e.literal,cursor),end=e.span?.[1]??start+e.literal.length;
   if(start<0)throw Error('Expected literal absent from fixture');cursor=end;
   const gold=names(e.targets);
   if(e.status==='A'){expectedDestinations+=gold.size;for(const t of gold)expectedUnique.add(key(g.code,g.article,t));}
   const i=candidates.findIndex((p,i)=>{const span=legacy?p.span:[p.location.start,p.location.end];return !used.has(i)&&start<span[1]&&end>span[0];});
   if(i<0){missed++;errors.push({source:[g.code,g.article,g.paragraph],expected:e,actual:null});continue;}
   used.add(i);matched++;
   const p=candidates[i],status=legacy?p.status:p.classification,targets=names(legacy?p.targets.map(v=>v.join(':')):p.resolution.targets);
   const accurate=status===e.status&&(e.status!=='A'||same(gold,targets));correctClassifications+=Number(accurate);
   if(!accurate)errors.push({source:[g.code,g.article,g.paragraph],expected:e,actual:legacy?p:{text:p.location.text,span:[p.location.start,p.location.end],classification:status,reason:p.reason,targets:[...targets]}});
   if(e.status==='A'&&status==='C')safetyOmissions+=gold.size;
   if(status==='A'){
    for(const t of targets){if(e.status==='A'&&gold.has(t)){correctDestinations++;correctUnique.add(key(g.code,g.article,t));}else incorrectDestinations++;}
   }
  }
  for(const [i,p] of candidates.entries())if(!used.has(i)){
   spurious++;const status=legacy?p.status:p.classification;if(status==='A')incorrectDestinations+=names(legacy?p.targets.map(v=>v.join(':')):p.resolution.targets).size;
   errors.push({source:[g.code,g.article,g.paragraph],expected:null,actual:legacy?p:{text:p.location.text,classification:status,reason:p.reason}});
  }
 }
 return {paragraphs:sample.length,articles:new Set(sample.map(g=>key(g.code,g.article,0))).size,expectedExpressions,detectedExpressions:detected,matchedExpressions:matched,missedExpressions:missed,spuriousExpressions:spurious,correctClassifications,classifications,expectedClassifications,expectedDestinations,emittedDestinations,correctDestinations,incorrectDestinations,safetyOmissions,expectedUniqueConnections:expectedUnique.size,emittedUniqueConnections:emittedUnique.size,correctUniqueConnections:correctUnique.size,detectionPrecision:ratio(matched,detected),detectionRecall:ratio(matched,expectedExpressions),connectionPrecision:ratio(correctDestinations,emittedDestinations),destinationRecall:ratio(correctDestinations,expectedDestinations),errors};
}
