import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, clearAccessToken } from '@/services/api'
import type { AuthCredentials, RegisterAccount, UserAccount } from '@/types'

interface AuthContextValue {
  user: UserAccount | null
  loading: boolean
  login: (credentials: AuthCredentials) => Promise<void>
  register: (details: RegisterAccount) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<UserAccount | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    const onUnauthorized = () => {
      setUser(null)
      setLoading(false)
      queryClient.clear()
    }
    window.addEventListener('career:unauthorized', onUnauthorized)
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return () => window.removeEventListener('career:unauthorized', onUnauthorized)
    }
    api
      .getCurrentAccount()
      .then((account) => {
        if (active) setUser(account)
      })
      .catch(() => {
        if (active) {
          clearAccessToken()
          setUser(null)
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
      window.removeEventListener('career:unauthorized', onUnauthorized)
    }
  }, [queryClient])

  const login = useCallback(async (credentials: AuthCredentials) => {
    const session = await api.login(credentials)
    queryClient.clear()
    setUser(session.user)
  }, [queryClient])

  const register = useCallback(async (details: RegisterAccount) => {
    const session = await api.register(details)
    queryClient.clear()
    setUser(session.user)
  }, [queryClient])

  const logout = useCallback(() => {
    api.logout()
    queryClient.clear()
    setUser(null)
  }, [queryClient])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider.')
  return context
}
