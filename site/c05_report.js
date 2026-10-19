/* Frozen accepted books only. Values are displayed, never resimulated. */
(function(root) {
  'use strict';
  const REPORT_SHA = '6d64486e83917a01976296c4688fb019f6c56d6d66a0f9862df36041cafb6f19';
  const CORE_SHA = '20d755a4332fb32aeab08b1973b650eeae10f31e';
  const CONFIG_SHA = '3efe8a17330c228a75fe879d4e7c7ed0cade766e4a07ca0c05832b88aa3d282b';
  const STRATEGY_SHA = 'a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787';
  async function load(fetcher, crypto, pkg) {
    const m = pkg.manifest, pin = m.renderer;
    if (!pin || pin.schema !== 'btc-c05-renderer-v1' || !/^[0-9a-f]{40}$/.test(pin.code_sha) ||
        pin.core_code_sha !== CORE_SHA || pin.runtime_config_sha256 !== CONFIG_SHA ||
        pin.strategy_sha256 !== STRATEGY_SHA || pin.report_sha256 !== REPORT_SHA ||
        pkg.value.pins.code_sha !== CORE_SHA || pkg.value.pins.config_sha256 !== CONFIG_SHA ||
        m.report?.path !== 'c05-report.json' || m.report.sha256 !== REPORT_SHA)
      throw Error('C05-Bericht und Webseitenstand passen nicht zusammen');
    const response = await fetcher('c05-report.json', {cache:'no-store'});
    if (!response.ok) throw Error('Geprüfter C05-Bericht fehlt');
    const reader = response.body.getReader(), chunks = []; let size = 0;
    for (;;) {
      const item = await reader.read(); if (item.done) break;
      size += item.value.length;
      if (size > 128*1024) { await reader.cancel(); throw Error('C05-Bericht zu groß'); }
      chunks.push(item.value);
    }
    const raw = new Uint8Array(size); let offset=0;
    for (const part of chunks) { raw.set(part,offset); offset+=part.length; }
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)))
      .map(x=>x.toString(16).padStart(2,'0')).join('');
    if (hash !== REPORT_SHA) throw Error('C05-Bericht wurde verändert');
    const r = JSON.parse(new TextDecoder().decode(raw));
    if (r.schema !== 'btc-c05-historical-report-v1' || r.currency !== 'USD' ||
        r.strategy_sha256 !== STRATEGY_SHA || r.runtime_config_sha256 !== CONFIG_SHA)
      throw Error('Fremder C05-Bericht');
    return r;
  }
  const money = v => v.toLocaleString('de-DE',{minimumFractionDigits:2,maximumFractionDigits:2});
  const pct = v => (v>=0?'+':'')+money(v)+' %';
  function render(el,r) {
    el.innerHTML = `<div class="c05-heading"><div><span class="c05-eyebrow">GEPRÜFTE HISTORISCHE MODELLRECHNUNG</span>
      <h2>C05 · Basisszenario S0</h2><p>18.01.2026, 20:00 UTC – 04.10.2026, 08:00 UTC</p></div>
      <div class="c05-return">${pct(r.base_return_pct)}<small>im geprüften Zeitraum</small></div></div>
      <div class="c05-value">10.000,00 USD <span>→</span> <strong>${money(r.base_end_usd)} USD</strong></div>
      <p>Start ohne BTC · Gebühren enthalten: ${money(r.base_fees_usd)} USD · Offene BTC im Endwert enthalten</p>
      <p class="c05-notice">Historische Simulation, kein Live-Konto und keine Rechnung bis heute.
      Die fortgeführte 75-%-Live-Signalreferenz und die Telegram-Planpreise gehören zur laufenden Projektion und gehen nicht in diese Rendite ein.</p>
      <details id="c05-details"><summary>10 Monatsstände und 5 Ausführungsannahmen ansehen</summary>
      <h3>Monat für Monat · C05 / S0</h3><div class="c05-scroll"><table>
      <thead><tr><th>Monat</th><th>Endwert USD</th><th>Änderung USD</th><th>Rendite</th></tr></thead><tbody>
      ${r.months.map(m=>`<tr><td>${m.month}${m.partial_month?' *':''}</td><td>${money(m.end_usd)}</td>
      <td>${money(m.change_usd)}</td><td class="${m.return_pct>=0?'c05-up':'c05-down'}">${pct(m.return_pct)}</td></tr>`).join('')}
      </tbody></table></div><p class="c05-note">* Januar und Oktober sind Teilmonate. Monatsrenditen sind geometrisch verkettet, nicht addiert.
      Der Endwert umfasst ${money(r.base_final_cash_usd)} USD Cash und ${r.base_final_btc.toLocaleString('de-DE',{maximumFractionDigits:10})} BTC
      (Bewertung: ${money(r.base_final_btc_value_usd)} USD).</p>
      <h3>Andere geprüfte Ausführungsannahmen</h3><div class="c05-scroll"><table>
      <thead><tr><th>Modell</th><th>Endwert USD</th><th>Rendite</th><th>4h-Open-Versatz</th><th>Slippage / Fill</th></tr></thead><tbody>
      ${r.scenarios.map(s=>`<tr><td>${s.id}</td><td>${money(s.end_usd)}</td><td>${pct(s.return_pct)}</td>
      <td>i + ${s.assumptions.next_open_offset}</td><td>${money(s.assumptions.slippage_pct)} %</td></tr>`).join('')}
      </tbody></table></div><p class="c05-note">Alle Szenarien: 0,1 % Gebühr je Fill. S0: nächstes 4h-Open, kein Slippage-Aufschlag.
      S1–S4 sind andere Ausführungsannahmen, keine prognostische Renditespanne.</p>
      <p class="c05-note">Bereits unabhängig geprüfte Rechenbücher; kein neuer Strategielauf. Historische Datenlücken und Missing-Gates bleiben erhalten.
      Fehlende historische Liquidationen wurden nicht ergänzt. H/V1 im Chart bleiben der separate alte Core20D-Stand und sind keine C05-Marken.</p>
      <p class="c05-note">C05: Pivot 6 · CVD USD · Long an · Short aus.
      <a href="c05-report.json">Geprüfte Berichtsdaten (USD)</a> · Datenende 04.10.2026, 08:00 UTC.</p></details>`;
  }
  async function mount(el,fetcher,crypto,packagePromise) {
    try { render(el,await load(fetcher,crypto,await packagePromise)); }
    catch(e) { el.textContent = 'C05-Bericht nicht verfügbar: '+e.message; }
  }
  const api = {load,render,mount};
  if (typeof module === 'object' && module.exports) module.exports=api;
  else root.C05Report=api;
})(typeof globalThis === 'object'?globalThis:this);
