import { Activity, ArrowRight, Eye, EyeOff, LockKeyhole, Mail, UserRound } from 'lucide-react'
import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ErrorState } from '@/components/ui'
import { apiErrorMessage } from '@/pages/hooks'

function AuthShell({
  mode,
  children,
}: {
  mode: 'login' | 'register'
  children: ReactNode
}) {
  return (
    <div className="grid min-h-screen bg-white lg:grid-cols-[1fr_1fr]">
      <section className="relative hidden overflow-hidden bg-[#092f31] px-12 py-12 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
        <div className="absolute -right-40 -top-40 h-[540px] w-[540px] rounded-full border border-white/10" />
        <div className="absolute -right-20 -top-20 h-[380px] w-[380px] rounded-full border border-white/10" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-400 text-teal-950"><Activity className="h-5 w-5" /></span>
          <span className="text-lg font-bold">trajectory<span className="text-teal-300">.</span></span>
        </div>
        <div className="relative max-w-xl pb-12">
          <p className="mb-5 inline-flex rounded-full border border-teal-300/25 bg-teal-300/10 px-3 py-1.5 text-xs font-semibold tracking-wide text-teal-200">A clearer path forward</p>
          <h1 className="text-4xl font-semibold leading-[1.15] tracking-tight xl:text-[52px]">Make your next career move a <span className="text-teal-300">confident one.</span></h1>
          <p className="mt-6 max-w-lg text-base leading-7 text-teal-50/70">Turn your experience, skills, and ambitions into practical career paths—with an honest view of what it takes to get there.</p>
          <div className="mt-10 grid max-w-md grid-cols-3 gap-5 border-t border-white/15 pt-6">
            {[['01', 'Map your skills'], ['02', 'Explore paths'], ['03', 'Plan your growth']].map(([number, text]) => <div key={number}><p className="text-xs font-bold text-teal-300">{number}</p><p className="mt-1.5 text-xs text-white/70">{text}</p></div>)}
          </div>
        </div>
        <p className="relative text-xs text-white/40">Built for thoughtful career growth</p>
      </section>
      <section className="flex min-h-screen flex-col justify-center px-5 py-12 sm:px-12 lg:px-16 xl:px-24">
        <div className="mx-auto w-full max-w-[420px]">
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-700 text-white"><Activity className="h-5 w-5" /></span>
            <span className="text-lg font-bold">trajectory<span className="text-teal-700">.</span></span>
          </div>
          <p className="eyebrow">{mode === 'login' ? 'Welcome back' : 'Get started'}</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{mode === 'login' ? 'Sign in to your account' : 'Create your account'}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">{mode === 'login' ? 'Continue building a career path that fits you.' : 'Your career profile and personalized insights start here.'}</p>
          <div className="mt-8">{children}</div>
          <p className="mt-8 text-center text-sm text-slate-500">
            {mode === 'login' ? 'New to trajectory?' : 'Already have an account?'}{' '}
            <Link className="font-semibold text-teal-800 hover:text-teal-600" to={mode === 'login' ? '/register' : '/login'}>{mode === 'login' ? 'Create an account' : 'Sign in'}</Link>
          </p>
        </div>
      </section>
    </div>
  )
}

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  if (user) return <Navigate to="/" replace />

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login({ email, password })
      navigate('/', { replace: true })
    } catch (reason) {
      setError(reason)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell mode="login">
      {error !== null && <div className="mb-5"><ErrorState error={{ message: apiErrorMessage(error) }} /></div>}
      <form className="space-y-5" onSubmit={submit}>
        <label className="field-label">Email address
          <span className="input-icon-wrap"><Mail className="input-icon" /><input className="input-control pl-10" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></span>
        </label>
        <label className="field-label">Password
          <span className="input-icon-wrap"><LockKeyhole className="input-icon" /><input className="input-control pl-10 pr-11" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" /><button type="button" className="input-trailing" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></span>
        </label>
        <button className="btn-primary w-full !py-3" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'} {!busy && <ArrowRight className="h-4 w-4" />}</button>
      </form>
    </AuthShell>
  )
}

export function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  if (user) return <Navigate to="/" replace />

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await register({ full_name: fullName.trim(), email, password })
      navigate('/profile', { replace: true })
    } catch (reason) {
      setError(reason)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell mode="register">
      {error !== null && <div className="mb-5"><ErrorState error={{ message: apiErrorMessage(error) }} /></div>}
      <form className="space-y-5" onSubmit={submit}>
        <label className="field-label">Full name
          <span className="input-icon-wrap"><UserRound className="input-icon" /><input className="input-control pl-10" autoComplete="name" required minLength={1} maxLength={255} value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Your name" /></span>
        </label>
        <label className="field-label">Email address
          <span className="input-icon-wrap"><Mail className="input-icon" /><input className="input-control pl-10" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></span>
        </label>
        <label className="field-label">Password
          <span className="input-icon-wrap"><LockKeyhole className="input-icon" /><input className="input-control pl-10 pr-11" type={showPassword ? 'text' : 'password'} autoComplete="new-password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 12 characters" /><button type="button" className="input-trailing" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></span>
          <span className="mt-1 block text-xs font-normal text-slate-400">Use at least 12 characters.</span>
        </label>
        <button className="btn-primary w-full !py-3" type="submit" disabled={busy}>{busy ? 'Creating account…' : 'Create account'} {!busy && <ArrowRight className="h-4 w-4" />}</button>
      </form>
    </AuthShell>
  )
}
