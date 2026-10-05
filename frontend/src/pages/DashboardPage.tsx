import {
  ArrowRight,
  ArrowUpRight,
  BookOpenCheck,
  BriefcaseBusiness,
  Clock3,
  Compass,
  Plus,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react'
import type { ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '@/services/api'
import { useAuth } from '@/context/AuthContext'
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

export function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { profile, history, isLoading, error, refetch } = useProfileAndHistory()
  const catalog = useCatalog()
  const latestSummary = history.data?.[0]
  const latest = useQuery({
    queryKey: ['simulation', latestSummary?.id],
    queryFn: () => api.getSimulation(latestSummary!.id),
    enabled: Boolean(latestSummary?.id),
  })
  const simulate = useMutation({
    mutationFn: () => api.simulate(profile.data!.id, { label: 'Dashboard simulation' }),
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ['history', profile.data?.id] })
      queryClient.setQueryData(['simulation', result.id], result)
      navigate(`/simulation?simulationId=${result.id}`)
    },
  })
  const completion = profile.data ? calculateCompletion(profile.data) : 0
  const today = new Intl.DateTimeFormat('en', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date())
  const gaps = latest.data?.paths[0]?.skill_gaps ?? []
  const paths = latest.data?.paths.slice(0, 3) ?? []

  if (isLoading) return <LoadingState />
  if (error && !profile.data) return <ErrorState error={error} onRetry={() => void refetch()} />

  return (
    <>
      <PageHeading
        eyebrow={`${today} · Your career workspace`}
        title={`Good to see you, ${user?.full_name?.split(' ')[0] ?? 'there'}.`}
        description="A thoughtful next step starts with understanding where you are—and where your strengths can take you."
        action={(
          <button
            className="btn-primary"
            disabled={!profile.data || simulate.isPending}
            onClick={() => simulate.mutate()}
          >
            <Sparkles className="h-4 w-4" />
            {simulate.isPending ? 'Mapping your paths…' : 'Run simulation'}
          </button>
        )}
      />

      {simulate.error && <div className="mb-6"><ErrorState error={simulate.error} /></div>}
      {!profile.data && (
        <div className="mb-6">
          <Panel className="flex flex-col items-start justify-between gap-5 border-teal-200 bg-gradient-to-r from-teal-50 to-white sm:flex-row sm:items-center">
            <div className="flex items-start gap-4"><span className="rounded-xl bg-white p-3 text-teal-700 shadow-sm"><UserRoundIcon /></span><div><h2 className="font-semibold text-slate-900">Start with your career profile</h2><p className="mt-1 text-sm text-slate-500">Add your role, skills, and experience to unlock personalized career paths.</p></div></div>
            <Link to="/profile" className="btn-primary">Build my profile <ArrowRight className="h-4 w-4" /></Link>
          </Panel>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={<Target />} label="Profile strength" value={`${completion}%`} note={profile.data ? 'Based on completed sections' : 'Profile not created yet'} color="teal" />
        <MetricCard icon={<BriefcaseBusiness />} label="Current role" value={profile.data ? roleName(profile.data, catalog.roles.data ?? []) : 'Add your role'} note={profile.data?.years_of_experience ? `${profile.data.years_of_experience} years experience` : 'Career starting point'} color="blue" />
        <MetricCard icon={<Compass />} label="Career paths" value={latest.data ? String(latest.data.paths.length) : '—'} note={latest.data ? 'Ranked for your profile' : 'Run a simulation to explore'} color="violet" />
        <MetricCard icon={<BookOpenCheck />} label="Skills to develop" value={latest.data ? String(gaps.length) : '—'} note={latest.data ? 'Across your top path' : 'Personalized gap analysis'} color="amber" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(300px,.8fr)]">
        <div className="space-y-6">
          {latest.isLoading && latestSummary && <LoadingState label="Loading your latest simulation…" />}
          {latest.data ? (
            <section>
              {profile.data && (
                <CareerTrajectory3D
                  simulation={latest.data}
                  profile={profile.data}
                  roles={catalog.roles.data ?? []}
                  compact
                />
              )}
              <div className="mb-3 flex items-center justify-between">
                <div><p className="eyebrow">Personalized recommendations</p><h2 className="mt-1 text-lg font-bold text-slate-900">Career paths to consider</h2></div>
                <Link to={`/simulation?simulationId=${latest.data.id}`} className="btn-quiet">View all <ArrowRight className="h-4 w-4" /></Link>
              </div>
              <div className="space-y-4">{paths.map((path) => <CareerPathCard key={path.id} path={path} simulationId={latest.data!.id} />)}</div>
            </section>
          ) : (
            <Panel className="p-0"><EmptyState title="Your career map is waiting" description="Run a simulation to see ranked paths, confidence explanations, skill gaps, and practical next steps." action={<button className="btn-primary" disabled={!profile.data || simulate.isPending} onClick={() => simulate.mutate()}><Compass className="h-4 w-4" /> Explore my paths</button>} /></Panel>
          )}

          <Panel>
            <div className="flex items-start justify-between gap-4"><div><p className="eyebrow">Growth focus</p><h2 className="mt-1 text-lg font-bold text-slate-900">Skills that can move you forward</h2></div><TrendingUp className="h-5 w-5 text-teal-700" /></div>
            {latest.data && gaps.length ? <div className="mt-5 space-y-4">{gaps.slice(0, 4).map((gap) => <div key={gap.id}><div className="mb-1.5 flex items-center justify-between text-sm"><span className="font-medium text-slate-800">{gap.skill?.name ?? 'Skill'}</span><span className="text-xs text-slate-500">{gap.current_proficiency ?? 0} / {gap.required_proficiency ?? 5} proficiency</span></div><ProgressBar value={((gap.current_proficiency ?? 0) / (gap.required_proficiency ?? 5)) * 100} /></div>)}</div> : <p className="mt-3 text-sm leading-6 text-slate-500">{latest.data ? 'Your leading path has no identified skill gaps—focus on interview and portfolio readiness.' : 'Your profile-specific skill priorities will appear here after a simulation.'}</p>}
            {latest.data && <Link to={`/roadmap/${latest.data.paths[0]?.id}`} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-teal-800">Open your learning roadmap <ArrowUpRight className="h-4 w-4" /></Link>}
          </Panel>
        </div>

        <aside className="space-y-6">
          <Panel>
            <div className="flex items-center justify-between"><div><p className="eyebrow">Profile progress</p><h2 className="mt-1 font-bold text-slate-900">Your foundation</h2></div><Link to="/profile" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="Edit profile"><ArrowUpRight className="h-4 w-4" /></Link></div>
            <div className="mt-5"><ProgressBar value={completion} label="Profile completion" /></div>
            <div className="mt-5 space-y-3">{[
              ['Current role', Boolean(profile.data?.current_role_id)],
              ['Skills', Boolean(profile.data?.user_skills.length)],
              ['Experience', Boolean(profile.data?.experiences.length)],
              ['Education or projects', Boolean(profile.data?.educations.length || profile.data?.projects.length)],
            ].map(([label, complete]) => <div key={String(label)} className="flex items-center justify-between text-sm"><span className="text-slate-600">{label}</span><span className={`text-xs font-semibold ${complete ? 'text-emerald-700' : 'text-slate-400'}`}>{complete ? 'Added' : 'Add details'}</span></div>)}</div>
            <Link to="/profile" className="btn-secondary mt-5 w-full">Review my profile</Link>
          </Panel>
          <Panel>
            <div className="flex items-center justify-between"><div><p className="eyebrow">Recent activity</p><h2 className="mt-1 font-bold text-slate-900">Simulation history</h2></div><Clock3 className="h-4 w-4 text-slate-400" /></div>
            {history.data?.length ? <div className="mt-3 divide-y divide-slate-100">{history.data.slice(0, 4).map((entry) => <Link key={entry.id} to={`/history/${entry.id}`} className="flex items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-800">{entry.label || (entry.parent_simulation_id ? 'What-If scenario' : 'Career simulation')}</p><p className="mt-1 text-xs text-slate-400">{new Date(entry.created_at).toLocaleDateString()} · {entry.path_count} paths</p></div><ArrowRight className="h-4 w-4 shrink-0 text-slate-400" /></Link>)}</div> : <p className="mt-3 text-sm text-slate-500">Your saved simulations will show here.</p>}
            <Link to="/history" className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-teal-800">View history <ArrowRight className="h-4 w-4" /></Link>
          </Panel>
          <Link to="/what-if" className="group flex items-center justify-between rounded-2xl bg-[#0c3c3c] p-5 text-white shadow-sm transition hover:bg-[#104c49]"><div><span className="inline-flex rounded-lg bg-white/10 p-2 text-teal-200"><Plus className="h-4 w-4" /></span><p className="mt-3 font-semibold">Try a What-If scenario</p><p className="mt-1 text-xs text-white/60">Explore hypothetical growth safely</p></div><ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" /></Link>
        </aside>
      </div>
    </>
  )
}

function MetricCard({ icon, label, value, note, color }: { icon: ReactNode; label: string; value: string; note: string; color: string }) {
  const colorClass = { teal: 'metric-teal', blue: 'metric-blue', violet: 'metric-violet', amber: 'metric-amber' }[color] ?? 'metric-teal'
  return <Panel className="p-5"><div className="flex items-center justify-between"><span className="text-xs font-semibold text-slate-500">{label}</span><span className={`metric-icon ${colorClass}`}>{icon}</span></div><p className="mt-4 truncate text-2xl font-bold tracking-tight text-slate-950">{value}</p><p className="mt-1 text-xs text-slate-400">{note}</p></Panel>
}

function UserRoundIcon() {
  return <BriefcaseBusiness className="h-5 w-5" />
}

function calculateCompletion(profile: import('@/types').UserProfile) {
  const checks = [
    Boolean(profile.current_role_id),
    profile.user_skills.length > 0,
    profile.experiences.length > 0,
    profile.educations.length > 0,
    profile.projects.length > 0,
    Boolean(profile.bio),
    Boolean(profile.location),
  ]
  return Math.round((checks.filter(Boolean).length / checks.length) * 100)
}
