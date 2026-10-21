import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');

export function checkRelease(manifest,bytes,readerBytes,validationBytes,{candidate=false}={}){
 const data=JSON.parse(bytes);
 if(hash(bytes)!==manifest.dataSha256||hash(String(readerBytes).replace(/\r\n/g,'\n'))!==manifest.readerSha256||hash(validationBytes)!==manifest.validationSha256)throw new Error('Integridade da candidata de redações anteriores inválida.');
 const ids=data.records.map(r=>r.id);
 const report=JSON.parse(validationBytes);
 if(ids.length!==manifest.recordCount||new Set(ids).size!==ids.length||JSON.stringify(ids)!==JSON.stringify(manifest.recordIds)||JSON.stringify(ids)!==JSON.stringify(report.checks.filter(r=>!r.excludedReason).map(r=>r.id)))throw new Error('Seleção de redações anteriores inconsistente.');
 if(data.records.some(r=>r.review?.status!=='pending'||r.wording?.status!=='previous'))throw new Error('A preparação não pode alterar homologação.');
 if(report.selectedCount!==manifest.recordCount||Object.entries(manifest.byLegislation).some(([code,count])=>data.records.filter(r=>r.codeId===code).length!==count))throw new Error('Contagens do manifesto inconsistentes.');
 if(!candidate&&!manifest.publicationAuthorized)return {demo:false,records:[]};
 if(!candidate&&![manifest.governanceDecision,manifest.riskReviewDecision,manifest.publicationDecision].every(v=>typeof v==='string'&&v.trim()))throw new Error('Publicação exige decisões expressas de governança, validação por risco e lançamento.');
 return {demo:false,candidate,publication:{authorized:!candidate,releaseId:manifest.releaseId},records:data.records};
}

export async function releaseData(options={}){
 const [manifest,bytes,readerBytes]=await Promise.all([
  readFile(new URL('data/previous-wordings/release.json',root),'utf8').then(JSON.parse),
  readFile(new URL('data/previous-wordings/candidate.json',root)),
  readFile(new URL('data/official/legislation.js',root))]);
 if(!/^experiments\/previous-wordings-release\/[A-Za-z0-9_-]+\/validation\.json$/.test(manifest.validationReport))throw new Error('Caminho de validação inválido.');
 const validationBytes=await readFile(new URL(manifest.validationReport,root));
 return checkRelease(manifest,bytes,readerBytes,validationBytes,options);
}
