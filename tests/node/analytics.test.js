import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const html = await readFile(new URL('../../dist/index.html', import.meta.url), 'utf8');
const loader = html.match(/<script type="module">\s*(if \(location\.origin[\s\S]*?)<\/script>/)?.[1];

test('analytics somente na publicação, sem duplicações nem tráfego local', () => {
  assert.ok(loader, 'loader presente no HTML final');
  for (const [origin, pathname, expected] of [
    ['https://pajaao.github.io', '/lexa./', 1],
    ['http://127.0.0.1:4317', '/', 0],
    ['http://localhost:4317', '/lexa./', 0],
    ['https://preview.vercel.app', '/', 0],
    ['https://pajaao.github.io', '/outro/', 0],
  ]) {
    const scripts = [];
    const context = {location: {origin, pathname}, document: {
      querySelector: () => scripts[0],
      createElement: () => ({setAttribute(key, value) {this[key] = value;}}),
      head: {append: node => scripts.push(node)},
    }};
    vm.runInNewContext(loader, context);
    vm.runInNewContext(loader, context);
    assert.equal(scripts.length, expected);
    if (expected) {
      assert.equal(scripts[0].type, 'module');
      assert.equal(scripts[0].src, 'https://static.cloudflareinsights.com/beacon.min.js');
      assert.equal(JSON.parse(scripts[0]['data-cf-beacon']).token, 'ce56a8770f484f11a8af59f3d85f481a');
    }
  }
});
