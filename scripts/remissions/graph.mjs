// A single edge table. Incoming is a derived adjacency of edge positions, never
// an independent source of legal relations. Only current, resolved A contributes.
export function relationGraph(extraction){
 const map=new Map();
 extraction.occurrences.forEach((o,index)=>{
  if(o.classification!=='A'||o.resolution.status!=='resolved'||o.historical.state!=='clear')return;
  for(const t of o.resolution.targets){
   const key=JSON.stringify([o.source.codeId,o.source.articleId,t.codeId,t.articleId]);
   if(!map.has(key))map.set(key,{source:[o.source.codeId,o.source.articleId],target:[t.codeId,t.articleId],occurrences:[]});
   map.get(key).occurrences.push(index);
  }
 });
 const edges=[...map].sort(([a],[b])=>a<b?-1:a>b?1:0).map(([,edge])=>edge),incoming={};
 edges.forEach((edge,i)=>(incoming[edge.target.join('/')]??=[]).push(i));
 return {edges,incoming};
}
export function compactBundle(extraction){
 const graph=relationGraph(extraction),codeIds=Object.keys(extraction.editions),ci=id=>codeIds.indexOf(id);
 return {schema:1,rules:extraction.rules,editionSetSha256:extraction.editionSetSha256,editions:extraction.editions,
 // tuple definitions are documented in docs/remissoes/fase-0-5.md.
 occurrences:extraction.occurrences.map(o=>[ci(o.source.codeId),o.source.articleId,o.location.paragraph,o.location.start,o.location.end,o.classification,o.resolution.status,o.reason,o.historical.core,o.historical.qualifiers,o.historical.context,o.qualifiers.map(q=>[q.start,q.end,q.kind,q.articleNumber??null]),o.normEvidence?[o.normEvidence.start,o.normEvidence.end]:null,o.norm.identity?[o.norm.identity.kind,o.norm.identity.number,o.norm.identity.year]:null,o.kind]),
 edges:graph.edges.map(e=>[ci(e.source[0]),e.source[1],ci(e.target[0]),e.target[1],e.occurrences]),incoming:graph.incoming};
}
