import { AlertCircle, ArrowRight, LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { ConfidenceLabel, SimulationPath } from '@/types'

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
          {title}
        </h1>
        {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export function Panel({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return <section className={`panel ${className}`}>{children}</section>
}

export function LoadingState({ label = 'Loading your career data…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white p-12 text-sm text-slate-500">
      <LoaderCircle className="h-5 w-5 animate-spin text-teal-700" />
      {label}
    </div>
  )
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message =
    typeof error === 'object' && error !== null && 'message' in error
      ? String(error.message)
      : 'We could not load this data. Please try again.'
  return (
    <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800" role="alert">
      <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
      <div className="flex-1">
        <p className="font-semibold">Something went wrong</p>
        <p className="mt-1">{message}</p>
      </div>
      {onRetry && <button className="btn-secondary !px-3 !py-1.5" onClick={onRetry}>Retry</button>}
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
        <ArrowRight className="h-5 w-5" />
      </div>
      <h3 className="font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-sm text-sm leading-6 text-slate-500">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function ProgressBar({ value, label }: { value: number; label?: string }) {
  const bounded = Math.min(100, Math.max(0, value))
  return (
    <div>
      {label && <div className="mb-2 flex justify-between text-xs font-medium text-slate-500"><span>{label}</span><span>{Math.round(bounded)}%</span></div>}
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-teal-600 transition-all" style={{ width: `${bounded}%` }} />
      </div>
    </div>
  )
}

export function ConfidenceBadge({ label }: { label: ConfidenceLabel }) {
  const style = label === 'High' ? 'badge-green' : label === 'Medium' ? 'badge-amber' : 'badge-slate'
  return <span className={`badge ${style}`}>{label} confidence</span>
}

export function CareerPathCard({
  path,
  simulationId,
}: {
  path: SimulationPath
  simulationId: string
}) {
  const title = path.target_role?.title ?? path.engine_metadata.target_role_title ?? 'Career path'
  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-slate-100 p-5 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="rank-chip">{String(path.rank).padStart(2, '0')}</span>
            <div>
              <Link to={`/careers/${path.target_role_id}?simulationId=${simulationId}`} className="text-lg font-bold text-slate-950 hover:text-teal-700">
                {title}
              </Link>
              <p className="mt-1 text-sm text-slate-500">
                {path.target_role?.domain ?? path.engine_metadata.target_role_domain ?? 'Career progression'}
                {path.estimated_months ? ` · ~${path.estimated_months} months` : ''}
              </p>
            </div>
          </div>
          <ConfidenceBadge label={path.confidence_label} />
        </div>
        <div className="mt-5 flex items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-teal-600" style={{ width: `${path.confidence_score * 100}%` }} />
          </div>
          <span className="w-12 text-right text-sm font-bold text-slate-800">{Math.round(path.confidence_score * 100)}%</span>
        </div>
      </div>
      <div className="grid gap-4 p-5 sm:grid-cols-2 sm:p-6">
        <div>
          <p className="section-label">Top skill gaps</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {path.skill_gaps.length ? path.skill_gaps.slice(0, 4).map((gap) => (
              <span key={gap.id} className="badge badge-slate">{gap.skill?.name ?? 'Skill'} · {gap.current_proficiency ?? 0}/{gap.required_proficiency ?? '?'}</span>
            )) : <span className="text-sm text-emerald-700">No catalog skill gaps</span>}
            {path.skill_gaps.length > 4 && <span className="badge badge-slate">+{path.skill_gaps.length - 4} more</span>}
          </div>
        </div>
        <div>
          <p className="section-label">Career transition</p>
          <p className="mt-2 text-sm text-slate-600">
            {path.engine_metadata.transition_path?.map((role) => role.replace(/_/g, ' ')).join(' → ') || 'Explore adjacent roles in the catalog'}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 border-t border-slate-100 bg-slate-50/70 p-4">
        <Link to={`/careers/${path.target_role_id}?simulationId=${simulationId}`} className="btn-quiet">View career details</Link>
        <Link to={`/roadmap/${path.id}`} className="btn-quiet">Open roadmap</Link>
        <Link to={`/comparison?simulationId=${simulationId}`} className="btn-quiet">Compare paths</Link>
      </div>
    </Panel>
  )
}
