'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const vm=require('node:vm');
const crypto=require('node:crypto').webcrypto;
const loader=require('../site/live_projection.js');
const dir=process.argv[2];
const seen=[];
function fetcher(url) {
  seen.push(url);
  const filename=path.join(dir,url);
  if (!fs.existsSync(filename)) return Promise.resolve(new Response('',{status:404}));
  return Promise.resolve(new Response(fs.readFileSync(filename)));
}
async function main() {
  const manifest=JSON.parse(fs.readFileSync(path.join(dir,'projection-manifest.json')));
  const value=JSON.parse(fs.readFileSync(path.join(dir,manifest.projection)));
  const pkg=await loader.load(fetcher,crypto,value.observed_ms);
  assert.equal(pkg.stale,false);
  assert.equal((await loader.load(fetcher,crypto,value.observed_ms+46*60*1000)).stale,true);
  await loader.history(fetcher,crypto,pkg,'backtest.json');
  assert(!seen.some(x=>x.includes('data/')||x.includes('raw.githubusercontent')));
  let altered=async url => url===manifest.projection ? new Response('{}') : fetcher(url);
  await assert.rejects(loader.load(altered,crypto,value.observed_ms),/uneinheitlich/);
  await assert.rejects(loader.load(async ()=>new Response('',{status:404}),crypto),/fehlt/);
  // Execute the actual index loader offline, with a chart/DOM double and only
  // synthetic candles. This exercises signal markers and preview/plan lines.
  const html=fs.readFileSync(path.join(__dirname,'../site/index.html'),'utf8');
  assert(!html.includes('raw.githubusercontent') && !html.includes('data/state.json'));
  const inline=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
  const elements={};
  const element=id=>elements[id]??={id,hidden:false,checked:true,clientWidth:800,clientHeight:500,
    textContent:'',innerHTML:'',children:[],classList:{add(){}},appendChild(x){this.children.push(x)},
    replaceChildren(){this.children=[]},addEventListener(){},querySelectorAll(){return []},append(...xs){this.children.push(...xs)}};
  const series={lines:[],markers:[],setData(x){this.data=x},setMarkers(x){this.markers=x},
    createPriceLine(x){this.lines.push(x);return x},removePriceLine(){}};
  const ChartSignals=require('../site/chart_signals.js');
  const context={console,crypto,TextDecoder,Date,Math,Promise,Set,setInterval(){},
    document:{getElementById:element,createElement:()=>element('node'+Math.random())},
    localStorage:{getItem(){return null}},ResizeObserver:class {observe(){}},
    LightweightCharts:{LineStyle:{Dashed:1,Dotted:2,SparseDotted:3},createChart(){return {
      addCandlestickSeries(){return series},applyOptions(){},subscribeCrosshairMove(){},timeScale(){return {fitContent(){}}}}}},
    ChartSignals,LiveProjection:loader,fetch:async url => url.startsWith('https://data-api.binance.vision/')
      ? new Response(JSON.stringify([[value.signal_asof_ms,100,110,90,105,0]])) : fetcher(url)};
  context.ChartSignals={...ChartSignals,renderList:(container,records,issues)=>ChartSignals.renderList(container,records,issues,context.document)};
  vm.createContext(context);
  const loaded=vm.runInContext(inline,context,{timeout:1000});
  assert(loaded && typeof loaded.then==='function','Actual initial chart load exposes completion');
  let deadline;
  try {
    await Promise.race([loaded,new Promise((_,reject)=>{
      deadline=setTimeout(()=>reject(new Error('Actual chart load did not finish within 5 seconds')),5000);
    })]);
  } finally { clearTimeout(deadline); }
  assert(series.data?.length>0,'Actual chart loads candles');
  assert(!element('status').textContent.startsWith('Fehler'),element('status').textContent);
  assert(element('status').textContent.includes('Bestätigter Export'));
  assert(element('btpanel').innerHTML.includes('keine neue C05-Berechnung'));
  assert.equal(series.markers.length,pkg.value.signals.signals.filter(s=>s.ts>=value.signal_asof_ms).length);
  const plan=pkg.value.state.plan;
  if (plan?.stop?.preis) assert(series.lines.some(x=>x.price===plan.stop.preis));
  console.log('PASS Pages loader: hashes, missing/stale source, no RAW fallback, actual chart/signals/preview/history');
}
main().catch(e=>{console.error(e);process.exitCode=1});
