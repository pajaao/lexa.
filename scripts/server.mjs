import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, extname, sep } from 'node:path';
const root = resolve(fileURLToPath(new URL('../dist/', import.meta.url)));
const types = { '.svg':'image/svg+xml', '.ico':'image/vnd.microsoft.icon', '.png':'image/png', '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.pdf': 'application/pdf' };
createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const path = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!path.startsWith(root + sep) || !Object.hasOwn(types, extname(path)) || (extname(path)==='.pdf' && !path.startsWith(resolve(root, 'sources')+sep))) { res.writeHead(404).end(); return; }
    const body = await readFile(path);
    res.writeHead(200, { 'Content-Type': types[extname(path)], 'X-Content-Type-Options': 'nosniff' }).end(body);
  } catch { res.writeHead(404).end('Não encontrado'); }
}).listen(Number(process.env.PORT || 3000), '0.0.0.0', () => console.log('Lexa disponível na porta ' + (process.env.PORT || 3000)));
