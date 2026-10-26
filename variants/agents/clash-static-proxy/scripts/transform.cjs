'use strict';

// Pure transformations. Credentials enter only via caller-provided data.
function transform(config, entries) {
  config = JSON.parse(JSON.stringify(config));
  const proxies = config.proxies || (config.proxies = []);
  const groups = config['proxy-groups'] || (config['proxy-groups'] = []);
  const names = new Set();
  for (const e of entries) {
    const n = e.node;
    if (!n || !['socks5', 'http'].includes(n.type) || !n.name || !n.server ||
        !Number.isInteger(n.port) || n.port < 1 || n.port > 65535) throw Error('Invalid proxy input');
    if (names.has(n.name)) throw Error('Duplicate managed name');
    names.add(n.name);
    if (groups.some(g => g.name === n.name)) throw Error('Proxy name collides with group');
    const matches = proxies.filter(p => p.name === n.name);
    if (matches.length > 1 || matches.some(p => p.type !== n.type)) throw Error('Conflicting proxy definition');
  }
  const upstreamNames = new Set(entries.filter(e => !e.direct).map(e => `🔗 ${e.node.name} 上游`));
  for (const e of entries) {
    const node = { ...e.node };
    if (node.type === 'socks5' && node.udp === undefined) node.udp = true;
    if (e.direct) delete node['dialer-proxy'];
    else node['dialer-proxy'] = `🔗 ${node.name} 上游`;
    const idx = proxies.findIndex(p => p.name === node.name);
    if (idx < 0) proxies.push(node); else proxies[idx] = node;
  }
  const physical = proxies.filter(p => !names.has(p.name) && !p['dialer-proxy'] &&
    !['direct', 'reject', 'dns'].includes(p.type)).map(p => p.name);
  for (const e of entries.filter(e => !e.direct)) {
    const name = `🔗 ${e.node.name} 上游`;
    if (proxies.some(p => p.name === name)) throw Error('Upstream name collides with proxy');
    if (!physical.length) throw Error('No physical upstream available');
    const existing = groups.find(g => g.name === name);
    if (existing && (existing.type !== 'select' ||
        (existing.proxies || []).some(p => !physical.includes(p)))) throw Error('Existing upstream requires manual migration');
    const preferred = physical.includes(e.preferred) ? e.preferred : physical[0];
    const candidates = [preferred, ...physical.filter(p => p !== preferred)];
    if (existing) existing.proxies = candidates;
    else groups.push({ name, type: 'select', proxies: candidates });
  }
  for (const g of groups) {
    if (upstreamNames.has(g.name)) continue;
    // Other independently managed upstream groups must never gain a chain node.
    if (/^🔗 .+ 上游$/.test(g.name)) continue;
    if (g.type === 'relay') throw Error('Relay group requires manual routing decision');
    if (g.proxies !== undefined && !Array.isArray(g.proxies)) throw Error('Invalid group members');
    g.proxies = [...(g.proxies || []).filter(n => !names.has(n)), ...names];
  }
  return config;
}

const START = '// BEGIN CLASH STATIC PROXY MANAGED V1';
const END = '// END CLASH STATIC PROXY MANAGED V1';
const DATA = '// STATIC_PROXY_ENTRIES ';
function buildEnhancer(existing, incoming) {
  let base = existing;
  let previous = [];
  const start = existing.indexOf(START);
  if (start >= 0) {
    const end = existing.indexOf(END, start);
    if (end < 0 || existing.slice(end + END.length).trim()) throw Error('Managed block is malformed or not last');
    const line = existing.slice(start, end).split('\n').find(l => l.startsWith(DATA));
    if (!line) throw Error('Missing managed entries');
    previous = JSON.parse(line.slice(DATA.length));
    base = existing.slice(0, start).trimEnd();
  }
  const entries = new Map(previous.map(e => [e.node.name, e]));
  for (const e of incoming) entries.set(e.node.name, e);
  const data = JSON.stringify([...entries.values()]);
  if (!base.trim()) base = 'function main(config) { return config; }';
  return base + '\n\n' + START + '\n' + DATA + data + '\n' +
    ';main = (function(original) {\n' +
    '  const apply = ' + transform.toString() + ';\n' +
    '  const entries = ' + data + ';\n' +
    '  return function(config, profileName) {\n' +
    '    const result = original(config, profileName);\n' +
    '    if (!result || typeof result !== "object" || typeof result.then === "function") throw Error("Unsupported original main result");\n' +
    '    return apply(result, entries);\n' +
    '  };\n' +
    '})(main);\n' + END + '\n';
}

module.exports = { transform, buildEnhancer };
