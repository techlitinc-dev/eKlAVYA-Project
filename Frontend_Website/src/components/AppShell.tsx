import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  BookOpen,
  ClipboardCheck,
  Sparkles,
  Wrench,
  Users,
  FileBarChart,
  CreditCard,
  ShieldCheck,
  Database,
  Layers,
  GraduationCap,
  Settings,
  LogOut,
  Flame,
  Zap,
  ChevronRight,
  Menu,
  X,
} from 'lucide-react';
import { useAuth, UserRole } from '../context/AuthContext';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, selectedExam, setSelectedExam, switchDemoRole, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [switching, setSwitching] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Fullscreen CBT Exam route hides the shell navigation for distraction-free mode
  if (location.pathname.startsWith('/student/exam/')) {
    return <div className="min-h-screen bg-slate-950 text-slate-100">{children}</div>;
  }

  const activeRole: UserRole = location.pathname.startsWith('/superadmin')
    ? 'superadmin'
    : location.pathname.startsWith('/parent')
    ? 'parent'
    : user?.role || 'student';

  const handleRoleSwitch = async (role: UserRole) => {
    setSwitching(true);
    try {
      await switchDemoRole(role);
      if (role === 'student') navigate('/student/dashboard');
      else if (role === 'parent') navigate('/parent/dashboard');
      else navigate('/superadmin/dashboard');
    } finally {
      setSwitching(false);
    }
  };

  const studentNav = [
    { to: '/student/dashboard', label: 'Home Hub', icon: LayoutDashboard, badge: 'Live' },
    { to: '/student/mentor', label: 'Hermes AI Mentor', icon: Bot, badge: 'Socratic' },
    { to: '/student/pyq', label: 'PYQ & NCERT Bank', icon: BookOpen, badge: '20+ Yrs' },
    { to: '/student/tests', label: 'CBT Tests & Homework', icon: ClipboardCheck },
    { to: '/student/revision', label: 'Flashcards & Notebooks', icon: Sparkles },
    { to: '/student/tools', label: 'Rank, Cutoffs & OMR', icon: Wrench },
  ];

  const parentNav = [
    { to: '/parent/dashboard', label: 'Command Center', icon: LayoutDashboard, badge: '7-Day' },
    { to: '/parent/reports', label: 'Bilingual Reports', icon: FileBarChart },
    { to: '/parent/assignments', label: 'Homework & Analytics', icon: ClipboardCheck },
    { to: '/parent/billing', label: 'Subscription & Plans', icon: CreditCard },
  ];

  const superAdminNav = [
    { to: '/superadmin/dashboard', label: 'Executive Overview', icon: ShieldCheck, badge: 'Root' },
    { to: '/superadmin/users', label: 'Users & Concept Walls', icon: Users },
    { to: '/superadmin/questions', label: 'PYQ Question CMS', icon: Database },
    { to: '/superadmin/content', label: 'Flashcards & Cutoffs', icon: Layers },
    { to: '/superadmin/ai-settings', label: 'Hermes AI & Audit Logs', icon: Settings },
  ];

  const navItems =
    activeRole === 'superadmin'
      ? superAdminNav
      : activeRole === 'parent'
      ? parentNav
      : studentNav;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Global Command Bar */}
      <header className="sticky top-0 z-40 h-16 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md px-4 lg:px-6 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <GraduationCap className="w-5 h-5 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-tight text-lg text-white">
                  eKlAVYA
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-sky-500/15 text-sky-400 border border-sky-500/30">
                  Mentor AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                JEE Main • JEE Advanced • NEET-UG Cognitive Platform
              </p>
            </div>
          </Link>
        </div>

        {/* Center Exam Selector (for Student mode) */}
        {activeRole === 'student' && (
          <div className="hidden md:flex items-center bg-slate-900/90 border border-slate-800 rounded-xl p-1 gap-1">
            {[
              { id: 'jee_main', label: 'JEE Main 2026', accent: 'bg-sky-500 text-slate-950' },
              { id: 'jee_advanced', label: 'JEE Advanced', accent: 'bg-indigo-500 text-white' },
              { id: 'neet', label: 'NEET-UG (Medical)', accent: 'bg-emerald-500 text-slate-950' },
            ].map((ex) => (
              <button
                key={ex.id}
                onClick={() => setSelectedExam(ex.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  selectedExam === ex.id
                    ? `${ex.accent} shadow-sm`
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {ex.label}
              </button>
            ))}
          </div>
        )}

        {/* Right: 1-Click Live Portal Switcher & User Profile */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1">
            <span className="text-[11px] text-slate-400 px-2 hidden xl:inline">Portal:</span>
            {(
              [
                { role: 'student', label: 'Student', color: 'bg-sky-500 text-slate-950' },
                { role: 'parent', label: 'Parent', color: 'bg-emerald-500 text-slate-950' },
                { role: 'superadmin', label: 'SuperAdmin', color: 'bg-amber-500 text-slate-950' },
              ] as const
            ).map((item) => (
              <button
                key={item.role}
                disabled={switching}
                onClick={() => handleRoleSwitch(item.role)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  activeRole === item.role
                    ? item.color
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <Link
            to="/login"
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-300"
            title="Switch Account / Onboarding Wizard"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="truncate max-w-[120px]">{user?.name || 'Aarav Sharma'}</span>
          </Link>
        </div>
      </header>

      {/* Main Workspace with Left Sidebar */}
      <div className="flex-1 flex">
        {/* Sidebar */}
        <aside
          className={`${
            mobileOpen ? 'fixed inset-y-0 left-0 z-50 w-64 bg-slate-950 pt-16' : 'hidden'
          } lg:flex lg:w-64 lg:flex-col border-r border-slate-800/80 bg-slate-950/60 p-4 justify-between shrink-0`}
        >
          <div className="space-y-6">
            <div className="px-3 py-2.5 rounded-xl bg-slate-900/80 border border-slate-800/90">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="uppercase tracking-wider font-bold text-[10px]">
                  Active Session
                </span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-semibold text-[10px]">
                  {activeRole.toUpperCase()}
                </span>
              </div>
              <div className="font-bold text-sm text-white truncate">
                {activeRole === 'superadmin'
                  ? 'eKlAVYA SuperAdmin'
                  : activeRole === 'parent'
                  ? 'Dr. Rajesh Sharma'
                  : user?.name || 'Aarav Sharma'}
              </div>
              <div className="text-xs text-slate-400 truncate mt-0.5">
                {activeRole === 'superadmin'
                  ? 'admin@eklavya.ai • Root Access'
                  : activeRole === 'parent'
                  ? 'Child: Aarav Sharma (Class 12)'
                  : `Target: ${selectedExam.replace('_', ' ').toUpperCase()}`}
              </div>
            </div>

            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  location.pathname === item.to ||
                  (item.to !== '/' && location.pathname.startsWith(item.to));
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                        {item.badge}
                      </span>
                    ) : (
                      isActive && <ChevronRight className="w-4 h-4 text-sky-400" />
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="space-y-3 pt-6 border-t border-slate-800/80">
            <div className="p-3 rounded-xl bg-gradient-to-br from-slate-900 to-slate-900/50 border border-slate-800 text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">FastAPI Backend</span>
                <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                  <Zap className="w-3 h-3" /> Online
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Firestore + Gemini</span>
                <span className="text-sky-400 font-mono">v1.0 Live</span>
              </div>
            </div>

            <div className="flex gap-2">
              <Link
                to="/onboarding"
                onClick={() => setMobileOpen(false)}
                className="flex-1 text-center py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-300"
              >
                Onboarding
              </Link>
              <button
                onClick={() => {
                  logout();
                  navigate('/login');
                }}
                className="p-2 rounded-xl bg-slate-900 hover:bg-rose-500/20 border border-slate-800 hover:border-rose-500/30 text-slate-400 hover:text-rose-400"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </aside>

        {/* Viewport Content */}
        <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
};

export default AppShell;
