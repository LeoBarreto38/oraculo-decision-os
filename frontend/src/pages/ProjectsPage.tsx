import { useMemo, useState, type FormEvent } from 'react';
import { CheckCircle2, Clock3, Edit3, Filter, Plus, RefreshCw, Search, Trash2 } from 'lucide-react';
import { DataModeBanner, EmptyState, Feedback, FormShell, Modal, PageHeader, ProgressBar, StatusBadge } from '../components/ui';
import { seedProjects, seedTasks } from '../data/fallback';
import { useApiResource } from '../hooks/useApiResource';
import { api } from '../services/api';
import { currency, formatDate } from '../utils/format';
import type { Project, ProjectStatus, StrategicCategory, Task } from '../types';

const emptyProject: Omit<Project, 'id'> = {
  name: '', description: '', type: 'PRIORIDADE_FINANCEIRA', status: 'ACTIVE', strategic_value: 5,
  revenue_potential: 5, time_to_value: 5, cash_requirement: 0, risk_level: 5,
  validation_level: 0, next_action: ''
};

const emptyTask: Omit<Task, 'id'> = {
  project_id: null, goal_id: null, title: '', description: '', priority: 2, due_at: null,
  status: 'TODO', estimated_minutes: 30, actual_minutes: 0, strategic_category: 'CASH'
};

export default function ProjectsPage() {
  const projects = useApiResource(api.projects.list, seedProjects);
  const tasks = useApiResource(api.tasks.list, seedTasks);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('ALL');
  const [projectModal, setProjectModal] = useState(false);
  const [taskModal, setTaskModal] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectForm, setProjectForm] = useState<Omit<Project, 'id'>>(emptyProject);
  const [taskForm, setTaskForm] = useState<Omit<Task, 'id'>>(emptyTask);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: 'idle' | 'success' | 'error'; message?: string }>({ kind: 'idle' });

  const filtered = useMemo(() => projects.data.filter((project) => {
    const matchesQuery = `${project.name} ${project.description} ${project.next_action}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (status === 'ALL' || project.status === status);
  }), [projects.data, query, status]);

  function openProject(project?: Project) {
    setEditingProject(project || null);
    setProjectForm(project ? { ...project } : emptyProject);
    setProjectModal(true);
  }

  function openTask(project?: Project) {
    setTaskForm({ ...emptyTask, project_id: project?.id ?? projects.data[0]?.id ?? null });
    setTaskModal(true);
  }

  async function saveProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      if (editingProject) {
        if (String(editingProject.id).startsWith('seed-')) throw new Error('Conecte a API local antes de editar os dados de referência.');
        await api.projects.update(editingProject.id, projectForm);
      } else await api.projects.create(projectForm);
      setProjectModal(false);
      setFeedback({ kind: 'success', message: editingProject ? 'Projeto atualizado.' : 'Projeto registrado.' });
      await projects.reload();
    } catch (error) {
      setFeedback({ kind: 'error', message: error instanceof Error ? error.message : 'Falha ao gravar o projeto.' });
    } finally { setBusy(false); }
  }

  async function saveTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      await api.tasks.create(taskForm);
      setTaskModal(false);
      setFeedback({ kind: 'success', message: 'Tarefa registrada.' });
      await tasks.reload();
    } catch (error) {
      setFeedback({ kind: 'error', message: error instanceof Error ? error.message : 'Falha ao gravar a tarefa.' });
    } finally { setBusy(false); }
  }

  async function removeProject(project: Project) {
    if (String(project.id).startsWith('seed-')) return setFeedback({ kind: 'error', message: 'Conecte a API local antes de excluir dados.' });
    if (!window.confirm(`Arquivar/excluir o projeto "${project.name}"? Esta ação pode afetar tarefas relacionadas.`)) return;
    try {
      await api.projects.remove(project.id);
      setFeedback({ kind: 'success', message: 'Projeto removido.' });
      await projects.reload();
    } catch (error) { setFeedback({ kind: 'error', message: error instanceof Error ? error.message : 'Falha ao remover projeto.' }); }
  }

  async function completeTask(task: Task) {
    if (String(task.id).startsWith('seed-')) return setFeedback({ kind: 'error', message: 'Conecte a API local para alterar tarefas.' });
    try {
      await api.tasks.update(task.id, { status: 'DONE' });
      await tasks.reload();
    } catch (error) { setFeedback({ kind: 'error', message: error instanceof Error ? error.message : 'Falha ao atualizar tarefa.' }); }
  }

  return (
    <div>
      <PageHeader eyebrow="Portfólio de execução" title="Projetos" description="Projetos recebem estado explícito. Criar algo novo não substitui silenciosamente um projeto que chegou à fronteira comercial." actions={<><button className="btn-secondary" type="button" onClick={() => openTask()}><Plus className="h-4 w-4" /> Tarefa</button><button className="btn-primary" type="button" onClick={() => openProject()}><Plus className="h-4 w-4" /> Projeto</button></>} />
      <DataModeBanner source={projects.source} error={projects.error} loading={projects.loading} onRetry={() => { void projects.reload(); void tasks.reload(); }} />
      <Feedback {...feedback} />

      <div className="mb-4 flex flex-col gap-3 rounded-xl border border-ink-700 bg-ink-900 p-3 sm:flex-row">
        <label className="relative flex-1"><span className="sr-only">Buscar projetos</span><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" /><input className="input pl-9" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por projeto, ação ou contexto…" /></label>
        <label className="relative sm:w-52"><span className="sr-only">Filtrar por estado</span><Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" /><select className="input pl-9" value={status} onChange={(event) => setStatus(event.target.value)}><option value="ALL">Todos os estados</option>{['ACTIVE','VALIDATING','PAUSED','INVALIDATED','COMPLETED','ARCHIVED'].map((value) => <option key={value}>{value}</option>)}</select></label>
        <button className="btn-secondary" type="button" onClick={() => { void projects.reload(); void tasks.reload(); }} aria-label="Atualizar"><RefreshCw className="h-4 w-4" /></button>
      </div>

      <div className="grid gap-4 2xl:grid-cols-2">
        {filtered.map((project) => {
          const projectTasks = tasks.data.filter((task) => String(task.project_id) === String(project.id));
          const done = projectTasks.filter((task) => task.status === 'DONE').length;
          return (
            <article key={project.id} className="panel overflow-hidden">
              <div className="border-b border-ink-700 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0"><div className="mb-2 flex flex-wrap items-center gap-2"><StatusBadge value={project.status} /><span className="font-mono text-[10px] uppercase tracking-wider text-slate-600">{project.type.replaceAll('_', ' ')}</span></div><h2 className="text-lg font-semibold text-slate-100">{project.name}</h2><p className="mt-1.5 line-clamp-2 text-xs leading-5 text-slate-500">{project.description}</p></div>
                  <div className="flex shrink-0"><button type="button" className="btn-ghost p-2" onClick={() => openProject(project)} aria-label={`Editar ${project.name}`}><Edit3 className="h-4 w-4" /></button><button type="button" className="btn-ghost p-2 hover:text-red-300" onClick={() => void removeProject(project)} aria-label={`Excluir ${project.name}`}><Trash2 className="h-4 w-4" /></button></div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2"><div className="rounded-lg bg-ink-950 p-2.5"><p className="eyebrow">Valor</p><p className="mt-1 font-mono text-sm text-slate-300">{project.strategic_value}/10</p></div><div className="rounded-lg bg-ink-950 p-2.5"><p className="eyebrow">Receita</p><p className="mt-1 font-mono text-sm text-slate-300">{currency(project.revenue_potential,true)}</p></div><div className="rounded-lg bg-ink-950 p-2.5"><p className="eyebrow">Caixa</p><p className="mt-1 font-mono text-sm text-slate-300">{currency(project.cash_requirement, true)}</p></div></div>
                <div className="mt-4"><ProgressBar value={project.validation_level} max={10} tone="sky" label="Nível de validação" /></div>
                <div className="mt-4 rounded-lg border border-signal-500/15 bg-signal-500/[.04] p-3"><p className="eyebrow !text-signal-500/70">Próxima ação</p><p className="mt-1.5 text-xs leading-5 text-slate-300">{project.next_action || 'Não definida'}</p></div>
              </div>
              <div>
                <div className="flex items-center justify-between px-4 py-3"><div><p className="eyebrow">Tarefas</p><p className="mt-1 text-[11px] text-slate-600">{done}/{projectTasks.length} concluídas</p></div><button className="btn-ghost text-xs" type="button" onClick={() => openTask(project)}><Plus className="h-3.5 w-3.5" /> Adicionar</button></div>
                <div className="divide-y divide-ink-700/70 border-t border-ink-700/70">
                  {projectTasks.slice(0, 4).map((task) => <div key={task.id} className="flex items-center gap-3 px-4 py-3"><button className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border ${task.status === 'DONE' ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300' : 'border-ink-700 text-slate-600 hover:border-slate-500'}`} type="button" onClick={() => void completeTask(task)} aria-label={`Concluir ${task.title}`}><CheckCircle2 className="h-3.5 w-3.5" /></button><div className="min-w-0 flex-1"><p className={`truncate text-xs ${task.status === 'DONE' ? 'text-slate-600 line-through' : 'text-slate-300'}`}>{task.title}</p><div className="mt-1 flex items-center gap-2 text-[10px] text-slate-600"><span>{task.strategic_category}</span>{task.due_at && <span>· {formatDate(task.due_at)}</span>}<span className="flex items-center gap-1"><Clock3 className="h-2.5 w-2.5" />{task.estimated_minutes}m</span></div></div></div>)}
                  {!projectTasks.length && <p className="px-4 pb-4 text-xs text-slate-600">Nenhuma tarefa associada.</p>}
                </div>
              </div>
            </article>
          );
        })}
      </div>
      {!filtered.length && <div className="panel"><EmptyState title="Nenhum projeto encontrado" description="Ajuste os filtros ou registre um projeto com objetivo e próxima ação claros." action={<button className="btn-primary" onClick={() => openProject()}><Plus className="h-4 w-4" /> Novo projeto</button>} /></div>}

      <Modal open={projectModal} onClose={() => setProjectModal(false)} title={editingProject ? 'Editar projeto' : 'Registrar projeto'} description="Métricas de 0 a 10 servem para comparação; não representam precisão científica.">
        <FormShell onSubmit={saveProject} busy={busy} submitLabel={editingProject ? 'Salvar alterações' : 'Registrar projeto'} onCancel={() => setProjectModal(false)}>
          <div className="grid gap-4 sm:grid-cols-2"><label><span className="label">Nome</span><input className="input" required value={projectForm.name} onChange={(e) => setProjectForm((v) => ({...v,name:e.target.value}))} /></label><label><span className="label">Tipo</span><input className="input" required value={projectForm.type} onChange={(e) => setProjectForm((v) => ({...v,type:e.target.value.toUpperCase().replaceAll(' ','_')}))} /></label></div>
          <label><span className="label">Descrição</span><textarea className="input min-h-24" required value={projectForm.description} onChange={(e) => setProjectForm((v) => ({...v,description:e.target.value}))} /></label>
          <div className="grid gap-4 sm:grid-cols-3"><label><span className="label">Estado</span><select className="input" value={projectForm.status} onChange={(e) => setProjectForm((v) => ({...v,status:e.target.value as ProjectStatus}))}>{['ACTIVE','VALIDATING','PAUSED','INVALIDATED','COMPLETED','ARCHIVED'].map((x)=><option key={x}>{x}</option>)}</select></label><label><span className="label">Potencial de receita (R$)</span><input className="input" type="number" min="0" step="0.01" value={projectForm.revenue_potential} onChange={(e) => setProjectForm((v)=>({...v,revenue_potential:Number(e.target.value)}))} /></label><label><span className="label">Necessidade de caixa (R$)</span><input className="input" type="number" min="0" step="0.01" value={projectForm.cash_requirement} onChange={(e) => setProjectForm((v)=>({...v,cash_requirement:Number(e.target.value)}))} /></label></div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{([['strategic_value','Valor estratégico'],['time_to_value','Velocidade até valor'],['risk_level','Risco'],['validation_level','Validação']] as const).map(([key,label])=><label key={key}><span className="label">{label}: {projectForm[key]}/10</span><input className="w-full accent-[#c8f06a]" type="range" min="0" max="10" value={projectForm[key]} onChange={(e)=>setProjectForm((v)=>({...v,[key]:Number(e.target.value)}))} /></label>)}</div>
          <label><span className="label">Próxima ação observável</span><input className="input" required value={projectForm.next_action} onChange={(e) => setProjectForm((v) => ({...v,next_action:e.target.value}))} /></label>
        </FormShell>
      </Modal>

      <Modal open={taskModal} onClose={() => setTaskModal(false)} title="Registrar tarefa" description="A tarefa deve produzir um resultado verificável e pertencer a uma categoria estratégica.">
        <FormShell onSubmit={saveTask} busy={busy} submitLabel="Registrar tarefa" onCancel={() => setTaskModal(false)}>
          <label><span className="label">Projeto</span><select className="input" required value={taskForm.project_id ?? ''} onChange={(e)=>setTaskForm((v)=>({...v,project_id:e.target.value}))}><option value="">Selecione</option>{projects.data.map((p)=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
          <label><span className="label">Título</span><input className="input" required value={taskForm.title} onChange={(e)=>setTaskForm((v)=>({...v,title:e.target.value}))} /></label>
          <label><span className="label">Descrição</span><textarea className="input min-h-20" value={taskForm.description} onChange={(e)=>setTaskForm((v)=>({...v,description:e.target.value}))} /></label>
          <div className="grid gap-4 sm:grid-cols-2"><label><span className="label">Categoria</span><select className="input" value={taskForm.strategic_category} onChange={(e)=>setTaskForm((v)=>({...v,strategic_category:e.target.value as StrategicCategory}))}>{['CASH','ASSET','LEARNING','MAINTENANCE','DISTRACTION'].map((x)=><option key={x}>{x}</option>)}</select></label><label><span className="label">Prazo</span><input className="input" type="datetime-local" value={taskForm.due_at || ''} onChange={(e)=>setTaskForm((v)=>({...v,due_at:e.target.value || null}))} /></label></div>
          <div className="grid gap-4 sm:grid-cols-2"><label><span className="label">Prioridade (1–5)</span><input className="input" type="number" min="1" max="5" value={taskForm.priority} onChange={(e)=>setTaskForm((v)=>({...v,priority:Number(e.target.value)}))} /></label><label><span className="label">Estimativa (min)</span><input className="input" type="number" min="5" step="5" value={taskForm.estimated_minutes} onChange={(e)=>setTaskForm((v)=>({...v,estimated_minutes:Number(e.target.value)}))} /></label></div>
        </FormShell>
      </Modal>
    </div>
  );
}
