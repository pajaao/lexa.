// A small working set for legal readers. Search uses independent compact data.
export function createCollectionCache(limit=3){
 const recent=new Map();let active=null;
 function trim(){
  for(const [id,code] of recent){
   if(recent.size<=limit)break;
   if(id===active)continue;
   recent.delete(id);
   code.articles=[];code.sections=[];delete code.introductions;code.loaded=false;
  }
 }
 return {
  activate(id){active=id;trim();},
  remember(code){recent.delete(code.id);recent.set(code.id,code);trim();},
  ids(){return [...recent.keys()];}
 };
}
