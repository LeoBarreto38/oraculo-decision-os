import { useMemo, useState, type FormEvent } from 'react';
import {
  AlertOctagon,
  ArrowRight,
  CalendarClock,
  Check,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Flag,
  RefreshCw,
  Save,
  Target,
  TriangleAlert
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { fallbackToday } from '../data/fallback';
import { useApiResource } from '../hooks/useApiResource';
import { currency, formatDate, toLocalDate } from '../utils/format';
import { DataModeBanner, EmptyState, Feedback, PageHeader, ProgressBar, StatusBadge } from '../components/ui';
import type { Task } from '../types';

const todayLabel = new Intl.DateTimeFormat('pt-BR', {
  weekday: 'long', day: '2-digit', month: 'long'
}).format(new Date());

const initialCheckin = {
  did: '',
  did_not: '',
  blocker: '',
  learned: '',
  strategy_change: '',
  notes: '',
  energy: 3,
  focus: 3
};

export default function TodayPage() {
  const resource = useApiResource(api.today, fallbackToday);
  const { data } = resource;
  const [checkin, setCheckin] = useState(initialCheckin);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: 'idle' | 'success' | 'error'; message?: string }>({ kind: 'idle' });
  const [taskBusy, setTaskBusy] = useState<string | number | null>(null);
  const [alertBusy, setAlertBusy] = useState<string | number | null>(null);

  const prioritySlots = useMemo(() => Array.from({ length: 3 }, (_, index) => data.priorities[index]), [data.priorities]);
  const progress = Math.min(100, Math.round((data.financial.current_income / Math.max(1, data.financial.target_income)) * 100));

  async function completeTask(task: Task) {
    if (String(task.id).startsWith('seed-')) {
      setFeedback({ kind: 'error', message: 'A API local precisa estar disponível para registrar a conclusão.' });
      return;
    }
    setTaskBusy(task.id);
    try {
      await api.tasks.update(task.id, { status: 'DONE' });
      setFeedback({ kind: 'success', message: `Tarefa concluída: ${task.title}` });
      await resource.reload();
    } catch (error) {
      setFeedback({ kind: 'error', message: error instanceof Error ? error.message : 'Não foi possível concluir a tarefa.' });
    } finally {
      setTaskBusy(null);
    }
  }

  async function acknowledgeAlert(alertId: string | number) {
    if (String(alertId).startsWith('seed-')) return setFeedback({ kind: 'error', message: 'Conecte a API local para reconhecer alertas.' });
    setAlertBusy(alertId);
    try {
      await api.alerts.acknowledge(alertId);
      setFeedback({ kind: 'success', message: 'Alerta reconhecido.' });
      await resource.reload();
    } catch (error) {
      setFeedback({ kind: 'error', message: error instanceof Error ? error.message : 'Falha ao reconhecer o alerta.' });
    } finally {
      setAlertBusy(null);
    }
  }

  async function submitCheckin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setFeedback({ kind: 'idle' });
    try {
      await api.checkins.create({
        date: toLocalDate(),
        energy: checkin.energy,
        focus: checkin.focus,
        main_result: checkin.did,
        what_worked: checkin.learned,
        what_failed: checkin.did_not,
        blockers: checkin.blocker,
        learning: checkin.learned,
        strategy_change: checkin.strategy_change,
        feedback: `Informação estratégica: ${checkin.strategy_change}\nNotas: ${checkin.notes}`,
        did: checkin.did,
        did_not: checkin.did_not,
        free_text: checkin.notes
      });
      setCheckin(initialCheckin);
      setFeedback({ kind: 'success', message: 'Check-in registrado no estado do Oráculo.' });
    } catch (error) {
      setFeedback({ kind: 'error', message: error instanceof Error ? error.message : 'Não foi possível salvar o check-in.' });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Execução diária"
        title="Hoje"
        description={`${todayLabel.charAt(0).toUpperCase()}${todayLabel.slice(1)}. O foco permanece em gerar caixa com evidência, não apenas atividade.`}
        actions={<button type="button" className="btn-secondary" onClick={resource.reload}><RefreshCw className="h-4 w-4" /> Atualizar</button>}
      />
      <DataModeBanner source={resource.source} error={resource.error} loading={resource.loading} onRetry={resource.reload} />
      <Feedback {...feedback} />

      <section className="panel mb-5 overflow-hidden" aria-labelledby="main-goal-title">
        <div className="grid lg:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(150px,.45fr))]">
          <div className="border-b border-ink-700 p-5 lg:border-b-0 lg:border-r">
            <div className="flex items-center gap-2 text-signal-500">
              <Target className="h-4 w-4" />
              <p className="eyebrow !text-signal-500">Meta principal</p>
            </div>
            <h2 id="main-goal-title" className="mt-3 text-xl font-semibold text-slate-100">{data.main_goal.title}</h2>
            <div className="mt-5 max-w-2xl">
              <ProgressBar value={data.financial.current_income} max={data.financial.target_income} label={`${progress}% da meta mensal`} />
            </div>
          </div>
          <div className="border-b border-r border-ink-700 p-5 lg:border-b-0">
            <p className="eyebrow">Renda atual</p>
            <p className="metric-value mt-3">{currency(data.financial.current_income, true)}</p>
            <p className="mt-1 text-xs text-slate-600">por mês</p>
          </div>
          <div className="border-b border-ink-700 p-5 sm:border-r lg:border-b-0">
            <p className="eyebrow">Meta</p>
            <p className="metric-value mt-3">{currency(data.financial.target_income, true)}</p>
            <p className="mt-1 text-xs text-slate-600">por mês</p>
          </div>
          <div className="p-5">
            <p className="eyebrow text-amber-400">Gap</p>
            <p className="metric-value mt-3 text-amber-200">{currency(data.financial.gap, true)}</p>
            <p className="mt-1 text-xs text-slate-600">a fechar</p>
          </div>
        </div>
      </section>

      <section className="mb-5" aria-labelledby="priorities-title">
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <p className="eyebrow mb-1">Limite operacional</p>
            <h2 id="priorities-title" className="text-lg font-semibold text-slate-100">As 3 prioridades</h2>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600">3 / 3</span>
        </div>
        <div className="grid gap-3 xl:grid-cols-3">
          {prioritySlots.map((task, index) => (
            <article key={task?.id ?? `empty-${index}`} className={`panel group p-4 ${index === 0 ? 'border-signal-500/25' : ''}`}>
              <div className="flex items-start gap-3">
                <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border font-mono text-xs ${index === 0 ? 'border-signal-500/35 bg-signal-500/10 text-signal-500' : 'border-ink-700 bg-ink-850 text-slate-500'}`}>0{index + 1}</span>
                <div className="min-w-0 flex-1">
                  {task ? (
                    <>
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="text-sm font-medium leading-5 text-slate-200">{task.title}</h3>
                        <button type="button" className="grid h-7 w-7 shrink-0 place-items-center rounded-full border border-ink-700 text-slate-600 transition hover:border-emerald-500/40 hover:text-emerald-300" onClick={() => void completeTask(task)} disabled={taskBusy === task.id} aria-label={`Concluir: ${task.title}`}>
                          <Check className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      {task.description && <p className="mt-1.5 line-clamp-2 text-xs leading-5 text-slate-500">{task.description}</p>}
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <StatusBadge value={task.strategic_category} />
                        <span className="flex items-center gap-1 text-[11px] text-slate-600"><Clock3 className="h-3 w-3" /> {task.estimated_minutes} min</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <h3 className="text-sm font-medium text-slate-500">Prioridade não definida</h3>
                      <p className="mt-1.5 text-xs leading-5 text-slate-600">Defina um resultado verificável para ocupar este espaço.</p>
                    </>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="mb-5 grid gap-4 xl:grid-cols-[1.15fr_.85fr]">
        <section className="panel" aria-labelledby="signals-title">
          <div className="panel-header">
            <div>
              <p className="eyebrow mb-1">Atenção operacional</p>
              <h2 id="signals-title" className="text-sm font-semibold text-slate-200">Sinais que exigem resposta</h2>
            </div>
            <span className="rounded-full border border-ink-700 bg-ink-850 px-2 py-1 font-mono text-[10px] text-slate-500">{data.overdue_tasks.length + data.alerts.length}</span>
          </div>
          <div className="divide-y divide-ink-700/70">
            {data.alerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 px-4 py-3.5">
                <AlertOctagon className={`mt-0.5 h-4 w-4 shrink-0 ${alert.severity === 'CRITICAL' || alert.severity === 'HIGH' ? 'text-red-400' : 'text-amber-400'}`} />
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2"><StatusBadge value={alert.severity} /><span className="font-mono text-[10px] text-slate-600">{alert.type}</span></div>
                  <p className="text-xs leading-5 text-slate-300">{alert.message}</p>
                  <button type="button" className="btn-ghost mt-2 px-2 py-1 text-[11px]" disabled={alertBusy === alert.id} onClick={() => void acknowledgeAlert(alert.id)}><Check className="h-3 w-3" />{alertBusy === alert.id ? 'Reconhecendo…' : 'Reconhecer'}</button>
                </div>
              </div>
            ))}
            {data.overdue_tasks.map((task) => (
              <div key={task.id} className="flex items-start gap-3 px-4 py-3.5">
                <CalendarClock className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
                <div className="min-w-0 flex-1"><p className="text-xs font-medium text-slate-300">{task.title}</p><p className="mt-1 text-[11px] text-slate-600">Atrasada desde {formatDate(task.due_at)}</p></div>
              </div>
            ))}
            {!data.alerts.length && !data.overdue_tasks.length && <EmptyState title="Sem sinais urgentes" description="Nenhum alerta ou atraso foi retornado pela API." />}
          </div>
        </section>

        <section className="panel" aria-labelledby="pending-title">
          <div className="panel-header">
            <div><p className="eyebrow mb-1">Fila de julgamento</p><h2 id="pending-title" className="text-sm font-semibold text-slate-200">Decisões pendentes</h2></div>
            <Link to="/decisoes" className="btn-ghost p-2 text-xs">Ver todas <ArrowRight className="h-3.5 w-3.5" /></Link>
          </div>
          <div className="divide-y divide-ink-700/70">
            {data.pending_decisions.slice(0, 4).map((decision) => (
              <Link key={decision.id} to="/decisoes" className="flex items-start gap-3 px-4 py-3.5 transition hover:bg-ink-850">
                <CircleAlert className="mt-0.5 h-4 w-4 shrink-0 text-sky-400" />
                <div className="min-w-0 flex-1"><div className="flex items-center gap-2"><span className="font-mono text-[10px] text-slate-600">{decision.code || `#${decision.id}`}</span><StatusBadge value={decision.status} /></div><p className="mt-1.5 text-xs font-medium leading-5 text-slate-300">{decision.title}</p></div>
                <ArrowRight className="mt-1 h-3.5 w-3.5 text-slate-700" />
              </Link>
            ))}
            {!data.pending_decisions.length && <EmptyState title="Nenhuma decisão pendente" description="A fila de decisões importantes está vazia." />}
          </div>
        </section>
      </div>

      <div className="mb-5 grid gap-4 sm:grid-cols-2">
        <section className="panel p-4">
          <div className="flex items-start gap-3"><TriangleAlert className="mt-0.5 h-4 w-4 text-amber-400" /><div><p className="eyebrow mb-1">Projetos sem avanço</p>{data.stalled_projects.length ? data.stalled_projects.map((project) => <div key={project.id} className="mt-2"><div className="flex items-center gap-2"><span className="text-sm font-medium text-slate-200">{project.name}</span><StatusBadge value={project.status} /></div><p className="mt-1 text-xs text-slate-500">Próxima ação: {project.next_action || 'não definida'}</p></div>) : <p className="mt-2 text-xs text-slate-500">Nenhum projeto estagnado detectado.</p>}</div></div>
        </section>
        <section className="panel p-4">
          <div className="flex items-start gap-3"><Flag className="mt-0.5 h-4 w-4 text-signal-500" /><div><p className="eyebrow mb-1">Próximo marco</p><p className="mt-2 text-sm font-medium text-slate-200">{typeof data.next_milestone === 'string' ? data.next_milestone : data.next_milestone.title}</p>{typeof data.next_milestone !== 'string' && data.next_milestone.due_at && <p className="mt-1 text-xs text-slate-500">Prazo: {formatDate(data.next_milestone.due_at)}</p>}</div></div>
        </section>
      </div>

      <section className="panel overflow-hidden" aria-labelledby="checkin-title">
        <div className="border-b border-ink-700 px-5 py-4">
          <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-signal-500" /><p className="eyebrow !text-signal-500">Fechamento do dia</p></div>
          <h2 id="checkin-title" className="mt-2 text-lg font-semibold text-slate-100">Check-in completo</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">Registre evidência antes de reinterpretar o dia. Texto simples e factual é suficiente.</p>
        </div>
        <form onSubmit={submitCheckin} className="p-5">
          <div className="grid gap-4 lg:grid-cols-2">
            {[
              ['did', 'O que você fez?', 'Resultados observáveis, entregas e interações externas.'],
              ['did_not', 'O que não fez?', 'Compromissos que ficaram em aberto, sem justificativa cosmética.'],
              ['blocker', 'O que impediu?', 'Restrição real, decisão ruim ou padrão comportamental.'],
              ['learned', 'O que aprendeu?', 'Nova evidência, objeção, capacidade ou limite descoberto.'],
              ['strategy_change', 'Há informação que muda nossa estratégia?', 'Diga qual conclusão deve ser atualizada e por quê.']
            ].map(([field, label, placeholder], index) => (
              <label key={field} className={index === 4 ? 'lg:col-span-2' : ''}>
                <span className="label">{label}</span>
                <textarea className="input min-h-24 resize-y" required={field === 'did'} placeholder={placeholder} value={checkin[field as keyof typeof checkin] as string} onChange={(event) => setCheckin((value) => ({ ...value, [field]: event.target.value }))} />
              </label>
            ))}
          </div>
          <label className="mt-4 block">
            <span className="label">Notas livres</span>
            <textarea className="input min-h-36 resize-y" placeholder="Contexto adicional que deve permanecer no histórico…" value={checkin.notes} onChange={(event) => setCheckin((value) => ({ ...value, notes: event.target.value }))} />
          </label>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {(['energy', 'focus'] as const).map((field) => (
              <label key={field}>
                <span className="label">{field === 'energy' ? 'Energia' : 'Foco'}: <strong className="font-mono text-slate-200">{checkin[field]}/5</strong></span>
                <input className="w-full accent-[#c8f06a]" type="range" min="1" max="5" value={checkin[field]} onChange={(event) => setCheckin((value) => ({ ...value, [field]: Number(event.target.value) }))} />
              </label>
            ))}
          </div>
          <div className="mt-5 flex justify-end border-t border-ink-700 pt-4"><button className="btn-primary" type="submit" disabled={saving}><Save className="h-4 w-4" />{saving ? 'Salvando…' : 'Registrar check-in'}</button></div>
        </form>
      </section>
    </div>
  );
}
