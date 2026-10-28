import {readFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=new URL('../data/amendments/',import.meta.url);
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function amendmentAssets({candidate=false,asset,directory}){
 const release=JSON.parse((await readFile(new URL('release.json',root),'utf8')).replace(/^\uFEFF/,''));
 if(!candidate&&!release.publicationAuthorized)return null;
 if(!candidate&&(!release.legalReview?.approved||!release.legalReview.reviewer||!release.legalReview.evidence||!release.approvedNumbers?.length))throw new Error('Publicação de ECs sem homologação/autorização documentada');
 if(directory&&!candidate)throw new Error('Diretório experimental não pode substituir dados publicados');
 const folder=directory?pathToFileURL(resolve(directory)+'/'):new URL('candidate/',root);
 const catalog=JSON.parse((await readFile(new URL('catalog.json',folder),'utf8')).replace(/^\uFEFF/,''));
 if(catalog.publicationAuthorized!==false||catalog.reviewStatus!=='pending')throw new Error('Estado da candidata inválido');
 const entries=[],numbers=new Set();
 for(const entry of catalog.entries){
  if(!candidate&&!release.approvedNumbers.includes(entry.number))continue;
  if(!Number.isSafeInteger(entry.number)||entry.number<1||!Number.isInteger(entry.year)||entry.review!=='pending'||!/^documents\/ec-\d+\.json$/.test(entry.document)||!/^originals\/ec-\d+\.html$/.test(entry.original))throw new Error('Registro candidato inválido');
  if(numbers.has(entry.number))throw new Error('EC duplicada no catálogo');numbers.add(entry.number);
  const bytes=await readFile(new URL(entry.document,folder));
  if(hash(bytes)!==entry.sha256)throw new Error('Documento de EC alterado');
  const document=JSON.parse(bytes);if(document.number!==entry.number||document.year!==entry.year||!document.blocks.length)throw new Error('Identidade da EC inconsistente');
  const sourceURL=new URL(document.source.url);if(sourceURL.protocol!=='https:'||sourceURL.hostname!=='www2.camara.leg.br'||!sourceURL.pathname.includes('publicacaooriginal')||!sourceURL.pathname.includes('emendaconstitucional-'+entry.number+'-'))throw new Error('Fonte diferente da publicação original oficial');
  if(document.blocks.some(b=>b.runs.map(r=>r.text).join('')!==b.text))throw new Error('Texto de EC inconsistente com os runs');
  const original=await readFile(new URL(entry.original,folder));
  if(hash(original)!==entry.originalSha256||document.source.sha256!==entry.originalSha256)throw new Error('Original de EC alterado');
  if(document.review.status!=='pending'||document.review.publicationAuthorized!==false)throw new Error('Revisão de EC inválida');
  entries.push({...entry,document:asset('ec-'+entry.number,document),original:{url:document.source.url,sha256:entry.originalSha256}});
 }
 const generated=spawnSync(process.env.LEXA_PYTHON||'python',['-X','utf8','-B',fileURLToPath(new URL('./generate_amendment_links.py',import.meta.url)),'--directory',fileURLToPath(folder)],{encoding:'utf8',maxBuffer:64*1024*1024});
 if(generated.status!==0)throw new Error('Falha ao gerar índice documental de ECs: '+(generated.stderr||generated.error?.message||''));
 const audit=JSON.parse(generated.stdout);
 const allowed=new Set(entries.map(x=>x.number));
 const links=audit.confirmed.filter(x=>allowed.has(x.ec)).map(x=>({ec:x.ec,year:x.ano,articleId:x.artigo_id,unit:x.unidade,note:x.nota_literal,block:x.origem.sourceBlock_base_1,previous:x.estado_documental==='anterior_riscada',state:x.estado_documental}));
 return {candidate,publicationAuthorized:!candidate&&release.publicationAuthorized,count:entries.length,index:asset('ec-index',{entries}),links:asset('ec-links',{constitutionSemanticHash:audit.constitutionSemanticHash,records:links}),auditSummary:audit.summary};
}
