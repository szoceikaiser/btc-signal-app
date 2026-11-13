// Synthetic HTTP fixtures only. No actual GitHub/Cloudflare/provider proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {check,handler,CONFIG} from './worker.mjs';
const TEST_TOKEN='github_pat_OFFLINE_FIXTURE_NOT_A_REAL_SECRET_123456';
const TEST_ENV={BTC_GITHUB_HEALTH_READ_TOKEN:TEST_TOKEN};
const DUE=Date.parse('2026-10-17T08:00:00Z'), NOW=DUE+200000;
const API='https://api.github.com/repos/szoceikaiser/btc-signal-app';
const QUOTA_HEADERS={
 'x-ratelimit-limit':'5000',
 'x-ratelimit-resource':'core',
 'x-ratelimit-remaining':'59',
 'x-ratelimit-reset':String((NOW+3600000)/1000),
};
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
  if(change) {const override=change(url,options,calls.length);if(override)return override;}
  const raw=url.includes('raw.githubusercontent.com');
  const body=raw?f.yaml:JSON.stringify(url.includes('/jobs?')?f.jobs:f.list);
  return new Response(body,{status:200,headers:raw?{}:QUOTA_HEADERS});
 };
 return{calls,fetchFn};
}
async function execute(f=fixtures(),change,config=READY){const t=transport(f,change);const value=await check(config,{fetchFn:t.fetchFn,now:NOW,cryptoApi:webcrypto,githubToken:TEST_TOKEN});return{value,calls:t.calls};}
test('published config authenticates the actual monitor workflow with a slow in-slot job',async()=>{
 const f=fixtures();
 f.yaml=await readFile(new URL('../.github/workflows/freshness.yml',import.meta.url),'utf8');
 f.list.workflow_runs[0].workflow_id=CONFIG.workflowId;
 f.jobs.jobs[0].started_at=iso(DUE+115000);
 f.jobs.jobs[0].completed_at=iso(DUE+175000);
 const good=await execute(f,null,CONFIG);
 assert.equal(good.value.healthy,true);
 assert.equal(good.calls.length,3);
 f.jobs.jobs[0].completed_at=iso(DUE+180001);
 assert.equal((await execute(f,null,CONFIG)).value.reason,'checker_late');
 f.jobs.jobs[0].completed_at=iso(DUE+175000);
 f.yaml+='\n';
 assert.equal((await execute(f,null,CONFIG)).value.reason,'unreviewed_checker');
});
test('disabled/unbound configuration never contacts a provider',async()=>{const r=await execute(fixtures(),null,{...CONFIG,enabled:false});assert.equal(r.value.healthy,false);assert.equal(r.calls.length,0);});
test('missing or invalid Worker bindings fail before fetch, including with caller credentials',async()=>{
 const t=transport(fixtures());
 const worker=handler(READY,{fetchFn:t.fetchFn,now:NOW,cryptoApi:webcrypto,githubToken:TEST_TOKEN});
 const request=new Request('https://example.test/health',{headers:{Authorization:'Bearer '+TEST_TOKEN}});
 for(const env of [undefined,{},...[
  null,123,'','github_pat_short','Bearer '+TEST_TOKEN,TEST_TOKEN+'\nX-Test: 1',
 ].map(token=>({BTC_GITHUB_HEALTH_READ_TOKEN:token}))]){
  const response=await worker.fetch(request,env);
  assert.equal(response.status,503);
  assert.deepEqual(await response.json(),{
   schema:'btc-external-checker-gate-v1',healthy:false,reason:'reader_credential_unavailable',
  });
  assert.equal(t.calls.length,0);
 }
});
test('complete evidence uses exactly two fixed authenticated API GETs and one anonymous RAW GET',async()=>{
 const t=transport(fixtures());
 const worker=handler(READY,{fetchFn:t.fetchFn,now:NOW,cryptoApi:webcrypto});
 const response=await worker.fetch(new Request('https://example.test/health'),TEST_ENV);
 assert.equal(response.status,200);
 assert.deepEqual(await response.json(),{schema:'btc-external-checker-gate-v1',healthy:true,reason:'ok'});
 const query=new URLSearchParams({per_page:'20',created:iso(DUE)+'..'+iso(NOW)});
 assert.deepEqual(t.calls.map(call=>call.url),[
  API+'/actions/workflows/123/runs?'+query,
  'https://raw.githubusercontent.com/szoceikaiser/btc-signal-app/'+HEAD+'/.github/workflows/freshness.yml',
  API+'/actions/runs/100/attempts/1/jobs?per_page=100',
 ]);
 for(const [index,{options}] of t.calls.entries()){
  const headers=new Headers(options.headers);
  assert.equal(options.method,'GET');
  assert.equal(options.redirect,'manual');
  assert.equal(headers.get('Authorization'),index===1?null:'Bearer '+TEST_TOKEN);
  assert.equal(headers.has('Cookie'),false);
  assert.equal(Object.hasOwn(options,'body'),false);
 }
});
test('missing due slot is not hidden by a later successful run',async()=>{const f=fixtures();const r=f.list.workflow_runs[0];r.display_title='btc-health:'+String((DUE+PERIOD+10000)/1000);r.created_at=iso(DUE+PERIOD+12000);const t=transport(f);const v=await check(READY,{fetchFn:t.fetchFn,now:DUE+PERIOD+130000,cryptoApi:webcrypto,githubToken:TEST_TOKEN});assert.equal(v.healthy,false);assert.equal(v.reason,'checker_missing');});
const PERIOD=600000;
test('latest failure cannot be filtered away',async()=>{const f=fixtures();f.list.workflow_runs[0].conclusion='failure';const r=await execute(f);assert.equal(r.value.reason,'checker_failed');assert.equal(r.calls.length,1);});
test('queued checker cannot become healthy',async()=>{const f=fixtures();Object.assign(f.list.workflow_runs[0],{status:'queued',conclusion:null});assert.equal((await execute(f)).value.reason,'checker_unfinished');});
test('attempt two is rejected',async()=>{const f=fixtures();f.list.workflow_runs[0].run_attempt=2;assert.equal((await execute(f)).value.reason,'run_identity');});
test('foreign branch/repository is rejected',async()=>{for(const key of ['head_branch','repository']){const f=fixtures();f.list.workflow_runs[0][key]=key==='head_branch'?'other':{id:1,full_name:'other/repo'};assert.equal((await execute(f)).value.reason,'run_identity');}});
test('changed workflow bytes never attest reviewed code',async()=>{const f=fixtures();f.yaml+='altered';assert.equal((await execute(f)).value.reason,'unreviewed_checker');});
test('wrong reviewed policy binding is not accepted by a matching YAML hash alone',async()=>{const r=await execute(fixtures(),null,{...READY,policyBindingSha256:'d'.repeat(64)});assert.equal(r.value.reason,'unreviewed_checker');});
test('wrong code pin is not accepted by a matching YAML hash alone',async()=>{
 const r=await execute(fixtures(),null,{...READY,codeSha:'d'.repeat(40)});
 assert.equal(r.value.reason,'unreviewed_checker');
 assert.equal(r.calls.length,2);
});
test('two successful runs for the same due slot are ambiguous',async()=>{const f=fixtures();f.list.workflow_runs.push({...f.list.workflow_runs[0],id:101});f.list.total_count=2;assert.equal((await execute(f)).value.reason,'duplicate_checker');});
test('a job from another run cannot attest this checker',async()=>{const f=fixtures();f.jobs.jobs[0].run_id=101;assert.equal((await execute(f)).value.reason,'job_identity');});
test('incomplete run query is refused',async()=>{const f=fixtures();f.list.total_count=2;assert.equal((await execute(f)).value.reason,'incomplete_metadata');});
test('skipped required checker step cannot become healthy',async()=>{const f=fixtures();f.jobs.jobs[0].steps[1].conclusion='skipped';assert.equal((await execute(f)).value.reason,'checker_steps');});
test('late completion is rejected independently of success badge',async()=>{const f=fixtures();f.jobs.jobs[0].completed_at=iso(DUE+190000);assert.equal((await execute(f)).value.reason,'checker_late');});
test('API rejection stops without retry or anonymous fallback at either API target',async()=>{
 for(const failedCall of [1,3]){
  for(const status of [401,403,429]){
   const r=await execute(fixtures(),(_url,_options,call)=>call===failedCall
    ?new Response(TEST_TOKEN,{status}):null);
   assert.deepEqual(r.value,{
    schema:'btc-external-checker-gate-v1',healthy:false,reason:'provider_unavailable',provider_status:status,
   });
   assert.equal(r.calls.length,failedCall);
   assert.equal(r.calls.at(-1).options.headers.Authorization,'Bearer '+TEST_TOKEN);
  }
 }
});
test('both authenticated responses require plausible core quota headers',async()=>{
 const invalidHeaders=[
  [{'x-ratelimit-resource':'search'},'quota_unverified'],
  [{'x-ratelimit-limit':''},'authenticated_quota_unverified'],
  [{'x-ratelimit-limit':'60'},'authenticated_quota_unverified'],
  [{'x-ratelimit-remaining':'5001'},'authenticated_quota_unverified'],
  [{'x-ratelimit-reset':String(NOW/1000)},'authenticated_quota_unverified'],
  [{'x-ratelimit-reset':String((NOW+7200000)/1000)},'authenticated_quota_unverified'],
 ];
 for(const failedCall of [1,3]){
  for(const [patch,reason] of invalidHeaders){
   const r=await execute(fixtures(),(_url,_options,call)=>call===failedCall
    ?new Response('{}',{headers:{...QUOTA_HEADERS,...patch}}):null);
   assert.equal(r.value.reason,reason);
   assert.equal(r.calls.length,failedCall);
  }
 }
});
test('oversized response is bounded',async()=>{const r=await execute(fixtures(),url=>url.includes('raw.githubusercontent.com')?new Response('x'.repeat(256*1024+1)):null);assert.equal(r.value.reason,'response_too_large');});
test('endpoint does not forward user query or write methods',async()=>{
 const t=transport(fixtures());
 const worker=handler(READY,{fetchFn:t.fetchFn,now:NOW,cryptoApi:webcrypto});
 for(const request of [
  new Request('https://example.test/health?target=other'),
  new Request('https://example.test/health',{method:'POST'}),
  new Request('https://example.test/not-health'),
 ]){
  assert.equal((await worker.fetch(request,TEST_ENV)).status,404);
 }
 assert.equal(t.calls.length,0);
});
test('network error text is not disclosed in HTTP body',async()=>{
 const t=transport(fixtures(),()=>{throw new TypeError('request failed: '+TEST_TOKEN);});
 const worker=handler(READY,{fetchFn:t.fetchFn,now:NOW,cryptoApi:webcrypto});
 const response=await worker.fetch(new Request('https://example.test/health'),TEST_ENV);
 assert.equal(response.status,503);
 assert.equal(response.headers.get('Cache-Control'),'no-store');
 assert.deepEqual(await response.json(),{
  schema:'btc-external-checker-gate-v1',healthy:false,reason:'evidence_unavailable_fetch_TypeError',
 });
 assert.equal(t.calls.length,1);
});

// Reproduce the native receiver requirement absent from Node's built-in fetch.
test('default transport preserves the actual global receiver',async()=>{
 const prior=globalThis.fetch;const fixture=transport(fixtures());
 globalThis.fetch=function(...args){assert.equal(this,globalThis,'native fetch requires global receiver');return fixture.fetchFn(...args);};
 try {const value=await check(READY,{now:NOW,cryptoApi:webcrypto,githubToken:TEST_TOKEN});
  assert.equal(value.healthy,true);assert.equal(fixture.calls.length,3);
 } finally {globalThis.fetch=prior;}
});

test('all redirect responses are refused without any second fetch',async()=>{
 for(const redirectedCall of [1,2,3]){
  for(const status of [301,302,303,307,308]){
   const r=await execute(fixtures(),(_url,_options,call)=>call===redirectedCall
    ?new Response(null,{status,headers:{Location:'https://foreign.invalid/'+TEST_TOKEN}}):null);
   assert.deepEqual(r.value,{
    schema:'btc-external-checker-gate-v1',healthy:false,reason:'provider_unavailable',provider_status:status,
   });
   assert.equal(r.calls.length,redirectedCall);
   assert.equal(r.calls.at(-1).options.redirect,'manual');
  }
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
test('creation after the three-minute slot deadline is rejected even with a fresh input',async()=>{
 const f=fixtures();f.list.workflow_runs[0].created_at=iso(DUE+180001);
 f.list.workflow_runs[0].display_title='btc-health:'+String((DUE+180000)/1000);
 assert.equal((await execute(f)).value.reason,'run_time');
});
test('a run started after thirty seconds can complete at the deadline, but a millisecond later fails',async()=>{
 const f=fixtures();
 f.list.workflow_runs[0].created_at=iso(DUE+59000);
 f.jobs.jobs[0].started_at=iso(DUE+64000);
 f.jobs.jobs[0].completed_at=iso(DUE+180000);
 assert.equal((await execute(f)).value.healthy,true);
 f.jobs.jobs[0].completed_at=iso(DUE+180001);
 assert.equal((await execute(f)).value.reason,'checker_late');
});
test('scheduler input older than two minutes or from future is rejected',async()=>{
 for(const delta of [-121000,1000]){const f=fixtures();f.list.workflow_runs[0].display_title='btc-health:'+String((DUE+12000+delta)/1000);
 assert.equal((await execute(f)).value.reason,'run_time');}
});
test('ten-minute cadence accepts exactly twenty remaining core reads and rejects nineteen without retry',async()=>{
 for(const remaining of [20,19]){
  const f=fixtures();const r=await execute(f,url=>url.includes('raw.githubusercontent.com')?null:new Response(JSON.stringify(url.includes('/jobs?')?f.jobs:f.list),{headers:{...QUOTA_HEADERS,'x-ratelimit-remaining':String(remaining)}}));
  assert.equal(r.value.healthy,remaining===20);if(remaining===19){assert.equal(r.value.reason,'quota_insufficient');assert.equal(r.calls.length,1);}
 }
});
test('provider rejection discloses only its numeric HTTP status and never response details or headers',async()=>{
 const r=await execute(fixtures(),()=>new Response('private-provider-body',{status:403,headers:{'X-Private':'do-not-disclose'}}));
 assert.deepEqual(r.value,{schema:'btc-external-checker-gate-v1',healthy:false,reason:'provider_unavailable',provider_status:403});
 assert.equal(r.calls.length,1);assert.ok(!JSON.stringify(r.value).includes('private'));
});
