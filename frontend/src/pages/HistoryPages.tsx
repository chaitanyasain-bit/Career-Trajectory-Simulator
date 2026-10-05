import {
  ArrowLeft,
  ArrowRight,
  Beaker,
  CalendarDays,
  Clock3,
  GitCompareArrows,
  History,
  Layers3,
  RotateCcw,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api } from '@/services/api'
import { CareerPathCard, EmptyState, ErrorState, LoadingState, PageHeading, Panel } from '@/components/ui'
import { useProfileAndHistory } from '@/pages/hooks'

export function HistoryPage() {
  const { history, profile, isLoading, error, refetch } = useProfileAndHistory()
  const roles = useQuery({
    queryKey: ['history', 'results', history.data?.map((item) => item.id)],
    queryFn: async () => {
      const entries = history.data ?? []
      return Promise.all(entries.map(async (entry) => ({ entry, simulation: await api.getSimulation(entry.id) })))
    },
    enabled: Boolean(history.data?.length),
  })
  if (isLoading) return <LoadingState />
  if (error && !profile.data) return <ErrorState error={error} onRetry={() => void refetch()} />
  return <>
    <PageHeading eyebrow="Your career journey" title="Simulation history" description="Revisit saved career maps and What-If scenarios. Replays show the original results and catalog context from when each simulation ran." />
    {history.data?.length ? roles.error ? <ErrorState error={roles.error} onRetry={() => void roles.refetch()} /> : roles.isLoading ? <LoadingState label="Loading saved career results…" /> : <div className="space-y-4">{roles.data?.map(({ entry, simulation }) => {
      const topPath = simulation.paths[0]
      const isScenario = Boolean(entry.parent_simulation_id)
      return <Link key={entry.id} to={`/history/${entry.id}`} className="group block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-teal-200 hover:shadow-md sm:p-6">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div className="flex items-start gap-4">
            <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${isScenario ? 'bg-violet-50 text-violet-700' : 'bg-teal-50 text-teal-700'}`}>{isScenario ? <Beaker className="h-5 w-5" /> : <History className="h-5 w-5" />}</span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2"><h2 className="font-bold text-slate-900">{entry.label || (isScenario ? 'What-If scenario' : 'Career simulation')}</h2><span className={`badge ${isScenario ? 'badge-violet' : 'badge-teal'}`}>{isScenario ? 'What-If scenario' : 'Baseline simulation'}</span></div>
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500"><span className="inline-flex items-center gap-1"><CalendarDays className="h-3.5 w-3.5" />{new Date(entry.created_at).toLocaleString()}</span><span className="inline-flex items-center gap-1"><Layers3 className="h-3.5 w-3.5" />{entry.path_count} career paths</span><span>Engine {entry.engine_version}</span></div>
              {isScenario && <p className="mt-2 text-xs text-violet-700">Branched from a saved baseline · <span className="font-mono">{entry.parent_simulation_id?.slice(0, 8)}</span></p>}
            </div>
          </div>
          <div className="flex items-center justify-between gap-5 border-t border-slate-100 pt-4 sm:border-0 sm:pt-0">
            <div><p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Top recommendation</p><p className="mt-1 text-sm font-semibold text-slate-800">{topPath?.target_role?.title ?? 'No paths saved'}</p><p className="mt-0.5 text-xs text-slate-500">{topPath ? `${Math.round(topPath.confidence_score * 100)}% confidence · ${topPath.skill_gaps.length} gaps` : ''}</p></div>
            <ArrowRight className="h-5 w-5 text-slate-300 transition group-hover:translate-x-1 group-hover:text-teal-700" />
          </div>
        </div>
      </Link>
    })}</div> : <Panel><EmptyState title="No simulations saved yet" description="When you explore career paths, your original results and What-If scenarios will be saved here for replay." action={<Link className="btn-primary" to="/simulation">Explore career paths <ArrowRight className="h-4 w-4" /></Link>} /></Panel>}
  </>
}

export function HistoryDetailPage() {
  const { simulationId = '' } = useParams()
  const simulation = useQuery({ queryKey: ['simulation', simulationId], queryFn: () => api.getSimulation(simulationId), enabled: Boolean(simulationId) })
  const parentId = simulation.data?.parent_simulation_id
  const parent = useQuery({ queryKey: ['simulation', parentId], queryFn: () => api.getSimulation(parentId!), enabled: Boolean(parentId) })
  if (simulation.isLoading) return <LoadingState label="Replaying saved career results…" />
  if (simulation.error) return <ErrorState error={simulation.error} onRetry={() => void simulation.refetch()} />
  const saved = simulation.data!
  const parentPaths = new Map((parent.data?.paths ?? []).map((path) => [path.target_role_id, path]))
  return <>
    <Link to="/history" className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-teal-800"><ArrowLeft className="h-4 w-4" />Back to history</Link>
    <PageHeading eyebrow={saved.parent_simulation_id ? 'Saved hypothetical branch' : 'Saved simulation · replay'} title={saved.label || 'Career simulation'} description={`Original results from ${new Date(saved.created_at).toLocaleString()}. This replay reads the saved output and does not rerun the current engine.`} action={<Link className="btn-secondary" to={`/simulation?simulationId=${saved.id}`}><RotateCcw className="h-4 w-4" />Open simulation</Link>} />
    {saved.parent_simulation_id && <Panel className="mb-5 border-violet-100 bg-violet-50/60"><div className="flex items-start gap-3"><Beaker className="h-5 w-5 text-violet-700" /><div><p className="font-semibold">What-If scenario</p><p className="mt-1 text-sm text-slate-600">This saved branch compares against the baseline <Link className="font-semibold text-violet-800 underline" to={`/history/${saved.parent_simulation_id}`}>{parent.data?.label || saved.parent_simulation_id.slice(0, 8)}</Link>.</p></div></div></Panel>}
    <div className="mb-5 flex flex-wrap gap-3"><span className="badge badge-slate"><Clock3 className="h-3 w-3" />{new Date(saved.created_at).toLocaleString()}</span><span className="badge badge-slate">{saved.paths.length} paths</span><span className="badge badge-slate">Engine {saved.engine_version}</span>{saved.parent_simulation_id && <span className="badge badge-violet">Linked scenario</span>}</div>
    {saved.parent_simulation_id && parent.data && <Panel className="mb-6"><div className="flex items-center gap-2"><GitCompareArrows className="h-4 w-4 text-violet-700" /><h2 className="font-bold">Saved scenario comparison</h2></div><div className="mt-4 grid gap-3 sm:grid-cols-2">{saved.paths.map((path) => { const base = parentPaths.get(path.target_role_id); const change = path.confidence_score - (base?.confidence_score ?? 0); return <div key={path.id} className="rounded-xl bg-slate-50 p-3"><div className="flex justify-between gap-2"><p className="truncate text-sm font-semibold">{path.target_role?.title}</p><span className={`text-xs font-bold ${change > 0 ? 'text-emerald-700' : 'text-slate-500'}`}>{base ? `${change > 0 ? '+' : ''}${Math.round(change * 100)} pts` : 'New path'}</span></div><p className="mt-1 text-xs text-slate-500">{base ? `${Math.round(base.confidence_score * 100)}% baseline` : 'Not in baseline'} → {Math.round(path.confidence_score * 100)}% scenario</p></div> })}</div></Panel>}
    <div className="mb-4"><p className="eyebrow">Persisted career paths</p><h2 className="mt-1 text-xl font-bold">Recommendations from this run</h2></div>
    <div className="space-y-4">{saved.paths.map((path) => <CareerPathCard key={path.id} path={path} simulationId={saved.id} />)}</div>
  </>
}
