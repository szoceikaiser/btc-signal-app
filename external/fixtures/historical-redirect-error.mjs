/* OFFLINE PREPARATION. Public, GET-only supervisor of the reviewed full checker.
   Default configuration cannot return healthy and performs no network access.
   No GitHub token, Telegram transport, Store mutation, dispatch or retry. */
export const CONFIG = Object.freeze({
  enabled: true,
  workflowId: 388631778,
  workflowSha256: "6df69894080678519901ae75bd49c3788ebc6e1ab6776e9dd60b114d6eeed7c8",
  policyBindingSha256: "756bacd49cbcb05b9c86504ad4e97f3b29a6c75c960a84f76b58a03a1cfb970f",
  codeSha: '20d755a4332fb32aeab08b1973b650eeae10f31e',
});
const REPO = 'szoceikaiser/btc-signal-app';
const REPO_ID = 1309164619;
const PATH = '.github/workflows/freshness.yml';
const PERIOD = 300000;
const GRACE = 180000;
const LIMIT = 256 * 1024;
const STEP_NAMES = ['Verify checkout pin before loading code', 'Read bounded candidate evidence'];
class Closed extends Error { constructor(reason) { super(reason); this.reason = reason; } }
const requireValue = (condition, reason) => { if (!condition) throw new Closed(reason); };
const timestamp = value => {
  requireValue(typeof value === 'string' && value.endsWith('Z'), 'invalid_time');
  const result = Date.parse(value); requireValue(Number.isFinite(result), 'invalid_time'); return result;
};
const result = (healthy, reason) => ({schema:'btc-external-checker-gate-v1', healthy, reason});
export async function check(config, {fetchFn=(...args)=>globalThis.fetch(...args), now=Date.now(), cryptoApi=crypto}={}) {
  let total=0, core=0, diagnosticPhase='prepare';
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    requireValue(config?.enabled === true && Number.isSafeInteger(config.workflowId) && config.workflowId > 0
      && /^[a-f0-9]{64}$/.test(config.workflowSha256) && /^[a-f0-9]{64}$/.test(config.policyBindingSha256)
      && /^[a-f0-9]{40}$/.test(config.codeSha) && Number.isSafeInteger(now), 'monitor_unconfigured');
    const due = Math.floor((now-GRACE)/PERIOD)*PERIOD;
    async function read(url, isCore) {
      requireValue(++total<=3 && (!isCore || ++core<=2), 'read_budget');
      diagnosticPhase='fetch';
      const response = await fetchFn(url, {method:'GET',redirect:'error',signal:controller.signal,
        headers:{'User-Agent':'btc-external-readonly-health-v1','Accept':isCore?'application/vnd.github+json':'text/plain'}});
      requireValue(response.status===200 && !response.redirected, 'provider_unavailable');
      requireValue(!response.headers.has('link'), 'incomplete_metadata');
      if(isCore) {
        const remaining=response.headers.get('x-ratelimit-remaining'), reset=response.headers.get('x-ratelimit-reset');
        requireValue(/^\d+$/.test(remaining||'') && /^\d+$/.test(reset||'')
          && response.headers.get('x-ratelimit-resource')==='core', 'quota_unverified');
        // A local headroom check, NOT a reservation or proof of an exclusive IP pool.
        const needed=2*Math.ceil(Math.max(0,Number(reset)*1000-now)/PERIOD)+8;
        requireValue(Number(remaining)>=needed, 'quota_insufficient');
      }
      const size=response.headers.get('content-length');
      requireValue(!size || (/^\d+$/.test(size) && Number(size)<=LIMIT), 'response_too_large');
      diagnosticPhase='body';
      const reader=response.body?.getReader(); requireValue(reader, 'invalid_response');
      let bytes=0; const chunks=[];
      while(true) { const part=await reader.read(); if(part.done) break;
        bytes+=part.value.byteLength;
        if(bytes>LIMIT) { await reader.cancel(); throw new Closed('response_too_large'); }
        chunks.push(part.value);
      }
      const buffer=new Uint8Array(bytes); let offset=0;
      for(const chunk of chunks) { buffer.set(chunk,offset); offset+=chunk.byteLength; }
      return buffer;
    }
    const text = bytes => { diagnosticPhase='decode'; return new TextDecoder('utf-8',{fatal:true,ignoreBOM:false}).decode(bytes); };
    const api = 'https://api.github.com/repos/'+REPO;
    const query=new URLSearchParams({per_page:'20',created:new Date(due).toISOString()+'..'+new Date(now).toISOString()});
    const list=JSON.parse(text(await read(api+'/actions/workflows/'+config.workflowId+'/runs?'+query,true)));
    requireValue(Array.isArray(list.workflow_runs) && list.total_count===list.workflow_runs.length
      && list.total_count<20, 'incomplete_metadata');
    const dueRuns=[];
    for(const run of list.workflow_runs) {
      requireValue(run.repository?.id===REPO_ID && run.repository.full_name===REPO
        && run.workflow_id===config.workflowId && run.path===PATH && run.head_branch==='main'
        && run.event==='workflow_dispatch' && run.run_attempt===1 && /^[a-f0-9]{40}$/.test(run.head_sha)
        && Number.isSafeInteger(run.id) && run.id>0, 'run_identity');
      requireValue(/^btc-health:\d{10}$/.test(run.display_title||''), 'run_identity');
      const invoked=Number(run.display_title.slice('btc-health:'.length))*1000;
      const slot=Math.floor(invoked/PERIOD)*PERIOD, created=timestamp(run.created_at);
      requireValue(invoked>=slot && invoked<slot+120000 && created>=invoked && created-invoked<=30000
        && created<=now && slot>=due, 'run_time');
      if(run.status==='completed' && run.conclusion!=='success') throw new Closed('checker_failed');
      if(slot===due) dueRuns.push(run);
    }
    requireValue(dueRuns.length===1, dueRuns.length?'duplicate_checker':'checker_missing');
    const run=dueRuns[0];
    requireValue(run.status==='completed' && run.conclusion==='success', 'checker_unfinished');
    const raw=await read('https://raw.githubusercontent.com/'+REPO+'/'+run.head_sha+'/'+PATH,false);
    const hash=Array.from(new Uint8Array(await cryptoApi.subtle.digest('SHA-256',raw)),b=>b.toString(16).padStart(2,'0')).join('');
    const workflow=text(raw);
    requireValue(hash===config.workflowSha256 && workflow.includes(config.codeSha)
      && workflow.includes(config.policyBindingSha256), 'unreviewed_checker');
    const jobs=JSON.parse(text(await read(api+'/actions/runs/'+run.id+'/attempts/1/jobs?per_page=100',true)));
    requireValue(jobs.total_count===1 && jobs.jobs?.length===1, 'job_identity');
    const job=jobs.jobs[0];
    requireValue(job.run_id===run.id && job.run_attempt===1 && job.head_sha===run.head_sha
      && job.name==='observe' && job.status==='completed' && job.conclusion==='success', 'job_identity');
    const started=timestamp(job.started_at), ended=timestamp(job.completed_at);
    requireValue(started>=timestamp(run.created_at) && ended>=started && ended<=now
      && ended<=due+GRACE && ended-started<=120000, 'checker_late');
    requireValue(Array.isArray(job.steps) && job.steps.length>=2 && job.steps.length<=20
      && job.steps.every(s=>s.status==='completed' && s.conclusion==='success')
      && STEP_NAMES.every(name=>job.steps.filter(s=>s.name===name).length===1), 'checker_steps');
    return result(true,'ok');
  } catch(error) {
    const kind=['TypeError','SyntaxError','RangeError','AbortError','Error'].includes(error?.name)?error.name:'other';
    return result(false,error instanceof Closed?error.reason:'evidence_unavailable_'+diagnosticPhase+'_'+kind);
  } finally { clearTimeout(timer); }
}
export function handler(config=CONFIG, dependencies={}) {
  return {async fetch(request) {
    const url=new URL(request.url);
    if(request.method!=='GET' || url.pathname!=='/health' || url.search) {
      return new Response('Not found',{status:404,headers:{'Cache-Control':'no-store'}});
    }
    const value=await check(config,dependencies);
    return new Response(JSON.stringify(value),{status:value.healthy?200:503,headers:{
      'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
  }};
}
export default handler();
