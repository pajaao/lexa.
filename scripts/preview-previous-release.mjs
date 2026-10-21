import {stagePages} from './build-pages.mjs';
import {fileURLToPath} from 'node:url';
process.env.LEXA_SERVE_DIR=fileURLToPath(new URL('../test-results/previous-wordings-release/site/',import.meta.url));
await stagePages(process.env.LEXA_SERVE_DIR,{previousWordingsCandidate:true});
process.env.LEXA_LOCAL_PREVIEW='1';
process.env.PORT||='3013';
console.log('Candidata local de Redações anteriores, PWA ativa; publicação bloqueada.');
await import('./server.mjs');
