export const historicalParts={caput:'Caput',rubric:'Rubrica',penalty:'Pena',paragraph:'Parágrafo',item:'Inciso',letter:'Alínea',article:'Artigo completo'};

// A record identifies one complete documented part, not necessarily an entire
// article. No date or inferred period of legal validity is required.
export function historyRecords(data,codeId,articleId){
 const ids=new Set();
 return data.records.filter(record=>{
  const valid=typeof record.id==='string'&&!ids.has(record.id)&&record.codeId===codeId&&record.articleId===articleId&&
   Object.hasOwn(historicalParts,record.part)&&typeof record.text==='string'&&record.text.trim()&&
   Number.isSafeInteger(record.sequence?.order)&&typeof record.sequence?.basis==='string'&&record.sequence.basis.trim()&&
   Array.isArray(record.notes)&&record.notes.every(note=>typeof note==='string')&&
   (data.demo?record.review?.status==='demonstration':record.review?.status==='approved'||(data.preview===true||data.candidate===true||data.publication?.authorized===true)&&record.review?.status==='pending');
  if(valid)ids.add(record.id);
  return valid;
 }).sort((a,b)=>a.sequence.order-b.sequence.order||a.id.localeCompare(b.id));
}

export function previousRecords(data,codeId,articleId){
 const records=historyRecords(data,codeId,articleId).filter(record=>record.wording?.status==='previous'||data.demo&&record.wording?.status!=='current_candidate');
 // A complete struck source block may include a caput already stored separately.
 // Prefer that verbatim block to displaying its caput twice.
 return records.filter(record=>record.part!=='caput'||!records.some(other=>other.part==='article'&&other.unitLabel==='Trecho da fonte: caput e pena'&&other.text.replace(/\s+/gu,' ').trim().startsWith(record.text.replace(/\s+/gu,' ').trim()+' Pena')));
}

export function sourceLink(url){
 if(typeof url!=='string')return null;
 try{const parsed=new URL(url);return ['https:','http:'].includes(parsed.protocol)&&!parsed.username&&!parsed.password?parsed.href:null;}catch{return null;}
}

// Comparison only: neither source runs nor stored history records are rewritten.
function normativeParagraph(paragraph){
 const raw=paragraph.runs.map(run=>run.text).join(''),mask=new Uint8Array(raw.length);
 const notes=/\((?:Redação|Incluíd[oa]|Acrescid[oa]|Alterad[oa]|Revogad[oa]|Vide\b|Vigência\b|Produção de efeitos?\b|Suspens[ao])/giu;
 let match;
 while((match=notes.exec(raw))){
  let depth=0,end=-1;
  for(let i=match.index;i<raw.length;i++){
   if(raw[i]==='(')depth++;if(raw[i]===')')depth--;
   if(depth===0){end=i+1;break;}
  }
  if(end<0)return null;
  mask.fill(1,match.index,end);notes.lastIndex=end;
 }
 for(const note of raw.matchAll(/\bVide art\.\s*\d+\s*[-–—]\s*ADCT\b/giu))mask.fill(1,note.index,note.index+note[0].length);
 let cursor=0;const states=[];
 for(const run of paragraph.runs){
  for(let i=0;i<run.text.length;i++)if(!mask[cursor+i]&&/[\p{L}\p{N}]/u.test(run.text[i])&&!/[º°]/u.test(run.text[i]))states.push(Boolean(run.deleted));
  cursor+=run.text.length;
 }
 const plain=raw.split('').filter((c,i)=>!mask[i]).join('').replace(/\s+/gu,' ').trim();
 const text=plain.normalize('NFC');
 return {text,plain,struck:states.length>0&&states.every(Boolean),unstruck:states.length>0&&states.every(value=>!value)};
}
// The source deletion mark controls reader separation, independently of whether
// an occurrence can be safely associated with a previous-wording record.
// Never mutate source paragraphs or infer replacement wording.
export function readingArticle(data,codeId,article){
 let changed=false;
 const paragraphs=article.paragraphs.flatMap(paragraph=>{
  if(!paragraph.runs.some(run=>run.deleted))return [paragraph];
  changed=true;
  const runs=paragraph.runs.filter(run=>!run.deleted);
  const remaining=normativeParagraph({...paragraph,runs});
  // Drop orphan unit markers and notes left by a wholly struck body.
  const body=(remaining?.plain??runs.map(run=>run.text).join('')).replace(/(?:Art\.?\s*\d+[º°]?(?:-[A-Z])?[.:-]?|Parágrafo\s+único|§\s*\d+[º°]?|[IVXLCDM]+\s*[-–—]|[a-z]\))/gu,'').replace(/[\s.:-]/gu,'');
  if(!body)return [];
  return [{...paragraph,runs}];
 });
 return changed?{...article,paragraphs}:article;
}

// “Current” is relative to the edition actually loaded, including when its
// current caput follows fully struck older caputs in the source array.
export function wordingLabel(record,currentArticle){
 if(record.wording?.status==='previous')return 'Redação anterior';
 if(record.part==='caput'&&record.wording?.status==='current_candidate'&&
  currentArticle?.paragraphs?.some(paragraph=>{const p=normativeParagraph(paragraph);return p?.unstruck&&p.plain===record.text.replace(/\s+/gu,' ').trim();}))return 'Redação atual na edição consultada';
 return record.wording?.status==='current_candidate'?'Redação mais recente documentada':'Redação documentada';
}
