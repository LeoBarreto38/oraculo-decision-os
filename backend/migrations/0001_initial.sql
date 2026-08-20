-- Oráculo v0: artefato auditável da migração inicial SQLite.
-- app.cli executa Base.metadata.create_all (equivalente SQLAlchemy), verifica este
-- arquivo por SHA-256 e registra 0001_initial em schema_migrations.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
  id INTEGER PRIMARY KEY, version VARCHAR(80) NOT NULL UNIQUE,
  checksum_sha256 VARCHAR(64) NOT NULL, applied_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS system_settings (
  id INTEGER PRIMARY KEY, key VARCHAR(100) NOT NULL UNIQUE, value JSON NOT NULL,
  description TEXT, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS goals (
  id INTEGER PRIMARY KEY, title VARCHAR(240) NOT NULL, description TEXT,
  target_value FLOAT, current_value FLOAT, unit VARCHAR(40), deadline DATE,
  priority INTEGER NOT NULL, status VARCHAR(32) NOT NULL,
  created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY, name VARCHAR(160) NOT NULL UNIQUE, description TEXT,
  type VARCHAR(80), status VARCHAR(32) NOT NULL, strategic_value FLOAT NOT NULL,
  revenue_potential FLOAT NOT NULL, time_to_value FLOAT NOT NULL,
  cash_requirement FLOAT NOT NULL, risk_level FLOAT NOT NULL,
  validation_level FLOAT NOT NULL, next_action TEXT, last_progress_at DATETIME,
  created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
  goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL, title VARCHAR(240) NOT NULL,
  description TEXT, priority INTEGER NOT NULL, due_at DATETIME, status VARCHAR(32) NOT NULL,
  estimated_minutes INTEGER, actual_minutes INTEGER, strategic_category VARCHAR(32) NOT NULL,
  completed_at DATETIME, is_external_interaction BOOLEAN NOT NULL,
  created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_checkins (
  id INTEGER PRIMARY KEY, date DATE NOT NULL UNIQUE, energy INTEGER, focus INTEGER,
  main_result TEXT, what_worked TEXT, what_failed TEXT, blockers TEXT, learning TEXT,
  strategy_change TEXT, feedback TEXT, free_text TEXT, created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY, code VARCHAR(64) UNIQUE, title VARCHAR(240) NOT NULL,
  question TEXT NOT NULL, context TEXT, status VARCHAR(32) NOT NULL,
  importance VARCHAR(32) NOT NULL, current_data VARCHAR(16) NOT NULL,
  selected_option VARCHAR(240), selected_option_id INTEGER, human_rationale TEXT,
  decided_at DATETIME, review_at DATETIME, actual_outcome TEXT, recommendation JSON,
  analysis_mode VARCHAR(40), created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS decision_options (
  id INTEGER PRIMARY KEY, decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
  title VARCHAR(240) NOT NULL, description TEXT, expected_upside FLOAT,
  expected_downside FLOAT, cash_cost FLOAT NOT NULL, time_cost FLOAT NOT NULL,
  reversibility FLOAT NOT NULL, strategic_alignment FLOAT NOT NULL,
  evidence_strength FLOAT NOT NULL, execution_risk FLOAT NOT NULL,
  personal_pattern_risk FLOAT NOT NULL, estimated_probability FLOAT,
  impact_financial FLOAT NOT NULL, speed_to_result FLOAT NOT NULL,
  asset_value FLOAT NOT NULL, useful_learning FLOAT NOT NULL,
  opportunity_cost FLOAT NOT NULL, uncertainty FLOAT NOT NULL, score FLOAT,
  score_breakdown JSON, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY, decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
  type VARCHAR(40) NOT NULL, title VARCHAR(240) NOT NULL, content TEXT NOT NULL,
  source_url TEXT, source_date DATE, captured_at DATETIME NOT NULL,
  reliability FLOAT NOT NULL, freshness FLOAT NOT NULL,
  supports_option_id INTEGER REFERENCES decision_options(id) ON DELETE SET NULL,
  contradicts_option_id INTEGER REFERENCES decision_options(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS hypotheses (
  id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
  title VARCHAR(240) NOT NULL, description TEXT, prior_probability FLOAT NOT NULL,
  current_probability FLOAT NOT NULL, status VARCHAR(32) NOT NULL, category VARCHAR(80),
  test_definition TEXT, success_condition TEXT, failure_condition TEXT, test_due_at DATETIME,
  resolved_at DATETIME, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY, decision_id INTEGER REFERENCES decisions(id) ON DELETE CASCADE,
  description TEXT NOT NULL, probability FLOAT NOT NULL, target_date DATE NOT NULL,
  category VARCHAR(80), outcome FLOAT, resolved_at DATETIME, brier_score FLOAT,
  created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY, type VARCHAR(64) NOT NULL, severity VARCHAR(20) NOT NULL,
  message TEXT NOT NULL, fingerprint VARCHAR(160) UNIQUE, metadata_json JSON,
  created_at DATETIME NOT NULL, due_at DATETIME, acknowledged_at DATETIME
);
CREATE TABLE IF NOT EXISTS journal_entries (
  id INTEGER PRIMARY KEY, date DATE NOT NULL, title VARCHAR(240) NOT NULL,
  content TEXT NOT NULL, tags JSON NOT NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS entity_nodes (
  id INTEGER PRIMARY KEY, type VARCHAR(64) NOT NULL, label VARCHAR(240) NOT NULL,
  reference_type VARCHAR(64), reference_id INTEGER, metadata_json JSON
);
CREATE TABLE IF NOT EXISTS entity_edges (
  id INTEGER PRIMARY KEY, source_node_id INTEGER NOT NULL REFERENCES entity_nodes(id) ON DELETE CASCADE,
  target_node_id INTEGER NOT NULL REFERENCES entity_nodes(id) ON DELETE CASCADE,
  relation VARCHAR(100) NOT NULL, weight FLOAT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_usage (
  id INTEGER PRIMARY KEY, model VARCHAR(100) NOT NULL, input_tokens INTEGER NOT NULL,
  cached_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL,
  web_search_calls INTEGER NOT NULL,
  estimated_cost_usd FLOAT NOT NULL, request_type VARCHAR(80) NOT NULL,
  decision_id INTEGER REFERENCES decisions(id) ON DELETE SET NULL, response_id VARCHAR(160),
  created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS llm_context_audits (
  id INTEGER PRIMARY KEY, decision_id INTEGER REFERENCES decisions(id) ON DELETE SET NULL,
  request_type VARCHAR(80) NOT NULL, model VARCHAR(100) NOT NULL, record_refs JSON NOT NULL,
  context_sha256 VARCHAR(64) NOT NULL, estimated_chars INTEGER NOT NULL, created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS analysis_runs (
  id INTEGER PRIMARY KEY, decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
  mode VARCHAR(40) NOT NULL, model VARCHAR(100), scorecards JSON NOT NULL,
  analysis JSON NOT NULL, red_team JSON, fallback_reason TEXT, created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS research_records (
  id INTEGER PRIMARY KEY, decision_id INTEGER REFERENCES decisions(id) ON DELETE CASCADE,
  query TEXT NOT NULL, searched_at DATETIME NOT NULL, sources JSON NOT NULL,
  relevant_excerpts JSON NOT NULL, response_id VARCHAR(160)
);
CREATE TABLE IF NOT EXISTS financial_snapshots (
  id INTEGER PRIMARY KEY, date DATE NOT NULL UNIQUE, cash_available FLOAT NOT NULL,
  monthly_income FLOAT NOT NULL, target_income FLOAT NOT NULL,
  experimental_spent FLOAT NOT NULL, pipeline_potential FLOAT NOT NULL, created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS project_activities (
  id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  type VARCHAR(60) NOT NULL, description TEXT NOT NULL, occurred_at DATETIME NOT NULL,
  is_external BOOLEAN NOT NULL
);
CREATE TABLE IF NOT EXISTS score_weight_changes (
  id INTEGER PRIMARY KEY, decision_id INTEGER NOT NULL REFERENCES decisions(id),
  previous_weights JSON NOT NULL, new_weights JSON NOT NULL, reason TEXT NOT NULL,
  changed_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY, user_message TEXT NOT NULL, assistant_answer TEXT NOT NULL,
  mode VARCHAR(40) NOT NULL, proposed_actions JSON NOT NULL, confirmed_actions JSON NOT NULL,
  created_at DATETIME NOT NULL, confirmed_at DATETIME
);
