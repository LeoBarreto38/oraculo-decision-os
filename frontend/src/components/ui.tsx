import { type FormEvent, type ReactNode, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  CloudOff,
  Database,
  LoaderCircle,
  RefreshCw,
  X
} from 'lucide-react';
import type { DataSource } from '../types';

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return (
    <header className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div className="min-w-0">
        {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
        <h1 className="text-2xl font-semibold tracking-tight text-slate-50 sm:text-[28px]">{title}</h1>
        {description && <p className="mt-1.5 max-w-3xl text-sm leading-6 text-slate-500">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}

export function DataModeBanner({ source, error, loading, onRetry }: { source: DataSource; error: string | null; loading?: boolean; onRetry?: () => void }) {
  if (source === 'api' && !error && !loading) {
    return (
      <div className="mb-4 flex items-center gap-2 text-xs text-slate-500" role="status">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
        Dados sincronizados com o banco local
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mb-4 flex items-center gap-2 text-xs text-slate-500" role="status">
        <LoaderCircle className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        Consultando o estado local…
      </div>
    );
  }

  return (
    <div className="mb-4 flex flex-col gap-3 rounded-lg border border-amber-500/25 bg-amber-500/[.06] px-3.5 py-3 text-sm sm:flex-row sm:items-center sm:justify-between" role="alert">
      <div className="flex items-start gap-2.5">
        {navigator.onLine ? <Database className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" /> : <CloudOff className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />}
        <div>
          <p className="font-medium text-amber-100">Exibindo Estado Zero de referência</p>
          <p className="mt-0.5 text-xs leading-5 text-amber-100/60">{error || 'A API local ainda não respondeu.'} Alterações só serão confirmadas se o backend gravar os dados.</p>
        </div>
      </div>
      {onRetry && (
        <button type="button" className="btn-ghost shrink-0 text-amber-100" onClick={onRetry}>
          <RefreshCw className="h-3.5 w-3.5" /> Tentar novamente
        </button>
      )}
    </div>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const normalized = value.toUpperCase();
  const style = normalized.includes('CRITICAL') || normalized.includes('INVALID') || normalized.includes('OVERDUE')
    ? 'border-red-500/30 bg-red-500/10 text-red-300'
    : normalized.includes('HIGH') || normalized.includes('PAUSED') || normalized.includes('PENDING')
      ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
      : normalized.includes('ACTIVE') || normalized.includes('DONE') || normalized.includes('COMPLETED') || normalized.includes('DECIDED')
        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
        : normalized.includes('VALIDATING') || normalized.includes('TESTING') || normalized.includes('OPEN')
          ? 'border-sky-500/30 bg-sky-500/10 text-sky-300'
          : 'border-ink-700 bg-ink-800 text-slate-400';
  return <span className={`inline-flex rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider ${style}`}>{value.replaceAll('_', ' ')}</span>;
}

export function MetricCard({ label, value, detail, icon, accent = false }: { label: string; value: ReactNode; detail?: ReactNode; icon?: ReactNode; accent?: boolean }) {
  return (
    <article className={`panel relative overflow-hidden p-4 ${accent ? 'border-signal-500/25' : ''}`}>
      {accent && <div className="absolute inset-x-0 top-0 h-px bg-signal-500/70" />}
      <div className="flex items-center justify-between gap-3">
        <p className="eyebrow">{label}</p>
        {icon && <span className="text-slate-600">{icon}</span>}
      </div>
      <div className="metric-value mt-3">{value}</div>
      {detail && <div className="mt-2 text-xs leading-5 text-slate-500">{detail}</div>}
    </article>
  );
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center px-5 py-8 text-center">
      <div className="mb-3 h-px w-8 bg-ink-700" />
      <p className="text-sm font-medium text-slate-300">{title}</p>
      <p className="mt-1 max-w-sm text-xs leading-5 text-slate-600">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Modal({ open, title, description, onClose, children, width = 'max-w-2xl' }: { open: boolean; title: string; description?: string; onClose: () => void; children: ReactNode; width?: string }) {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/75 p-0 backdrop-blur-sm sm:items-center sm:p-4" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className={`max-h-[92vh] w-full overflow-y-auto rounded-t-2xl border border-ink-700 bg-ink-900 shadow-2xl sm:rounded-2xl ${width}`} role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <header className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-ink-700 bg-ink-900/95 px-5 py-4 backdrop-blur">
          <div>
            <h2 id="modal-title" className="font-semibold text-slate-100">{title}</h2>
            {description && <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>}
          </div>
          <button type="button" className="btn-ghost -mr-2 -mt-1 p-2" onClick={onClose} aria-label="Fechar">
            <X className="h-4 w-4" />
          </button>
        </header>
        <div className="p-5">{children}</div>
      </section>
    </div>
  );
}

export function Feedback({ kind, message }: { kind: 'success' | 'error' | 'idle'; message?: string | null }) {
  if (kind === 'idle' || !message) return null;
  return (
    <div className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 text-xs leading-5 ${kind === 'success' ? 'border-emerald-500/25 bg-emerald-500/[.07] text-emerald-200' : 'border-red-500/25 bg-red-500/[.07] text-red-200'}`} role={kind === 'error' ? 'alert' : 'status'}>
      {kind === 'success' ? <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" /> : <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />}
      {message}
    </div>
  );
}

export function FormShell({ onSubmit, children, busy, submitLabel, cancelLabel = 'Cancelar', onCancel }: { onSubmit: (event: FormEvent<HTMLFormElement>) => void; children: ReactNode; busy?: boolean; submitLabel: string; cancelLabel?: string; onCancel?: () => void }) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {children}
      <div className="flex flex-col-reverse gap-2 border-t border-ink-700 pt-4 sm:flex-row sm:justify-end">
        {onCancel && <button type="button" className="btn-secondary" onClick={onCancel}>{cancelLabel}</button>}
        <button type="submit" className="btn-primary" disabled={busy}>
          {busy && <LoaderCircle className="h-4 w-4 animate-spin" />}
          {busy ? 'Gravando…' : submitLabel}
        </button>
      </div>
    </form>
  );
}

export function ProgressBar({ value, max = 100, tone = 'signal', label }: { value: number; max?: number; tone?: 'signal' | 'sky' | 'amber' | 'red'; label?: string }) {
  const width = Math.max(0, Math.min(100, max ? (value / max) * 100 : 0));
  const color = tone === 'sky' ? 'bg-sky-400' : tone === 'amber' ? 'bg-amber-400' : tone === 'red' ? 'bg-red-400' : 'bg-signal-500';
  return (
    <div>
      {label && <div className="mb-1.5 flex justify-between text-[11px] text-slate-500"><span>{label}</span><span className="font-mono">{Math.round(width)}%</span></div>}
      <div className="h-1.5 overflow-hidden rounded-full bg-ink-700" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={value}>
        <div className={`h-full rounded-full transition-[width] ${color}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}
