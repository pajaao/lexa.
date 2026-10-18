// Local audit artifacts only. Not imported by the public build.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';import {pathToFileURL} from 'node:url';
import {buildPackage} from '../build.mjs';import {buildRemissions} from '../remissions/build-resource.mjs';
import {hash,plain,spanCheck,inspectOccurrence,emptyReview,sampleRejected,csv} from './checks.mjs';
const BASE='5b218d9dc38c94194e0a13c51984d2b6d14c2f14';
const reasonCounts=rows=>Object.fromEntries(['Consistente na verificação automatizada','Suspeita','Inconclusiva','Erro confirmado'].map(s=>[s,rows.filter(r=>r.status===s).length]));
function normInfo(corpus,codeId,articleId){const c=corpus.collections.find(c=>c.code.id===codeId),a=c.code.articles.find(a=>a.id===articleId);return {codeId,name:c.code.name,law:c.code.law,scope:a.scope||'main',articleId,number:a.number,editionSha256:c.sha256,articleSha256:hash(JSON.stringify(a)),article:a};}
export function auditBundle(corpus,built){
 const decision=new Map(built.audit.decisions.map(d=>[d.occurrenceId,d])),occurrences=new Map(built.audit.occurrences.map(o=>[o.id,o]));
 const edges=built.index.edges.map(e=>{
  const source=normInfo(corpus,built.index.editions[e[0]][0],e[1]),target=normInfo(corpus,built.index.editions[e[2]][0],e[3]);
  const edgeId=hash(JSON.stringify([built.index.generationSha256,source.codeId,source.articleId,target.codeId,target.articleId]));
  const evidence=e[4].map(i=>{
   const id=built.index.occurrences[i][0],o=occurrences.get(id),syntaxClass=decision.get(id).syntaxClass,verification=inspectOccurrence(corpus,o,syntaxClass,{codeId:target.codeId,articleId:target.articleId,scope:target.scope,editionSha256:target.editionSha256});
   return {occurrenceId:id,paragraph:o.location.paragraph,offsetUnit:'utf16',span:o.location,literal:o.location.text,normEvidence:o.normEvidence,qualifiers:o.qualifiers,syntaxClass,historical:o.historical,paragraphRuns:source.article.paragraphs[o.location.paragraph].runs,verification};
  });
  const statuses=evidence.map(e=>e.verification.status),status=['Erro confirmado','Suspeita','Inconclusiva','Consistente na verificação automatizada'].find(s=>statuses.includes(s));
  return {edgeId,source,target,occurrenceIds:evidence.map(e=>e.occurrenceId),evidence,status,review:emptyReview()};
 });
 const rejected=built.audit.occurrences.filter(o=>!decision.get(o.id).eligible).map(o=>{
  const source=normInfo(corpus,o.source.codeId,o.source.articleId),exclusionReason=decision.get(o.id).reason;
  const facets={historical:o.historical.state!=='clear',ambiguity:/norm|scope|identity|qualifier|implicit/iu.test(o.reason),reproduction:/amendment|reproduc/iu.test(o.reason),unauthorizedSyntax:/syntax|range|complex/iu.test(exclusionReason)};
  const category=facets.historical?'Omissão intencional: evidência histórica':o.classification==='B'?'Omissão intencional: destino externo':facets.reproduction?'Omissão intencional: atribuição de reprodução não suportada':facets.unauthorizedSyntax?'Omissão intencional: classe não autorizada':o.classification==='E'?'Candidato classificado E: conferir se falso positivo':o.classification==='C'?'Limitação de reconhecimento ou ambiguidade: conferir sem presumir destino':'Omissão de política: conferir justificativa';
  return {id:o.id,source:o.source,sourceDocument:source,classification:o.classification,exclusionReason,diagnosticReason:o.reason,span:o.location,literal:o.location.text,normEvidence:o.normEvidence,qualifiers:o.qualifiers,historical:o.historical,resolution:o.resolution,paragraphRuns:source.article.paragraphs[o.location.paragraph].runs,facets,category,review:emptyReview()};
 });
 const sample=sampleRejected(rejected);
 for(const r of sample.records){const core=spanCheck(r.span,{runs:r.paragraphRuns});r.independentEvidence={sourceHash:hash(JSON.stringify(corpus.collections.find(c=>c.code.id===r.source.codeId).code))===r.source.editionSha256,coreSpan:core,qualifiers:r.qualifiers.map(q=>spanCheck(q,{runs:r.paragraphRuns})),norm:r.normEvidence?spanCheck(r.normEvidence,{runs:r.paragraphRuns}):null,hasArticlePrefix:!!(r.literal.match(/^(?:arts?\.|artigos?)\s/iu)),noPromotion:true};}

 return {schema:1,baseCommit:BASE,editionSet:built.index.legalEditionSetSha256,generation:built.index.generationSha256,extractor:built.index.extractor,policy:built.index.policy,counts:{candidates:built.audit.candidates,occurrences:built.audit.eligibleOccurrences,edges:edges.length,statuses:reasonCounts(edges),rejected:rejected.length,sampledRejections:sample.records.length,samplingStrata:sample.strata},edges,sample};
}
export function artifacts(bundle){
 const meta={schema:bundle.schema,baseCommit:bundle.baseCommit,editionSet:bundle.editionSet,generation:bundle.generation,extractor:bundle.extractor,policy:bundle.policy,counts:bundle.counts};
 const edgeRows=bundle.edges.map(e=>({recordType:'edge',id:e.edgeId,source:e.source.codeId,sourceScope:e.source.scope,sourceArticle:e.source.articleId,sourceSHA:e.source.editionSha256,target:e.target.codeId,targetScope:e.target.scope,targetArticle:e.target.articleId,targetSHA:e.target.editionSha256,occurrenceIds:e.occurrenceIds,status:e.status,paragraphs:e.evidence.map(v=>v.paragraph).join(' | '),startUTF16:e.evidence.map(v=>v.span.start).join(' | '),endUTF16:e.evidence.map(v=>v.span.end).join(' | '),literal:e.evidence.map(v=>v.literal).join(' | '),normativeEvidence:e.evidence.map(v=>v.normEvidence?.text||'').join(' | '),syntaxClasses:e.evidence.map(v=>v.syntaxClass).join(' | '),historicalState:e.evidence.map(v=>JSON.stringify(v.historical)).join(' | '),eligibilityReason:e.evidence.map(v=>v.verification.objectiveReason).join(' | '),evidence:e.evidence,sourceContext:e.evidence.map(v=>plain(e.source.article.paragraphs[v.paragraph])),targetContext:plain(e.target.article.paragraphs[0]),evidenceFile:'arestas.json#'+e.edgeId,decision:'',justification:'',evidenceConsulted:'',needsAdjudication:''}));
 const rejectRows=bundle.sample.records.map(r=>({recordType:'rejection',id:r.id,source:r.source.codeId,sourceScope:r.source.scope,sourceArticle:r.source.articleId,sourceSHA:r.source.editionSha256,target:'',targetScope:'',targetArticle:'',targetSHA:'',occurrenceIds:[r.id],status:r.category,paragraphs:r.span.paragraph,startUTF16:r.span.start,endUTF16:r.span.end,literal:r.literal,normativeEvidence:r.normEvidence?.text||'',syntaxClasses:'',historicalState:r.historical,eligibilityReason:r.exclusionReason+' / '+r.diagnosticReason,evidence:{span:r.span,normEvidence:r.normEvidence,qualifiers:r.qualifiers,historical:r.historical,resolution:r.resolution,exclusionReason:r.exclusionReason,diagnosticReason:r.diagnosticReason,sampling:r.sampling},sourceContext:plain(r.sourceDocument.article.paragraphs[r.span.paragraph]),targetContext:'',evidenceFile:'rejeicoes-amostra.json#'+r.id,decision:'',justification:'',evidenceConsulted:'',needsAdjudication:''}));
 const columns=Object.keys(edgeRows[0]);
 return new Map([
  ['arestas.json',JSON.stringify({...meta,edges:bundle.edges},null,2)+'\n'],
  ['arestas.csv',csv(edgeRows,columns)],
  ['rejeicoes-amostra.json',JSON.stringify({...meta,sampling:bundle.sample},null,2)+'\n'],
  ['revisao-humana.csv',csv([...edgeRows,...rejectRows],columns)]
 ]);
}
export async function generate(destination='docs/remissoes/fase-1a-2'){
 const plainBuild=await buildPackage(),corpus={collections:plainBuild.manifest.collections.map(c=>({code:JSON.parse(plainBuild.files.get(c.file)),sha256:c.sha256}))};
 const original=hash(JSON.stringify(corpus)),built=buildRemissions(corpus),bundle=auditBundle(corpus,built),files=artifacts(bundle);
 if(original!==hash(JSON.stringify(corpus)))throw Error('Audit mutated legal objects');
 if(built.bytes!==buildRemissions(corpus).bytes)throw Error('Non-deterministic experimental index');
 if(JSON.stringify([...artifacts(auditBundle(corpus,built))])!==JSON.stringify([...artifacts(bundle)]))throw Error('Non-deterministic audit');
 const protectedFiles=['scripts/remissions/grammar.mjs','scripts/remissions/norms.mjs','scripts/remissions/extract.mjs','scripts/remissions/context.mjs','scripts/remissions/graph.mjs','scripts/remissions/eligibility.mjs','scripts/build.mjs','scripts/build-pages.mjs','src/sw.js','src/pwa.js','src/reader.js'];
 const fingerprints=Object.fromEntries(await Promise.all(protectedFiles.map(async f=>[f,hash(await readFile(new URL('../../'+f,import.meta.url)))])));
 const defaultBuildHash=hash(JSON.stringify([plainBuild.html,plainBuild.manifest,[...plainBuild.files].map(([p,b])=>[p,hash(b)])]));
 const auditScripts=Object.fromEntries(await Promise.all(['checks.mjs','run.mjs'].map(async f=>[f,hash(await readFile(new URL(f,import.meta.url)))])));
 files.set('manifesto.json',JSON.stringify({auditVersion:'1a2.0',auditScripts,baseCommit:BASE,counts:bundle.counts,protectedFiles:fingerprints,defaultBuildHash,legalCorpusHash:original,files:Object.fromEntries([...files].map(([p,b])=>[p,{sha256:hash(b),bytes:Buffer.byteLength(b)}]))},null,2)+'\n');
 await mkdir(destination,{recursive:true});for(const [p,b] of files)await writeFile(resolve(destination,p),b);
 return bundle.counts;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)console.log(JSON.stringify(await generate(process.argv[2]),null,2));
