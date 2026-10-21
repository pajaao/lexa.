import {stagePages} from './build-pages.mjs';
import {fileURLToPath} from 'node:url';
// The preview lives in ignored test artifacts, never in the publishable dist.
process.env.LEXA_SERVE_DIR=fileURLToPath(new URL('../test-results/legislative-history-demo/',import.meta.url));
await stagePages(process.env.LEXA_SERVE_DIR,{legislativeHistoryDemo:!process.argv.includes('--pilot')&&!process.argv.includes('--simple'),legislativeHistoryPilot:process.argv.includes('--pilot'),legislativeHistorySimple:process.argv.includes('--simple')});
process.env.LEXA_LOCAL_PREVIEW='1';
process.env.PORT ||= '3001';
console.log(process.argv.includes('--simple')?'Prévia HTML simplificada: abra /#/penal/215. Não autorizado para publicação.':process.argv.includes('--pilot')?'Piloto documental local: abra /#/penal/215. Não autorizado para publicação.':'Demonstração fictícia: abra /#/penal/1.');
await import('./server.mjs');
