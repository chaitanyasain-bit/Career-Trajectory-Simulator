/**
 * API service client — typed wrapper around axios.
 *
 * Authenticated typed client for the versioned FastAPI endpoints.
 *
 * All calls go to /api/v1/* — proxied to FastAPI in development (see vite.config.ts).
 */

import axios, { AxiosInstance } from 'axios'
import type {
  UserProfile,
  UserProfileCreate,
  UserProfileUpdate,
  UserAccount,
  AuthCredentials,
  RegisterAccount,
  TokenResponse,
  CatalogPage,
  RoleSummary,
  RoleCatalogDetail,
  SkillCatalogItem,
  SkillCategory,
  SimulationResult,
  SimulationSummary,
  RoadmapStep,
  WhatIfChange,
  WhatIfResult,
} from '@/types'

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const configuredApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  (import.meta.env.DEV ? '' : 'https://career-trajectory-simulator.onrender.com')
const normalizedApiBaseUrl = configuredApiBaseUrl.replace(/\/+$/, '')
const apiBaseUrl = normalizedApiBaseUrl.endsWith('/api/v1')
  ? normalizedApiBaseUrl
  : `${normalizedApiBaseUrl}/api/v1`

const http: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

const TOKEN_KEY = 'access_token'

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearAccessToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

// ── Request interceptor — attach JWT token when available ─────────────────────
http.interceptors.request.use((config) => {
  const token = typeof localStorage === 'undefined' ? null : localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor — normalize errors ───────────────────────────────────
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearAccessToken()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('career:unauthorized'))
      }
    }
    const apiError = error?.response?.data?.error
    if (apiError) return Promise.reject(apiError)
    return Promise.reject({
      code: error?.code ?? 'NETWORK_ERROR',
      message: error?.message ?? 'Unable to reach the career simulator API.',
      details: error?.response?.data ?? null,
    })
  },
)

export const api = {
  async register(payload: RegisterAccount): Promise<TokenResponse> {
    const { data } = await http.post<TokenResponse>('/auth/register', payload)
    setAccessToken(data.access_token)
    return data
  },

  async login(payload: AuthCredentials): Promise<TokenResponse> {
    const { data } = await http.post<TokenResponse>('/auth/login', payload)
    setAccessToken(data.access_token)
    return data
  },

  async getCurrentAccount(): Promise<UserAccount> {
    const { data } = await http.get<UserAccount>('/auth/me')
    return data
  },

  logout(): void {
    clearAccessToken()
  },

  async createProfile(profile: UserProfileCreate): Promise<UserProfile> {
    const { data } = await http.post<UserProfile>('/profiles/me', profile)
    return data
  },

  async getProfile(): Promise<UserProfile> {
    const { data } = await http.get<UserProfile>('/profiles/me')
    return data
  },

  async getProfileOrNull(): Promise<UserProfile | null> {
    try {
      return await this.getProfile()
    } catch (error) {
      if ((error as { code?: string }).code === 'NOT_FOUND') return null
      throw error
    }
  },

  async updateProfile(profile: UserProfileUpdate): Promise<UserProfile> {
    const { data } = await http.patch<UserProfile>('/profiles/me', profile)
    return data
  },

  async saveProfile(profile: UserProfileUpdate): Promise<UserProfile> {
    const { data } = await http.patch<UserProfile>('/profiles/me', profile)
    return data
  },

  async getRoles(params?: { search?: string; domain?: string; limit?: number; offset?: number }): Promise<CatalogPage<RoleSummary>> {
    const { data } = await http.get<CatalogPage<RoleSummary>>('/roles', { params })
    return data
  },

  async getRole(roleId: string): Promise<RoleCatalogDetail> {
    const { data } = await http.get<RoleCatalogDetail>(`/roles/${encodeURIComponent(roleId)}`)
    return data
  },

  async getSkills(params?: { search?: string; category_id?: string; limit?: number; offset?: number }): Promise<CatalogPage<SkillCatalogItem>> {
    const { data } = await http.get<CatalogPage<SkillCatalogItem>>('/skills', { params })
    return data
  },

  async getSkillCategories(params?: { search?: string; limit?: number; offset?: number }): Promise<CatalogPage<SkillCategory>> {
    const { data } = await http.get<CatalogPage<SkillCategory>>('/skill-categories', { params })
    return data
  },

  /** Run a career trajectory simulation using the saved authenticated profile. */
  async simulate(
    profileId: string,
    options: { label?: string; notes?: string } = {},
  ): Promise<SimulationResult> {
    const { data } = await http.post<SimulationResult>(
      `/simulate/${encodeURIComponent(profileId)}`,
      options,
    )
    return data
  },

  /** Persist a hypothetical scenario linked to an earlier simulation. */
  async whatif(simulationId: string, change: WhatIfChange): Promise<WhatIfResult> {
    const { data } = await http.post<WhatIfResult>(
      `/simulate/${encodeURIComponent(simulationId)}/whatif`,
      change,
    )
    return data
  },

  /** Retrieve the saved simulation history for an owned profile. */
  async getHistory(profileId: string): Promise<SimulationSummary[]> {
    const { data } = await http.get<SimulationSummary[]>(
      `/history/${encodeURIComponent(profileId)}`,
    )
    return data
  },

  /** Replay the exact persisted result without recalculating it. */
  async getSimulation(simulationId: string): Promise<SimulationResult> {
    const { data } = await http.get<SimulationResult>(
      `/history/replay/${encodeURIComponent(simulationId)}`,
    )
    return data
  },

  /** Retrieve persisted roadmap steps for a career path. */
  async getRoadmap(pathId: string): Promise<RoadmapStep[]> {
    const { data } = await http.get<RoadmapStep[]>(
      `/roadmap/${encodeURIComponent(pathId)}`,
    )
    return data
  },
}

export default http
