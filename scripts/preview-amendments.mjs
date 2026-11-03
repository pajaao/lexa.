import {stagePages} from './build-pages.mjs';
import {fileURLToPath} from 'node:url';
process.env.LEXA_SERVE_DIR=fileURLToPath(new URL('../test-results/amendments-preview/',import.meta.url));
await stagePages(process.env.LEXA_SERVE_DIR,{amendmentsCandidate:true});
process.env.LEXA_LOCAL_PREVIEW='1';process.env.PORT||='3044';
console.log('Base candidata local de ECs: publicação não autorizada.');
await import('./server.mjs');
