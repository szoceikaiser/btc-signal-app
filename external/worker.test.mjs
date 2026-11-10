// Synthetic HTTP fixtures only. No actual GitHub/Cloudflare/provider proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {check,handler,CONFIG} from './worker.mjs';
const DUE=Date.parse('2026-10-17T08:00:00Z'), NOW=DUE+200000;
const CODE='a'.repeat(40), POLICY='b'.repeat(64), HEAD='c'.repeat(40);
const YAML=`synthetic reviewed fixture code ${CODE} policy ${POLICY}`;
const HASH=Buffer.from(await webcrypto.subtle.digest('SHA-256',new TextEncoder().encode(YAML))).toString('hex');
const READY={enabled:true,workflowId:123,workflowSha256:HASH,policyBindingSha256:POLICY,codeSha:CODE};
const iso = n=>new Date(n).toISOString();
function fixtures() {
 const run={id:100,workflow_id:123,path:'.github/workflows/freshness.yml',head_branch:'main',event:'workflow_dispatch',
  run_attempt:1,head_sha:HEAD,repository:{id:1309164619,full_name:'szoceikaiser/btc-signal-app'},
  display_title:'btc-health:'+String((DUE+10000)/1000),created_at:iso(DUE+12000),status:'completed',conclusion:'success'};
 const job={run_id:100,run_attempt:1,head_sha:HEAD,name:'observe',status:'completed',conclusion:'success',
  started_at:iso(DUE+15000),completed_at:iso(DUE+45000),steps:[
   {name:'Verify checkout pin before loading code',status:'completed',conclusion:'success'},
   {name:'Read bounded candidate evidence',status:'completed',conclusion:'success'}]};
 return {list:{total_count:1,workflow_runs:[run]},jobs:{total_count:1,jobs:[job]},yaml:YAML};
}
function transport(f,change) {
 const calls=[];
 const fetchFn=async(url,options)=>{
  calls.push({url,options});
  assert.equal(options.method,'GET');assert.equal(options.redirect,'manual');
  assert.ok(!Object.keys(options.headers).some(k=>/authorization|cookie/i.test(k)));
  assert.ok(!Object.hasOwn(options,'body'));
  assert.ok(url.startsWith('https://api.github.com/repos/szoceikaiser/btc-signal-app/')||url.startsWith('https://raw.githubusercontent.com/szoceikaiser/btc-signal-app/'));
  if(change) {const override=change(url,options,calls.length);if(override)return override;}
  const raw=url.includes('raw.githubusercontent.com');
  const body=raw?f.yaml:JSON.stringify(url.includes('/jobs?')?f.jobs:f.list);
  return new Response(body,{status:200,headers:raw?{}:{'x-ratelimit-resource':'core','x-ratelimit-remaining':'59','x-ratelimit-reset':String((NOW+3600000)/1000)}});
 };
 return{calls,fetchFn};
}
async function execute(f=fixtures(),change,config=READY){const t=transport(f,change);const value=await check(config,{fetchFn:t.fetchFn,now:NOW,cryptoApi:webcrypto});return{value,calls:t.calls};}
test('disabled/unbound configuration never contacts a provider',async()=>{const r=await execute(fixtures(),null,{...CONFIG,enabled:false});assert.equal(r.value.healthy,false);assert.equal(r.calls.length,0);});
test('reviewed synthetic success requires all three exact GETs',async()=>{const r=await execute();assert.equal(r.value.healthy,true);assert.equal(r.calls.length,3);});
test('missing due slot is not hidden by a later successful run',async()=>{const f=fixtures();const r=f.list.workflow_runs[0];r.display_title='btc-health:'+String((DUE+PERIOD+10000)/1000);r.created_at=iso(DUE+PERIOD+12000);const t=transport(f);const v=await check(READY,{fetchFn:t.fetchFn,now:DUE+PERIOD+130000,cryptoApi:webcrypto});assert.equal(v.healthy,false);assert.equal(v.reason,'checker_missing');});
const PERIOD=600000;
test('latest failure cannot be filtered away',async()=>{const f=fixtures();f.list.workflow_runs[0].conclusion='failure';const r=await execute(f);assert.equal(r.value.reason,'checker_failed');assert.equal(r.calls.length,1);});
test('queued checker cannot become healthy',async()=>{const f=fixtures();Object.assign(f.list.workflow_runs[0],{status:'queued',conclusion:null});assert.equal((await execute(f)).value.reason,'checker_unfinished');});
test('attempt two is rejected',async()=>{const f=fixtures();f.list.workflow_runs[0].run_attempt=2;assert.equal((await execute(f)).value.reason,'run_identity');});
test('foreign branch/repository is rejected',async()=>{for(const key of ['head_branch','repository']){const f=fixtures();f.list.workflow_runs[0][key]=key==='head_branch'?'other':{id:1,full_name:'other/repo'};assert.equal((await execute(f)).value.reason,'run_identity');}});
test('changed workflow bytes never attest reviewed code',async()=>{const f=fixtures();f.yaml+='altered';assert.equal((await execute(f)).value.reason,'unreviewed_checker');});
test('wrong reviewed policy binding is not accepted by a matching YAML hash alone',async()=>{const r=await execute(fixtures(),null,{...READY,policyBindingSha256:'d'.repeat(64)});assert.equal(r.value.reason,'unreviewed_checker');});
test('two successful runs for the same due slot are ambiguous',async()=>{const f=fixtures();f.list.workflow_runs.push({...f.list.workflow_runs[0],id:101});f.list.total_count=2;assert.equal((await execute(f)).value.reason,'duplicate_checker');});
test('a job from another run cannot attest this checker',async()=>{const f=fixtures();f.jobs.jobs[0].run_id=101;assert.equal((await execute(f)).value.reason,'job_identity');});
test('incomplete run query is refused',async()=>{const f=fixtures();f.list.total_count=2;assert.equal((await execute(f)).value.reason,'incomplete_metadata');});
test('skipped required checker step cannot become healthy',async()=>{const f=fixtures();f.jobs.jobs[0].steps[1].conclusion='skipped';assert.equal((await execute(f)).value.reason,'checker_steps');});
test('late completion is rejected independently of success badge',async()=>{const f=fixtures();f.jobs.jobs[0].completed_at=iso(DUE+190000);assert.equal((await execute(f)).value.reason,'checker_late');});
test('quota exhaustion stops without retry or token fallback',async()=>{const r=await execute(fixtures(),()=>new Response('{}',{status:429}));assert.equal(r.value.healthy,false);assert.equal(r.calls.length,1);});
test('insufficient aggregate headroom fails closed',async()=>{const r=await execute(fixtures(),()=>new Response('{}',{headers:{'x-ratelimit-resource':'core','x-ratelimit-remaining':'1','x-ratelimit-reset':String((NOW+3600000)/1000)}}));assert.equal(r.value.reason,'quota_insufficient');assert.equal(r.calls.length,1);});
test('oversized response is bounded',async()=>{const r=await execute(fixtures(),url=>url.includes('raw.githubusercontent.com')?new Response('x'.repeat(256*1024+1)):null);assert.equal(r.value.reason,'response_too_large');});
test('endpoint does not forward user query or write methods',async()=>{const t=transport(fixtures()), h=handler(READY,{fetchFn:t.fetchFn,now:NOW,cryptoApi:webcrypto});assert.equal((await h.fetch(new Request('https://example.test/health?target=other'))).status,404);assert.equal((await h.fetch(new Request('https://example.test/health',{method:'POST'}))).status,404);assert.equal(t.calls.length,0);});
test('network error text is not disclosed in HTTP body',async()=>{const h=handler(READY,{fetchFn:async()=>{throw Error('private-details-should-not-escape');},now:NOW,cryptoApi:webcrypto});const r=await h.fetch(new Request('https://example.test/health'));assert.equal(r.status,503);assert.ok(!(await r.text()).includes('private-details'));assert.equal(r.headers.get('Cache-Control'),'no-store');});

// Reproduce the native receiver requirement absent from Node's built-in fetch.
test('default transport preserves the actual global receiver',async()=>{
 const prior=globalThis.fetch;const fixture=transport(fixtures());
 globalThis.fetch=function(...args){assert.equal(this,globalThis,'native fetch requires global receiver');return fixture.fetchFn(...args);};
 try {const value=await check(READY,{now:NOW,cryptoApi:webcrypto});
  assert.equal(value.healthy,true);assert.equal(fixture.calls.length,3);
 } finally {globalThis.fetch=prior;}
});

test('all redirect responses are refused without any second fetch',async()=>{
 for(const status of [301,302,303,307,308]){
  const r=await execute(fixtures(),()=>new Response(null,{status,headers:{Location:'https://foreign.invalid/'}}));
  assert.equal(r.value.healthy,false);assert.equal(r.value.reason,'provider_unavailable');assert.equal(r.calls.length,1);
 }
});
test('documented platform rejects the old error mode; old defect is positively detected',async()=>{
 const {check:oldCheck}=await import('./fixtures/historical-redirect-error.mjs');let calls=0;
 const platform=async(url,options)=>{calls++;if(options.redirect==='error')throw new TypeError('unsupported redirect mode');throw new Error('unexpected branch');};
 const r=await oldCheck(READY,{fetchFn:platform,now:NOW,cryptoApi:webcrypto});
 assert.equal(r.healthy,false);assert.equal(r.reason,'evidence_unavailable_fetch_TypeError');assert.equal(calls,1);
});

test('actual scheduler timestamp 70 seconds earlier passes the stricter GitHub start slot',async()=>{
 const f=fixtures();f.list.workflow_runs[0].display_title='btc-health:'+String((DUE-58000)/1000);
 assert.equal((await execute(f)).value.healthy,true);
});
test('GitHub start later than 30 seconds is rejected even with a fresh input',async()=>{
 const f=fixtures();f.list.workflow_runs[0].created_at=iso(DUE+31000);
 f.list.workflow_runs[0].display_title='btc-health:'+String((DUE+30000)/1000);
 assert.equal((await execute(f)).value.reason,'run_time');
});
test('scheduler input older than two minutes or from future is rejected',async()=>{
 for(const delta of [-121000,1000]){const f=fixtures();f.list.workflow_runs[0].display_title='btc-health:'+String((DUE+12000+delta)/1000);
 assert.equal((await execute(f)).value.reason,'run_time');}
});
test('only six checker slots per hour and at most twenty initial public core requests are needed',async()=>{
 const f=fixtures();const r=await execute(f);assert.equal(r.value.healthy,true);
 assert.ok(r.calls[0].url.includes('2026-10-17T08%3A00%3A00.000Z'));
});
test('ten-minute cadence accepts exactly twenty remaining core reads and rejects nineteen without retry',async()=>{
 for(const remaining of [20,19]){
  const f=fixtures();const r=await execute(f,url=>url.includes('raw.githubusercontent.com')?null:new Response(JSON.stringify(url.includes('/jobs?')?f.jobs:f.list),{headers:{'x-ratelimit-resource':'core','x-ratelimit-remaining':String(remaining),'x-ratelimit-reset':String((NOW+3600000)/1000)}}));
  assert.equal(r.value.healthy,remaining===20);if(remaining===19){assert.equal(r.value.reason,'quota_insufficient');assert.equal(r.calls.length,1);}
 }
});
test('provider rejection discloses only its numeric HTTP status and never response details or headers',async()=>{
 const r=await execute(fixtures(),()=>new Response('private-provider-body',{status:403,headers:{'X-Private':'do-not-disclose'}}));
 assert.deepEqual(r.value,{schema:'btc-external-checker-gate-v1',healthy:false,reason:'provider_unavailable',provider_status:403,phase:'fetch'});
 assert.equal(r.calls.length,1);assert.ok(!JSON.stringify(r.value).includes('private'));
});

 test('public evidence identifies checked run and entry without private data',async()=>{const r=await execute();assert.equal(r.value.run_id,100);assert.equal(r.value.entry_commit,HEAD);assert.equal(r.value.phase,'complete');});
