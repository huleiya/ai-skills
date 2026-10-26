const assert = require('node:assert/strict');
const vm = require('node:vm');
const { transform, buildEnhancer } = require('./transform.cjs');
const config = {
  proxies: [{ name: 'US', type: 'trojan', server: '192.0.2.1', port: 443 },
    { name: 'JP', type: 'socks5', server: '192.0.2.2', port: 1080 }],
  'proxy-groups': [{ name: '🚀 节点选择', type: 'select', proxies: ['US', 'JP'] },
    { name: '🤖 ChatGPT', type: 'select', proxies: ['🚀 节点选择'] }],
  rules: ['MATCH,🚀 节点选择'], dns: { enable: true }
};
const entry = { node: { name: 'Home', type: 'socks5', server: '192.0.2.10', port: 1080 }, preferred: 'JP' };
const original = JSON.stringify(config);
const first = transform(config, [entry]);
assert.equal(JSON.stringify(config), original);
assert.deepEqual(first.rules, config.rules);
assert.deepEqual(first.dns, config.dns);
assert.equal(first.proxies.at(-1)['dialer-proxy'], '🔗 Home 上游');
assert.equal(first.proxies.at(-1).udp, true);
assert.equal(transform(config, [{ ...entry, node: { ...entry.node, udp: false } }]).proxies.at(-1).udp, false);
assert.deepEqual(first['proxy-groups'].at(-1).proxies, ['JP', 'US']);
assert(first['proxy-groups'][0].proxies.includes('Home'));
assert(first['proxy-groups'][1].proxies.includes('Home'));
assert.deepEqual(transform(first, [entry]), first);
const changed = { ...entry, node: { ...entry.node, port: 8888 } };
const second = transform(first, [changed]);
assert.equal(second.proxies.filter(p => p.name === 'Home').length, 1);
assert.equal(second.proxies.at(-1).port, 8888);
const direct = transform(config, [{ ...entry, direct: true }]);
assert(!direct.proxies.at(-1)['dialer-proxy']);
assert.equal(direct['proxy-groups'].length, 2);
assert.throws(() => transform({ proxies: [], 'proxy-groups': [] }, [entry]), /upstream/);
assert.throws(() => transform({ ...config, 'proxy-groups': [{name:'relay',type:'relay',proxies:['US']}] }, [entry]), /Relay/);
assert.throws(() => transform(config, [{...entry,node:{...entry.node,port:0}}]), /Invalid/);
const base = 'function main(c) { c.custom = "preserved"; return c; }';
const script = buildEnhancer(base, [entry]);
const newEntry = { node: { name: 'Home2', type: 'http', server: '192.0.2.11', port: 80 }, preferred: 'US' };
const update = buildEnhancer(script, [changed, newEntry]);
assert.equal(update.split('// BEGIN CLASH STATIC PROXY MANAGED V1').length, 2);
const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(update, sandbox);
const result = sandbox.main(JSON.parse(original));
assert.equal(result.custom, 'preserved');
assert(result['proxy-groups'][0].proxies.includes('Home2'));
assert.equal(result.proxies.find(p => p.name === 'Home').port, 8888);
assert.equal(result.proxies.find(p => p.name === 'Home').udp, true);
assert.equal(result.proxies.find(p => p.name === 'Home2').udp, undefined);
for (const g of result['proxy-groups'].filter(g => g.name.startsWith('🔗'))) {
  assert(!g.proxies.some(p => ['Home', 'Home2'].includes(p)));
}
assert.equal(JSON.stringify(sandbox.main(result)), JSON.stringify(result));
assert.throws(() => buildEnhancer(script + '\nfunction later() {}', [entry]), /not last/);
console.log('PASS: idempotency, updates, upstream isolation, direct mode, script preservation, multiple nodes, input rejection');
