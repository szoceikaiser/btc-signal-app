/* GET-only external supervisor. Dedicated public-read GitHub credential is
   supplied exclusively by the encrypted Worker secret binding, never source.
   No Telegram, Store mutation, dispatch, retry or anonymous fallback. */
export const CONFIG = Object.freeze({
  enabled: true,
  workflowId: 388631778,
  workflowSha256: "211f0668a3aa7d4168092f7215de5e7842efb8cefcb5e98e3cfbb5f8d4070ef5",
  policyBindingSha256: "4fe5f956e2e54b631344e30203c8b4972980279851f23e07a8c4c6a8e272af73",
  codeSha: 'f3f054851f500af1926b149f13a2ee8890a8c2bc',
});
const REPO = 'szoceikaiser/btc-signal-app';
const REPO_ID = 1309164619;
const PATH = '.github/workflows/freshness.yml';
const PERIOD = 600000;
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
export async function check(config, {fetchFn=(input,init)=>globalThis.fetch(input,init), now=Date.now(), cryptoApi=crypto, githubToken=''}={}) {
  let total=0, core=0, diagnosticPhase='prepare', providerStatus=null;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    requireValue(config?.enabled === true && Number.isSafeInteger(config.workflowId) && config.workflowId > 0
      && /^[a-f0-9]{64}$/.test(config.workflowSha256) && /^[a-f0-9]{64}$/.test(config.policyBindingSha256)
      && /^[a-f0-9]{40}$/.test(config.codeSha) && Number.isSafeInteger(now), 'monitor_unconfigured');
    requireValue(typeof githubToken==='string' && /^github_pat_[A-Za-z0-9_]{20,240}$/.test(githubToken), 'reader_credential_unavailable');
    const due = Math.floor((now-GRACE)/PERIOD)*PERIOD;
    async function read(url, isCore) {
      requireValue(++total<=3 && (!isCore || ++core<=2), 'read_budget');
      diagnosticPhase='fetch';
      const origin = new URL(url);
      requireValue(origin.protocol==='https:' && !origin.username && !origin.password
        && (isCore ? origin.origin==='https://api.github.com'
          && origin.pathname.startsWith('/repos/'+REPO+'/actions/')
          : origin.origin==='https://raw.githubusercontent.com'
          && origin.pathname.startsWith('/'+REPO+'/')), 'provider_target');
      const headers={'User-Agent':'btc-external-readonly-health-v1',
        'Accept':isCore?'application/vnd.github+json':'text/plain'};
      if(isCore) headers.Authorization='Bearer '+githubToken;
      const response = await fetchFn(url, {method:'GET',redirect:'manual',signal:controller.signal,headers});
      providerStatus=response.status;
      requireValue(response.status===200 && !response.redirected, 'provider_unavailable');
      requireValue(!response.headers.has('link'), 'incomplete_metadata');
      if(isCore) {
        const remaining=response.headers.get('x-ratelimit-remaining'), reset=response.headers.get('x-ratelimit-reset');
        requireValue(/^\d+$/.test(remaining||'') && /^\d+$/.test(reset||'')
          && response.headers.get('x-ratelimit-resource')==='core', 'quota_unverified');
        const limit=response.headers.get('x-ratelimit-limit');
        requireValue(/^\d+$/.test(limit||'') && Number.isSafeInteger(Number(limit))
          && Number(limit)>=1000 && Number(remaining)<=Number(limit)
          && Number(reset)*1000>now && Number(reset)*1000<=now+3660000, 'authenticated_quota_unverified');
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
      // GitHub creation time establishes the actual slot. The scheduler's
      // earlier queue-preparation timestamp is only a bounded correlation value.
      const created=timestamp(run.created_at), slot=Math.floor(created/PERIOD)*PERIOD;
      requireValue(created>=invoked && created-invoked<=120000 && created-slot<=GRACE
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
    const value=result(false,error instanceof Closed?error.reason:'evidence_unavailable_'+diagnosticPhase+'_'+kind);
    if(error instanceof Closed && error.reason==='provider_unavailable' && Number.isInteger(providerStatus)) value.provider_status=providerStatus;
    return value;
  } finally { clearTimeout(timer); }
}
export function handler(config=CONFIG, dependencies={}) {
  return {async fetch(request, env) {
    const url=new URL(request.url);
    if(request.method!=='GET' || url.pathname!=='/health' || url.search) {
      return new Response('Not found',{status:404,headers:{'Cache-Control':'no-store'}});
    }
    const value=await check(config,{...dependencies, githubToken:env?.BTC_GITHUB_HEALTH_READ_TOKEN});
    return new Response(JSON.stringify(value),{status:value.healthy?200:503,headers:{
      'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
  }};
}
export default handler();
