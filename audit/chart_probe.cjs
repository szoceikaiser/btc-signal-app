// Execute the actual chart merge block on an independent deliberately conflicting pair.
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'site/index.html'), 'utf8');
const start = html.indexOf('    const seen = new Set();');
const end = html.indexOf('    const markers = ', start);
if (start < 0 || end < 0) throw Error('Chart merge block not found');
const merge = new Function('sig', 'btsig', html.slice(start, end) + '\nreturn allSig;');
const live = {signals:[{ts:1000,type:'KAUF_1',price:105,tranche_pct:25,reason:'actual live'}]};
const historical = {signals:[{ts:1000,type:'KAUF_1',price:100,tranche_pct:25,reason:'historical simulation'}]};
const shown = merge(live, historical);
if (shown.length !== 1 || shown[0].price !== 100) throw Error('Expected current defect not reached');
const actualLive = JSON.parse(fs.readFileSync(path.join(root,'site/data/signals.json'),'utf8'));
const actualBT = JSON.parse(fs.readFileSync(path.join(root,'site/data/backtest_signals.json'),'utf8'));
const btByKey = new Map((actualBT.signals||[]).map(s=>[s.ts+'|'+s.type,s]));
const conflicting = (actualLive.signals||[]).filter(s=>{
  const b = btByKey.get(s.ts+'|'+s.type);
  return b && (b.price!==s.price || b.tranche_pct!==s.tranche_pct || b.reason!==s.reason);
}).map(s=>({live:s,backtest:btByKey.get(s.ts+'|'+s.type)}));
const result={finding:'F17_backtest_overrides_live_chart_marker',source:'site/index.html:389',
  controlled_case:{expected_live_price:105,shown_price:shown[0].price},
  snapshot_conflicts:conflicting,
  scope:'Code defect confirmed; actual screenshot/user session and current remote page were not inspected'};
fs.writeFileSync(path.join(root,'docs/audit-2026-09-27/chart-gegenprobe.json'),JSON.stringify(result,null,2)+'\n');
console.log('Live-price override:',shown[0].price,'instead of 105; saved snapshot conflicts:',conflicting.length);
