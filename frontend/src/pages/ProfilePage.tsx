import {
  BriefcaseBusiness,
  Check,
  GraduationCap,
  MapPin,
  Plus,
  Save,
  Search,
  Trash2,
  UserRound,
  Wrench,
} from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { api } from '@/services/api'
import type {
  EducationInput,
  ExperienceInput,
  ProjectInput,
  UserProfile,
  UserSkillInput,
} from '@/types'
import { ErrorState, LoadingState, PageHeading, Panel } from '@/components/ui'
import { apiErrorMessage, useCatalog, useProfileAndHistory } from '@/pages/hooks'

export function ProfilePage() {
  const { profile, isLoading, error, refetch } = useProfileAndHistory()
  const catalog = useCatalog()
  if (isLoading || catalog.roles.isLoading || catalog.skills.isLoading) return <LoadingState label="Loading your profile and career catalog…" />
  if (error && (error as { code?: string }).code !== 'NOT_FOUND') return <ErrorState error={error} onRetry={() => void refetch()} />
  if (catalog.roles.error) return <ErrorState error={catalog.roles.error} onRetry={() => void catalog.roles.refetch()} />
  if (catalog.skills.error) return <ErrorState error={catalog.skills.error} onRetry={() => void catalog.skills.refetch()} />
  return <ProfileEditor initial={profile.data ?? null} roles={catalog.roles.data ?? []} skills={catalog.skills.data ?? []} />
}

function ProfileEditor({ initial, roles, skills }: { initial: UserProfile | null; roles: import('@/types').RoleSummary[]; skills: import('@/types').SkillCatalogItem[] }) {
  const client = useQueryClient()
  const [roleId, setRoleId] = useState(initial?.current_role_id ?? '')
  const [years, setYears] = useState(initial?.years_of_experience ?? 0)
  const [bio, setBio] = useState(initial?.bio ?? '')
  const [location, setLocation] = useState(initial?.location ?? '')
  const [linkedin, setLinkedin] = useState(initial?.linkedin_url ?? '')
  const [github, setGithub] = useState(initial?.github_url ?? '')
  const [userSkills, setUserSkills] = useState<UserSkillInput[]>(initial?.user_skills.map(({ skill_id, proficiency_level, months_of_experience }) => ({ skill_id, proficiency_level, months_of_experience })) ?? [])
  const [educations, setEducations] = useState<EducationInput[]>(initial?.educations.map(({ institution, degree, field_of_study, start_year, end_year, is_current }) => ({ institution, degree, field_of_study, start_year, end_year, is_current })) ?? [])
  const [experiences, setExperiences] = useState<ExperienceInput[]>(initial?.experiences.map(({ company, title, description, start_date, end_date, is_current }) => ({ company, title, description, start_date, end_date, is_current })) ?? [])
  const [projects, setProjects] = useState<ProjectInput[]>(initial?.projects.map(({ company, title, description, start_date, end_date, is_current }) => ({ company, title, description, start_date, end_date, is_current })) ?? [])
  const [skillSearch, setSkillSearch] = useState('')
  const [message, setMessage] = useState('')
  const [validationMessage, setValidationMessage] = useState('')
  const existingIds = useMemo(() => new Set(userSkills.map((skill) => skill.skill_id)), [userSkills])
  const visibleSkills = skills.filter((skill) => !existingIds.has(skill.id) && `${skill.name} ${skill.category?.name ?? ''}`.toLowerCase().includes(skillSearch.toLowerCase())).slice(0, 8)
  const save = useMutation({
    mutationFn: () => {
      const payload = {
        current_role_id: roleId || null,
        years_of_experience: Number(years),
        bio: bio.trim() || null,
        location: location.trim() || null,
        linkedin_url: linkedin.trim() || null,
        github_url: github.trim() || null,
        skills: userSkills,
        educations,
        experiences,
        projects,
      }
      return initial ? api.updateProfile(payload) : api.createProfile(payload)
    },
    onSuccess: async (saved) => {
      setMessage('Your profile has been saved.')
      setValidationMessage('')
      await client.invalidateQueries({ queryKey: ['profile'] })
      client.setQueryData(['profile'], saved)
    },
  })

  useEffect(() => {
    if (save.isSuccess) {
      const timeout = window.setTimeout(() => setMessage(''), 4000)
      return () => window.clearTimeout(timeout)
    }
  }, [save.isSuccess])

  function submit(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    setValidationMessage('')
    if (userSkills.some((skill) => !skill.skill_id || skill.proficiency_level! < 1 || skill.proficiency_level! > 5)) {
      setValidationMessage('Choose a valid skill proficiency from 1 to 5.')
      return
    }
    save.mutate()
  }

  return (
    <>
      <PageHeading eyebrow="Your career foundation" title="Career profile" description="Your profile powers recommendations and skill-gap analysis. Keep it accurate as your experience grows." action={<button className="btn-primary" type="submit" form="profile-form" disabled={save.isPending}><Save className="h-4 w-4" />{save.isPending ? 'Saving…' : 'Save profile'}</button>} />
      {save.error && <div className="mb-5"><ErrorState error={{ message: apiErrorMessage(save.error) }} /></div>}
      {validationMessage && <p className="mb-5 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800" role="alert">{validationMessage}</p>}
      {message && <p className="mb-5 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800" role="status"><Check className="h-4 w-4" />{message}</p>}
      <form id="profile-form" onSubmit={submit} className="space-y-6">
        <Panel>
          <SectionTitle icon={<UserRound />} title="Career overview" description="A little context helps us understand your next step." />
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <label className="field-label">Current role
              <select className="input-control" value={roleId} onChange={(event) => setRoleId(event.target.value)}><option value="">Select your current role</option>{roles.map((role) => <option key={role.id} value={role.id}>{role.title}{role.domain ? ` · ${role.domain}` : ''}</option>)}</select>
            </label>
            <label className="field-label">Years of experience
              <input className="input-control" type="number" min="0" max="60" step="0.5" value={years} onChange={(event) => setYears(Number(event.target.value))} />
            </label>
            <label className="field-label sm:col-span-2">Professional summary
              <textarea className="input-control min-h-24 resize-y" maxLength={3000} value={bio} onChange={(event) => setBio(event.target.value)} placeholder="What do you work on? What are you proud of?" />
            </label>
            <label className="field-label"><span className="flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" />Location</span><input className="input-control" maxLength={200} value={location} onChange={(event) => setLocation(event.target.value)} placeholder="City, country" /></label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="field-label">LinkedIn URL<input className="input-control" type="url" value={linkedin} onChange={(event) => setLinkedin(event.target.value)} placeholder="https://linkedin.com/in/…" /></label>
              <label className="field-label">GitHub URL<input className="input-control" type="url" value={github} onChange={(event) => setGithub(event.target.value)} placeholder="https://github.com/…" /></label>
            </div>
          </div>
        </Panel>

        <Panel>
          <SectionTitle icon={<Wrench />} title="Skills & proficiency" description="Rate your current working proficiency. Being honest helps make the recommendations useful." />
          <div className="mt-5 space-y-3">
            {userSkills.map((item, index) => {
              const skill = skills.find((entry) => entry.id === item.skill_id)
              return <div key={item.skill_id} className="grid gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-3 sm:grid-cols-[minmax(0,1fr)_190px_190px_40px] sm:items-center">
                <div><p className="text-sm font-semibold text-slate-800">{skill?.name ?? 'Catalog skill'}</p><p className="mt-0.5 text-xs text-slate-400">{skill?.category?.name ?? 'Skill'}</p></div>
                <label className="field-label !gap-1">Proficiency<select className="input-control !py-2" value={item.proficiency_level ?? 3} onChange={(event) => setUserSkills((current) => current.map((row, idx) => idx === index ? { ...row, proficiency_level: Number(event.target.value) } : row))}>{['Beginner', 'Basic', 'Intermediate', 'Advanced', 'Expert'].map((label, idx) => <option key={label} value={idx + 1}>{idx + 1} · {label}</option>)}</select></label>
                <label className="field-label !gap-1">Practice (months)<input className="input-control !py-2" type="number" min="0" max="720" value={item.months_of_experience ?? ''} onChange={(event) => setUserSkills((current) => current.map((row, idx) => idx === index ? { ...row, months_of_experience: event.target.value === '' ? null : Number(event.target.value) } : row))} placeholder="Optional" /></label>
                <button type="button" className="icon-button self-end sm:self-auto" aria-label={`Remove ${skill?.name ?? 'skill'}`} onClick={() => setUserSkills((current) => current.filter((_, idx) => idx !== index))}><Trash2 className="h-4 w-4" /></button>
              </div>
            })}
          </div>
          <div className="mt-5">
            <label className="field-label">Add a skill
              <span className="input-icon-wrap"><Search className="input-icon" /><input className="input-control pl-10" value={skillSearch} onChange={(event) => setSkillSearch(event.target.value)} placeholder="Search the skill catalog…" /></span>
            </label>
            {skillSearch && <div className="mt-2 flex flex-wrap gap-2">{visibleSkills.map((skill) => <button type="button" key={skill.id} className="badge badge-button" onClick={() => { setUserSkills((current) => [...current, { skill_id: skill.id, proficiency_level: 3, months_of_experience: null }]); setSkillSearch('') }}><Plus className="h-3.5 w-3.5" />{skill.name}</button>)}</div>}
            {skillSearch && !visibleSkills.length && <p className="mt-2 text-sm text-slate-500">No additional catalog skills match “{skillSearch}”.</p>}
          </div>
        </Panel>

        <CollectionEditor title="Work experience" description="Roles, responsibilities, and meaningful outcomes." icon={<BriefcaseBusiness />} items={experiences} setItems={setExperiences} kind="experience" />
        <CollectionEditor title="Education" description="Degrees, programs, and relevant study." icon={<GraduationCap />} items={educations} setItems={setEducations} kind="education" />
        <CollectionEditor title="Projects" description="Projects that show your applied skills." icon={<Wrench />} items={projects} setItems={setProjects} kind="project" />
        <div className="flex justify-end"><button className="btn-primary min-w-40" type="submit" disabled={save.isPending}><Save className="h-4 w-4" />{save.isPending ? 'Saving profile…' : 'Save profile'}</button></div>
      </form>
    </>
  )
}

type CollectionKind = 'experience' | 'education' | 'project'
type CollectionItem = ExperienceInput | EducationInput | ProjectInput

function CollectionEditor<T extends CollectionItem>({ title, description, icon, items, setItems, kind }: { title: string; description: string; icon: React.ReactNode; items: T[]; setItems: React.Dispatch<React.SetStateAction<T[]>>; kind: CollectionKind }) {
  const add = () => {
    const item = kind === 'education'
      ? { institution: '', degree: '', field_of_study: '', start_year: null, end_year: null, is_current: false }
      : kind === 'experience'
        ? { company: '', title: '', description: '', start_date: null, end_date: null, is_current: false }
        : { company: '', title: '', description: '', start_date: null, end_date: null, is_current: false }
    setItems((current) => [...current, item as T])
  }
  return (
    <Panel>
      <div className="flex items-start justify-between gap-4"><SectionTitle icon={icon} title={title} description={description} /><button className="btn-secondary !px-3 !py-2" type="button" onClick={add}><Plus className="h-4 w-4" />Add</button></div>
      {!items.length ? <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No entries added yet.</p> : <div className="mt-5 space-y-4">{items.map((item, index) => <div key={index} className="rounded-xl border border-slate-100 p-4">
        <div className="mb-3 flex items-center justify-between"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{kind === 'experience' ? `Position ${index + 1}` : kind === 'education' ? `Education ${index + 1}` : `Project ${index + 1}`}</p><button type="button" className="icon-button" aria-label={`Remove ${kind}`} onClick={() => setItems((current) => current.filter((_, idx) => idx !== index))}><Trash2 className="h-4 w-4" /></button></div>
        {kind === 'education' ? <EducationFields item={item as EducationInput} update={(next) => setItems((current) => current.map((row, idx) => idx === index ? next as T : row))} /> : <WorkFields item={item as ExperienceInput | ProjectInput} project={kind === 'project'} update={(next) => setItems((current) => current.map((row, idx) => idx === index ? next as T : row))} />}
      </div>)}</div>}
    </Panel>
  )
}

function EducationFields({ item, update }: { item: EducationInput; update: (item: EducationInput) => void }) {
  const change = (field: keyof EducationInput, value: string | number | boolean | null) => update({ ...item, [field]: value })
  return <div className="grid gap-3 sm:grid-cols-2"><TextField label="Institution" required value={item.institution} onChange={(value) => change('institution', value)} /><TextField label="Degree" required value={item.degree} onChange={(value) => change('degree', value)} /><TextField label="Field of study" value={item.field_of_study ?? ''} onChange={(value) => change('field_of_study', value)} /><div className="grid grid-cols-2 gap-3"><TextField label="Start year" type="number" value={item.start_year ?? ''} onChange={(value) => change('start_year', value ? Number(value) : null)} /><TextField label="End year" type="number" value={item.end_year ?? ''} onChange={(value) => change('end_year', value ? Number(value) : null)} /></div><label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={Boolean(item.is_current)} onChange={(event) => change('is_current', event.target.checked)} />Currently studying</label></div>
}

function WorkFields({ item, project, update }: { item: ExperienceInput | ProjectInput; project: boolean; update: (item: ExperienceInput | ProjectInput) => void }) {
  const change = (field: keyof ExperienceInput | keyof ProjectInput, value: string | boolean | null) => update({ ...item, [field]: value })
  return <div className="grid gap-3 sm:grid-cols-2"><TextField label={project ? 'Project title' : 'Position title'} required value={item.title} onChange={(value) => change('title', value)} /><TextField label={project ? 'Organization (optional)' : 'Company'} value={item.company ?? ''} onChange={(value) => change('company', value)} /><TextField label="Start month" type="month" value={item.start_date ?? ''} onChange={(value) => change('start_date', value || null)} /><TextField label="End month" type="month" value={item.end_date ?? ''} onChange={(value) => change('end_date', value || null)} /><label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={Boolean(item.is_current)} onChange={(event) => change('is_current', event.target.checked)} />{project ? 'Ongoing project' : 'Current role'}</label><label className="field-label sm:col-span-2">Description<textarea className="input-control min-h-20" value={item.description ?? ''} onChange={(event) => change('description', event.target.value)} /></label></div>
}

function TextField({ label, value, onChange, type = 'text', required = false }: { label: string; value: string | number; onChange: (value: string) => void; type?: string; required?: boolean }) {
  return <label className="field-label">{label}<input className="input-control" type={type} required={required} value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function SectionTitle({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return <div className="flex items-start gap-3"><span className="section-icon">{icon}</span><div><h2 className="font-bold text-slate-900">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{description}</p></div></div>
}
