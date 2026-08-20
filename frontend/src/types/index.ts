export type DataSource = 'api' | 'fallback';
export type ProjectStatus = 'ACTIVE' | 'VALIDATING' | 'PAUSED' | 'INVALIDATED' | 'COMPLETED' | 'ARCHIVED';
export type WorkStatus = 'TODO' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';
export type StrategicCategory = 'CASH' | 'ASSET' | 'LEARNING' | 'MAINTENANCE' | 'DISTRACTION';

export interface Goal {
  id: number | string;
  title: string;
  description?: string;
  target_value: number;
  current_value: number;
  unit: string;
  deadline?: string | null;
  priority: number;
  status: string;
  created_at?: string;
  updated_at?: string;
}

export interface Project {
  id: number | string;
  name: string;
  description: string;
  type: string;
  status: ProjectStatus | string;
  strategic_value: number;
  revenue_potential: number;
  time_to_value: number;
  cash_requirement: number;
  risk_level: number;
  validation_level: number;
  next_action: string;
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  id: number | string;
  project_id?: number | string | null;
  goal_id?: number | string | null;
  title: string;
  description?: string;
  priority: number;
  due_at?: string | null;
  status: WorkStatus | string;
  estimated_minutes: number;
  actual_minutes?: number;
  strategic_category: StrategicCategory;
}

export interface Hypothesis {
  id: number | string;
  title: string;
  description: string;
  prior_probability: number;
  current_probability: number;
  status: string;
  test_definition: string;
  success_condition: string;
  failure_condition: string;
  created_at?: string;
  resolved_at?: string | null;
}

export interface DecisionOption {
  id?: number | string;
  decision_id?: number | string;
  title: string;
  description: string;
  expected_upside: number;
  expected_downside: number;
  cash_cost: number;
  time_cost: number;
  reversibility: number;
  strategic_alignment: number;
  evidence_strength: number;
  execution_risk: number;
  personal_pattern_risk: number;
  estimated_probability: number;
  impact_financial?: number;
  speed_to_result?: number;
  asset_value?: number;
  useful_learning?: number;
  opportunity_cost?: number;
  uncertainty?: number;
  score?: number;
}

export interface Decision {
  id: number | string;
  code?: string;
  title: string;
  question: string;
  context: string;
  importance?: 'NORMAL' | 'CRITICAL' | string;
  current_data?: 'AUTO' | 'SIM' | 'NAO' | string;
  status: string;
  selected_option?: string | number | null;
  selected_option_id?: string | number | null;
  options?: DecisionOption[];
  evidence?: Array<{
    id: number | string;
    type: string;
    title: string;
    content: string;
    source_url?: string | null;
    reliability?: number;
    freshness?: number;
  }>;
  predictions?: Array<{
    id: number | string;
    description: string;
    probability: number;
    target_date: string;
    category?: string | null;
    outcome?: number | null;
    brier_score?: number | null;
  }>;
  recommendation?: OracleAnalysis | null;
  analysis_mode?: string | null;
  created_at?: string;
  decided_at?: string | null;
  review_at?: string | null;
  actual_outcome?: string | null;
}

export interface Alert {
  id: number | string;
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  message: string;
  created_at?: string;
  due_at?: string | null;
  acknowledged_at?: string | null;
}

export interface TodayData {
  main_goal: Goal | { title: string; current_value: number; target_value: number; unit: string };
  financial: {
    current_income: number;
    target_income: number;
    gap: number;
  };
  priorities: Task[];
  overdue_tasks: Task[];
  pending_decisions: Decision[];
  alerts: Alert[];
  stalled_projects: Project[];
  next_milestone: string | { title: string; due_at?: string | null };
}

export interface DashboardData {
  cards: {
    cash_available: number;
    monthly_income: number;
    financial_target: number;
    financial_gap: number;
    experimental_capital_spent: number;
    potential_pipeline: number;
    active_projects: number;
    open_decisions: number;
    testing_hypotheses: number;
    critical_alerts: number;
  };
  financial_progress: Array<{ date: string; income: number; target?: number }>;
  time_distribution: Array<{ category: StrategicCategory; minutes: number }>;
}

export interface OracleAnalysis {
  recommendation?: string;
  why?: string;
  evidence?: string[];
  assumptions?: string[];
  principal_risk?: string;
  change_condition?: string;
  evidence_confidence?: string | number;
  next_action?: string;
  review_date?: string;
  red_team?: string;
  red_team_synthesis?: string;
  red_team_final_position?: string;
  change_conditions?: string[];
  budget_authorization_required?: boolean;
  [key: string]: unknown;
}

export interface AnalysisResult {
  analysis_run_id?: number | string;
  stage?: string;
  budget_blocked_stage?: 'PRIMARY' | 'RED_TEAM' | null;
  red_team_warning?: string | null;
  resume_red_team?: {
    method: 'POST';
    path: string;
    payload: { analysis_run_id: number | string; explicitly_authorized_over_budget: true };
  } | null;
  mode: 'ai' | 'deterministic_fallback' | string;
  analysis: OracleAnalysis | string;
  scorecards: Array<{ option_id?: string | number; option_title?: string; score: number; [key: string]: unknown }>;
  requires_human_confirmation: boolean;
  research?: Array<{ title?: string; url?: string; source?: string; excerpt?: string; origin?: string; captured_at?: string }>;
}

export interface RedTeamResumeResult {
  analysis_run_id: number | string;
  decision_id: number | string;
  stage: string;
  budget_blocked_stage: null;
  analysis: OracleAnalysis;
  red_team: Record<string, unknown>;
  requires_human_confirmation: boolean;
  already_completed: boolean;
}

export interface AnalysisHistoryItem {
  id: number | string;
  analysis_run_id?: number | string;
  mode: string;
  model?: string | null;
  scorecards: AnalysisResult['scorecards'];
  analysis: OracleAnalysis;
  red_team?: Record<string, unknown> | null;
  fallback_reason?: string | null;
  created_at?: string;
  stage?: string;
  budget_blocked_stage?: 'PRIMARY' | 'RED_TEAM' | null;
  red_team_warning?: string | null;
  resume_red_team?: AnalysisResult['resume_red_team'];
  research?: {
    searched_at?: string;
    sources: Array<{ title?: string; url?: string; source?: string; excerpt?: string; origin?: string }>;
  } | null;
}

export interface AIUsageData {
  today: number | { estimated_cost_usd: number };
  week: number | { estimated_cost_usd: number };
  month: number | { estimated_cost_usd: number };
  budget: number;
  soft_warning: number;
  hard_limit: number;
  recent: Array<{
    id?: number | string;
    model: string;
    input_tokens: number;
    cached_tokens?: number;
    output_tokens: number;
    estimated_cost_usd: number;
    request_type: string;
    created_at: string;
  }>;
}

export interface JournalEntry {
  id: number | string;
  date: string;
  title: string;
  content: string;
  tags: string[] | string;
}

export interface CalibrationData {
  message?: string;
  total_predictions?: number;
  brier_score?: number | null;
  mean_prediction_error?: number | null;
  accuracy_by_category?: Array<{ category: string; accuracy: number; count: number }>;
  bands?: Array<{ band: string; predicted: number; observed: number; count: number }>;
}

export interface ScoreWeights {
  version?: number;
  benefits: Record<string, number>;
  penalties: Record<string, number>;
}

export interface PublicSettings {
  models: { critical: string; standard: string; light: string };
  budgets: { monthly: number; soft_warning: number; hard_limit: number };
  openai_configured: boolean;
  web_search_enabled: boolean;
  timezone: string;
  morning_briefing_time: string;
  evening_checkin_time: string;
  scheduler?: { running?: boolean; jobs?: unknown[]; [key: string]: unknown };
  secret_values_exposed: boolean;
}

export interface GraphData {
  nodes: Array<{
    id: string | number;
    type?: string;
    label: string;
    reference_type?: string;
    reference_id?: string | number;
    position?: { x: number; y: number };
  }>;
  edges: Array<{
    id?: string | number;
    source: string | number;
    target: string | number;
    relation: string;
    weight?: number;
  }>;
}

export interface ProposedAction {
  type: 'CREATE_DECISION' | 'CREATE_TASK' | 'CREATE_HYPOTHESIS' | 'CREATE_EVIDENCE' | string;
  summary?: string;
  payload?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ChatResponse {
  message_id?: string | number;
  mode: string;
  answer: string;
  proposed_actions: ProposedAction[];
  confirmation_required: boolean;
}
