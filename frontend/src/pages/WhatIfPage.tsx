import {
  ArrowRight,
  Beaker,
  Info,
  Lightbulb,
  Plus,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/services/api'
import type { WhatIfChange, WhatIfResult } from '@/types'
import { CareerPathCard, EmptyState, ErrorState, LoadingState, PageHeading, Panel, ProgressBar } from '@/components/ui'
import { useCatalog, useProfileAndHistory } from '@/pages/hooks'

export function WhatIfPage() {
  const { profile, history, isLoading } = useProfileAndHistory()
  const catalog = useCatalog()
  const queryClient = useQueryClient()
  const [baselineId, setBaselineId] = useState('')
  const [addedSkills, setAddedSkills] = useState<string[]>([])
  const [overrides, setOverrides] = useState<Record<string, number>>({})
  const [months, setMonths] = useState(0)
  const [projectTitle, setProjectTitle] = useState('')
  const [projectDescription, setProjectDescription] = useState('')
  const [projectMonth, setProjectMonth] = useState('')
  const [label, setLabel] = useState('What-If scenario')
  const [result, setResult] = useState<WhatIfResult | null>(null)
  const [skillSearch, setSkillSearch] = useState('')

  const baselineQuery = useQuery({
    queryKey: ['simulation', baselineId],
    queryFn: () => api.getSimulation(baselineId),
    enabled: Boolean(baselineId),
  })
  const run = useMutation({
    mutationFn: (change: WhatIfChange) => api.whatif(baselineId, change),
    onSuccess: async (response) => {
      setResult(response)
      const child = response.hypothetical_simulation
      queryClient.setQueryData(['simulation', child.id], child)
      await queryClient.invalidateQueries({ queryKey: ['history', profile.data?.id] })
    },
  })

  const profileSkillIds = useMemo(() => new Set(profile.data?.user_skills.map((item) => item.skill_id) ?? []), [profile.data])
  const availableSkills = (catalog.skills.data ?? []).filter((skill) => !profileSkillIds.has(skill.id) && !addedSkills.includes(skill.id) && skill.name.toLowerCase().includes(skillSearch.toLowerCase())).slice(0, 10)
  const baselineOptions = history.data?.filter((item) => !item.parent_simulation_id) ?? []

  if (isLoading || catalog.skills.isLoading) return <LoadingState />
  if (!profile.data) return <Panel><EmptyState title="Build your profile first" description="What-If scenarios start from a saved simulation of your career profile." action={<Link to="/profile" className="btn-primary">Create my profile <ArrowRight className="h-4 w-4" /></Link>} /></Panel>

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!baselineId) return
    const change: WhatIfChange = {
      add_skill_ids: addedSkills,
      add_proficiency_overrides: overrides,
      add_experience_months: Number(months),
      add_projects: projectTitle.trim() ? [{
        title: projectTitle.trim(),
        description: projectDescription.trim() || null,
        start_date: projectMonth || null,
      }] : [],
      label: label.trim() || null,
    }
    run.mutate(change)
  }

  return <>
    <PageHeading eyebrow="A safe space to experiment" title="What-If simulator" description="Test how new skills, deeper proficiency, experience, and projects could change your career paths—without changing your real profile." />
    <div className="mb-6 flex items-start gap-3 rounded-2xl border border-violet-200 bg-violet-50 px-4 py-4 text-sm text-violet-950"><span className="rounded-xl bg-white p-2 text-violet-700 shadow-sm"><Beaker className="h-5 w-5" /></span><div><p className="font-semibold">This is hypothetical. Your profile stays unchanged.</p><p className="mt-1 leading-5 text-violet-800/80">We branch from the saved simulation snapshot you select below. Scenario inputs are stored only on the linked What-If result.</p></div></div>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <form onSubmit={submit} className="space-y-5">
        <Panel>
          <FieldHeading icon={<Sparkles />} title="Choose your starting point" description="Pick a saved baseline simulation. Scenarios always compare against this exact result." />
          <label className="field-label mt-5">Baseline simulation<select className="input-control" required value={baselineId} onChange={(event) => { setBaselineId(event.target.value); setResult(null) }}><option value="">Choose a baseline</option>{baselineOptions.map((item) => <option key={item.id} value={item.id}>{item.label || 'Career simulation'} · {new Date(item.created_at).toLocaleDateString()}</option>)}</select></label>
          {baselineQuery.error && <div className="mt-4"><ErrorState error={baselineQuery.error} onRetry={() => void baselineQuery.refetch()} /></div>}
        </Panel>
        <Panel>
          <FieldHeading icon={<TrendingUp />} title="Build a scenario" description="Choose one or more changes to test. You can combine all of them." />
          <div className="mt-5 space-y-5">
            <div>
              <label className="field-label" htmlFor="what-if-skill-search">Add hypothetical skills</label>
              {addedSkills.length > 0 && <div className="mb-2 flex flex-wrap gap-2">{addedSkills.map((id) => { const skill = catalog.skills.data?.find((item) => item.id === id); return <button key={id} type="button" className="badge badge-teal" onClick={() => setAddedSkills((current) => current.filter((item) => item !== id))}>{skill?.name} ×</button> })}</div>}
              <div className="input-icon-wrap"><Lightbulb className="input-icon" /><input id="what-if-skill-search" className="input-control pl-10" value={skillSearch} onChange={(event) => setSkillSearch(event.target.value)} placeholder="Search the live skill catalog…" /></div>
              {skillSearch && <div className="mt-2 flex flex-wrap gap-2">{availableSkills.map((skill) => <button type="button" className="badge badge-button" key={skill.id} onClick={() => { setAddedSkills((current) => [...current, skill.id]); setSkillSearch('') }}><Plus className="h-3.5 w-3.5" />{skill.name}</button>)}</div>}
              {addedSkills.map((id) => <label key={id} className="field-label mt-3 sm:max-w-xs">{catalog.skills.data?.find((skill) => skill.id === id)?.name} proficiency<select className="input-control" value={overrides[id] ?? 3} onChange={(event) => setOverrides((current) => ({ ...current, [id]: Number(event.target.value) }))}>{['Beginner', 'Basic', 'Intermediate', 'Advanced', 'Expert'].map((name, index) => <option key={name} value={index + 1}>{index + 1} · {name}</option>)}</select></label>)}
            </div>

            <div>
              <p className="field-label">Change proficiency on your current skills</p>
              <div className="mt-2 grid gap-3 sm:grid-cols-2">{profile.data.user_skills.map((item) => <label key={item.id} className="field-label rounded-xl border border-slate-100 bg-slate-50 p-3">{item.skill?.name ?? 'Skill'} <span className="font-normal text-slate-400">now {item.proficiency_level}/5</span><select className="input-control mt-2" value={overrides[item.skill_id] ?? item.proficiency_level} onChange={(event) => setOverrides((current) => ({ ...current, [item.skill_id]: Number(event.target.value) }))}>{['Beginner', 'Basic', 'Intermediate', 'Advanced', 'Expert'].map((name, index) => <option key={name} value={index + 1}>{index + 1} · {name}</option>)}</select></label>)}</div>
              {!profile.data.user_skills.length && <p className="mt-2 text-sm text-slate-500">Add a hypothetical skill above to test its proficiency.</p>}
            </div>
            <label className="field-label sm:max-w-xs">Additional experience<input className="input-control" type="number" min="0" max="720" step="1" value={months} onChange={(event) => setMonths(Number(event.target.value))} /><span className="text-xs font-normal text-slate-400">Months beyond the selected baseline</span></label>
            <div className="grid gap-3 sm:grid-cols-2"><label className="field-label">Hypothetical project title<input className="input-control" maxLength={200} value={projectTitle} onChange={(event) => setProjectTitle(event.target.value)} placeholder="e.g. Customer churn model" /></label><label className="field-label">Project start month<input className="input-control" type="month" value={projectMonth} onChange={(event) => setProjectMonth(event.target.value)} /></label><label className="field-label sm:col-span-2">Project description<textarea className="input-control min-h-20" maxLength={3000} value={projectDescription} onChange={(event) => setProjectDescription(event.target.value)} placeholder="What would you build or accomplish?" /></label></div>
            <label className="field-label">Scenario label<input className="input-control" maxLength={200} value={label} onChange={(event) => setLabel(event.target.value)} /></label>
          </div>
          {run.error && <div className="mt-4"><ErrorState error={run.error} /></div>}
          <button className="btn-primary mt-5 w-full sm:w-auto" type="submit" disabled={!baselineId || run.isPending}><Beaker className="h-4 w-4" />{run.isPending ? 'Running scenario…' : 'Run What-If scenario'}</button>
        </Panel>
      </form>

      <aside className="space-y-5">
        <Panel className="border-violet-100 bg-violet-50/60"><Info className="h-5 w-5 text-violet-700" /><h3 className="mt-3 font-semibold text-slate-900">What gets compared?</h3><ul className="mt-3 space-y-2 text-sm leading-5 text-slate-600"><li>Confidence changes for every recommended role</li><li>Newly unlocked or improved career paths</li><li>Skill gaps that improve or resolve</li><li>Roadmap actions added or removed</li></ul></Panel>
        {baselineQuery.data && <Panel><p className="eyebrow">Selected baseline</p><h3 className="mt-1 font-bold text-slate-900">{baselineQuery.data.label || 'Career simulation'}</h3><p className="mt-1 text-xs text-slate-500">{baselineQuery.data.paths.length} paths · {new Date(baselineQuery.data.created_at).toLocaleDateString()}</p><div className="mt-4 space-y-3">{baselineQuery.data.paths.slice(0, 3).map((path) => <div key={path.id}><div className="mb-1 flex justify-between gap-2 text-xs"><span className="truncate font-medium text-slate-700">{path.target_role?.title}</span><span>{Math.round(path.confidence_score * 100)}%</span></div><ProgressBar value={path.confidence_score * 100} /></div>)}</div></Panel>}
      </aside>
    </div>
    {result && <ScenarioResults result={result} />}
  </>
}

function ScenarioResults({ result }: { result: WhatIfResult }) {
  const scenario = result.hypothetical_simulation
  return <section className="mt-9">
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><p className="eyebrow">Scenario analysis</p><h2 className="mt-1 text-xl font-bold text-slate-950">What changed in your career map</h2></div><span className="badge badge-violet">Saved as linked scenario</span></div>
    <div className="mb-5 grid gap-4 sm:grid-cols-3"><ResultStat label="Newly unlocked" value={result.newly_unlocked_roles.length} note="paths moved above medium confidence" /><ResultStat label="Improved paths" value={result.improved_confidence_roles.length} note="with a confidence increase" /><ResultStat label="Gap / roadmap updates" value={result.skill_gap_changes.length + result.roadmap_changes.length} note="roles with actionable changes" /></div>
    <Panel className="mb-5"><div className="flex items-start gap-3"><TrendingUp className="mt-0.5 h-5 w-5 text-teal-700" /><div><h3 className="font-semibold">Confidence changes vs. baseline</h3><p className="mt-1 text-xs text-slate-500">Positive changes are green; the comparison uses the saved baseline.</p></div></div><div className="mt-5 space-y-4">{result.confidence_changes.map((change) => <div key={change.role_id} className="grid gap-2 sm:grid-cols-[180px_1fr_100px] sm:items-center"><p className="truncate text-sm font-medium text-slate-800">{change.role_title}</p><div className="flex items-center gap-2"><div className="relative h-2 flex-1 overflow-hidden rounded-full bg-slate-100"><div className="absolute inset-y-0 left-0 rounded-full bg-slate-300" style={{ width: `${(change.original_score ?? 0) * 100}%` }} /><div className="absolute inset-y-0 left-0 rounded-full bg-teal-600/80" style={{ width: `${change.scenario_score * 100}%` }} /></div><span className="w-10 text-right text-xs font-semibold">{Math.round(change.scenario_score * 100)}%</span></div><span className={`text-xs font-bold ${change.delta > 0 ? 'text-emerald-700' : change.delta < 0 ? 'text-rose-700' : 'text-slate-400'}`}>{change.original_score === null ? 'NEW PATH' : `${change.delta > 0 ? '+' : ''}${Math.round(change.delta * 100)} pts`}</span></div>)}</div><div className="mt-4 flex gap-4 text-[11px] text-slate-500"><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-slate-300" />Baseline</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-teal-600" />Scenario</span></div></Panel>
    <div className="grid gap-5 xl:grid-cols-2">
      <Panel><h3 className="font-bold">Skill-gap changes</h3>{result.skill_gap_changes.length ? <div className="mt-4 space-y-4">{result.skill_gap_changes.map((change) => <div key={change.role_id} className="border-t border-slate-100 pt-3"><p className="text-sm font-semibold">{change.role_title}</p><div className="mt-2 flex flex-wrap gap-1.5">{change.resolved.map((item) => <span className="badge badge-green" key={item}>Resolved · {item}</span>)}{change.improved.map((item) => <span className="badge badge-teal" key={item}>Improved · {item}</span>)}{change.newly_missing.map((item) => <span className="badge badge-amber" key={item}>New gap · {item}</span>)}</div></div>)}</div> : <p className="mt-3 text-sm text-slate-500">No skill-gap changes from this scenario.</p>}</Panel>
      <Panel><h3 className="font-bold">Roadmap changes</h3>{result.roadmap_changes.length ? <div className="mt-4 space-y-4">{result.roadmap_changes.map((change) => <div key={change.role_id} className="border-t border-slate-100 pt-3"><p className="text-sm font-semibold">{change.role_title}</p><div className="mt-2 space-y-1 text-xs">{change.removed_steps.map((item) => <p className="text-emerald-700" key={item}>− {item}</p>)}{change.added_steps.map((item) => <p className="text-teal-800" key={item}>+ {item}</p>)}</div></div>)}</div> : <p className="mt-3 text-sm text-slate-500">No roadmap changes from this scenario.</p>}</Panel>
    </div>
    <div className="mb-4 mt-8 flex items-end justify-between"><div><p className="eyebrow">Scenario paths</p><h3 className="mt-1 text-lg font-bold">Updated career recommendations</h3></div><Link to={`/history/${scenario.id}`} className="btn-quiet">View saved scenario <ArrowRight className="h-4 w-4" /></Link></div>
    <div className="space-y-4">{scenario.paths.slice(0, 5).map((path) => <CareerPathCard key={path.id} path={path} simulationId={scenario.id} />)}</div>
  </section>
}

function FieldHeading({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return <div className="flex items-start gap-3"><span className="section-icon">{icon}</span><div><h2 className="font-bold">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{description}</p></div></div>
}

function ResultStat({ label, value, note }: { label: string; value: number; note: string }) {
  return <Panel className="p-4"><p className="text-xs font-semibold text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-950">{value}</p><p className="mt-1 text-xs text-slate-400">{note}</p></Panel>
}
