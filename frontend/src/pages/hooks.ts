import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { RoleSummary, UserProfile } from '@/types'

export function useProfileAndHistory() {
  const profile = useQuery({
    queryKey: ['profile'],
    queryFn: () => api.getProfileOrNull(),
  })
  const history = useQuery({
    queryKey: ['history', profile.data?.id],
    queryFn: () => api.getHistory(profile.data!.id),
    enabled: Boolean(profile.data?.id),
  })
  return {
    profile,
    history,
    isLoading: profile.isLoading,
    error: profile.error,
    refetch: profile.refetch,
  }
}

export function useCatalog() {
  const roles = useQuery({
    queryKey: ['catalog', 'roles'],
    queryFn: async () => (await api.getRoles({ limit: 100 })).items,
    staleTime: 5 * 60_000,
  })
  const skills = useQuery({
    queryKey: ['catalog', 'skills'],
    queryFn: async () => (await api.getSkills({ limit: 100 })).items,
    staleTime: 5 * 60_000,
  })
  const categories = useQuery({
    queryKey: ['catalog', 'categories'],
    queryFn: async () => (await api.getSkillCategories({ limit: 100 })).items,
    staleTime: 5 * 60_000,
  })
  return { roles, skills, categories }
}

export function roleName(profile: UserProfile, roles: RoleSummary[]) {
  return roles.find((role) => role.id === profile.current_role_id)?.title ?? 'Role not set'
}

export function apiErrorMessage(error: unknown): string {
  if (!error || typeof error !== 'object') return 'Please check the information and try again.'
  const details = (error as { details?: unknown }).details
  if (Array.isArray(details)) {
    return details.map((item) => {
      if (!item || typeof item !== 'object') return ''
      const row = item as { location?: unknown[]; message?: string }
      return `${row.location?.slice(-1)[0] ?? 'Input'}: ${row.message ?? 'Invalid value'}`
    }).filter(Boolean).join(' · ')
  }
  return (error as { message?: string }).message ?? 'Please check the information and try again.'
}
