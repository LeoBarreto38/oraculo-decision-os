import { Activity, AlertTriangle, Banknote, BrainCircuit, BriefcaseBusiness, CircleDollarSign, Crosshair, FlaskConical, Gauge, RefreshCw } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { DataModeBanner, EmptyState, MetricCard, PageHeader } from '../components/ui';
import { fallbackAIUsage, fallbackCalibration, fallbackDashboard } from '../data/fallback';
import { useApiResource } from '../hooks/useApiResource';
import { api } from '../services/api';
import { asCost, currency, usd } from '../utils/format';

const chartTooltipStyle = { background: '#0c1013', border: '1px solid #222c33', borderRadius: 8, color: '#e8edf0', fontSize: 12 };

export default function DashboardPage() {
  const dashboard = useApiResource(api.dashboard, fallbackDashboard);
  const calibration = useApiResource(api.calibration, fallbackCalibration);
  const usage = useApiResource(api.usage, fallbackAIUsage);
  const { cards } = dashboard.data;
  const metrics = [
    ['Caixa disponível', currency(cards.cash_available, true), 'Valor registrado', Banknote, true],
    ['Renda mensal', currency(cards.monthly_income, true), 'Linha de base atual', CircleDollarSign, false],
    ['Meta financeira', currency(cards.financial_target, true), 'Objetivo mensal', Crosshair, false],
    ['Gap financeiro', currency(cards.financial_gap, true), 'Prioridade estratégica', Gauge, true],
    ['Capital exp. gasto', currency(cards.experimental_capital_spent, true), 'Valor registrado', Activity, false],
    ['Pipeline potencial', currency(cards.potential_pipeline, true), 'Receita ainda não confirmada', Banknote, false],
    ['Projetos ativos', String(cards.active_projects), 'Inclui projetos em validação', BriefcaseBusiness, false],
    ['Decisões abertas', String(cards.open_decisions), 'Aguardando análise ou escolha', BrainCircuit, false],
    ['Hipóteses em teste', String(cards.testing_hypotheses), 'Exigem resultado observável', FlaskConical, false],
    ['Alertas críticos', String(cards.critical_alerts), 'Revisão imediata', AlertTriangle, cards.critical_alerts > 0]
  ] as const;

  return (
    <div>
      <PageHeader eyebrow="Leitura do sistema" title="Painel" description="Estado financeiro, alocação de tempo e qualidade das previsões. Ausência de dados permanece visível; o painel não completa lacunas com estimativas." actions={<button className="btn-secondary" type="button" onClick={() => { void dashboard.reload(); void calibration.reload(); void usage.reload(); }}><RefreshCw className="h-4 w-4" /> Atualizar</button>} />
      <DataModeBanner source={dashboard.source} error={dashboard.error} loading={dashboard.loading} onRetry={dashboard.reload} />

      <section className="mb-5 grid gap-3 sm:grid-cols-3" aria-label="Custos de inteligência artificial">
        <MetricCard label="IA hoje" value={usd(asCost(usage.data.today))} detail={usage.source === 'api' ? 'Custo estimado registrado' : 'Referência local; API indisponível'} icon={<BrainCircuit className="h-4 w-4" />} />
        <MetricCard label="IA esta semana" value={usd(asCost(usage.data.week))} detail={usage.source === 'api' ? 'Custo estimado registrado' : 'Referência local; API indisponível'} icon={<BrainCircuit className="h-4 w-4" />} />
        <MetricCard label="IA este mês" value={usd(asCost(usage.data.month))} detail={`${usage.source === 'api' ? 'Limite' : 'Limite de referência'}: ${usd(usage.data.hard_limit)}`} icon={<BrainCircuit className="h-4 w-4" />} accent={asCost(usage.data.month) >= usage.data.soft_warning} />
      </section>

      <section className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5" aria-label="Indicadores principais">
        {metrics.map(([label, value, detail, Icon, accent]) => <MetricCard key={label} label={label} value={value} detail={detail} icon={<Icon className="h-4 w-4" />} accent={accent} />)}
      </section>

      <div className="mb-5 grid gap-4 xl:grid-cols-[1.35fr_.85fr]">
        <section className="panel min-w-0" aria-labelledby="financial-chart-title">
          <div className="panel-header"><div><p className="eyebrow mb-1">Trajetória</p><h2 id="financial-chart-title" className="text-sm font-semibold text-slate-200">Progresso financeiro</h2></div><span className="font-mono text-[10px] text-slate-600">BRL / MÊS</span></div>
          <div className="h-[290px] px-2 py-4 sm:px-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dashboard.data.financial_progress} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#1d252b" strokeDasharray="3 5" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: '#65727b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#65727b', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(value) => `R$${Number(value) / 1000}k`} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => currency(Number(value), true)} />
                <Line type="monotone" dataKey="target" name="Meta" stroke="#4b5760" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
                <Line type="monotone" dataKey="income" name="Renda" stroke="#c8f06a" strokeWidth={2.5} dot={{ r: 3, fill: '#c8f06a', strokeWidth: 0 }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel min-w-0" aria-labelledby="time-chart-title">
          <div className="panel-header"><div><p className="eyebrow mb-1">Alocação</p><h2 id="time-chart-title" className="text-sm font-semibold text-slate-200">Tempo por categoria</h2></div><span className="font-mono text-[10px] text-slate-600">MINUTOS</span></div>
          <div className="h-[290px] px-2 py-4 sm:px-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dashboard.data.time_distribution} layout="vertical" margin={{ top: 5, right: 12, left: 8, bottom: 0 }}>
                <CartesianGrid stroke="#1d252b" strokeDasharray="3 5" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#65727b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="category" width={92} tick={{ fill: '#8b969d', fontSize: 9 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => `${value} min`} />
                <Bar dataKey="minutes" name="Tempo" fill="#78b8d8" radius={[0, 4, 4, 0]} maxBarSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <section className="panel" aria-labelledby="calibration-title">
        <div className="panel-header"><div><p className="eyebrow mb-1">Analytics</p><h2 id="calibration-title" className="text-sm font-semibold text-slate-200">Calibração de previsões</h2></div><span className="font-mono text-[10px] text-slate-600">BRIER SCORE</span></div>
        {calibration.data.total_predictions ? (
          <div className="grid gap-4 p-4 md:grid-cols-[220px_1fr]">
            <div className="rounded-lg border border-ink-700 bg-ink-950 p-4"><p className="eyebrow">Brier Score</p><p className="metric-value mt-3">{calibration.data.brier_score?.toFixed(3) ?? '—'}</p><p className="mt-2 text-xs leading-5 text-slate-500">Quanto menor, melhor. Este número descreve as previsões registradas; não demonstra significância estatística.</p></div>
            <div className="grid gap-2 sm:grid-cols-5">{calibration.data.bands?.map((band) => <div key={band.band} className="rounded-lg border border-ink-700 bg-ink-950 p-3"><p className="font-mono text-[10px] text-slate-500">{band.band}</p><p className="mt-3 text-lg font-semibold text-slate-200">{Math.round(band.observed * 100)}%</p><p className="mt-1 text-[10px] text-slate-600">observado · n={band.count}</p></div>)}</div>
          </div>
        ) : <EmptyState title="DADOS INSUFICIENTES PARA CALIBRAÇÃO." description="Resolva previsões com resultados observáveis para iniciar o cálculo de Brier Score e faixas de calibração." />}
      </section>
    </div>
  );
}
