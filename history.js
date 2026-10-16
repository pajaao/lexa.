export function filterUpdates(events, codeId = '', articleId = '') {
 const query=articleId.trim().replace(/^art\.?\s*/i,'').replace(/\.(?=\d{3}(?:\D|$))/g,'').toUpperCase();
 return events.filter(event=>!codeId||event.codeId===codeId).map(event=>({...event,changes:event.changes.filter(change=>!query||change.articleId.toUpperCase()===query||change.number.toUpperCase()===query)})).filter(event=>!query||event.changes.length);
}

function historyTokens(version) {
 if(!version)return [];
 const paragraphs=version.title?[{runs:[{text:version.title,deleted:false}]},...version.paragraphs]:version.paragraphs;
 return paragraphs.flatMap((p,paragraph)=>p.runs.flatMap(run=>(run.text.match(/\s+|\S+/g)||[]).map(text=>({text,deleted:!!run.deleted,paragraph}))));
}

export function compareVersions(before, after, maxCells = 250000) {
 const left=historyTokens(before),right=historyTokens(after);
 const key=t=>`${t.deleted?'1':'0'}:${t.text}`;
 const a=left.map(key),b=right.map(key);
 const sameA=new Set(),sameB=new Set();
 // A bounded LCS gives precise word highlights for ordinary articles. For very
 // long articles, retain exact common edges and highlight the changed middle.
 // Every original token is retained in both modes; no approximate text is made.
 if((a.length+1)*(b.length+1)<=maxCells){
  const width=b.length+1,table=new Uint32Array((a.length+1)*width);
  for(let i=a.length-1;i>=0;i--)for(let j=b.length-1;j>=0;j--)table[i*width+j]=a[i]===b[j]?table[(i+1)*width+j+1]+1:Math.max(table[(i+1)*width+j],table[i*width+j+1]);
  let i=0,j=0;
  while(i<a.length&&j<b.length){if(a[i]===b[j]){sameA.add(i++);sameB.add(j++);}else if(table[(i+1)*width+j]>=table[i*width+j+1])i++;else j++;}
 }else{
  let start=0;
  while(start<a.length&&start<b.length&&a[start]===b[start]){sameA.add(start);sameB.add(start++);}
  let i=a.length-1,j=b.length-1;
  while(i>=start&&j>=start&&a[i]===b[j]){sameA.add(i--);sameB.add(j--);}
 }
 return {before:left.map((t,i)=>({...t,changed:!sameA.has(i)})),after:right.map((t,i)=>({...t,changed:!sameB.has(i)}))};
}
