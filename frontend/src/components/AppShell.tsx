import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Activity,
  BookOpen,
  Bot,
  BriefcaseBusiness,
  ChevronRight,
  CircleGauge,
  GitBranch,
  Lightbulb,
  Menu,
  PanelLeftClose,
  Settings,
  Target,
  X
} from 'lucide-react';
import { useAlertNotifications } from '../hooks/useAlertNotifications';

const items = [
  { to: '/', label: 'Hoje', icon: Activity, end: true },
  { to: '/painel', label: 'Painel', icon: CircleGauge },
  { to: '/decisoes', label: 'Decisões', icon: GitBranch },
  { to: '/projetos', label: 'Projetos', icon: BriefcaseBusiness },
  { to: '/metas', label: 'Metas', icon: Target },
  { to: '/hipoteses', label: 'Hipóteses', icon: Lightbulb },
  { to: '/mapa', label: 'Mapa', icon: GitBranch },
  { to: '/diario', label: 'Diário', icon: BookOpen },
  { to: '/oraculo', label: 'Oráculo', icon: Bot },
  { to: '/configuracoes', label: 'Configurações', icon: Settings }
];

function Sidebar({ compact, onCompact, onNavigate }: { compact: boolean; onCompact: () => void; onNavigate?: () => void }) {
  return (
    <aside className={`flex h-full flex-col border-r border-ink-700/80 bg-ink-950/95 ${compact ? 'w-[76px]' : 'w-[238px]'}`}>
      <div className={`flex h-[70px] items-center border-b border-ink-700/70 ${compact ? 'justify-center px-3' : 'justify-between px-5'}`}>
        <NavLink to="/" className="flex min-w-0 items-center gap-3" onClick={onNavigate} aria-label="Oráculo, ir para Hoje">
          <span className="relative grid h-8 w-8 shrink-0 place-items-center rounded-full border border-signal-500/60" aria-hidden="true">
            <span className="h-1.5 w-1.5 rounded-full bg-signal-500 shadow-[0_0_12px_rgba(200,240,106,.65)]" />
            <span className="absolute -right-0.5 top-1 h-1 w-1 rounded-full bg-slate-500" />
          </span>
          {!compact && (
            <span className="min-w-0">
              <span className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-100">Oráculo</span>
              <span className="mt-0.5 block font-mono text-[9px] uppercase tracking-widest text-slate-600">Estado Zero</span>
            </span>
          )}
        </NavLink>
        {!compact && (
          <button type="button" className="btn-ghost hidden p-2 lg:inline-flex" onClick={onCompact} aria-label="Recolher navegação">
            <PanelLeftClose className="h-4 w-4" />
          </button>
        )}
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Navegação principal">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={compact ? label : undefined}
            onClick={onNavigate}
            className={({ isActive }) => `group flex min-h-10 items-center rounded-lg text-xs font-medium uppercase tracking-[0.08em] transition ${compact ? 'justify-center px-2' : 'gap-3 px-3'} ${isActive ? 'bg-signal-500/10 text-signal-500' : 'text-slate-500 hover:bg-ink-800 hover:text-slate-200'}`}
          >
            <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
            {!compact && <span className="truncate">{label}</span>}
            {!compact && <ChevronRight className="ml-auto h-3.5 w-3.5 opacity-0 transition group-hover:opacity-50" />}
          </NavLink>
        ))}
      </nav>

      <div className={`border-t border-ink-700/70 p-4 ${compact ? 'text-center' : ''}`}>
        {!compact ? (
          <>
            <div className="flex items-center gap-2 text-[11px] text-slate-500">
              <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
              Modo local
            </div>
            <p className="mt-2 font-mono text-[9px] uppercase tracking-widest text-slate-700">Local-first // v0.1</p>
          </>
        ) : (
          <button type="button" className="btn-ghost p-2" onClick={onCompact} aria-label="Expandir navegação">
            <Menu className="h-4 w-4" />
          </button>
        )}
      </div>
    </aside>
  );
}

export default function AppShell() {
  useAlertNotifications();
  const [compact, setCompact] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const current = items.find((item) => item.end ? location.pathname === item.to : location.pathname.startsWith(item.to));

  return (
    <div className="min-h-screen bg-transparent">
      <a href="#main-content" className="fixed left-3 top-3 z-[70] -translate-y-20 rounded-lg bg-signal-500 px-3 py-2 text-sm font-semibold text-ink-950 focus:translate-y-0">Pular para o conteúdo</a>
      <div className="fixed inset-y-0 left-0 z-40 hidden lg:block">
        <Sidebar compact={compact} onCompact={() => setCompact((value) => !value)} />
      </div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm lg:hidden" onMouseDown={() => setMobileOpen(false)} role="presentation">
          <div className="h-full w-[min(86vw,280px)]" onMouseDown={(event) => event.stopPropagation()}>
            <Sidebar compact={false} onCompact={() => undefined} onNavigate={() => setMobileOpen(false)} />
          </div>
          <button className="absolute right-4 top-4 rounded-full border border-ink-700 bg-ink-900 p-2 text-slate-300" onClick={() => setMobileOpen(false)} aria-label="Fechar menu"><X className="h-5 w-5" /></button>
        </div>
      )}

      <div className={`min-h-screen transition-[padding] ${compact ? 'lg:pl-[76px]' : 'lg:pl-[238px]'}`}>
        <div className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-ink-700/70 bg-ink-950/85 px-4 backdrop-blur-xl lg:hidden">
          <button type="button" className="btn-ghost -ml-2 p-2" onClick={() => setMobileOpen(true)} aria-label="Abrir menu"><Menu className="h-5 w-5" /></button>
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-200">{current?.label || 'Oráculo'}</span>
          <span className="h-2 w-2 rounded-full bg-slate-600" aria-label="Modo local" />
        </div>
        <main id="main-content" className="mx-auto w-full max-w-[1620px] px-4 py-5 sm:px-6 sm:py-7 xl:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
