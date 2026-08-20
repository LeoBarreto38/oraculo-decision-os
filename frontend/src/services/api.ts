import type {
  AIUsageData,
  Alert,
  AnalysisHistoryItem,
  AnalysisResult,
  CalibrationData,
  ChatResponse,
  DashboardData,
  Decision,
  Goal,
  GraphData,
  Hypothesis,
  JournalEntry,
  Project,
  PublicSettings,
  RedTeamResumeResult,
  ScoreWeights,
  Task,
  TodayData
} from '../types';

const API_BASE = (
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  (import.meta.env.VITE_API_URL as string | undefined) ||
  '/api'
).replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status = 0, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 12_000): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  headers.set('Accept', 'application/json');

  try {
    const response = await fetch(`${API_BASE}${path}`, { ...init, headers, signal: controller.signal });
    const contentType = response.headers.get('content-type') || '';
    const payload = response.status === 204
      ? undefined
      : contentType.includes('application/json')
        ? await response.json()
        : await response.text();

    if (!response.ok) {
      const rawDetail = typeof payload === 'object' && payload && 'detail' in payload
        ? (payload as { detail: unknown }).detail
        : null;
      const detail = typeof rawDetail === 'string'
        ? rawDetail
        : rawDetail && typeof rawDetail === 'object' && 'message' in rawDetail
          ? String((rawDetail as { message: unknown }).message)
        : `A API respondeu com status ${response.status}.`;
      throw new ApiError(detail, response.status, payload);
    }
    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`A API demorou mais de ${Math.round(timeoutMs / 1000)} segundos para responder.`);
    }
    throw new ApiError(navigator.onLine ? 'Não foi possível conectar ao backend local.' : 'Este dispositivo está offline.');
  } finally {
    window.clearTimeout(timeout);
  }
}

const json = (value: unknown) => JSON.stringify(value);

function normalizeProject(item: Project): Project {
  return { ...item, description: item.description || '', type: item.type || '', next_action: item.next_action || '' };
}

function normalizeTask(item: Task): Task {
  return { ...item, description: item.description || '', estimated_minutes: item.estimated_minutes || 0, actual_minutes: item.actual_minutes || 0 };
}

function normalizeGoal(item: Goal): Goal {
  return { ...item, description: item.description || '', target_value: item.target_value || 0, current_value: item.current_value || 0, unit: item.unit || '' };
}

function normalizeHypothesis(item: Hypothesis): Hypothesis {
  return { ...item, description: item.description || '', test_definition: item.test_definition || '', success_condition: item.success_condition || '', failure_condition: item.failure_condition || '' };
}

function normalizeDecision(item: Decision): Decision {
  return { ...item, context: item.context || '', options: (item.options || []).map((option) => ({ ...option, description: option.description || '' })) };
}

function normalizeToday(raw: any): TodayData {
  const financial = raw?.financial || {};
  const milestone = raw?.next_milestone;
  return {
    main_goal: raw?.main_goal || { title: 'Meta principal não definida', current_value: 0, target_value: 0, unit: '' },
    financial: {
      current_income: Number(financial.current_income ?? financial.monthly_income ?? 0),
      target_income: Number(financial.target_income ?? 0),
      gap: Number(financial.gap ?? 0)
    },
    priorities: (raw?.priorities || []).map(normalizeTask),
    overdue_tasks: (raw?.overdue_tasks || []).map(normalizeTask),
    pending_decisions: (raw?.pending_decisions || []).map(normalizeDecision),
    alerts: raw?.alerts || [],
    stalled_projects: (raw?.stalled_projects || []).map(normalizeProject),
    next_milestone: milestone ? (typeof milestone === 'string' ? milestone : { title: milestone.title || 'Marco sem título', due_at: milestone.due_at }) : 'Nenhum marco com prazo definido'
  };
}

function normalizeDashboard(raw: any): DashboardData {
  const cards = raw?.cards || {};
  return {
    cards: {
      cash_available: Number(cards.cash_available || 0),
      monthly_income: Number(cards.monthly_income || 0),
      financial_target: Number(cards.financial_target ?? cards.target_income ?? 0),
      financial_gap: Number(cards.financial_gap ?? cards.income_gap ?? 0),
      experimental_capital_spent: Number(cards.experimental_capital_spent ?? cards.experimental_spent ?? 0),
      potential_pipeline: Number(cards.potential_pipeline ?? cards.pipeline_potential ?? 0),
      active_projects: Number(cards.active_projects || 0),
      open_decisions: Number(cards.open_decisions || 0),
      testing_hypotheses: Number(cards.testing_hypotheses || 0),
      critical_alerts: Number(cards.critical_alerts || 0)
    },
    financial_progress: (raw?.financial_progress || []).map((item: any) => ({ date: item.date, income: Number(item.income ?? item.monthly_income ?? 0), target: Number(item.target ?? item.target_income ?? 0) })),
    time_distribution: raw?.time_distribution || []
  };
}

function normalizeGraph(raw: any): GraphData {
  return {
    nodes: (raw?.nodes || []).map((node: any) => ({ id: node.id, type: node.type || node.data?.entity_type, label: node.label || node.data?.label || 'Entidade', reference_type: node.reference_type || node.data?.reference_type, reference_id: node.reference_id || node.data?.reference_id, position: node.position })),
    edges: (raw?.edges || []).map((edge: any) => ({ id: edge.id, source: edge.source, target: edge.target, relation: edge.relation || edge.label || 'relaciona', weight: edge.weight ?? edge.data?.weight }))
  };
}

function normalizeCalibration(raw: any): CalibrationData {
  return {
    message: raw?.message,
    total_predictions: Number(raw?.total_predictions ?? raw?.resolved_predictions ?? 0),
    brier_score: raw?.brier_score ?? raw?.mean_brier_score ?? null,
    mean_prediction_error: raw?.mean_prediction_error ?? raw?.mean_absolute_error ?? null,
    accuracy_by_category: Array.isArray(raw?.accuracy_by_category) ? raw.accuracy_by_category : Object.entries(raw?.accuracy_by_category || {}).map(([category, value]: [string, any]) => ({ category, accuracy: value.accuracy, count: value.count })),
    bands: (raw?.bands || []).map((band: any) => ({ band: band.band || band.range, predicted: Number(band.predicted ?? band.mean_forecast ?? 0), observed: Number(band.observed ?? band.observed_frequency ?? 0), count: Number(band.count || 0) }))
  };
}

function normalizeAnalysisResult(result: any): AnalysisResult {
  const sources = Array.isArray(result?.research) ? result.research : result?.research?.sources || [];
  const capturedAt = result?.research?.searched_at;
  return {
    ...result,
    analysis: {
      ...(result?.analysis || {}),
      ...(result?.red_team ? { red_team: result.red_team.synthesis || result.red_team.final_position || JSON.stringify(result.red_team) } : {})
    },
    research: sources.map((source: any) => ({ ...source, origin: source.origin || 'WEB', captured_at: source.captured_at || capturedAt }))
  } as AnalysisResult;
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  today: () => request<unknown>('/today').then(normalizeToday),
  dashboard: () => request<unknown>('/dashboard').then(normalizeDashboard),

  projects: {
    list: () => request<Project[]>('/projects').then((items) => items.map(normalizeProject)),
    create: (data: Omit<Project, 'id'>) => request<Project>('/projects', { method: 'POST', body: json(data) }),
    update: (id: Project['id'], data: Partial<Project>) => request<Project>(`/projects/${id}`, { method: 'PATCH', body: json(data) }),
    remove: (id: Project['id']) => request<void>(`/projects/${id}`, { method: 'DELETE' })
  },
  tasks: {
    list: () => request<Task[]>('/tasks').then((items) => items.map(normalizeTask)),
    create: (data: Omit<Task, 'id'>) => request<Task>('/tasks', { method: 'POST', body: json(data) }),
    update: (id: Task['id'], data: Partial<Task>) => request<Task>(`/tasks/${id}`, { method: 'PATCH', body: json(data) }),
    remove: (id: Task['id']) => request<void>(`/tasks/${id}`, { method: 'DELETE' })
  },
  goals: {
    list: () => request<Goal[]>('/goals').then((items) => items.map(normalizeGoal)),
    create: (data: Omit<Goal, 'id'>) => request<Goal>('/goals', { method: 'POST', body: json(data) }),
    update: (id: Goal['id'], data: Partial<Goal>) => request<Goal>(`/goals/${id}`, { method: 'PATCH', body: json(data) }),
    remove: (id: Goal['id']) => request<void>(`/goals/${id}`, { method: 'DELETE' })
  },
  hypotheses: {
    list: () => request<Hypothesis[]>('/hypotheses').then((items) => items.map(normalizeHypothesis)),
    create: (data: Omit<Hypothesis, 'id'>) => request<Hypothesis>('/hypotheses', { method: 'POST', body: json(data) }),
    update: (id: Hypothesis['id'], data: Partial<Hypothesis>) => request<Hypothesis>(`/hypotheses/${id}`, { method: 'PATCH', body: json(data) }),
    remove: (id: Hypothesis['id']) => request<void>(`/hypotheses/${id}`, { method: 'DELETE' })
  },
  decisions: {
    list: () => request<Decision[]>('/decisions').then((items) => items.map(normalizeDecision)),
    create: (data: Record<string, unknown>) => request<Decision>('/decisions', { method: 'POST', body: json(data) }).then(normalizeDecision),
    update: (id: Decision['id'], data: Partial<Decision>) => request<Decision>(`/decisions/${id}`, { method: 'PATCH', body: json(data) }),
    addOption: (id: Decision['id'], data: NonNullable<Decision['options']>[number]) => request(`/decisions/${id}/options`, { method: 'POST', body: json(data) }),
    addEvidence: (id: Decision['id'], data: Record<string, unknown>) => request(`/decisions/${id}/evidence`, { method: 'POST', body: json(data) }),
    addPrediction: (id: Decision['id'], data: Record<string, unknown>) => request(`/decisions/${id}/predictions`, { method: 'POST', body: json(data) }),
    analyze: (id: Decision['id'], data: { use_ai: boolean; current_data: 'AUTO' | 'SIM' | 'NAO'; explicitly_authorized_over_budget?: boolean }) => request<any>(`/decisions/${id}/analyze`, { method: 'POST', body: json(data) }, 180_000).then(normalizeAnalysisResult),
    resumeRedTeam: (id: Decision['id'], data: { analysis_run_id: number | string; explicitly_authorized_over_budget: true }) => request<RedTeamResumeResult>(`/decisions/${id}/red-team`, { method: 'POST', body: json(data) }, 180_000),
    analyses: (id: Decision['id']) => request<AnalysisHistoryItem[]>(`/decisions/${id}/analyses`),
    confirm: (id: Decision['id'], data: { selected_option_id: string | number; rationale: string; review_at: string }) => request<Decision>(`/decisions/${id}/confirm`, { method: 'POST', body: json(data) }),
    outcome: (id: Decision['id'], data: { actual_outcome: string; prediction_outcomes: Array<{ prediction_id: string | number; outcome: 0 | 1 }> }) => request<Decision>(`/decisions/${id}/outcome`, { method: 'POST', body: json(data) })
  },

  checkins: {
    list: () => request('/checkins'),
    create: (data: Record<string, unknown>) => request('/checkins', { method: 'POST', body: json(data) })
  },
  journal: {
    list: () => request<JournalEntry[]>('/journal'),
    create: (data: Omit<JournalEntry, 'id'>) => request<JournalEntry>('/journal', { method: 'POST', body: json(data) }),
    update: (id: JournalEntry['id'], data: Partial<JournalEntry>) => request<JournalEntry>(`/journal/${id}`, { method: 'PATCH', body: json(data) }),
    remove: (id: JournalEntry['id']) => request<void>(`/journal/${id}`, { method: 'DELETE' })
  },
  alerts: {
    list: () => request<Alert[]>('/alerts'),
    run: () => request<Alert[]>('/alerts/run', { method: 'POST' }),
    acknowledge: (id: Alert['id']) => request<Alert>(`/alerts/${id}/ack`, { method: 'POST' })
  },
  chat: {
    send: (message: string, use_ai = true) => request<ChatResponse>('/chat', { method: 'POST', body: json({ message, use_ai }) }, 180_000),
    confirm: (messageId: string | number, actionIndexes: number[]) => request(`/chat/${messageId}/confirm`, { method: 'POST', body: json({ action_indexes: actionIndexes }) })
  },
  usage: () => request<AIUsageData>('/ai-usage'),
  map: () => request<unknown>('/map').then(normalizeGraph),
  calibration: () => request<unknown>('/analytics/calibration').then(normalizeCalibration),
  settings: {
    public: () => request<PublicSettings>('/settings'),
    weights: () => request<ScoreWeights>('/settings/score-weights'),
    updateWeights: (data: ScoreWeights & { reason: string }) => request('/settings/score-weights', { method: 'PATCH', body: json(data) })
  },
  async exportBackup(): Promise<void> {
    const response = await fetch(`${API_BASE}/backup/export`, { method: 'POST' });
    if (!response.ok) throw new ApiError('Não foi possível gerar o backup.', response.status);
    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || `oraculo-backup-${new Date().toISOString().slice(0, 10)}.zip`;
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = href;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
  }
};
