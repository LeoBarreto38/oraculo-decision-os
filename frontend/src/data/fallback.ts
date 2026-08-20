import type {
  AIUsageData, Alert, CalibrationData, DashboardData, Decision, Goal,
  GraphData, Hypothesis, JournalEntry, Project, Task, TodayData
} from '../types';

export const seedGoal: Goal = {
  id: 'demo-goal', title: 'DEMO: Reach first measurable objective',
  description: 'Neutral sample data. Replace it with your own goal.',
  current_value: 0, target_value: 10, unit: 'milestones', priority: 10, status: 'ACTIVE'
};

export const seedProjects: Project[] = [{
  id: 'demo-project', name: 'DEMO: Example Project',
  description: 'Neutral sample project for exploring the application.',
  type: 'DEMO', status: 'ACTIVE', strategic_value: 5, revenue_potential: 0,
  time_to_value: 5, cash_requirement: 0, risk_level: 2, validation_level: 1,
  next_action: 'Replace this demo with a real project.'
}];

export const seedTasks: Task[] = [{
  id: 'demo-task', project_id: 'demo-project',
  title: 'DEMO: Define one measurable milestone',
  description: 'Choose a small result that can be verified objectively.',
  priority: 10, status: 'TODO', estimated_minutes: 30, strategic_category: 'LEARNING'
}];

export const seedAlerts: Alert[] = [];

export const seedDecisions: Decision[] = [{
  id: 'demo-decision', code: 'DEMO-DECISION-001',
  title: 'DEMO: Allocate time between two example strategies',
  question: 'Which example strategy should receive the next focused work session?',
  context: 'Neutral demonstration data without personal or financial information.',
  importance: 'STANDARD', status: 'OPEN', review_at: null,
  options: [
    {
      title: 'DEMO: Strategy A', description: 'Validate the most uncertain assumption.',
      expected_upside: 10, expected_downside: 0, cash_cost: 0, time_cost: 5,
      reversibility: 9, strategic_alignment: 7, evidence_strength: 4,
      execution_risk: 3, personal_pattern_risk: 2, estimated_probability: 0.6
    },
    {
      title: 'DEMO: Strategy B', description: 'Improve the existing example workflow.',
      expected_upside: 8, expected_downside: 0, cash_cost: 0, time_cost: 5,
      reversibility: 9, strategic_alignment: 6, evidence_strength: 5,
      execution_risk: 2, personal_pattern_risk: 2, estimated_probability: 0.7
    }
  ]
}];

export const seedHypotheses: Hypothesis[] = [{
  id: 'demo-hypothesis',
  title: 'DEMO: A focused strategy will produce a measurable result',
  description: 'Example hypothesis. Replace it with an assumption you can test.',
  prior_probability: 0.5, current_probability: 0.5, status: 'TESTING',
  test_definition: 'Run one small test and record the result.',
  success_condition: 'The selected milestone is reached.',
  failure_condition: 'The milestone is not reached within the test period.'
}];

export const fallbackToday: TodayData = {
  main_goal: seedGoal, financial: { current_income: 0, target_income: 0, gap: 0 },
  priorities: seedTasks, overdue_tasks: [], pending_decisions: seedDecisions,
  alerts: seedAlerts, stalled_projects: [], next_milestone: 'DEMO: First measurable result'
};

export const fallbackDashboard: DashboardData = {
  cards: {
    cash_available: 0, monthly_income: 0, financial_target: 0, financial_gap: 0,
    experimental_capital_spent: 0, potential_pipeline: 0, active_projects: 1,
    open_decisions: 1, testing_hypotheses: 1, critical_alerts: 0
  },
  financial_progress: [{ date: 'DEMO', income: 0, target: 0 }],
  time_distribution: [
    { category: 'CASH', minutes: 0 }, { category: 'ASSET', minutes: 0 },
    { category: 'LEARNING', minutes: 0 }, { category: 'MAINTENANCE', minutes: 0 },
    { category: 'DISTRACTION', minutes: 0 }
  ]
};

export const fallbackAIUsage: AIUsageData = {
  today: 0, week: 0, month: 0, budget: 5, soft_warning: 4, hard_limit: 5, recent: []
};

export const fallbackGraph: GraphData = {
  nodes: [
    { id: 'person', type: 'Person', label: 'DEMO: Demo User', position: { x: 20, y: 140 } },
    { id: 'project', type: 'Project', label: 'DEMO: Example Project', position: { x: 260, y: 60 } },
    { id: 'goal', type: 'Goal', label: 'DEMO: Measurable Objective', position: { x: 510, y: 140 } },
    { id: 'decision', type: 'Decision', label: 'DEMO-DECISION-001', position: { x: 260, y: 270 } }
  ],
  edges: [
    { source: 'person', target: 'project', relation: 'owns' },
    { source: 'project', target: 'goal', relation: 'contributes_to' },
    { source: 'decision', target: 'project', relation: 'affects' }
  ]
};

export const fallbackCalibration: CalibrationData = {
  message: 'DADOS INSUFICIENTES PARA CALIBRAÇÃO.', total_predictions: 0,
  brier_score: null, bands: []
};

export const fallbackJournal: JournalEntry[] = [];
