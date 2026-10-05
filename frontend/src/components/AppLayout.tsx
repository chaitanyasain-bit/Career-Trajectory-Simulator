import {
  Activity,
  ArrowUpRight,
  ChevronDown,
  Clock3,
  Compass,
  GitCompareArrows,
  LayoutDashboard,
  LogOut,
  Menu,
  UserRound,
  X,
  Zap,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

const navigation = [
  { label: 'Overview', to: '/', icon: LayoutDashboard },
  { label: 'My profile', to: '/profile', icon: UserRound },
  { label: 'Career simulation', to: '/simulation', icon: Compass },
  { label: 'What-If lab', to: '/what-if', icon: Zap },
  { label: 'Compare paths', to: '/comparison', icon: GitCompareArrows },
  { label: 'Simulation history', to: '/history', icon: Clock3 },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const currentPage = navigation.find((item) => item.to === location.pathname)

  const signOut = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-[#f5f7f8] text-slate-900">
      {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/30 lg:hidden" onClick={() => setOpen(false)} />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[268px] flex-col border-r border-slate-200 bg-white transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-[76px] items-center justify-between border-b border-slate-100 px-6">
          <NavLink to="/" className="flex items-center gap-3" onClick={() => setOpen(false)}>
            <span className="brand-mark"><Activity className="h-5 w-5" /></span>
            <span>
              <span className="block text-sm font-bold tracking-tight text-slate-950">trajectory<span className="text-teal-700">.</span></span>
              <span className="block text-[10px] font-semibold uppercase tracking-[.16em] text-slate-400">Career intelligence</span>
            </span>
          </NavLink>
          <button onClick={() => setOpen(false)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden" aria-label="Close menu"><X className="h-5 w-5" /></button>
        </div>
        <div className="px-4 pt-7">
          <p className="nav-section-label">Workspace</p>
          <nav className="mt-3 space-y-1">
            {navigation.map(({ label, to, icon: Icon }) => (
              <NavLink key={to} to={to} end={to === '/'} onClick={() => setOpen(false)} className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}>
                <Icon className="h-[18px] w-[18px]" strokeWidth={1.8} />
                <span>{label}</span>
                {label === 'What-If lab' && <span className="ml-auto rounded-md bg-teal-50 px-1.5 py-0.5 text-[10px] font-bold text-teal-700">NEW</span>}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="mt-auto p-4">
          <div className="rounded-2xl border border-teal-100 bg-gradient-to-br from-teal-50 to-cyan-50 p-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-teal-700 shadow-sm"><Activity className="h-[18px] w-[18px]" /></div>
            <p className="mt-3 text-sm font-semibold text-slate-900">Your next chapter</p>
            <p className="mt-1 text-xs leading-5 text-slate-600">Build a clear path from your skills to your next role.</p>
            <NavLink to="/simulation" className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-teal-800">Explore paths <ArrowUpRight className="h-3.5 w-3.5" /></NavLink>
          </div>
          <div className="mt-4 flex items-center gap-3 rounded-xl px-2 py-3">
            <div className="avatar">{user?.full_name?.slice(0, 1).toUpperCase() ?? 'U'}</div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-800">{user?.full_name}</p>
              <p className="truncate text-xs text-slate-500">{user?.email}</p>
            </div>
            <button onClick={signOut} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700" title="Sign out" aria-label="Sign out"><LogOut className="h-4 w-4" /></button>
          </div>
        </div>
      </aside>

      <div className="min-h-screen lg:pl-[268px]">
        <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur sm:px-7 lg:px-10">
          <div className="flex items-center gap-3">
            <button className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu className="h-5 w-5" /></button>
            <div>
              <p className="text-xs font-medium text-slate-400">Workspace <span className="px-1">/</span> <span className="text-slate-600">{currentPage?.label ?? (location.pathname.startsWith('/careers') ? 'Career details' : 'Roadmap')}</span></p>
              <p className="mt-0.5 text-sm font-semibold text-slate-900 sm:text-base">{currentPage?.label ?? (location.pathname.startsWith('/history/') ? 'Simulation replay' : 'Career trajectory')}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700 sm:inline-flex"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> API connected</span>
            <div className="hidden h-8 w-px bg-slate-200 sm:block" />
            <button onClick={() => navigate('/profile')} className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-slate-100">
              <span className="avatar avatar-small">{user?.full_name?.slice(0, 1).toUpperCase() ?? 'U'}</span>
              <span className="hidden max-w-32 truncate text-sm font-medium text-slate-700 sm:block">{user?.full_name}</span>
              <ChevronDown className="hidden h-4 w-4 text-slate-400 sm:block" />
            </button>
          </div>
        </header>
        <main className="mx-auto max-w-[1440px] px-4 py-7 sm:px-7 sm:py-9 lg:px-10">
          <Outlet />
        </main>
        <footer className="border-t border-slate-200/80 px-4 py-5 text-center text-xs text-slate-400 sm:px-7 lg:px-10">
          Career decisions, grounded in your skills and goals.
        </footer>
      </div>
    </div>
  )
}
