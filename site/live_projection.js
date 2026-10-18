/* One authenticated-by-hash Pages package; never fall back to legacy live files. */
(function (root) {
  'use strict';
  async function bytes(fetcher, path, limit) {
    const r = await fetcher(path, {cache:'no-store'});
    if (!r.ok) throw Error('Bestätigte Projektion fehlt');
    const reader = r.body.getReader(), chunks = [];
    let size = 0;
    for (;;) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.length;
      if (size > limit) { await reader.cancel(); throw Error('Projektion zu groß'); }
      chunks.push(part.value);
    }
    const out = new Uint8Array(size); let offset = 0;
    for (const chunk of chunks) { out.set(chunk, offset); offset += chunk.length; }
    return out;
  }
  async function verified(fetcher, crypto, item, limit) {
    const raw = await bytes(fetcher, item.path, limit);
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)))
      .map(x => x.toString(16).padStart(2,'0')).join('');
    if (hash !== item.sha256) throw Error('Webseitenstand uneinheitlich');
    return JSON.parse(new TextDecoder().decode(raw));
  }
  async function load(fetcher, crypto, now = Date.now()) {
    const manifest = JSON.parse(new TextDecoder().decode(await bytes(fetcher, 'projection-manifest.json', 16384)));
    if (manifest.schema !== 'btc-pages-manifest-v1' || !/^[0-9a-f]{64}$/.test(manifest.sha256) ||
        manifest.projection !== 'projection-'+manifest.sha256+'.json') throw Error('Unbekannter Webseitenstand');
    const value = await verified(fetcher, crypto, {path:manifest.projection, sha256:manifest.sha256}, 750*1024);
    if (value.schema !== 'btc-public-projection-v1' ||
        JSON.stringify(value.pins) !== JSON.stringify(manifest.pins) ||
        !Number.isFinite(value.observed_ms) || !Number.isFinite(value.signal_asof_ms) ||
        !value.state || !Array.isArray(value.signals?.signals)) throw Error('Projektion nicht zusammengehörig');
    const stale = now-value.observed_ms > 45*60*1000 || now-(value.signal_asof_ms+4*3600000) > 8*3600000 || now < value.observed_ms;
    return {value, manifest, stale};
  }
  async function history(fetcher, crypto, packageData, name) {
    const item = packageData.manifest.history[name];
    if (!item) return null;
    if (!['backtest.json','backtest_signals.json','execution_v1.json'].includes(name) ||
        item.path !== 'history/'+name || !/^[0-9a-f]{64}$/.test(item.sha256) ||
        item.source_code_sha !== packageData.value.pins.code_sha) throw Error('Historischer Stand uneinheitlich');
    return verified(fetcher, crypto, item, 16*1024*1024);
  }
  const api = {load, history};
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.LiveProjection = api;
})(typeof globalThis === 'object' ? globalThis : this);
