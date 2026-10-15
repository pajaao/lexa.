import { readFile, writeFile } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
const [template, css, content, data, app] = await Promise.all([
  'scripts/index.template.html', 'style.css', 'content.js', 'data.js', 'app.js'
].map(path => readFile(new URL(path, root), 'utf8')));
const javascript = [content, data, app].map(source => source.replace(/^export /gm, '').replace(/^import .*?;\n/gm, '')).join('\n');
if (/<\/script/i.test(javascript) || /<\/style/i.test(css)) throw new Error('Conteúdo incompatível com incorporação HTML');
const html = template.replace('<link rel="stylesheet" href="/style.css">', () => `<style>${css}</style>`)
  .replace('<script type="module" src="/app.js"></script>', () => `<script>${javascript}</script>`);
await writeFile(new URL('index.html', root), html);
console.log('index.html gerado: estilos, dados e aplicação incorporados.');
