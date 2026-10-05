// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from '@/App'
import { api } from '@/services/api'

vi.mock('@/services/api', () => ({
  api: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentAccount: vi.fn(),
  },
  clearAccessToken: vi.fn(),
}))

afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.clearAllMocks()
})

describe('authentication routes', () => {
  it('redirects guests to login and displays the sign-in form', async () => {
    window.history.replaceState({}, '', '/profile')
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Sign in to your account' })).toBeTruthy()
    expect(screen.getByLabelText('Email address')).toBeTruthy()
    expect(screen.getByLabelText('Password')).toBeTruthy()
  })

  it('shows the API error when login fails', async () => {
    vi.mocked(api.login).mockRejectedValueOnce(new Error('Invalid credentials'))
    window.history.replaceState({}, '', '/login')
    render(<App />)

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'person@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'incorrect-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toContain('Invalid credentials')
    })
  })
})
