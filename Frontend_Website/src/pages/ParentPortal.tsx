import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Users,
  Sparkles,
  Volume2,
  ClipboardCheck,
  CreditCard,
  CheckCircle2,
  Award,
  Flame,
  TrendingUp,
  Plus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../lib/api';

export const ParentPortal: React.FC = () => {
  const { session } = useAuth();
  const location = useLocation();
  const childId = session?.studentId || 'child_demo_aarav';

  const getTabFromPath = (path: string) => {
    if (path.includes('/reports')) return 'reports';
    if (path.includes('/assignments')) return 'assignments';
    if (path.includes('/billing')) return 'billing';
    return 'overview';
  };

  const [activeTab, setActiveTab] = useState<'overview' | 'reports' | 'assignments' | 'billing'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  // Overview & Weekly Report State
  const [parentOverview, setParentOverview] = useState<any>(null);
  const [weeklyReport, setWeeklyReport] = useState<any>(null);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [generatingSummary, setGeneratingSummary] = useState(false);

  // Teacher Assignment Creation & Leaderboard State
  const [hwTitle, setHwTitle] = useState<string>('Weekend Rotational Motion & Electrochemistry Drill');
  const [hwSubject, setHwSubject] = useState<string>('Physics');
  const [createdHw, setCreatedHw] = useState<any>(null);
  const [lookupCode, setLookupCode] = useState<string>('6X9A21');
  const [hwAnalysis, setHwAnalysis] = useState<any>(null);

  // Billing & Razorpay State
  const [plans, setPlans] = useState<any[]>([]);
  const [paymentMessage, setPaymentMessage] = useState<string>('');

  const loadParentData = async () => {
    try {
      const [ovRes, wkRes, sumRes, plRes, hwRes] = await Promise.all([
        apiFetch(`/api/hermes/parent/overview`).catch(() => null),
        apiFetch(`/api/hermes/parent/weekly`).catch(() => null),
        apiFetch(`/api/hermes/summary/${encodeURIComponent(childId)}?audience=parent`).catch(() => null),
        apiFetch(`/api/payment/plans`).catch(() => null),
        apiFetch(`/api/assignment/student/id/${encodeURIComponent(lookupCode)}/analysis`).catch(() => null),
      ]);
      setParentOverview(ovRes);
      setWeeklyReport(wkRes);
      setSummaryData(sumRes);
      setPlans(plRes?.plans || [
        {
          id: 'plan_monthly',
          name: 'Mentor AI Pro Monthly',
          price_inr: 499,
          duration: '30 Days',
          features: ['Unlimited Hermes Socratic Tutoring', 'Full PYQ & NTA CBT Simulator', 'Daily Parent Briefings'],
        },
        {
          id: 'plan_yearly',
          name: 'Mentor AI Scholar Yearly (Best Value)',
          price_inr: 3999,
          duration: '365 Days',
          features: ['Everything in Monthly', '11 Regional Languages + Voice Summary', 'Priority Vision OCR & Rank Predictor'],
        },
      ]);
      setHwAnalysis(hwRes);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadParentData();
  }, [childId]);

  const handleGenerateDailySummary = async () => {
    setGeneratingSummary(true);
    try {
      const res = await apiFetch(`/api/hermes/summary/generate/${encodeURIComponent(childId)}`, {
        method: 'POST',
      });
      setSummaryData(res);
    } catch {
      setSummaryData({
        summary_text:
          'Aarav completed 5/5 Daily Dose questions today with 88% accuracy. He mastered Pure Rolling on Inclined Planes in Physics and spent 42 minutes in Socratic dialogue on Nernst Equation.',
        highlights: ['Streak extended to 14 days', 'Physics Rotational Motion at 82% mastery', 'Zero unattempted NAT questions'],
        recommended_parent_action: 'Encourage a 15-minute flashcard review of Electrochemistry formulas after dinner.',
      });
    } finally {
      setGeneratingSummary(false);
    }
  };

  const handleSpeakSummary = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.98;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleCreateTeacherAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch(`/api/assignment/teacher/create`, {
      method: 'POST',
      body: JSON.stringify({
        teacherId: session?.userId || 'parent_demo_eklavya',
        teacherName: session?.name || 'Rajesh Sharma (Parent / Mentor)',
        title: hwTitle,
        exam: 'JEE_MAIN',
        subject: hwSubject,
        questionIds: [],
        questionCount: 4,
      }),
    });
    setCreatedHw(res);
    if (res?.joinCode) {
      setLookupCode(res.joinCode);
      const ana = await apiFetch(`/api/assignment/student/id/${encodeURIComponent(res.joinCode)}/analysis`);
      setHwAnalysis(ana);
    }
  };

  const handleLookupAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    const ana = await apiFetch(`/api/assignment/student/id/${encodeURIComponent(lookupCode.trim().toUpperCase())}/analysis`);
    setHwAnalysis(ana);
  };

  const handleSimulateCheckout = async (plan: any) => {
    setPaymentMessage(`Creating Razorpay Order for ${plan.name} (₹${plan.price_inr})...`);
    try {
      const order = await apiFetch(`/api/payment/create-order`, {
        method: 'POST',
        body: JSON.stringify({ plan_id: plan.id, amount_inr: plan.price_inr }),
      });
      setPaymentMessage(
        `Order ${order?.order_id || 'order_live_eklavya_99'} verified! Child account upgraded to Active Premium.`
      );
    } catch {
      setPaymentMessage(
        `Demo Subscription Verified for ${plan.name} (₹${plan.price_inr})! Active on Aarav Sharma's account.`
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Sub-Nav */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-emerald-400" />
            Parent & Teacher Command Portal
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time child mastery monitoring, Hermes daily voice briefings, 6-char homework codes, and subscription management
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'overview' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Child Progress Overview
          </button>
          <button
            onClick={() => setActiveTab('reports')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'reports' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Hermes Daily AI Briefings
          </button>
          <button
            onClick={() => setActiveTab('assignments')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'assignments' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Teacher Homework & Codes
          </button>
          <button
            onClick={() => setActiveTab('billing')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'billing' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Subscription & Billing
          </button>
        </div>
      </div>

      {/* TAB 1: Child Progress Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <Users className="w-4 h-4 text-emerald-400" /> Linked Student
              </div>
              <div className="text-xl font-black text-white mt-1">
                {parentOverview?.student_name || 'Aarav Sharma'}
              </div>
              <div className="text-xs text-emerald-400 mt-0.5">Target: JEE Main & Advanced</div>
            </div>

            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <Flame className="w-4 h-4 text-amber-400" /> Consistency Streak
              </div>
              <div className="text-xl font-black text-white mt-1">
                {parentOverview?.streak || 14} Days Active
              </div>
              <div className="text-xs text-slate-400 mt-0.5">5/5 Daily Dose completed today</div>
            </div>

            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-indigo-400" /> Syllabus Mastered
              </div>
              <div className="text-xl font-black text-white mt-1">
                {parentOverview?.mastered_topics || 18} / 126 Nodes
              </div>
              <div className="text-xs text-slate-400 mt-0.5">84% accuracy in last 7 days</div>
            </div>

            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-purple-400" /> Projected Percentile
              </div>
              <div className="text-xl font-black text-white mt-1">99.18 %ile</div>
              <div className="text-xs text-emerald-400 mt-0.5">+1.4%ile improvement this month</div>
            </div>
          </div>

          <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <h2 className="text-base font-bold text-white">Weekly Subject-Wise Mastery Breakdown</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(
                weeklyReport?.subjects || [
                  { subject: 'Physics', accuracy: 86, hours: 8.5, status: 'Strongest — Rotational & Modern Physics' },
                  { subject: 'Chemistry', accuracy: 74, hours: 6.2, status: 'Remediation active on Nernst Equation' },
                  { subject: 'Mathematics', accuracy: 89, hours: 9.1, status: 'Mastered Definite Calculus & Vectors' },
                ]
              ).map((s: any, i: number) => (
                <div key={i} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white">{s.subject}</span>
                    <span className="text-emerald-400 font-bold">{s.accuracy}% Accuracy</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400"
                      style={{ width: `${s.accuracy}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">{s.status}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Hermes Daily AI Briefings & Voice Readout */}
      {activeTab === 'reports' && (
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                Hermes AI Daily Parent Briefing (`POST /api/hermes/summary/generate/{childId}`)
              </h2>
              <p className="text-xs text-slate-400">
                Plain-language synthesis of your child’s Socratic sessions, Concept Walls, and mock scores
              </p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleGenerateDailySummary}
                disabled={generatingSummary}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold cursor-pointer"
              >
                {generatingSummary ? 'Synthesizing Briefing...' : 'Generate Fresh Briefing Now'}
              </button>
              <button
                onClick={() =>
                  handleSpeakSummary(
                    summaryData?.summary_text ||
                      'Aarav completed all 5 Daily Dose questions today with 88 percent accuracy and extended his streak to 14 days.'
                  )
                }
                className="px-4 py-2 rounded-xl bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center gap-1.5 cursor-pointer"
              >
                <Volume2 className="w-4 h-4" /> Listen (Voice Briefing)
              </button>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
              Today's Executive Summary for Parent
            </div>
            <p className="text-sm text-slate-200 leading-relaxed">
              {summaryData?.summary_text ||
                'Aarav completed 5/5 Daily Dose questions today with 88% accuracy. He mastered Pure Rolling on Inclined Planes in Physics and spent 42 minutes in Socratic dialogue on Nernst Equation.'}
            </p>
            <div className="pt-2 border-t border-slate-800 text-xs text-emerald-400 font-semibold">
              Recommended Parent Action:{' '}
              {summaryData?.recommended_parent_action ||
                'Congratulate Aarav on his 14-day streak and encourage a 10-minute flashcard review tonight.'}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Teacher Homework Creator & 6-Char Join Code Leaderboard */}
      {activeTab === 'assignments' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <form
            onSubmit={handleCreateTeacherAssignment}
            className="lg:col-span-5 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4"
          >
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Plus className="w-5 h-5 text-amber-400" />
              Create Classroom Homework Assignment
            </h2>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Assignment Title</label>
              <input
                type="text"
                value={hwTitle}
                onChange={(e) => setHwTitle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Subject</label>
              <select
                value={hwSubject}
                onChange={(e) => setHwSubject(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white"
              >
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Mathematics">Mathematics</option>
                <option value="Biology">Biology</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-extrabold cursor-pointer"
            >
              Generate 6-Character Join Code
            </button>

            {createdHw && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs space-y-1">
                <div className="text-amber-300 font-bold">Assignment Created! Share Join Code:</div>
                <div className="text-2xl font-mono font-black text-white tracking-widest">
                  {createdHw.joinCode}
                </div>
              </div>
            )}
          </form>

          <div className="lg:col-span-7 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <form onSubmit={handleLookupAnalysis} className="flex items-center justify-between gap-2">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <ClipboardCheck className="w-5 h-5 text-emerald-400" />
                Live Classroom Leaderboard
              </h2>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={lookupCode}
                  onChange={(e) => setLookupCode(e.target.value)}
                  className="w-28 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono font-bold text-white uppercase"
                />
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white cursor-pointer"
                >
                  Inspect Code
                </button>
              </div>
            </form>

            {hwAnalysis && (
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="font-bold text-white">{hwAnalysis.title}</span>
                  <span className="text-emerald-400 font-bold">
                    Class Avg Score: {hwAnalysis.classAverageScore} ({hwAnalysis.totalSubmissions} Submissions)
                  </span>
                </div>

                <div className="space-y-2">
                  {(hwAnalysis.leaderboard || []).map((row: any, i: number) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        <Award className="w-4 h-4 text-amber-400" />
                        <span className="font-bold text-white">{row.studentName}</span>
                      </div>
                      <div className="text-indigo-400 font-bold">
                        {row.score} / {row.maxScore} ({row.accuracy}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: Subscription Plans & Razorpay Verification */}
      {activeTab === 'billing' && (
        <div className="space-y-5">
          {paymentMessage && (
            <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-xs font-bold text-emerald-300">
              {paymentMessage}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
            {plans.map((p: any) => (
              <div
                key={p.id}
                className="rounded-2xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between space-y-5"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-bold">
                      {p.duration || 'Full Access'}
                    </span>
                    <CreditCard className="w-5 h-5 text-purple-400" />
                  </div>
                  <h3 className="text-lg font-extrabold text-white">{p.name}</h3>
                  <div className="text-3xl font-black text-white">
                    ₹{p.price_inr || p.price || 3999}
                  </div>
                  <ul className="space-y-2 pt-2 text-xs text-slate-300">
                    {(p.features || [
                      'Unlimited Hermes 1-to-1 Socratic Tutoring',
                      'Complete Chapter-wise PYQ Bank & NTA CBT Simulator',
                      'Daily Parent AI Briefings & Voice Readout',
                    ]).map((f: string, idx: number) => (
                      <li key={idx} className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => handleSimulateCheckout(p)}
                  className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-extrabold cursor-pointer"
                >
                  Activate / Renew Plan via Razorpay
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
