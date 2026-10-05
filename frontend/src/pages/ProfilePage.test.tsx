// @vitest-environment jsdom

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { api } from '@/services/api'
import type { UserProfile } from '@/types'
import { ProfilePage } from '@/pages/ProfilePage'

vi.mock('@/services/api', () => ({
  api: {
    getProfileOrNull: vi.fn(),
    getHistory: vi.fn(),
    getRoles: vi.fn(),
    getSkills: vi.fn(),
    getSkillCategories: vi.fn(),
    createProfile: vi.fn(),
    updateProfile: vi.fn(),
  },
  clearAccessToken: vi.fn(),
}))

const savedProfile: UserProfile = {
  id: 'profile-1',
  user_id: 'user-1',
  current_role_id: null,
  years_of_experience: 0,
  bio: null,
  location: null,
  linkedin_url: null,
  github_url: null,
  user_skills: [],
  educations: [],
  experiences: [],
  projects: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('profile editing', () => {
  it('creates a profile through the API and shows a success state', async () => {
    vi.mocked(api.getProfileOrNull).mockResolvedValue(null)
    vi.mocked(api.getRoles).mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 })
    vi.mocked(api.getSkills).mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 })
    vi.mocked(api.getSkillCategories).mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 })
    vi.mocked(api.createProfile).mockResolvedValue(savedProfile)

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ProfilePage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await screen.findByRole('heading', { name: 'Career profile' })
    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[0])
    fireEvent.change(screen.getByLabelText('Position title'), {
      target: { value: 'Analyst' },
    })
    const saveButtons = await screen.findAllByRole('button', { name: 'Save profile' })
    fireEvent.click(saveButtons[0])

    expect(await screen.findByRole('status')).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('Your profile has been saved')
    expect(api.createProfile).toHaveBeenCalledWith(
      expect.objectContaining({
        years_of_experience: 0,
        skills: [],
        projects: [],
        experiences: [
          expect.objectContaining({ title: 'Analyst', start_date: null, end_date: null }),
        ],
      }),
    )
  })
})
