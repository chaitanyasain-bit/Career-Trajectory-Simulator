/**
 * Shared TypeScript contracts for the versioned FastAPI API.
 * Field names match the Pydantic JSON schemas (snake_case).
 */

export interface UserAccount {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
}

export interface AuthCredentials {
  email: string
  password: string
}

export interface RegisterAccount extends AuthCredentials {
  full_name: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  user: UserAccount
}

export interface SkillSummary {
  id: string
  name: string
  normalized_name: string
  category_id: string
}

export interface UserSkillInput {
  skill_id: string
  proficiency_level?: number
  months_of_experience?: number | null
}

export interface UserSkill extends UserSkillInput {
  id: string
  profile_id: string
  is_self_assessed: boolean
  skill: SkillSummary | null
  created_at: string
  updated_at: string
}

export interface EducationInput {
  institution: string
  degree: string
  field_of_study?: string | null
  start_year?: number | null
  end_year?: number | null
  is_current?: boolean
}

export interface Education extends EducationInput {
  id: string
  profile_id: string
  created_at: string
  updated_at: string
}

export interface ExperienceInput {
  company?: string | null
  title: string
  description?: string | null
  start_date?: string | null
  end_date?: string | null
  is_current?: boolean
}

export interface WorkExperience extends ExperienceInput {
  id: string
  profile_id: string
  is_project: false
  created_at: string
  updated_at: string
}

export interface ProjectInput {
  title: string
  company?: string | null
  description?: string | null
  start_date?: string | null
  end_date?: string | null
  is_current?: boolean
}

export interface Project extends ProjectInput {
  id: string
  profile_id: string
  is_project: true
  created_at: string
  updated_at: string
}

export interface UserProfileFields {
  current_role_id?: string | null
  years_of_experience?: number
  bio?: string | null
  location?: string | null
  linkedin_url?: string | null
  github_url?: string | null
}

export interface UserProfileCreate extends UserProfileFields {
  skills?: UserSkillInput[]
  educations?: EducationInput[]
  experiences?: ExperienceInput[]
  projects?: ProjectInput[]
}

export interface UserProfileUpdate {
  current_role_id?: string | null
  years_of_experience?: number
  bio?: string | null
  location?: string | null
  linkedin_url?: string | null
  github_url?: string | null
  skills?: UserSkillInput[]
  educations?: EducationInput[]
  experiences?: ExperienceInput[]
  projects?: ProjectInput[]
}

export interface UserProfile {
  id: string
  user_id: string
  current_role_id: string | null
  years_of_experience: number
  bio: string | null
  location: string | null
  linkedin_url: string | null
  github_url: string | null
  user_skills: UserSkill[]
  educations: Education[]
  experiences: WorkExperience[]
  projects: Project[]
  created_at: string
  updated_at: string
}

export interface RoleSummary {
  id: string
  title: string
  normalized_title: string
  domain: string | null
  seniority_level: number
}

export interface RoleSkillRequirement {
  id: string
  role_id: string
  skill_id: string
  importance_level: number
  required_proficiency: number
  is_mandatory: boolean
  notes: string | null
  skill: SkillSummary | null
  created_at: string
  updated_at: string
}

export interface RoleCatalogDetail extends RoleSummary {
  description: string | null
  avg_salary_inr: number | null
  avg_years_to_reach: number | null
  skill_requirements?: RoleSkillRequirement[]
}

export interface SkillCatalogItem extends SkillSummary {
  description: string | null
  created_at: string
  updated_at: string
  category: {
    id: string
    name: string
    description: string | null
    display_order: number
    created_at: string
    updated_at: string
  } | null
}

export interface SkillCategory {
  id: string
  name: string
  description: string | null
  display_order: number
  skill_count: number
  created_at: string
  updated_at: string
}

export interface CatalogPage<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export type ConfidenceLabel = 'High' | 'Medium' | 'Low'

export interface SkillGap {
  id: string
  skill_id: string
  skill: SkillSummary | null
  priority_rank: number
  gap_score: number
  current_proficiency: number | null
  required_proficiency: number | null
  importance_level: number | null
  is_mandatory: boolean | null
  learning_resource: string | null
  notes: string | null
}

export interface RoadmapStep {
  id: string
  step_order: number
  title: string
  description: string | null
  step_type: 'skill' | 'project' | 'certification' | 'networking' | 'experience'
  estimated_weeks: number | null
  resource_url: string | null
  skill_id: string | null
  skill: SkillSummary | null
}

export interface ConfidenceFactor {
  factor: string
  weight: number
  value: number
  contribution: number
  explanation: string
}

export interface SimulationPath {
  id: string
  simulation_id: string
  target_role_id: string
  target_role: RoleSummary | null
  confidence_score: number
  confidence_label: ConfidenceLabel
  estimated_months: number | null
  rank: number
  engine_metadata: {
    target_role_title?: string
    target_role_domain?: string | null
    target_seniority_level?: number
    confidence_factors?: ConfidenceFactor[]
    why_recommended?: string[]
    transition_path?: string[]
    gap_count?: number
    profile_completeness?: number
    required_skill_count?: number
    [key: string]: unknown
  }
  skill_gaps: SkillGap[]
  roadmap_steps: RoadmapStep[]
}

export interface SimulationResult {
  id: string
  profile_id: string
  parent_simulation_id: string | null
  label: string | null
  engine_version: string
  notes: string | null
  paths: SimulationPath[]
  created_at: string
  updated_at: string
}

export interface WhatIfChange {
  add_skill_ids?: string[]
  add_proficiency_overrides?: Record<string, number>
  add_experience_months?: number
  add_projects?: WhatIfProject[]
  label?: string | null
}

export interface WhatIfProject {
  title: string
  company?: string | null
  description?: string | null
  start_date?: string | null
}

export interface SimulationSummary {
  id: string
  parent_simulation_id: string | null
  label: string | null
  engine_version: string
  path_count: number
  created_at: string
}

export interface WhatIfResult {
  original_simulation_id: string
  hypothetical_simulation: SimulationResult
  newly_unlocked_roles: string[]
  improved_confidence_roles: string[]
  confidence_changes: {
    role_id: string
    role_title: string
    original_score: number | null
    scenario_score: number
    delta: number
  }[]
  skill_gap_changes: {
    role_id: string
    role_title: string
    newly_missing: string[]
    resolved: string[]
    improved: string[]
  }[]
  roadmap_changes: {
    role_id: string
    role_title: string
    added_steps: string[]
    removed_steps: string[]
  }[]
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  code: string
  message: string
  details?: unknown
}
