/* F17: read-only projection. Chart IDs never prove delivery or broker execution. */
(function (root) {
  'use strict';
  const sources = {
    live_reference: {rank:0, short:'L', label:'Live-Signalreferenz (kein belegter Fill)'},
    historical_signal_band: {rank:1, short:'H', label:'Historische Signalband-Diagnostik'},
    simulated_v1_fill: {rank:2, short:'V1', label:'Simulierter V1-Fill (kein Brokerbeleg)'},
  };
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).sort()
      .map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
    return JSON.stringify(value);
  }
  const compareText = (a,b) => a < b ? -1 : a > b ? 1 : 0;
  const number = x => typeof x === 'number' && Number.isFinite(x);
  async function loadOptional(fetcher,url) {
    try {
      const response = await fetcher(url,{cache:'no-store'});
      if (response.status === 404) return null;
      if (!response.ok) throw Error('Unavailable V1 result');
      const value = await response.json();
      return value || {model:'invalid'};
    } catch (_) { return {model:'unreadable'}; }
  }
  function merge(live, historical, execution) {
    const records = [], issues = [], groups = new Map(), occurrences = new Map();
    function add(raw, source, ts, price) {
      if (!raw || !number(ts) || ts < 0 || ts > 8640000000000000 || !number(price) || price <= 0 ||
          typeof raw.type !== 'string' || !raw.type) {
        issues.push(source + ': ungültige Ereigniszeile'); return;
      }
      const payload = canonical(raw);
      const supplied = raw.signal_id ?? raw.id;
      const explicit = typeof supplied === 'string' && supplied.length > 0;
      const base = canonical([source, explicit ? supplied : null, payload]);
      const n = occurrences.get(base) || 0;
      occurrences.set(base,n+1);
      if (explicit && n > 0) return; // Only exact repeats of an explicit source ID.
      const chart_id = 'chart-v1:' + base + ':' + (explicit ? 0 : n);
      const record = {raw, source, ts, price, chart_id, source_id:explicit ? supplied : null,
        legacy:!explicit, collision:false, sequence:number(raw.sequence) ? raw.sequence : 0};
      records.push(record);
      if (explicit) {
        const key = canonical([source,supplied]);
        if (!groups.has(key)) groups.set(key,[]);
        groups.get(key).push(record);
      }
    }
    for (const [data,source] of [[live,'live_reference'],[historical,'historical_signal_band']]) {
      if (data && !Array.isArray(data.signals)) issues.push(source + ': Signalliste fehlt');
      for (const raw of (data && Array.isArray(data.signals) ? data.signals : []))
        add(raw,source,raw && raw.ts,raw && raw.price);
    }
    if (execution) {
      if (execution.model !== 'V1_close_to_next_open_zero_latency' || !Array.isArray(execution.ledger))
        issues.push('V1: unbekanntes Modell oder fehlendes Ledger');
      else for (const raw of execution.ledger) {
        if (raw && raw.status === 'filled') add(raw,'simulated_v1_fill',raw.fill_at,raw.fill_price);
      }
    }
    for (const group of groups.values()) if (group.length > 1)
      for (const record of group) record.collision = true;
    records.sort((a,b) => a.ts-b.ts || sources[a.source].rank-sources[b.source].rank ||
      a.sequence-b.sequence || compareText(a.chart_id,b.chart_id));
    return {records,issues};
  }
  function markers(records,candles,styles,snap) {
    return records.map(s => {
      const time = snap(s.ts/1000,candles);
      if (time === null) return null;
      const st = styles[s.raw.type] || {c:'#8b94a7',s:'circle',p:'aboveBar',t:'?'};
      const flush = s.raw.tag === 'FLUSH';
      return {id:s.chart_id,time,position:st.p,shape:st.s,color:flush ? '#a855f7' : st.c,
        text:sources[s.source].short + (s.collision ? ' !' : '') + ' ' +
          (flush ? '⚡' : '') + st.t + ' ' + Math.round(s.price).toLocaleString('de-DE')};
    }).filter(Boolean).sort((a,b) => a.time-b.time); // Stable order inside snapped bars.
  }
  function renderList(container,records,issues,doc) {
    doc = doc || document;
    container.replaceChildren();
    const note = doc.createElement('p');
    note.textContent = 'L = Live-Referenz · H = historische Diagnostik · V1 = Modell-Fill. ' +
      'Keine Marker-ID belegt Telegram-Zustellung oder eine manuelle/Broker-Ausführung.' +
      (issues.length ? ' Datenhinweise: ' + issues.join('; ') : '');
    container.appendChild(note);
    const list = doc.createElement('ol');
    for (const s of records) {
      const row = doc.createElement('li');
      const when = new Date(s.ts).toISOString();
      const amount = s.source === 'simulated_v1_fill' ? 'BTC ' + s.raw.quantity :
        'Tranche ' + (s.raw.tranche_pct ?? 'unbekannt') + ' %';
      row.textContent = when + ' · ' + sources[s.source].label + ' · ' + s.raw.type +
        ' · ' + (s.source === 'simulated_v1_fill' ? 'Fillpreis ' : 'Referenzpreis ') +
        s.price + ' · ' + amount + ' · ' + (s.raw.signal_reason ?? s.raw.reason ?? '') +
        (s.legacy ? ' · Altbestand: abgeleitete Chartidentität' : '') +
        (s.collision ? ' · ID-Kollision: widersprüchliche Inhalte erhalten' : '');
      const identity = doc.createElement('details');
      const title = doc.createElement('summary'); title.textContent = 'Chartidentität';
      const code = doc.createElement('code'); code.textContent = s.chart_id;
      identity.appendChild(title); identity.appendChild(code); row.appendChild(identity);
      list.appendChild(row);
    }
    container.appendChild(list);
  }
  const api = {canonical,merge,markers,renderList,loadOptional,sources};
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ChartSignals = api;
})(typeof globalThis === 'object' ? globalThis : this);
