// Read-only comparison: verified TLS, IPv4, no redirects, bounded body/time.
import https from 'node:https';
import tls from 'node:tls';

const url = 'https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm';
const agent = new https.Agent({keepAlive: false, rejectUnauthorized: true, checkServerIdentity: tls.checkServerIdentity});
const result = await new Promise(resolve => {
  let done = false;
  const finish = value => { if (!done) { done = true; clearTimeout(timer); resolve(value); } };
  const request = https.get(url, {agent, family: 4, rejectUnauthorized: true, headers: {
    'User-Agent': 'Mozilla/5.0 (compatible; Lexa/0.1; public legislation research)',
    Accept: 'text/html,application/xhtml+xml', 'Accept-Encoding': 'identity'
  }}, response => {
    let bytes = 0;
    const prefix = [];
    const record = {client: 'node-https', node: process.versions.node, openssl: process.versions.openssl,
      status: response.statusCode, remote_ip: response.socket.remoteAddress, tls_valid: response.socket.authorized,
      tls_protocol: response.socket.getProtocol(), cipher: response.socket.getCipher()?.standardName,
      http_version: response.httpVersion, server: response.headers.server, content_type: response.headers['content-type']};
    if (response.headers.location) {
      const destination = new URL(response.headers.location, url);
      record.redirect = destination.origin + destination.pathname;
    }
    response.on('data', chunk => {
      const before = bytes;
      bytes += chunk.length;
      if (before < 8192) prefix.push(chunk.subarray(0, 8192 - before));
      if (bytes > 12 * 1024 * 1024) {
        request.destroy(); finish({...record, error: 'size_limit'});
      }
    });
    response.on('end', () => finish({...record, bytes, sample: Buffer.concat(prefix).toString('latin1')
      .replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, '')
      .replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').slice(0, 600)}));
    response.on('error', error => finish({...record, error: error.code || 'response_failed'}));
  });
  const timer = setTimeout(() => { request.destroy(); finish({client: 'node-https', error: 'timeout'}); }, 25000);
  request.on('error', error => finish({client: 'node-https', error: error.code || 'connection_failed'}));
});
agent.destroy();
console.log(JSON.stringify(result));
