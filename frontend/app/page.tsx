'use client';

import { useEffect, useState } from 'react';
import { analyzeImage, cancelJob, enqueueIngestion, checkPolicy, exportPolicy, getCompliance, getRecovery, getApiContract, getIncidentCenter, getPreflight, getReleaseManifest, getReleaseReadiness, getDiagnostics, getJob, getReadiness, listDocuments, sendChat, uploadDocument } from '../src/lib/api';
import type { ChatResult, Citation, DocumentRecord } from '../src/lib/types';

const useCursorField = () => {
  useEffect(() => {
    const root = document.querySelector<HTMLElement>('.fi-shell');
    if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const move = (event: PointerEvent) => {
      const rect = root.getBoundingClientRect();
      const x = Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100));
      const y = Math.max(0, Math.min(100, ((event.clientY - rect.top) / rect.height) * 100));
      root.style.setProperty('--mx', `${x}%`);
      root.style.setProperty('--my', `${y}%`);
    };
    root.addEventListener('pointermove', move);
    return () => root.removeEventListener('pointermove', move);
  }, []);
};

export default function Home() {
  useCursorField();
  const [file, setFile] = useState<File | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selected, setSelected] = useState<DocumentRecord | null>(null);
  const [progress, setProgress] = useState(0);
  const [vision, setVision] = useState<Record<string, unknown> | null>(null);
  const [chat, setChat] = useState<ChatResult | null>(null);
  const [query, setQuery] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [ready, setReady] = useState<boolean | null>(null);
  const [diagnostics, setDiagnostics] = useState<Record<string, any> | null>(null);
  const [compliance, setCompliance] = useState<Record<string, any> | null>(null);
  const [policyResult, setPolicyResult] = useState<Record<string, any> | null>(null);
  const [exportResult, setExportResult] = useState<Record<string, any> | null>(null);
  const [recovery, setRecovery] = useState<Record<string, any> | null>(null);
  const [release, setRelease] = useState<Record<string, any> | null>(null);
  const [releaseInfo, setReleaseInfo] = useState<Record<string, any> | null>(null);
  const [contract, setContract] = useState<Record<string, any> | null>(null);
  const [incident, setIncident] = useState<Record<string, any> | null>(null);
  const [preflight, setPreflight] = useState<Record<string, any> | null>(null);
  const [job, setJob] = useState<Record<string, any> | null>(null);

  const refresh = async () => {
    try {
      const data = await listDocuments();
      const items = Array.isArray(data) ? data : data.items ?? [];
      setDocuments(items);
      if (selected) setSelected(items.find(d => d.id === selected.id) ?? selected);
    } catch { /* endpoint may be unavailable in a partial local environment */ }
  };

  useEffect(() => {
    refresh();
    getReadiness().then(() => setReady(true)).catch(() => setReady(false));
  }, []);

  const run = async (label: string, fn: () => Promise<void>) => {
    setBusy(label); setError('');
    try { await fn(); } catch (e) { setError(e instanceof Error ? e.message : 'Request failed'); }
    finally { setBusy(''); }
  };

  const loadPreflight = () => run('Running preflight…', async () => {
    setPreflight(await getPreflight());
  });

  const loadIncident = () => run('Building incident report…', async () => {
    setIncident(await getIncidentCenter());
  });

  const loadContract = () => run('Reading API contract…', async () => {
    setContract(await getApiContract());
  });

  const loadReleaseInfo = () => run('Reading release…', async () => {
    setReleaseInfo(await getReleaseManifest());
  });

  const loadReleaseReadiness = () => run('Checking release…', async () => {
    setRelease(await getReleaseReadiness());
  });

  const loadRecovery = () => run('Checking recovery…', async () => {
    setRecovery(await getRecovery());
  });

  const loadExportPolicy = () => run('Checking export…', async () => {
    setExportResult(await exportPolicy('operator', 'user-requested-export', false, false));
  });

  const loadPolicy = () => run('Evaluating access…', async () => {
    setPolicyResult(await checkPolicy('sensitive', 'operator', 'food-analysis', false, false));
  });

  const loadCompliance = () => run('Checking policy…', async () => {
    setCompliance(await getCompliance());
  });

  const loadDiagnostics = () => run('Inspecting…', async () => {
    setDiagnostics(await getDiagnostics());
  });

  const upload = () => run('Uploading…', async () => {
    if (!file) throw new Error('Choose a document or image first.');
    const doc = await uploadDocument(file, setProgress);
    setSelected(doc);
    setProgress(100);
    await refresh();
  });

  const ingest = () => run('Queueing…', async () => {
    if (!selected) throw new Error('Select a document.');
    const queued = await enqueueIngestion(selected.id);
    setJob(queued);
    for (let i = 0; i < 60; i++) {
      await new Promise(r => setTimeout(r, 500));
      const current = await getJob(queued.job_id);
      setJob(current);
      if (current.status === 'completed' || current.status === 'failed') break;
    }
    await refresh();
  });

  const visionRun = () => run('Analyzing…', async () => {
    if (!selected || selected.document_type !== 'image') throw new Error('Select an image.');
    setVision(await analyzeImage(selected.id));
  });

  const ask = () => run('Reasoning…', async () => {
    if (!query.trim()) throw new Error('Enter a question.');
    setChat(await sendChat(query, vision?.document_id as string | undefined));
  });

  return (
    <main className="fi-shell shell">
      <section className="fi-interactive-hero" aria-label="FoodInsightAI">
        <div className="fi-hero-grid" aria-hidden="true"></div>
        <div className="fi-cursor-orb" aria-hidden="true"></div>
        <div className="fi-hero-content">
          <div className="fi-eyebrow"><span className="fi-pulse-dot"></span> Food intelligence workbench</div>
          <h1>FoodInsight<span>AI</span></h1>
          <p>Understand food. Connect evidence. Reason with confidence.</p>
          <div className="fi-hero-flow" aria-label="FoodInsightAI reasoning flow">
            <span>UNDERSTAND</span><i>→</i><span>RETRIEVE</span><i>→</i><span>REASON</span><i>→</i><span>VALIDATE</span>
          </div>
          <div className="fi-capability-rail" aria-label="Core capabilities">
            <span>Sources</span><span>Vision</span><span>Grounded Chat</span><span>Nutrition</span><span>Safety</span><span>Knowledge</span>
          </div>
        </div>
        <div className="fi-hero-status">{ready === true ? '● API ready' : ready === false ? '● API unavailable' : '● Checking API'}</div>
      </section>

      {job && <section className="panel jobpanel">
        <p className="eyebrow">LIVE JOB</p><h2>{job.kind ?? 'Background task'}</h2>
        <div className="jobline"><span>{job.message ?? job.status}</span><b>{job.progress ?? 0}%</b></div>
        <div className="progress"><span style={{width:`${job.progress ?? 0}%`}} /></div>
        <p className="muted">{job.status}{job.error ? ` · ${job.error}` : ''}</p>
        {job.status === 'queued' || job.status === 'running' ? <button onClick={() => run('Cancelling…', async () => setJob(await cancelJob(job.id)))}>Cancel job</button> : null}
      </section>}

      <section className="grid">
        <article className="panel">
          <p className="eyebrow">SOURCE LIFECYCLE</p><h2>Upload & process</h2>
          <input type="file" accept=".pdf,.txt,.csv,.json,.jpg,.jpeg,.png,.webp" onChange={e => {setFile(e.target.files?.[0] ?? null);setProgress(0)}} />
          {file && <p className="meta">{file.name} · {(file.size/1024).toFixed(1)} KB</p>}
          {progress > 0 && <div className="progress"><span style={{width:`${progress}%`}} /></div>}
          <div className="actions">
            <button onClick={upload} disabled={!!busy}>{busy || 'Upload'}</button>
            <button onClick={ingest} disabled={!!busy || !selected}>Ingest</button>
            <button onClick={visionRun} disabled={!!busy || selected?.document_type !== 'image'}>Analyze image</button>
          </div>
          {selected && <p className="meta"><b>{selected.filename}</b><br/>status: {selected.status ?? 'unknown'}<br/>id: {selected.id}</p>}
        </article>

        <article className="panel">
          <p className="eyebrow">DOCUMENTS</p><h2>Persistent source list</h2>
          <div className="doclist">
            {documents.length ? documents.map(d =>
              <button className={`doc ${selected?.id === d.id ? 'active' : ''}`} key={d.id} onClick={() => setSelected(d)}>
                <b>{d.filename}</b><span>{d.status ?? 'unknown'} · {d.document_type}</span>
              </button>
            ) : <span className="muted">No documents returned yet.</span>}
          </div>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <p className="eyebrow">VISUAL EVIDENCE</p><h2>Observation result</h2>
          <JsonView value={vision ?? {hint:'Select an image and run analysis.'}} />
        </article>
        <article className="panel">
          <p className="eyebrow">GROUNDED CHAT</p><h2>Conversation</h2>
          <div className="query"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ask about the selected evidence…" /><button onClick={ask} disabled={!!busy}>Ask</button></div>
          {chat?.answer && <div className="answer">{chat.answer}</div>}
          {chat?.uncertainty?.length ? <div className="uncertainty">Uncertainty: {chat.uncertainty.join(' ')}</div> : null}
        </article>
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">PRODUCTION PREFLIGHT</p><h2>Launch controls</h2></div><button onClick={loadPreflight} disabled={!!busy}>Run preflight</button></div>
        {preflight ? <div className="opsgrid">
          <div><b>Status</b><span>{preflight.ready ? 'Ready' : 'Blocked'}</span></div>
          <div><b>Checks</b><span>{preflight.checks?.length ?? 0}</span></div>
          <div><b>Blockers</b><span>{preflight.blockers?.length ?? 0}</span></div>
          <div><b>Warnings</b><span>{preflight.warnings?.length ?? 0}</span></div>
        </div> : <p className="muted">Run environment and security invariants before a production launch.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">INCIDENT CENTER</p><h2>Cross-system status</h2></div><button onClick={loadIncident} disabled={!!busy}>Generate report</button></div>
        {incident ? <div className="opsgrid">
          <div><b>Status</b><span>{incident.status}</span></div>
          <div><b>Severity</b><span>{incident.severity}</span></div>
          <div><b>Signals</b><span>{incident.signals?.length ?? 0}</span></div>
          <div><b>Actions</b><span>{incident.recommended_actions?.length ?? 0}</span></div>
        </div> : <p className="muted">Correlate SRE, release, readiness and recovery signals into one incident view.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">API CONTRACT</p><h2>Capability discovery</h2></div><button onClick={loadContract} disabled={!!busy}>Inspect</button></div>
        {contract ? <div className="opsgrid">
          <div><b>Version</b><span>{contract.version}</span></div>
          <div><b>Status</b><span>{contract.status}</span></div>
          <div><b>Supported</b><span>{contract.supported_versions?.join(', ')}</span></div>
          <div><b>Capabilities</b><span>{contract.capabilities?.length ?? 0}</span></div>
        </div> : <p className="muted">Inspect the stable API contract and available platform capabilities.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">RELEASE PROVENANCE</p><h2>Deployment snapshot</h2></div><button onClick={loadReleaseInfo} disabled={!!busy}>Inspect</button></div>
        {releaseInfo ? <div className="opsgrid">
          <div><b>Version</b><span>{releaseInfo.version}</span></div>
          <div><b>Schema</b><span>{releaseInfo.schema_revision}</span></div>
          <div><b>Git ref</b><span>{releaseInfo.git_ref}</span></div>
          <div><b>Features</b><span>{Object.values(releaseInfo.features ?? {}).filter(Boolean).length} enabled</span></div>
        </div> : <p className="muted">Inspect the version and schema provenance of the running application.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">RELEASE READINESS</p><h2>Production gate</h2></div><button onClick={loadReleaseReadiness} disabled={!!busy}>Run gate</button></div>
        {release ? <div className="opsgrid">
          <div><b>Status</b><span>{release.ready ? 'Ready' : 'Blocked'}</span></div>
          <div><b>Checks</b><span>{release.checks?.length ?? 0}</span></div>
          <div><b>Blockers</b><span>{release.blockers?.length ?? 0}</span></div>
          <div><b>Recovery</b><span>Verified separately</span></div>
        </div> : <p className="muted">Run the production readiness gate before deployment.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">RECOVERY READINESS</p><h2>Business continuity</h2></div><button onClick={loadRecovery} disabled={!!busy}>Check recovery</button></div>
        {recovery ? <div className="opsgrid">
          <div><b>RPO</b><span>{recovery.rpo_minutes} min</span></div>
          <div><b>RTO</b><span>{recovery.rto_minutes} min</span></div>
          <div><b>Verification</b><span>{recovery.restore_verification_supported ? 'Supported' : 'Unavailable'}</span></div>
          <div><b>Destructive restore</b><span>{recovery.automated_destructive_restore ? 'Enabled' : 'Manual'}</span></div>
        </div> : <p className="muted">Review recovery objectives and restore-verification capability.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">EXPORT CONTROL</p><h2>Data export gate</h2></div><button onClick={loadExportPolicy} disabled={!!busy}>Check export</button></div>
        {exportResult ? <div className="opsgrid">
          <div><b>Decision</b><span>{exportResult.allowed ? 'Allowed' : 'Blocked'}</span></div>
          <div><b>Reason</b><span>{exportResult.reason}</span></div>
          <div><b>Audit</b><span>{exportResult.audit?.event_id?.slice(0, 12) ?? '—'}</span></div>
          <div><b>Policy</b><span>Consent / admin</span></div>
        </div> : <p className="muted">Sensitive exports are gated by consent or authorized administration.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">GOVERNANCE CHECK</p><h2>Access policy</h2></div><button onClick={loadPolicy} disabled={!!busy}>Evaluate</button></div>
        {policyResult ? <div className="opsgrid">
          <div><b>Decision</b><span>{policyResult.allowed ? 'Allowed' : 'Consent required'}</span></div>
          <div><b>Class</b><span>{policyResult.data_class}</span></div>
          <div><b>Reason</b><span>{policyResult.reason}</span></div>
          <div><b>Audit</b><span>{policyResult.audit?.event_id?.slice(0, 12) ?? '—'}</span></div>
        </div> : <p className="muted">Check whether a requested data operation satisfies governance policy.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">DATA GOVERNANCE</p><h2>Privacy & retention</h2></div><button onClick={loadCompliance} disabled={!!busy}>Check policy</button></div>
        {compliance ? <div className="opsgrid">
          <div><b>Retention</b><span>{compliance.retention_days} days</span></div>
          <div><b>Email</b><span>{compliance.redaction?.email ? 'Redacted' : 'Raw'}</span></div>
          <div><b>Phone</b><span>{compliance.redaction?.phone ? 'Redacted' : 'Raw'}</span></div>
          <div><b>Secrets</b><span>{compliance.redaction?.api_keys ? 'Redacted' : 'Raw'}</span></div>
        </div> : <p className="muted">Review configured retention and audit-data redaction policy.</p>}
      </section>

      <section className="panel ops">
        <div className="opshead"><div><p className="eyebrow">OPERATIONS</p><h2>Runtime diagnostics</h2></div><button onClick={loadDiagnostics} disabled={!!busy}>Inspect</button></div>
        {diagnostics ? <div className="opsgrid">
          <div><b>SRE</b><span>{diagnostics.sre?.healthy ? 'Healthy' : 'Attention required'}</span></div>
          <div><b>Queue</b><span>{diagnostics.worker?.queue ?? 'unknown'}</span></div>
          <div><b>Concurrency</b><span>{diagnostics.worker?.concurrency ?? 'unknown'}</span></div>
          <div><b>Jobs</b><span>{JSON.stringify(diagnostics.jobs ?? {})}</span></div>
        </div> : <p className="muted">Inspect runtime health, job counts and SRE threshold status.</p>}
      </section>

      <section className="panel">
        <p className="eyebrow">CITATION GRAPH</p><h2>Evidence trail</h2>
        <CitationCards citations={chat?.citations ?? chat?.sources ?? []} />
      </section>

      {error && <div className="error">{error}</div>}
      <footer>UNDERSTAND → RETRIEVE → REASON → VALIDATE → RESPOND</footer>
    </main>
  );
}

function CitationCards({citations}:{citations:Citation[]}) {
  if (!citations.length) return <p className="muted">No citations returned for this response.</p>;
  return <div className="citations">{citations.map((c,i)=><div className="citation" key={`${c.chunk_id ?? c.source_id ?? i}`}>
    <b>{c.filename ?? c.source_id ?? 'Source'}</b>
    {c.page !== undefined && <span>Page {c.page}</span>}
    {c.score !== undefined && <span>Score {Number(c.score).toFixed(3)}</span>}
    {c.text && <p>{c.text}</p>}
  </div>)}</div>;
}
function JsonView({value}:{value:Record<string,unknown>}) {
  return <pre>{JSON.stringify(value,null,2)}</pre>;
}
