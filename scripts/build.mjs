import { readFile } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
export async function buildHtml() {
const [template, css, content, official, updates, history, sumulas, officialSumulas, sumulaUpdates, data, pwa, app] = await Promise.all([
  'src/index.html', 'src/styles.css', 'data/archive/legislation.js', 'data/official/legislation.js', 'data/history/legislation.js', 'src/history.js', 'data/archive/sumulas.js', 'data/official/sumulas.js', 'data/history/sumulas.js', 'src/data.js', 'src/pwa.js', 'src/app.js'
].map(path => readFile(new URL(path, root), 'utf8')));
function jsonExport(source, name) {
  const marker = `export const ${name} = `;
  const index = source.indexOf(marker);
  if (index < 0) throw new Error(`Dados ausentes: ${name}`);
  return JSON.parse(source.slice(index + marker.length).trim().replace(/;$/, ''));
}
const officialData = jsonExport(official, 'officialImported');
// Keep archived PDFs in the repository, but do not embed duplicate old text in
// previews after an official edition has replaced it for a given legislation.
const archivedData = Object.fromEntries(Object.entries(jsonExport(content, 'imported')).filter(([id])=>!officialData[id]));
const stfData=jsonExport(officialSumulas,'officialSumulas');
const embedded = `const imported = ${JSON.stringify(archivedData)};\nconst officialImported = ${JSON.stringify(officialData)};\nconst updateHistory = ${JSON.stringify(jsonExport(updates,'updateHistory'))};\nconst sumulas = ${JSON.stringify(stfData.length?[]:jsonExport(sumulas,'sumulas'))};\nconst officialSumulas = ${JSON.stringify(stfData)};\nconst sumulaUpdates = ${JSON.stringify(jsonExport(sumulaUpdates,'sumulaUpdates'))};`;
const javascript = [embedded, history, data, pwa, app].map(source => source.replace(/^export /gm, '').replace(/^import .*?;\n/gm, '')).join('\n');
if (/<\/script/i.test(javascript) || /<\/style/i.test(css)) throw new Error('Conteúdo incompatível com incorporação HTML');
const html = template.replace('<link rel="stylesheet" href="./styles.css">', () => `<style>${css}</style>`)
  .replace('<script type="module" src="./app.js"></script>', () => `<script>${javascript}</script>`);
return html;
}
