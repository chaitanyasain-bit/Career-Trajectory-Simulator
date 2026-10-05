import { ArrowLeft, BookOpen, Check, Circle, Clock3, ExternalLink, RotateCcw } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '@/services/api'
import { ErrorState, LoadingState, PageHeading, Panel, ProgressBar } from '@/components/ui'
import { useProfileAndHistory } from '@/pages/hooks'

export function RoadmapPage() {
  const { pathId = '' } = useParams()
  const { history, profile } = useProfileAndHistory()
  const roadmap = useQuery({ queryKey: ['roadmap', pathId], queryFn: () => api.getRoadmap(pathId), enabled: Boolean(pathId) })
  const simulationList = useQuery({
    queryKey: ['roadmap', 'simulations', history.data?.map((entry) => entry.id)],
    queryFn: async () => Promise.all((history.data ?? []).map(async (entry) => ({ entry, simulation: await api.getSimulation(entry.id) }))),
    enabled: Boolean(history.data?.length),
  })
  const owner = simulationList.data?.find(({ simulation }) => simulation.paths.some((path) => path.id === pathId))
  const path = owner?.simulation.paths.find((item) => item.id === pathId)
  const key = `roadmap-progress:${pathId}`
  const [done, setDone] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(key)
      return saved ? JSON.parse(saved) as string[] : []
    } catch {
      return []
    }
  })
  const complete = (stepId: string) => {
    setDone((current) => {
      const updated = current.includes(stepId) ? current.filter((id) => id !== stepId) : [...current, stepId]
      localStorage.setItem(key, JSON.stringify(updated))
      return updated
    })
  }
  const progress = roadmap.data?.length ? (done.filter((id) => roadmap.data?.some((step) => step.id === id)).length / roadmap.data.length) * 100 : 0
  const totalWeeks = useMemo(() => roadmap.data?.reduce((total, step) => total + (step.estimated_weeks ?? 0), 0) ?? 0, [roadmap.data])
  if (roadmap.isLoading || (history.isLoading && profile.data?.id) || simulationList.isLoading) return <LoadingState label="Loading your persisted learning roadmap…" />
  if (roadmap.error) return <ErrorState error={roadmap.error} onRetry={() => void roadmap.refetch()} />
  const steps = roadmap.data ?? []
  return <>
    {owner && <Link to={`/history/${owner.simulation.id}`} className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-teal-800"><ArrowLeft className="h-4 w-4" />Back to saved career paths</Link>}
    <PageHeading eyebrow="Your practical next steps" title={path?.target_role?.title ? `${path.target_role.title} roadmap` : 'Career roadmap'} description="A prioritized sequence of learning and action steps generated from your saved skill-gap analysis." action={<button className="btn-secondary" onClick={() => { localStorage.removeItem(key); setDone([]) }}><RotateCcw className="h-4 w-4" />Reset progress</button>} />
    <div className="grid gap-4 sm:grid-cols-3"><InfoCard label="Roadmap steps" value={steps.length} note="Ordered actions" /><InfoCard label="Estimated effort" value={totalWeeks ? `${totalWeeks} weeks` : '—'} note="Planning estimate, not a deadline" /><InfoCard label="Your progress" value={`${Math.round(progress)}%`} note="Saved on this device" /></div>
    <Panel className="mt-5"><ProgressBar value={progress} label="Roadmap progress" /><p className="mt-3 text-xs text-slate-500">Progress is stored in this browser only. The API currently persists roadmap steps, but does not sync completion status across devices.</p></Panel>
    <div className="mt-7">
      {steps.length ? <ol className="space-y-0">{steps.map((step, index) => {
        const checked = done.includes(step.id)
        return <li key={step.id} className="relative flex gap-4 pb-5 sm:gap-6">
          {index < steps.length - 1 && <span className="absolute bottom-0 left-[19px] top-10 w-px bg-slate-200 sm:left-[23px]" />}
          <button className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border transition sm:h-12 sm:w-12 ${checked ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-slate-200 bg-white text-slate-400 hover:border-teal-500 hover:text-teal-700'}`} onClick={() => complete(step.id)} aria-label={checked ? `Mark ${step.title} incomplete` : `Mark ${step.title} complete`} aria-pressed={checked}>{checked ? <Check className="h-5 w-5" /> : <span className="text-sm font-bold">{String(step.step_order).padStart(2, '0')}</span>}</button>
          <Panel className={`flex-1 p-4 sm:p-5 ${checked ? 'opacity-70' : ''}`}>
            <div className="flex flex-wrap items-center justify-between gap-2"><div className="flex flex-wrap items-center gap-2"><span className={`badge ${step.step_type === 'skill' ? 'badge-teal' : step.step_type === 'project' ? 'badge-violet' : 'badge-slate'}`}>{step.step_type}</span>{step.skill?.name && <span className="text-xs font-medium text-slate-500">{step.skill.name}</span>}</div>{step.estimated_weeks && <span className="inline-flex items-center gap-1 text-xs text-slate-500"><Clock3 className="h-3.5 w-3.5" />~{step.estimated_weeks} weeks</span>}</div>
            <h2 className={`mt-3 font-bold ${checked ? 'text-slate-500 line-through' : 'text-slate-900'}`}>{step.title}</h2>
            {step.description && <p className="mt-1.5 text-sm leading-6 text-slate-600">{step.description}</p>}
            {step.resource_url && <a className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-teal-800 hover:text-teal-600" href={step.resource_url} target="_blank" rel="noreferrer"><BookOpen className="h-4 w-4" />Open learning resource <ExternalLink className="h-3.5 w-3.5" /></a>}
          </Panel>
        </li>
      })}</ol> : <Panel><div className="empty-state"><Circle className="h-8 w-8 text-teal-700" /><h2 className="mt-3 font-semibold">No roadmap steps are saved</h2><p className="mt-1 text-sm text-slate-500">Run a career simulation to generate a persisted roadmap for its paths.</p><Link className="btn-primary mt-5" to="/simulation">Explore career paths</Link></div></Panel>}
    </div>
  </>
}

function InfoCard({ label, value, note }: { label: string; value: number | string; note: string }) {
  return <Panel className="p-4"><p className="text-xs font-semibold text-slate-500">{label}</p><p className="mt-2 text-xl font-bold text-slate-950">{value}</p><p className="mt-1 text-xs text-slate-400">{note}</p></Panel>
}
