import {stagePages} from './build-pages.mjs';
import {fileURLToPath} from 'node:url';
// The preview lives in ignored test artifacts, never in the publishable dist.
process.env.LEXA_SERVE_DIR=fileURLToPath(new URL('../test-results/legislative-history-demo/',import.meta.url));
await stagePages(process.env.LEXA_SERVE_DIR,{legislativeHistoryDemo:true});
process.env.LEXA_LOCAL_PREVIEW='1';
process.env.PORT ||= '3001';
console.log('Demonstração fictícia: abra /#/penal/1 e selecione Histórico do artigo.');
await import('./server.mjs');
