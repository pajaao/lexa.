import {performance} from 'node:perf_hooks';
import {extractRemissions,sha256} from './extract.mjs';
import {applyEligibility,POLICY} from './eligibility.mjs';
import {relationGraph} from './graph.mjs';
import {INDEX_SCHEMA,legalEditions} from '../../src/optional/remissions-contract.js';
export function buildRemissions(corpus,{policy=POLICY,extract=extractRemissions}={}){
 if(policy.mode!=='experimental-only')throw Error('Public activation requires separate approval.');
 const t0=performance.now(),extraction=extract(corpus),t1=performance.now(),eligibility=applyEligibility(corpus,extraction,{policy}),t2=performance.now();
 const editions=legalEditions(corpus.collections.map(c=>({...c.code,sha256:c.sha256}))),ci=id=>editions.findIndex(([code])=>code===id);
 const legalEditionSetSha256=sha256(JSON.stringify(editions));
 const extractor={version:extraction.rules.version,sha256:extraction.rules.sha256,editionSetSha256:extraction.editionSetSha256};
 const policySpec={version:policy.version,sha256:policy.sha256,mode:policy.mode,classes:[...policy.classes]};
 const generationSha256=sha256(JSON.stringify({schema:INDEX_SCHEMA,legalEditionSetSha256,extractor,policy:policySpec}));
 const graph=relationGraph({...extraction,occurrences:eligibility.accepted});
 const index={schema:INDEX_SCHEMA,provenance:{field:'paragraphs',offsetUnit:'utf16'},mode:'experimental-only',legalEditionSetSha256,extractor,policy:policySpec,generationSha256,editions,
  occurrences:eligibility.accepted.map(o=>[o.id,ci(o.source.codeId),o.source.articleId,o.location.paragraph,o.location.start,o.location.end,o.syntaxClass,o.kind,o.qualifiers.map(q=>[q.start,q.end]),o.normEvidence?[o.normEvidence.start,o.normEvidence.end]:null]),
  edges:graph.edges.map(e=>[ci(e.source[0]),e.source[1],ci(e.target[0]),e.target[1],e.occurrences]),incoming:graph.incoming};
 const bytes=JSON.stringify(index),t3=performance.now();
 const audit={schema:1,extractor,policy:policySpec,legalEditionSetSha256,generationSha256,candidates:extraction.occurrences.length,eligibleOccurrences:eligibility.accepted.length,edges:index.edges.length,rejections:eligibility.rejections,decisions:eligibility.decisions,occurrences:extraction.occurrences,timingsMs:{extraction:t1-t0,eligibility:t2-t1,graphAndSerialization:t3-t2}};
 return {index,bytes,audit,descriptor:{schema:INDEX_SCHEMA,legalEditionSetSha256,extractor,policy:policySpec,generationSha256,mode:'experimental-only'}};
}
