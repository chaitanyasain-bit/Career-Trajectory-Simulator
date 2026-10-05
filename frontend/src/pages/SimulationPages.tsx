import {
  ArrowLeft,
  ArrowRight,
  Check,
  GitCompareArrows,
  Info,
  Sparkles,
  Target,
} from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '@/services/api'
import type { RoleSkillRequirement, SimulationPath } from '@/types'
import {
  CareerPathCard,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeading,
  Panel,
  ProgressBar,
} from '@/components/ui'
import { roleName, useCatalog, useProfileAndHistory } from '@/pages/hooks'
import { LazyCareerTrajectory3D as CareerTrajectory3D } from '@/components/career3d/LazyCareerTrajectory3D'

export function SimulationPage() {
  const { profile, history, isLoading } = useProfileAndHistory()
  const catalog = useCatalog()
  const [params] = useSearchParams()
  const simulationId = params.get('simulationId')
  const client = useQueryClient()
  const navigate = useNavigate()
  const savedSimulation = useQuery({
    queryKey: ['simulation', simulationId],
    queryFn: () => api.getSimulation(simulationId!),
    enabled: Boolean(simulationId),
  })
  const run = useMutation({
    mutationFn: () => api.simulate(profile.data!.id, { label: 'Career path exploration' }),
    onSuccess: async (simulation) => {
      client.setQueryData(['simulation', simulation.id], simulation)
      await client.invalidateQueries({ queryKey: ['history', profile.data?.id] })
      navigate(`/simulation?simulationId=${simulation.id}`, { replace: true })
    },
  })
  const selected = savedSimulation.data

  if (isLoading || (simulationId && savedSimulation.isLoading)) return <LoadingState label="Loading your career paths…" />
  if (!profile.data) return <Panel><EmptyState title="Create your profile first" description="Your career simulation uses your real role, skills, and experience." action={<Link className="btn-primary" to="/profile">Build my profile <ArrowRight className="h-4 w-4" /></Link>} /></Panel>
  if (savedSimulation.error) return <ErrorState error={savedSimulation.error} onRetry={() => void savedSimulation.refetch()} />

  const role = profile.data ? roleName(profile.data, catalog.roles.data ?? []) : 'your career'
  const completed = history.data ?? []
  return (
    <>
      <PageHeading eyebrow="Career trajectory" title="Explore your next move" description={`Discover realistic next roles from your experience as ${role}. Recommendations use the live career catalog and explain what drives each score.`} action={(
        <button className="btn-primary" disabled={!profile.data || run.isPending} onClick={() => run.mutate()}><Sparkles className="h-4 w-4" />{run.isPending ? 'Analyzing your profile…' : 'Run new simulation'}</button>
      )} />
      {run.error && <div className="mb-5"><ErrorState error={run.error} /></div>}
      {run.isPending && <Panel className="mb-6"><div className="flex items-center gap-4"><span className="spinner spinner-large" /><div><p className="font-semibold text-slate-900">Mapping your career possibilities</p><p className="mt-1 text-sm text-slate-500">Matching profile evidence against role requirements and career transitions.</p></div></div><div className="mt-5"><ProgressBar value={72} label="Analyzing skills and adjacent paths" /></div></Panel>}

      {selected ? (
        <>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-teal-100 bg-teal-50/70 px-4 py-3">
            <div className="flex items-center gap-2 text-sm"><Check className="h-4 w-4 text-teal-700" /><span className="font-semibold text-slate-800">{selected.label || 'Saved career simulation'}</span><span className="text-slate-500">· {new Date(selected.created_at).toLocaleString()}</span></div>
            <span className="badge badge-teal">Saved result · Engine {selected.engine_version}</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <MiniStat title="Where you are now" value={role} detail={`${profile.data.years_of_experience} years of experience`} />
            <MiniStat
              title="Recommended next"
              value={selected.paths[0]?.target_role?.title ?? '—'}
              detail={selected.paths[0] ? `Rank #${selected.paths[0].rank} · ${selected.paths.length} paths explored` : 'No ranked path available'}
            />
            <MiniStat
              title="Current fit"
              value={selected.paths[0] ? `${Math.round(selected.paths[0].confidence_score * 100)}%` : '—'}
              detail={selected.paths[0]?.confidence_label ?? 'No confidence score'}
            />
            <MiniStat title="Skills to develop" value={selected.paths[0]?.skill_gaps.length ?? 0} detail="for the recommended role" />
            <MiniStat
              title="Estimated transition"
              value={selected.paths[0]?.estimated_months ? `~${selected.paths[0].estimated_months} mo` : 'Not estimated'}
              detail="based on this saved simulation"
            />
          </div>
          <div className="mt-6">
            <CareerTrajectory3D
              simulation={selected}
              profile={profile.data}
              roles={catalog.roles.data ?? []}
            />
          </div>
          <div className="mb-4 mt-8 flex flex-wrap items-end justify-between gap-3"><div><p className="eyebrow">Your personalized career paths</p><h2 className="mt-1 text-xl font-bold text-slate-950">Recommendations ranked by fit</h2></div><Link to={`/comparison?simulationId=${selected.id}`} className="btn-secondary"><GitCompareArrows className="h-4 w-4" />Compare paths</Link></div>
          <div className="space-y-4">{selected.paths.map((path) => <CareerPathCard key={path.id} path={path} simulationId={selected.id} />)}</div>
          <Panel className="mt-6 border-blue-100 bg-blue-50/50"><div className="flex gap-3"><Info className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" /><div><h3 className="text-sm font-semibold text-slate-900">How to read confidence</h3><p className="mt-1 text-sm leading-6 text-slate-600">Confidence is an explainable estimate based on proficiency-adjusted skill fit (60%), catalog transition likelihood (20%), experience (10%), and profile evidence (10%). It is a planning signal—not a guarantee of hiring outcomes.</p></div></div></Panel>
        </>
      ) : completed.length ? (
        <Panel><EmptyState title="Choose a saved simulation or run a new one" description="You have saved career results in your history. Open a previous run or create an updated simulation from your current profile." action={<Link className="btn-primary" to={`/history/${completed[0].id}`}>Open latest result <ArrowRight className="h-4 w-4" /></Link>} /></Panel>
      ) : (
        <Panel><EmptyState title="Your career map starts here" description="Run a simulation to explore ranked career paths based on the profile you have built." action={<button className="btn-primary" disabled={!profile.data || run.isPending} onClick={() => run.mutate()}><Sparkles className="h-4 w-4" />Run my first simulation</button>} /></Panel>
      )}
    </>
  )
}

export function CareerDetailPage() {
  const [params] = useSearchParams()
  const roleId = window.location.pathname.split('/').pop() ?? ''
  const role = useQuery({ queryKey: ['role', roleId], queryFn: () => api.getRole(roleId), enabled: Boolean(roleId) })
  const simulation = useQuery({ queryKey: ['simulation', params.get('simulationId')], queryFn: () => api.getSimulation(params.get('simulationId')!), enabled: Boolean(params.get('simulationId')) })
  const path = simulation.data?.paths.find((candidate) => candidate.target_role_id === roleId)
  if (role.isLoading || simulation.isLoading) return <LoadingState label="Loading career role details…" />
  if (role.error) return <ErrorState error={role.error} onRetry={() => void role.refetch()} />
  if (!role.data) return <ErrorState error={{ message: 'Career role not found.' }} />
  const requirements = role.data.skill_requirements ?? []
  const actualSkills = simulation.data?.paths.find((item) => item.target_role_id === roleId)?.skill_gaps ?? []
  const gapBySkill = new Map(actualSkills.map((gap) => [gap.skill_id, gap]))

  return <>
    <Link to={simulation.data ? `/simulation?simulationId=${simulation.data.id}` : '/simulation'} className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-teal-800"><ArrowLeft className="h-4 w-4" />Back to career paths</Link>
    <PageHeading eyebrow={`${role.data.domain ?? 'Career'} · Level ${role.data.seniority_level}`} title={role.data.title} description={role.data.description ?? 'Explore the role requirements and use your personalized skill-gap analysis to plan a path forward.'} action={<Link to={path ? `/roadmap/${path.id}` : '/simulation'} className="btn-primary">View my roadmap <ArrowRight className="h-4 w-4" /></Link>} />
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <Panel>
        <div className="flex items-start justify-between"><div><p className="eyebrow">Role requirements</p><h2 className="mt-1 text-lg font-bold">Skills that matter for this role</h2></div><span className="badge badge-teal">{requirements.length} skills</span></div>
        {requirements.length ? <div className="mt-5 divide-y divide-slate-100">{requirements.map((requirement) => <RequirementRow key={requirement.id} requirement={requirement} gap={gapBySkill.get(requirement.skill_id)} />)}</div> : <p className="mt-5 text-sm text-slate-500">Role requirements are not available in the catalog yet.</p>}
      </Panel>
      <div className="space-y-5">
        <Panel>
          <p className="eyebrow">Role snapshot</p>
          <div className="mt-4 space-y-4"><div><p className="section-label">Domain</p><p className="mt-1 font-semibold">{role.data.domain ?? 'Not specified'}</p></div><div><p className="section-label">Seniority</p><p className="mt-1 font-semibold">{['', 'Junior', 'Mid-level', 'Senior', 'Lead / Principal', 'Executive'][role.data.seniority_level]}</p></div>{role.data.avg_salary_inr !== null && <div><p className="section-label">Catalog salary estimate</p><p className="mt-1 font-semibold">₹{role.data.avg_salary_inr.toLocaleString('en-IN')} <span className="text-xs font-normal text-slate-400">average / year</span></p></div>}</div>
        </Panel>
        {path && <Panel><div className="flex items-center gap-2"><Target className="h-4 w-4 text-teal-700" /><p className="font-semibold">Your current fit</p></div><div className="mt-4 flex items-end justify-between"><span className="text-3xl font-bold">{Math.round(path.confidence_score * 100)}%</span><span className="text-xs text-slate-500">confidence</span></div><div className="mt-3"><ProgressBar value={path.confidence_score * 100} /></div><p className="mt-3 text-xs leading-5 text-slate-500">{path.skill_gaps.length} proficiency gaps · estimated {path.estimated_months ?? '—'} months</p></Panel>}
        <Link to="/what-if" className="flex items-center justify-between rounded-2xl bg-[#0c3c3c] p-4 text-white"><div><p className="font-semibold">Test a What-If</p><p className="mt-1 text-xs text-white/60">See how a new skill can change your fit</p></div><ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  </>
}

function RequirementRow({ requirement, gap }: { requirement: RoleSkillRequirement; gap?: SimulationPath['skill_gaps'][number] }) {
  const current = gap?.current_proficiency ?? requirement.required_proficiency
  const missing = Boolean(gap)
  return <div className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_150px_120px] sm:items-center">
    <div><p className="text-sm font-semibold text-slate-800">{requirement.skill?.name ?? 'Skill'}</p><p className="mt-0.5 text-xs text-slate-400">{requirement.skill?.category_id ? 'Catalog skill' : ''}{requirement.notes ? ` · ${requirement.notes}` : ''}</p></div>
    <div><div className="mb-1 flex justify-between text-[11px] text-slate-500"><span>Your level</span><span>{current}/5</span></div><ProgressBar value={(current / 5) * 100} /></div>
    <span className={`badge justify-center ${missing ? 'badge-amber' : 'badge-green'}`}>{missing ? `Gap · needs ${requirement.required_proficiency}` : `Met · ${requirement.required_proficiency} required`}</span>
  </div>
}

export function ComparisonPage() {
  const [params] = useSearchParams()
  const { history, isLoading } = useProfileAndHistory()
  const [simulationId, setSimulationId] = useState(params.get('simulationId') ?? '')
  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    const pathId = params.get('pathId')
    return pathId ? [pathId] : []
  })
  const simulation = useQuery({ queryKey: ['simulation', simulationId], queryFn: () => api.getSimulation(simulationId), enabled: Boolean(simulationId) })
  const paths = simulation.data?.paths ?? []
  const selected = paths.filter((path) => selectedIds.includes(path.id))
  if (isLoading) return <LoadingState />
  return <>
    <PageHeading eyebrow="Make the trade-offs visible" title="Compare career paths" description="Review your strongest options side by side: current fit, required skills, effort, and what you could work on next." />
    <Panel className="mb-5">
      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)] sm:items-end">
        <label className="field-label">Simulation result<select className="input-control" value={simulationId} onChange={(event) => { setSimulationId(event.target.value); setSelectedIds([]) }}><option value="">Choose a saved simulation</option>{history.data?.map((item) => <option key={item.id} value={item.id}>{item.label || 'Career simulation'} · {new Date(item.created_at).toLocaleDateString()}</option>)}</select></label>
        <p className="text-xs leading-5 text-slate-500">
          {selectedIds.length === 1
            ? 'One path is preselected. Choose at least one more to compare confidence, skill requirements, gaps, and estimated time.'
            : 'Select two or more careers to compare their confidence, skill requirements, gaps, and estimated time.'}
        </p>
      </div>
      {simulation.error && <div className="mt-4"><ErrorState error={simulation.error} onRetry={() => void simulation.refetch()} /></div>}
      {simulation.isLoading && <div className="mt-4"><LoadingState label="Loading career paths…" /></div>}
      {paths.length > 0 && <div className="mt-5 flex flex-wrap gap-2">{paths.map((path) => <button key={path.id} onClick={() => setSelectedIds((current) => current.includes(path.id) ? current.filter((id) => id !== path.id) : current.length < 4 ? [...current, path.id] : current)} className={`rounded-xl border px-3 py-2 text-sm font-medium transition ${selectedIds.includes(path.id) ? 'border-teal-700 bg-teal-50 text-teal-900' : 'border-slate-200 bg-white text-slate-600 hover:border-teal-300'}`}><span className="mr-2">{selectedIds.includes(path.id) ? '☑' : '□'}</span>{path.target_role?.title ?? path.engine_metadata.target_role_title}</button>)}</div>}
    </Panel>
    {selected.length >= 2 ? <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm"><table className="min-w-[760px] w-full border-collapse text-left"><thead><tr className="bg-slate-50"><th className="w-48 p-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Dimension</th>{selected.map((path) => <th className="border-l border-slate-100 p-4 text-sm font-bold text-slate-900" key={path.id}>{path.target_role?.title ?? path.engine_metadata.target_role_title}</th>)}</tr></thead><tbody>
      <CompareRow label="Confidence">{selected.map((path) => <td key={path.id} className="border-l border-t border-slate-100 p-4"><p className="text-xl font-bold">{Math.round(path.confidence_score * 100)}%</p><p className="mt-1 text-xs text-slate-500">{path.confidence_label} fit</p></td>)}</CompareRow>
      <CompareRow label="Estimated timeline">{selected.map((path) => <td key={path.id} className="border-l border-t border-slate-100 p-4 text-sm">{path.estimated_months ? `~${path.estimated_months} months` : 'Not estimated'}</td>)}</CompareRow>
      <CompareRow label="Skills to develop">{selected.map((path) => <td key={path.id} className="border-l border-t border-slate-100 p-4"><span className="font-semibold">{path.skill_gaps.length}</span><div className="mt-2 flex flex-wrap gap-1">{path.skill_gaps.slice(0, 6).map((gap) => <span className="badge badge-slate" key={gap.id}>{gap.skill?.name}</span>)}</div></td>)}</CompareRow>
      <CompareRow label="Required skills">{selected.map((path) => <td key={path.id} className="border-l border-t border-slate-100 p-4"><div className="flex flex-wrap gap-1">{path.engine_metadata.required_skill_count ? <span className="badge badge-teal">{path.engine_metadata.required_skill_count} role requirements</span> : <span className="text-xs text-slate-400">See career details</span>}</div><Link className="mt-3 inline-flex text-xs font-semibold text-teal-800" to={`/careers/${path.target_role_id}?simulationId=${simulationId}`}>View requirements <ArrowRight className="ml-1 h-3.5 w-3.5" /></Link></td>)}</CompareRow>
      <CompareRow label="Recommended next step">{selected.map((path) => <td key={path.id} className="border-l border-t border-slate-100 p-4 text-sm text-slate-600">{path.roadmap_steps[0]?.title ?? 'Review your profile'}<Link className="mt-2 flex items-center gap-1 text-xs font-semibold text-teal-800" to={`/roadmap/${path.id}`}>Open roadmap <ArrowRight className="h-3 w-3" /></Link></td>)}</CompareRow>
    </tbody></table></div> : <Panel><div className="empty-state"><GitCompareArrows className="h-8 w-8 text-teal-700" /><h3 className="mt-3 font-semibold">Choose at least two career paths</h3><p className="mt-1 text-sm text-slate-500">Select careers above to see the differences side by side.</p></div></Panel>}
  </>
}

function CompareRow({ label, children }: { label: string; children: React.ReactNode }) {
  return <tr><th className="border-t border-slate-100 bg-slate-50/60 p-4 align-top text-xs font-semibold text-slate-600">{label}</th>{children}</tr>
}

function MiniStat({ title, value, detail }: { title: string; value: string | number; detail: string }) {
  return <Panel className="p-4"><p className="text-xs font-semibold text-slate-500">{title}</p><p className="mt-2 truncate text-xl font-bold text-slate-900">{value}</p><p className="mt-1 text-xs text-slate-400">{detail}</p></Panel>
}
