import { useState, type FormEvent } from 'react';
import { BookOpen, Plus, Trash2 } from 'lucide-react';
import { DataModeBanner, EmptyState, Feedback, FormShell, Modal, PageHeader } from '../components/ui';
import { fallbackJournal } from '../data/fallback';
import { useApiResource } from '../hooks/useApiResource';
import { api } from '../services/api';
import { formatDate, toLocalDate } from '../utils/format';
import type { JournalEntry } from '../types';

export default function JournalPage() {
  const resource = useApiResource(api.journal.list, fallbackJournal);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{kind:'idle'|'success'|'error';message?:string}>({kind:'idle'});
  const [form, setForm] = useState({date: toLocalDate(), title: '', content: '', tags: ''});

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true);
    try {
      await api.journal.create({...form, tags: form.tags.split(',').map(tag => tag.trim()).filter(Boolean)});
      setOpen(false); setForm({date: toLocalDate(), title: '', content: '', tags: ''});
      setFeedback({kind:'success', message:'Entrada registrada.'}); await resource.reload();
    } catch (error) {
      setFeedback({kind:'error', message:error instanceof Error ? error.message : 'Falha ao registrar entrada.'});
    } finally { setBusy(false); }
  }

  async function remove(entry: JournalEntry) {
    if (!window.confirm(`Excluir a entrada "${entry.title}"?`)) return;
    try { await api.journal.remove(entry.id); await resource.reload(); }
    catch (error) { setFeedback({kind:'error', message:error instanceof Error ? error.message : 'Falha ao excluir entrada.'}); }
  }

  return <div>
    <PageHeader eyebrow="Memória factual" title="Diário" description="Registre fatos separadamente das interpretações." actions={<button className="btn-primary" onClick={()=>setOpen(true)}><Plus className="h-4 w-4"/> Nova entrada</button>}/>
    <DataModeBanner source={resource.source} error={resource.error} loading={resource.loading} onRetry={resource.reload}/>
    <Feedback {...feedback}/>
    <div className="space-y-3">{resource.data.map(entry=><article className="panel p-4" key={entry.id}>
      <div className="flex items-start gap-3"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-ink-700 bg-ink-950 text-slate-500"><BookOpen className="h-4 w-4"/></div>
      <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="font-mono text-[10px] uppercase tracking-widest text-slate-600">{formatDate(entry.date)}</p><h2 className="mt-1 text-sm font-semibold text-slate-200">{entry.title}</h2></div><button className="btn-ghost p-2 hover:text-red-300" onClick={()=>void remove(entry)} aria-label={`Excluir ${entry.title}`}><Trash2 className="h-4 w-4"/></button></div>
      <p className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-400">{entry.content}</p><div className="mt-3 flex flex-wrap gap-1.5">{(Array.isArray(entry.tags)?entry.tags:entry.tags.split(',')).filter(Boolean).map(tag=><span key={tag} className="rounded border border-ink-700 bg-ink-950 px-2 py-1 font-mono text-[9px] uppercase tracking-wider text-slate-500">{tag}</span>)}</div></div></div>
    </article>)}</div>
    {!resource.data.length&&<div className="panel"><EmptyState title="Diário vazio" description="Nenhuma entrada persistida."/></div>}
    <Modal open={open} onClose={()=>setOpen(false)} title="Nova entrada no diário"><FormShell onSubmit={save} busy={busy} submitLabel="Registrar entrada" onCancel={()=>setOpen(false)}>
      <div className="grid gap-4 sm:grid-cols-[170px_1fr]"><label><span className="label">Data</span><input className="input" type="date" required value={form.date} onChange={e=>setForm(v=>({...v,date:e.target.value}))}/></label><label><span className="label">Título</span><input className="input" required value={form.title} onChange={e=>setForm(v=>({...v,title:e.target.value}))}/></label></div>
      <label><span className="label">Conteúdo</span><textarea className="input min-h-56" required value={form.content} onChange={e=>setForm(v=>({...v,content:e.target.value}))}/></label>
      <label><span className="label">Tags separadas por vírgula</span><input className="input" value={form.tags} onChange={e=>setForm(v=>({...v,tags:e.target.value}))} placeholder="projeto, aprendizado, evidência"/></label>
    </FormShell></Modal>
  </div>;
}
