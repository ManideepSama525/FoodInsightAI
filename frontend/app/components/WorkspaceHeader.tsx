'use client';

type WorkspaceHeaderProps = {
  ready: boolean | null;
  busy: string;
};

export default function WorkspaceHeader({ ready, busy }: WorkspaceHeaderProps) {
  const state = ready === true ? 'online' : ready === false ? 'offline' : 'checking';
  const label = ready === true ? 'API Operational' : ready === false ? 'API Unavailable' : 'Checking API';

  return (
    <header className="workspace-header">
      <div className="workspace-brand">
        <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
        <div><div className="brand-name">FoodInsight<span>AI</span></div><div className="brand-subtitle">Evidence-aware food intelligence</div></div>
      </div>
      <div className="workspace-center"><div className="workspace-search"><span>⌕</span><span>Evidence workspace</span><small>LOCAL-FIRST</small></div></div>
      <div className="workspace-status">
        <div className={`status-pill ${state}`}><span className="status-dot" />{label}</div>
        {busy && <div className="activity-pill"><span className="activity-spinner" />{busy}</div>}
      </div>
    </header>
  );
}
