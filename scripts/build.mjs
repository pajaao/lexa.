import { readFile, writeFile } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
const [template, css, content, official, data, app] = await Promise.all([
  'scripts/index.template.html', 'style.css', 'content.js', 'official-content.js', 'data.js', 'app.js'
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
const embedded = `const imported = ${JSON.stringify(archivedData)};\nconst officialImported = ${JSON.stringify(officialData)};`;
const javascript = [embedded, data, app].map(source => source.replace(/^export /gm, '').replace(/^import .*?;\n/gm, '')).join('\n');
if (/<\/script/i.test(javascript) || /<\/style/i.test(css)) throw new Error('Conteúdo incompatível com incorporação HTML');
const html = template.replace('<link rel="stylesheet" href="/style.css">', () => `<style>${css}</style>`)
  .replace('<script type="module" src="/app.js"></script>', () => `<script>${javascript}</script>`);
await writeFile(new URL('index.html', root), html);
console.log('index.html gerado: estilos, dados e aplicação incorporados.');
