import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {catalog} from '../src/catalog.js';
import {imported} from '../data/archive/legislation.js';
import {officialImported} from '../data/official/legislation.js';
import {sumulas} from '../data/archive/sumulas.js';
import {officialSumulas} from '../data/official/sumulas.js';
import {updateHistory} from '../data/history/legislation.js';
import {sumulaUpdates} from '../data/history/sumulas.js';
const root=new URL('../',import.meta.url);
export const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function buildPackage({css:cssOverride}={}){
 const files=new Map();
 function asset(id,value){
  const bytes=JSON.stringify(value),sha=sha256(bytes),file=`data/${id}.${sha}.json`;
  files.set(file,bytes);return {file,sha256:sha};
 }
 const history=[...updateHistory,...sumulaUpdates];
 const norms=[...catalog.map(code=>({...code,...(officialImported[code.id]||imported[code.id])})),...(officialSumulas.length?officialSumulas:sumulas)];
 const metadata=norms.map(norm=>{
  const {articles,sections,introductions,...fields}=norm;
  return {...fields,articleCount:articles.length,...asset(norm.id,norm),changedArticleIds:[...new Set(history.filter(event=>event.codeId===norm.id).flatMap(event=>event.changes.map(change=>change.articleId)))]};
 });
 const manifest={collections:metadata,history:asset('history',history)};
 files.set('catalog.json',JSON.stringify(manifest));
 const paths=['index.html','styles.css','history.js','collection-model.js','data.js','structure.js','copy.js','library-search.js','loading.js','pwa.js','app.js'];
 const [template,originalCss,...modules]=await Promise.all(paths.map(path=>readFile(new URL('src/'+path,root),'utf8')));
 const css=cssOverride??originalCss;
 const bootstrap=`const initialCatalog=${JSON.stringify(manifest)};\nconst collections=initialCatalog.collections.map(code=>({...code,articles:[],sections:[],loaded:false}));\nconst codes=collections.filter(code=>code.kind!=='sumulas');\nconst catalog=codes;\nconst updateHistory=[];const sumulaUpdates=[];`;
 const javascript=[bootstrap,...modules].map(source=>source.replace(/^export \{[^\n]*\};?\n/gm,'').replace(/^export /gm,'').replace(/^import .*?;\n/gm,'')).join('\n');
 if(/<\/script/i.test(javascript)||/<\/style/i.test(css))throw new Error('Conteúdo incompatível com incorporação HTML');
 const html=template.replace('<link rel="stylesheet" href="./styles.css">',()=>`<style>${css}</style>`).replace('<script type="module" src="./app.js"></script>',()=>`<script>${javascript}</script>`);
 return {html,files,manifest};
}
export async function buildHtml(){return (await buildPackage()).html;}
