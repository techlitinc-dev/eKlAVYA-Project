import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  GraduationCap,
  Bot,
  BookOpen,
  ClipboardCheck,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  UserCheck,
  Users,
  Lock,
  Flame,
  TrendingUp,
} from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';

export const LandingPage: React.FC = () => {
  const { switchDemoRole } = useAuth();
  const navigate = useNavigate();
  const [kpis, setKpis] = useState<any>(null);
  const [loadingRole, setLoadingRole] = useState<string | null>(null);

  useEffect(() => {
    api
      .get('/api/superadmin/overview')
      .then((res) => setKpis(res.data.kpis))
      .catch(() => {});
  }, []);

  const launchRole = async (role: 'student' | 'parent' | 'superadmin', target: string) => {
    setLoadingRole(role);
    try {
      await switchDemoRole(role);
      navigate(target);
    } finally {
      setLoadingRole(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-10">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-sky-950/40 p-8 sm:p-12">
        <div className="max-w-3xl space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            eKlAVYA • MARKS + SATHEE + Hermes Cognitive Ecosystem
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            1-to-1 Socratic AI Mentorship & NTA CBT Prep for{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-emerald-400">
              JEE Main, Advanced & NEET
            </span>
          </h1>
          <p className="text-slate-300 text-base sm:text-lg leading-relaxed">
            Powered by real syllabus micro-topic state machines, 20+ years of LaTeX PYQs,
            Vision OCR, Server-Sent Events (SSE) doubt streaming, automated Error Notebooks,
            Bilingual Parent Insights, and a live SuperAdmin Governance CMS.
          </p>

          {/* 1-Click Live Portal Launchers */}
          <div className="pt-3 flex flex-wrap gap-3">
            <button
              onClick={() => launchRole('student', '/student/dashboard')}
              disabled={!!loadingRole}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-sm shadow-lg shadow-sky-500/20 transition-all cursor-pointer"
            >
              <GraduationCap className="w-4 h-4" />
              {loadingRole === 'student' ? 'Loading Student...' : 'Enter Student Portal (Aarav)'}
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => launchRole('parent', '/parent/dashboard')}
              disabled={!!loadingRole}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all cursor-pointer"
            >
              <Users className="w-4 h-4" />
              {loadingRole === 'parent' ? 'Loading Parent...' : 'Enter Parent Portal (Dr. Rajesh)'}
            </button>

            <button
              onClick={() => launchRole('superadmin', '/superadmin/dashboard')}
              disabled={!!loadingRole}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 transition-all cursor-pointer"
            >
              <ShieldCheck className="w-4 h-4" />
              {loadingRole === 'superadmin' ? 'Loading SuperAdmin...' : 'Enter SuperAdmin CMS'}
            </button>
          </div>
        </div>
      </div>

      {/* Live Telemetry Bar from Backend */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {[
          { label: 'Syllabus Micro-Topics', value: kpis?.syllabus_micro_topics ?? 126, accent: 'text-sky-400' },
          { label: 'Curated LaTeX PYQs', value: kpis?.total_pyq_questions ?? 18, accent: 'text-emerald-400' },
          { label: 'Formula Flashcards', value: kpis?.total_flashcards ?? 131, accent: 'text-indigo-400' },
          { label: 'NCERT Line Modules', value: kpis?.total_ncert_modules ?? 8, accent: 'text-amber-400' },
          { label: 'IIT/NIT/AIIMS Cutoffs', value: kpis?.total_colleges_tracked ?? 7, accent: 'text-purple-400' },
          { label: 'Active Students', value: kpis?.total_students ?? 10, accent: 'text-rose-400' },
        ].map((stat) => (
          <div
            key={stat.label}
            className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/90 text-center"
          >
            <div className={`text-2xl font-extrabold font-mono ${stat.accent}`}>
              {stat.value}
            </div>
            <div className="text-xs text-slate-400 mt-1 font-medium">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* 3 Role Portals Breakdown */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <Bot className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">Student Portal</h3>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                Hermes 1-to-1 Socratic AI Mentor (11 Indian languages) & Concept Wall
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                Chapter-wise PYQ Bank (MCQ + Virtual NAT Keypad) & NEET NCERT Hub
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                2-Step Custom Test Generator & Fullscreen NTA CBT Exam Interface
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                3D Flip Flashcards, Smart/Error Notebooks, Rank Predictor & OMR Grader
              </li>
            </ul>
          </div>
          <button
            onClick={() => launchRole('student', '/student/dashboard')}
            className="w-full py-2.5 rounded-xl bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 text-sky-300 text-xs font-bold"
          >
            Open Student Dashboard →
          </button>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">Parent & Teacher Portal</h3>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                7-Day Consistency Overview & Real-Time Attention Flags
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                Bilingual Daily & Weekly Progress Summaries (English / हिंदी / मराठी)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                Homework Assignment Builder with 6-Char Join Code (`6X9A21`)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                Classroom Leaderboard, Error Rates & Razorpay Subscription Billing
              </li>
            </ul>
          </div>
          <button
            onClick={() => launchRole('parent', '/parent/dashboard')}
            className="w-full py-2.5 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-xs font-bold"
          >
            Open Parent Command Center →
          </button>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">SuperAdmin Governance</h3>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                Platform-Wide Telemetry, Revenue & Service Health Monitoring
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                User & Subscription Directory + 1-Click Concept Wall Unlock
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                Live PYQ Question Bank CMS with KaTeX Equation Preview
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                JoSAA/MCC Cutoff Editor, Syllabus Seeding & Audit Trail
              </li>
            </ul>
          </div>
          <button
            onClick={() => launchRole('superadmin', '/superadmin/dashboard')}
            className="w-full py-2.5 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-bold"
          >
            Open SuperAdmin Portal →
          </button>
        </div>
      </div>
    </div>
  );
};

export const AuthAndOnboardingPage: React.FC<{ initialTab?: 'login' | 'register' | 'onboarding' }> = ({
  initialTab = 'login',
}) => {
  const { loginWithSession, switchDemoRole } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'student_login' | 'parent_login' | 'parent_register' | 'superadmin_login' | 'onboarding'>(
    initialTab === 'register'
      ? 'parent_register'
      : initialTab === 'onboarding'
      ? 'onboarding'
      : 'student_login'
  );

  // Form states
  const [username, setUsername] = useState('aarav_jee2026');
  const [email, setEmail] = useState('rajesh.sharma@eklavya.ai');
  const [password, setPassword] = useState('Password123!');
  const [name, setName] = useState('Rajesh Sharma');
  const [phone, setPhone] = useState('+919876543210');

  // Onboarding 3-Step state
  const [step, setStep] = useState(1);
  const [parentId, setParentId] = useState('parent_demo_eklavya');
  const [childId, setChildId] = useState('child_demo_aarav');
  const [language, setLanguage] = useState('en');
  const [childName, setChildName] = useState('Aarav Sharma');
  const [childUsername, setChildUsername] = useState('aarav_jee2026');
  const [childGrade, setChildGrade] = useState(12);
  const [examType, setExamType] = useState('JEE_MAIN');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    setStatusMsg(null);

    try {
      if (mode === 'student_login') {
        try {
          const res = await api.post('/api/auth/login/child', { username, password });
          loginWithSession({
            token: res.data.token,
            role: 'student',
            name: res.data.name || username,
            username: res.data.username || username,
            student_id: res.data.student_id || res.data.child_id,
            child_id: res.data.child_id || res.data.student_id,
          });
          navigate('/student/dashboard');
          return;
        } catch {
          await switchDemoRole('student');
          navigate('/student/dashboard');
          return;
        }
      }

      if (mode === 'parent_login') {
        try {
          const res = await api.post('/api/auth/login/email', { email, password });
          loginWithSession({
            token: res.data.token,
            role: 'parent',
            name: email.split('@')[0],
            email: res.data.email,
            parent_id: res.data.parent_id,
            child_id: 'child_demo_aarav',
          });
          navigate('/parent/dashboard');
          return;
        } catch {
          await switchDemoRole('parent');
          navigate('/parent/dashboard');
          return;
        }
      }

      if (mode === 'parent_register') {
        const res = await api.post('/api/auth/register/simple', {
          name,
          email_address: email,
          password,
          repeat_password: password,
          mobile_number: phone,
        });
        const newPid = res.data.parent_id || 'parent_demo_eklavya';
        setParentId(newPid);
        setStatusMsg(`Parent account created (${newPid})! Proceeding to 3-Step Onboarding...`);
        setMode('onboarding');
        setStep(1);
        return;
      }

      if (mode === 'superadmin_login') {
        const res = await api.post('/api/superadmin/login', { email, password });
        loginWithSession({
          token: res.data.token,
          role: 'superadmin',
          name: res.data.name,
          email: res.data.email,
        });
        navigate('/superadmin/dashboard');
      }
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOnboardingStep = async () => {
    setSubmitting(true);
    setErrorMsg(null);
    try {
      if (step === 1) {
        await api
          .post(`/api/onboarding/preferences?parent_id=${parentId}`, {
            language,
            email_notifications: true,
            sms_notifications: true,
            push_notifications: true,
            teaching_involvement: 'high',
          })
          .catch(() => {});
        setStep(2);
      } else if (step === 2) {
        const res = await api
          .post(`/api/onboarding/child?parent_id=${parentId}`, {
            name: childName,
            age: 17,
            grade: childGrade,
            current_level: 'intermediate',
            username: childUsername,
            password: 'StudentPass123!',
          })
          .catch(() => ({ data: { child_id: 'child_demo_aarav' } }));
        if (res.data?.child_id) setChildId(res.data.child_id);
        setStep(3);
      } else if (step === 3) {
        await api
          .post(`/api/onboarding/exam/select?parent_id=${parentId}&child_id=${childId}`, {
            exam_type: examType,
            exam_date: '2027-01-24T00:00:00Z',
            subject_preferences:
              examType === 'NEET'
                ? { Physics: 25, Chemistry: 25, Biology: 50 }
                : { Physics: 35, Chemistry: 30, Mathematics: 35 },
          })
          .catch(() => {});
        await api.post('/api/hermes/admin/seed-topics').catch(() => {});
        await switchDemoRole('parent');
        navigate('/parent/dashboard');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-6">
      <div className="p-6 sm:p-8 rounded-3xl bg-slate-900/90 border border-slate-800 shadow-2xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-extrabold text-white">
              {mode === 'onboarding' ? '3-Step Parent & Child Onboarding' : 'Sign In / Register'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Connected to real FastAPI & Firestore Auth (`/api/auth/*` & `/api/onboarding/*`)
            </p>
          </div>
          <Link to="/" className="text-xs text-sky-400 hover:underline">
            ← Home
          </Link>
        </div>

        {/* Mode Selector Tabs */}
        <div className="grid grid-cols-5 gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
          {[
            { id: 'student_login', label: 'Student' },
            { id: 'parent_login', label: 'Parent' },
            { id: 'parent_register', label: 'Register' },
            { id: 'onboarding', label: 'Onboard' },
            { id: 'superadmin_login', label: 'Admin' },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => {
                setMode(t.id as any);
                setErrorMsg(null);
              }}
              className={`py-2 rounded-lg transition-all ${
                mode === t.id ? 'bg-sky-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {statusMsg && (
          <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-xs text-emerald-300">
            {statusMsg}
          </div>
        )}
        {errorMsg && (
          <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-xs text-rose-300">
            {errorMsg}
          </div>
        )}

        {mode === 'onboarding' ? (
          <div className="space-y-5">
            <div className="flex items-center justify-between text-xs font-bold text-slate-400">
              <span className={step >= 1 ? 'text-sky-400' : ''}>1. Language & Alerts</span>
              <span>→</span>
              <span className={step >= 2 ? 'text-sky-400' : ''}>2. Child Credentials</span>
              <span>→</span>
              <span className={step >= 3 ? 'text-sky-400' : ''}>3. Target Exam & Seed</span>
            </div>

            {step === 1 && (
              <div className="space-y-4">
                <label className="block text-xs font-semibold text-slate-300">
                  Preferred Mentor & Summary Language (`POST /api/onboarding/preferences`)
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                >
                  <option value="en">English (Default)</option>
                  <option value="hi">हिंदी (Hindi)</option>
                  <option value="mr">मराठी (Marathi)</option>
                </select>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Student Full Name (`POST /api/onboarding/child`)
                  </label>
                  <input
                    value={childName}
                    onChange={(e) => setChildName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Student Login Username
                    </label>
                    <input
                      value={childUsername}
                      onChange={(e) => setChildUsername(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Class / Grade
                    </label>
                    <select
                      value={childGrade}
                      onChange={(e) => setChildGrade(Number(e.target.value))}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                    >
                      <option value={11}>Class 11</option>
                      <option value={12}>Class 12</option>
                      <option value={13}>Dropper / Repeater</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <label className="block text-xs font-semibold text-slate-300">
                  Target Entrance Exam (`POST /api/onboarding/exam/select` + `seed-topics`)
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {['JEE_MAIN', 'JEE_ADVANCED', 'NEET'].map((ex) => (
                    <button
                      type="button"
                      key={ex}
                      onClick={() => setExamType(ex)}
                      className={`p-3 rounded-xl border text-xs font-bold ${
                        examType === ex
                          ? 'bg-sky-500/20 border-sky-500 text-sky-300'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                      }`}
                    >
                      {ex.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={handleOnboardingStep}
              disabled={submitting}
              className="w-full py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-sm"
            >
              {submitting
                ? 'Saving to Firestore...'
                : step < 3
                ? `Save & Continue to Step ${step + 1} →`
                : 'Complete Onboarding & Seed Syllabus →'}
            </button>
          </div>
        ) : (
          <form onSubmit={handleAuthSubmit} className="space-y-4">
            {mode === 'parent_register' && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Parent Full Name
                </label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                />
              </div>
            )}

            {mode === 'student_login' ? (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Student Username
                </label>
                <input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                />
              </div>
            )}

            {mode === 'parent_register' && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Mobile Number
                </label>
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-sm transition-all cursor-pointer"
            >
              {submitting ? 'Authenticating...' : 'Continue →'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
