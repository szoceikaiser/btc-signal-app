'use strict';
const fs=require('fs'), path=require('path'), vm=require('vm'), assert=require('assert');
const root=path.resolve(__dirname,'..');
let code=fs.readFileSync(path.join(root,'site/chart_signals.js'),'utf8');
const mutations = [
  ['source erased',"canonical([source, explicit ? supplied : null, payload])","canonical(['all', explicit ? supplied : null, payload])",'origins'],
  ['legacy duplicates lost','if (explicit && n > 0) return;','if (n > 0) return;','legacy_duplicates'],
  ['explicit repeats retained','if (explicit && n > 0) return;','if (false) return;','explicit_repeat'],
  ['ID conflict hidden','record.collision = true','record.collision = false','id_collision'],
  ['content removed','const payload = canonical(raw);',"const payload = canonical([raw.ts,raw.type]);",'id_collision'],
  ['ID source ignored','const supplied = raw.signal_id ?? raw.id;','const supplied = null;','explicit_repeat'],
  ['order unsorted','a.ts-b.ts || sources[a.source].rank-sources[b.source].rank ||','0 ||','sort'],
  ['unstable identity',"const chart_id = 'chart-v1:' + base", "const chart_id = 'chart-v1:' + Math.random() + base",'reload'],
  ['V1 reference time','raw.fill_at,raw.fill_price','raw.candle_id,raw.fill_price','v1'],
  ['V1 reference price','raw.fill_at,raw.fill_price','raw.fill_at,raw.reference_price','v1'],
  ['rejections shown',"raw.status === 'filled'","raw.status !== 'ignored'",'v1'],
  ['unknown model accepted',"execution.model !== 'V1_close_to_next_open_zero_latency'",'false','unknown_model'],
  ['marker origin erased',"sources[s.source].short + (s.collision", "'' + (s.collision",'markers'],
  ['HTML injection','row.textContent = when','row.innerHTML = when','safe_list'],
  ['invalid time accepted','ts > 8640000000000000','false','invalid'],
  ['sequence ignored','a.sequence-b.sequence','0','sequence'],
];
if (process.argv[2]==='--mutant') {
  const m=mutations[Number(process.argv[3])]; assert(code.includes(m[1]),m[0]);
  code=code.replace(m[1],m[2]);
}
const context={module:{exports:{}},globalThis:{}}; vm.runInNewContext(code,context);
const api=context.module.exports;
const s=(price=105,extra={})=>({ts:1000,type:'KAUF_1',price,tranche_pct:25,reason:'live',...extra});
const data=(...signals)=>({signals});
const json=x=>JSON.stringify(x);
const equal=(a,b)=>assert.strictEqual(json(a),json(b));
const candles=[{time:0},{time:2}];
const snap=(ts,cs)=>{let t=null;for(const c of cs) if(c.time<=ts)t=c.time;return t;};
const styles={KAUF_1:{c:'green',s:'arrowUp',p:'belowBar',t:'K1'}};
function dom() {
  const elements={};
  function element() {return {children:[],textContent:'',hidden:false,checked:false,
    appendChild(x){this.children.push(x);},replaceChildren(){this.children=[];},
    set innerHTML(v){throw Error('Unsafe HTML write: '+v);}};}
  return {createElement:element,getElementById(id){return elements[id]||(elements[id]=element());}};
}
const tests={
  origins(){const r=api.merge(data(s(105,{id:'same'})),data(s(105,{id:'same'})));assert.strictEqual(r.records.length,2);assert.notStrictEqual(r.records[0].chart_id,r.records[1].chart_id);},
  conflict(){const r=api.merge(data(s()),data(s(100)));equal(r.records.map(x=>x.price),[105,100]);},
  same_bar(){const r=api.merge(data(s(),s(110),s(105,{reason:'second'})),data());assert.strictEqual(r.records.length,3);assert.strictEqual(new Set(r.records.map(x=>x.chart_id)).size,3);},
  legacy_duplicates(){const r=api.merge(data(s(),s()),data());assert.strictEqual(r.records.length,2);assert.notStrictEqual(r.records[0].chart_id,r.records[1].chart_id);assert(r.records.every(x=>x.legacy));},
  explicit_repeat(){const r=api.merge(data(s(105,{id:'one'}),s(105,{id:'one'}),s(105,{id:'two'})),data());assert.strictEqual(r.records.length,2);assert(r.records.every(x=>!x.legacy));},
  id_collision(){const r=api.merge(data(s(105,{signal_id:'same'}),s(100,{signal_id:'same'})),data());assert.strictEqual(r.records.length,2);assert(r.records.every(x=>x.collision));},
  reload(){const a=data(s(),s(110),s(105,{reason:'second'}));const r=api.merge(a,data());equal(api.merge(JSON.parse(json(a)),data()),r);equal(api.merge(data(...a.signals.slice().reverse()),data()),r);const extended=api.merge(data(s(90),...a.signals),data());assert(r.records.every(x=>extended.records.some(y=>y.chart_id===x.chart_id)));const child=require('child_process').execFileSync(process.execPath,['-e',`const a=require(${JSON.stringify(path.join(root,'site/chart_signals.js'))}); console.log(JSON.stringify(a.merge(${json(a)},{signals:[]})))`],{encoding:'utf8'});equal(JSON.parse(child),r);},
  sort(){const r=api.merge(data(s(105,{ts:4000}),s()),data(s(90,{ts:2000}),s(100)));equal(r.records.map(x=>[x.ts,x.source]),[[1000,'live_reference'],[1000,'historical_signal_band'],[2000,'historical_signal_band'],[4000,'live_reference']]);},
  sequence(){const r=api.merge(data(s(105,{sequence:2,id:'a'}),s(105,{sequence:1,id:'z'})),data());equal(r.records.map(x=>x.sequence),[1,2]);},
  v1(){const e={id:'fill:0',type:'KAUF_1',status:'filled',candle_id:1000,fill_at:2000,fill_price:125,reference_price:100,quantity:2};const r=api.merge(data(s()),data(),{model:'V1_close_to_next_open_zero_latency',ledger:[e,{...e,id:'reject',status:'rejected'}]});const f=r.records.find(x=>x.source==='simulated_v1_fill');assert(f);assert.strictEqual(r.records.length,2);assert.strictEqual(f.ts,2000);assert.strictEqual(f.price,125);},
  async unknown_model(){assert.strictEqual(await api.loadOptional(async()=>({status:404}),'local'),null);for(const response of [{status:500,ok:false},{status:200,ok:true,json:async()=>{throw Error('bad JSON');}}]){const v=await api.loadOptional(async()=>response,'local');assert.strictEqual(api.merge(data(),data(),v).issues.length,1);}const valid={model:'V1_close_to_next_open_zero_latency',ledger:[]};equal(await api.loadOptional(async()=>({status:200,ok:true,json:async()=>valid}),'local'),valid);const r=api.merge(data(),data(),{model:'old',ledger:[{status:'filled',fill_at:1000,fill_price:100,type:'KAUF_1'}]});assert.strictEqual(r.records.length,0);assert.strictEqual(r.issues.length,1);},
  invalid(){const r=api.merge(data(null,s(0),s(1,{ts:1e16}),s(105)),data());assert.strictEqual(r.records.length,1);assert.strictEqual(r.issues.length,3);},
  markers(){const r=api.merge(data(s(),s(110)),data(s(100)));const m=api.markers(r.records,candles,styles,snap);assert.strictEqual(m.length,3);assert(m[0].text.startsWith('L '));assert(m[2].text.startsWith('H '));assert.strictEqual(new Set(m.map(x=>x.id)).size,3);equal(m.map(x=>x.time),[0,0,0]);},
  safe_list(){const r=api.merge(data(s(105,{reason:'<img src=x onerror=alert(1)>'})),data());const d=dom(),c=d.createElement('div');api.renderList(c,r.records,[],d);const row=c.children[1].children[0];assert(row.textContent.includes('<img'));assert(row.textContent.includes('Referenzpreis 105'));assert(row.children[0].children[1].textContent.startsWith('chart-v1:'));},
  snapshot(){const live=JSON.parse(fs.readFileSync(path.join(root,'site/data/signals.json'))), historical=JSON.parse(fs.readFileSync(path.join(root,'site/data/backtest_signals.json')));const r=api.merge(live,historical);assert.strictEqual(r.records.length,live.signals.length+historical.signals.length);const baseline=JSON.parse(fs.readFileSync(path.join(root,'docs/nacharbeit-2026-09-28/5b-baseline-f17.json')));for(const pair of baseline.original_f17.conflicts){const fixed=api.merge(data(pair.live),data(pair.historical));assert.strictEqual(fixed.records.length,2);assert(fixed.records.some(x=>json(x.raw)===json(pair.live)));assert(fixed.records.some(x=>json(x.raw)===json(pair.historical)));}for(const ts of [1787716800000,1788753600000])assert(r.records.filter(x=>x.ts===ts).some(x=>x.source==='live_reference')&&r.records.filter(x=>x.ts===ts).some(x=>x.source==='historical_signal_band'));},
  async page(){const html=fs.readFileSync(path.join(root,'site/index.html'),'utf8');assert(html.includes('<script src="chart_signals.js"></script>'));const a=html.indexOf('async function load(tf)'),b=html.indexOf('// E24.3: Der Schalter',a);const document=dom();let shown=[];const sandbox={ChartSignals:{...api,renderList:(c,r,i)=>api.renderList(c,r,i,document)},document,RAW:'raw/',fetch:async()=>({status:404}),Date,Set,MARKER_STYLE:styles,snap,priceLines:[],lastBar:null,showBar(){},series:{setData(){},setMarkers(m){shown=m;}},loadCandles:async()=>candles,fetchJson:async url=>url.includes('backtest_signals')?data(s(100)):url.includes('signals.json')?data(s()):null};vm.createContext(sandbox);vm.runInContext(html.slice(a,b),sandbox);await sandbox.load('4h');assert.strictEqual(shown.length,2);assert(shown.some(m=>m.text==='L K1 105'));assert(shown.some(m=>m.text==='H K1 100'));assert(document.getElementById('signalList').children[1].children.length===2);assert(!document.getElementById('status').textContent.startsWith('Fehler'));},
};
(async()=>{
  if(process.argv[2]==='--sabotage') {
    const child=require('child_process'), results=[];
    for(let i=0;i<mutations.length;i++) {const m=mutations[i];await tests[m[3]]();const p=child.spawnSync(process.execPath,[__filename,'--mutant',String(i),m[3]],{encoding:'utf8'});assert(p.status!==0,m[0]);assert(!p.stderr.includes('SyntaxError'),m[0]);results.push({name:m[0],reached_baseline:true,caught:true});}
    console.log(JSON.stringify({passed:results.length,total:mutations.length,results},null,2));
  } else {const name=process.argv[2]==='--mutant'?process.argv[4]:process.argv[2];if(name){await tests[name]();console.log('PASS '+name);}else {for(const [n,f]of Object.entries(tests)){await f();console.log('PASS '+n);}}}
})().catch(e=>{console.error(e);process.exit(1);});
