// Browser-safe contract only. No legal extraction or legal texts here.
export const INDEX_SCHEMA=1;
const HASH=/^[a-f0-9]{64}$/u,ID=/^(?:adct-)?\d+(?:-[A-Z]+)*$/u;
const check=(ok,message)=>{if(!ok)throw Error('Índice de remissões incompatível: '+message);};
export const legalEditions=collections=>collections.filter(c=>c.id!=='sv'&&c.kind!=='sumulas').map(c=>[c.id,c.sha256]).sort(([a],[b])=>a<b?-1:a>b?1:0);
export async function digestJSON(value){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(value)))),b=>b.toString(16).padStart(2,'0')).join('');}
export async function validateRemissions(index,spec,collections){
 check(index?.schema===INDEX_SCHEMA&&spec.schema===INDEX_SCHEMA,'schema');
 check(index.provenance?.field==='paragraphs'&&index.provenance?.offsetUnit==='utf16','unidade da proveniência');
 check(index.mode==='experimental-only'&&index.policy?.mode==='experimental-only','aprovação');
 const editions=legalEditions(collections);
 check(JSON.stringify(index.editions)===JSON.stringify(editions),'edições jurídicas');
 check(index.legalEditionSetSha256===await digestJSON(editions),'hash jurídico');
 check(JSON.stringify(index.extractor)===JSON.stringify(spec.extractor)&&JSON.stringify(index.policy)===JSON.stringify(spec.policy),'regras/política');
 check(index.legalEditionSetSha256===spec.legalEditionSetSha256&&index.generationSha256===spec.generationSha256,'descritor');
 check(index.generationSha256===await digestJSON({schema:index.schema,legalEditionSetSha256:index.legalEditionSetSha256,extractor:index.extractor,policy:index.policy}),'geração');
 check(HASH.test(index.extractor.sha256)&&HASH.test(index.policy.sha256)&&typeof index.extractor.version==='string'&&typeof index.policy.version==='string','versões');
 check(Array.isArray(index.occurrences)&&Array.isArray(index.edges),'tabelas');
 const validNode=(code,id)=>Number.isInteger(code)&&code>=0&&code<editions.length&&ID.test(id);
 const validSpan=s=>Array.isArray(s)&&s.length===2&&Number.isSafeInteger(s[0])&&Number.isSafeInteger(s[1])&&s[0]>=0&&s[1]>s[0];
 const occurrences=new Set();
 for(const o of index.occurrences){
  check(Array.isArray(o)&&o.length===10&&HASH.test(o[0])&&!occurrences.has(o[0]),'ocorrência');occurrences.add(o[0]);
  check(validNode(o[1],o[2])&&Number.isInteger(o[3])&&o[3]>=0&&validSpan([o[4],o[5]]),'proveniência');
  check(index.policy.classes.includes(o[6])&&['internal-explicit','cross-norm-explicit'].includes(o[7]),'classe');
  check(Array.isArray(o[8])&&o[8].every(validSpan)&&(o[9]===null||validSpan(o[9])),'qualificadores');
 }
 const unique=new Set(),incoming={};
 for(const [i,e] of index.edges.entries()){
  check(Array.isArray(e)&&e.length===5&&validNode(e[0],e[1])&&validNode(e[2],e[3])&&Array.isArray(e[4])&&e[4].length>0,'aresta');
  const key=JSON.stringify(e.slice(0,4));check(!unique.has(key),'aresta duplicada');unique.add(key);
  check(new Set(e[4]).size===e[4].length,'ocorrência repetida');
  for(const oi of e[4]){const o=index.occurrences[oi];check(Number.isInteger(oi)&&o&&o[1]===e[0]&&o[2]===e[1],'origem da aresta');}
  (incoming[editions[e[2]][0]+'/'+e[3]]??=[]).push(i);
 }
 check(JSON.stringify(incoming)===JSON.stringify(index.incoming),'adjacência inversa');
 // Immutable to prevent a caller from corrupting a shared cached graph.
 const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
 return freeze(index);
}
export function relationStore(index){
 const codeIndex=new Map(index.editions.map(([id],i)=>[id,i]));
 const outgoing=(code,id)=>index.edges.filter(e=>e[0]===codeIndex.get(code)&&e[1]===id);
 const incoming=(code,id)=>(index.incoming[code+'/'+id]||[]).map(i=>index.edges[i]);
 return Object.freeze({edition:index.legalEditionSetSha256,generation:index.generationSha256,outgoing,incoming,hasConnections:(code,id)=>outgoing(code,id).length>0||incoming(code,id).length>0,occurrence:i=>index.occurrences[i],norm:i=>index.editions[i]?.[0]??null});
}
