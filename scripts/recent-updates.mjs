// Build-time projection only: never ship before/after legal text in the shell.
function signature(version){
 if(!version)return [];
 const runs=[{text:version.title||''},...(version.paragraphs||[]).flatMap(paragraph=>paragraph.runs)];
 return runs.flatMap(run=>(run.text.match(/\S+/g)||[]).map(text=>[Boolean(run.deleted),text]));
}
export function recentTextUpdates(events,limit=3,articleLimit=4){
 return events.map((event,index)=>({event,index}))
  .filter(({event})=>event.kind==='text'&&Number.isFinite(Date.parse(event.capturedAt)))
  .sort((a,b)=>Date.parse(b.event.capturedAt)-Date.parse(a.event.capturedAt)||b.index-a.index)
  .map(({event})=>{
   const articles=new Map();
   for(const change of event.changes){
    if(!['added','changed','removed'].includes(change.type))continue;
    const before=signature(change.before),after=signature(change.after);
    if(!(before.length||after.length)||JSON.stringify(before)===JSON.stringify(after))continue;
    const {articleId,number,scope,kind,rangeEnd}=change;
    if(!articles.has(articleId))articles.set(articleId,{articleId,number,scope,...(kind!==undefined?{kind}:{}),...(rangeEnd!==undefined?{rangeEnd}:{})});
   }
   return {id:event.id,codeId:event.codeId,capturedAt:event.capturedAt,
    articles:[...articles.values()].slice(0,articleLimit),totalChanges:articles.size};
  }).filter(event=>event.totalChanges).slice(0,limit);
}
