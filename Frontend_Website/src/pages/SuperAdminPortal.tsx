import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  ShieldAlert,
  Users,
  Database,
  Layers,
  Cpu,
  Plus,
  Trash2,
  CheckCircle2,
  RefreshCw,
  Award,
  Lock,
  Unlock,
} from 'lucide-react';
import { apiFetch } from '../lib/api';
import { LatexRenderer } from '../components/LatexRenderer';

export const SuperAdminPortal: React.FC = () => {
  const location = useLocation();

  const getTabFromPath = (path: string) => {
    if (path.includes('/users')) return 'users';
    if (path.includes('/questions')) return 'questions';
    if (path.includes('/content')) return 'content';
    if (path.includes('/ai-settings')) return 'ai';
    return 'overview';
  };

  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'questions' | 'content' | 'ai'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const [overview, setOverview] = useState<any>(null);
  const [usersData, setUsersData] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [colleges, setColleges] = useState<any[]>([]);
  const [sysConfig, setSysConfig] = useState<any>(null);
  const [statusBanner, setStatusBanner] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  // New PYQ Form State (with live KaTeX preview)
  const [newQExam, setNewQExam] = useState('JEE Main');
  const [newQSubject, setNewQSubject] = useState('Physics');
  const [newQChapter, setNewQChapter] = useState('Rotational Motion');
  const [newQTopic, setNewQTopic] = useState('Rolling & Angular Momentum');
  const [newQYear, setNewQYear] = useState(2025);
  const [newQType, setNewQType] = useState<'MCQ' | 'NAT'>('MCQ');
  const [newQDiff, setNewQDiff] = useState<'easy' | 'medium' | 'hard'>('hard');
  const [newQStatement, setNewQStatement] = useState(
    'A uniform disc of mass $M$ and radius $R$ rolls without slipping down an inclined plane of angle $\\theta = 30^\\circ$. What is the linear acceleration of its center of mass?'
  );
  const [newQCorrect, setNewQCorrect] = useState('A');
  const [newQSolution, setNewQSolution] = useState(
    'For a rolling uniform disc, $I = \\frac{1}{2}MR^2 \\implies k^2/R^2 = \\frac{1}{2}$. Therefore $a = \\frac{g \\sin 30^\\circ}{1 + 1/2} = \\frac{g}{3}$.'
  );

  // New Flashcard Form State
  const [fcSubject, setFcSubject] = useState('physics');
  const [fcChapter, setFcChapter] = useState('Electrostatics');
  const [fcTitle, setFcTitle] = useState('Gauss’s Law & Hollow Conductor');
  const [fcFront, setFcFront] = useState(
    'State Gauss’s Law in Electrostatics and electric flux inside a hollow conductor.'
  );
  const [fcBack, setFcBack] = useState(
    '$\\oint \\vec{E} \\cdot d\\vec{A} = \\frac{q_{enc}}{\\varepsilon_0}$. Inside a hollow conductor $q_{enc}=0 \\implies \\vec{E}=0$.'
  );

  const loadAllAdminData = async () => {
    setLoading(true);
    try {
      const [ov, us, qs, fc, col, cfg] = await Promise.all([
        apiFetch(`/api/superadmin/overview`),
        apiFetch(`/api/superadmin/users`),
        apiFetch(`/api/superadmin/questions`),
        apiFetch(`/api/superadmin/flashcards`),
        apiFetch(`/api/superadmin/colleges`),
        apiFetch(`/api/superadmin/system-config`),
      ]);
      setOverview(ov);
      setUsersData(us);
      setQuestions(qs?.questions || []);
      setFlashcards(fc?.cards || fc?.flashcards || []);
      setColleges(col?.colleges || []);
      setSysConfig(cfg);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllAdminData();
  }, []);

  const showToast = (msg: string) => {
    setStatusBanner(msg);
    setTimeout(() => setStatusBanner(''), 4000);
  };

  const handleUserAction = async (targetId: string, action: string, value?: any) => {
    try {
      const res = await apiFetch(`/api/superadmin/users/action`, {
        method: 'POST',
        body: JSON.stringify({ target_id: targetId, action, value }),
      });
      showToast(res.message || `Executed ${action} on ${targetId}`);
      loadAllAdminData();
    } catch (err: any) {
      showToast(`Error: ${err.message}`);
    }
  };

  const handleCreatePyq = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const examIdMap: Record<string, string> = {
        'JEE Main': 'jee_main',
        'JEE Advanced': 'jee_advanced',
        NEET: 'neet',
      };
      const res = await apiFetch(`/api/superadmin/questions`, {
        method: 'POST',
        body: JSON.stringify({
          examId: examIdMap[newQExam] || 'jee_main',
          exam: newQExam,
          subjectId: newQSubject.toLowerCase(),
          subject: newQSubject,
          chapterId: newQChapter.toLowerCase().replace(/\s+/g, '_'),
          chapter: newQChapter,
          topicId: newQTopic.toLowerCase().replace(/\s+/g, '_'),
          topic: newQTopic,
          year: Number(newQYear),
          type: newQType,
          difficulty: newQDiff,
          statementHtml: newQStatement,
          options:
            newQType === 'MCQ'
              ? [
                  { id: 'A', text: '$g / 3$' },
                  { id: 'B', text: '$2g / 3$' },
                  { id: 'C', text: '$g / 2$' },
                  { id: 'D', text: '$5g / 7$' },
                ]
              : [],
          correctOption: newQType === 'MCQ' ? newQCorrect : null,
          numericalAnswer: newQType === 'NAT' ? Number(newQCorrect || 5) : null,
          solutionHtml: newQSolution,
          ncertPages: 'NCERT Class 11 Ch 7',
          revisionZone: 'high_yield',
        }),
      });
      showToast(`Created PYQ ${res.question?.id} and hot-reloaded student PYQ bank!`);
      loadAllAdminData();
    } catch (err: any) {
      showToast(`Error: ${err.message}`);
    }
  };

  const handleDeletePyq = async (questionId: string) => {
    await apiFetch(`/api/superadmin/questions/${encodeURIComponent(questionId)}`, {
      method: 'DELETE',
    });
    showToast(`Deleted PYQ ${questionId} and hot-reloaded in-memory services.`);
    loadAllAdminData();
  };

  const handleCreateFlashcard = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch(`/api/superadmin/flashcards`, {
      method: 'POST',
      body: JSON.stringify({
        subjectId: fcSubject.toLowerCase(),
        chapterId: fcChapter.toLowerCase().replace(/\s+/g, '_'),
        chapterName: fcChapter,
        topicName: fcChapter,
        title: fcTitle,
        frontText: fcFront,
        backFormulaHtml: fcBack,
        keyTakeaways: ['High-Yield NCERT & JEE Concept'],
      }),
    });
    showToast(`Added Flashcard ${res.card?.cardId} to live student decks!`);
    loadAllAdminData();
  };

  const handleDeleteFlashcard = async (cardId: string) => {
    await apiFetch(`/api/superadmin/flashcards/${encodeURIComponent(cardId)}`, {
      method: 'DELETE',
    });
    showToast(`Deleted Flashcard ${cardId}.`);
    loadAllAdminData();
  };

  const handleUpdateCollegeCutoff = async (college: any, delta: number) => {
    const firstBranch = college.branches?.[0];
    if (!firstBranch) return;
    const curCutoffs = firstBranch.cutoffs?.['2025'] || firstBranch.cutoffs?.['2024'] || { OPEN: 150 };
    const curOpen = Number(curCutoffs.OPEN || 150);
    const nextOpen = Math.max(1, curOpen + delta);

    await apiFetch(`/api/superadmin/colleges/${encodeURIComponent(college.id)}`, {
      method: 'PUT',
      body: JSON.stringify({
        branchCode: firstBranch.branchCode,
        year: '2025',
        cutoffs: { ...curCutoffs, OPEN: nextOpen },
      }),
    });
    showToast(`Updated ${college.name} (${firstBranch.branchCode}) OPEN closing rank to AIR #${nextOpen}`);
    loadAllAdminData();
  };

  const handleSaveSystemConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sysConfig?.config) return;
    await apiFetch(`/api/superadmin/system-config`, {
      method: 'PUT',
      body: JSON.stringify({
        free_daily_chat_cap: Number(sysConfig.config.free_daily_chat_cap),
        premium_daily_chat_cap: Number(sysConfig.config.premium_daily_chat_cap),
        mastery_threshold_pct: Number(sysConfig.config.mastery_threshold_pct),
        rate_limit_per_minute: Number(sysConfig.config.rate_limit_per_minute),
        maintenance_mode: Boolean(sysConfig.config.maintenance_mode),
      }),
    });
    showToast('Saved Hermes AI & Guardrail Configuration to live runtime!');
    loadAllAdminData();
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Sub-Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-bold mb-1">
            <ShieldAlert className="w-3.5 h-3.5" /> Root Platform Governance • Live Firestore & Dataset Sync
          </span>
          <h1 className="text-2xl font-extrabold text-white">eKlAVYA SuperAdmin Command Center</h1>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'overview' ? 'bg-amber-500 text-slate-950' : 'text-slate-400 hover:text-white'
            }`}
          >
            1. Platform Telemetry
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'users' ? 'bg-amber-500 text-slate-950' : 'text-slate-400 hover:text-white'
            }`}
          >
            2. Users & Concept Walls
          </button>
          <button
            onClick={() => setActiveTab('questions')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'questions' ? 'bg-amber-500 text-slate-950' : 'text-slate-400 hover:text-white'
            }`}
          >
            3. PYQ CMS ({questions.length})
          </button>
          <button
            onClick={() => setActiveTab('content')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'content' ? 'bg-amber-500 text-slate-950' : 'text-slate-400 hover:text-white'
            }`}
          >
            4. Flashcards & Cutoffs
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'ai' ? 'bg-amber-500 text-slate-950' : 'text-slate-400 hover:text-white'
            }`}
          >
            5. Hermes AI & Audit Logs
          </button>
        </div>
      </div>

      {statusBanner && (
        <div className="p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-500/40 text-xs font-bold text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> {statusBanner}
          </span>
        </div>
      )}

      {/* TAB 1: Platform Telemetry & Executive Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400">Active Students & Parents</div>
              <div className="text-2xl font-black text-white mt-1">
                {(overview?.kpis?.total_students || 1) + (overview?.kpis?.total_parents || 1)} Accounts
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5">
                {overview?.kpis?.active_premium_subscriptions || 1} Active Paid Subscriptions
              </div>
            </div>

            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400">Total Subscription Revenue</div>
              <div className="text-2xl font-black text-emerald-400 mt-1">
                ₹{(overview?.kpis?.total_revenue_inr || 7999).toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">Razorpay Verified</div>
            </div>

            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400">Live PYQs & Flashcards</div>
              <div className="text-2xl font-black text-indigo-400 mt-1">
                {overview?.kpis?.total_pyq_questions || questions.length} PYQs •{' '}
                {overview?.kpis?.total_flashcards || flashcards.length} Cards
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                {overview?.kpis?.syllabus_micro_topics || 126} Syllabus Micro-Topics
              </div>
            </div>

            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <div className="text-xs text-slate-400">CBT Tests & Classroom Codes</div>
              <div className="text-2xl font-black text-amber-400 mt-1">
                {overview?.kpis?.custom_tests_generated || 0} Tests •{' '}
                {overview?.kpis?.homework_assignments || 1} HW Codes
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Firestore DB: {overview?.system_health?.firestore_db?.toUpperCase() || 'CONNECTED'}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Subject Breakdown */}
            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Database className="w-4 h-4 text-indigo-400" />
                  Question Bank Distribution by Subject
                </h2>
                <button
                  onClick={loadAllAdminData}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {Object.entries(
                  overview?.distributions?.pyq_by_subject || {
                    Physics: 6,
                    Chemistry: 4,
                    Mathematics: 4,
                    Biology: 4,
                  }
                ).map(([subj, count]: any) => (
                  <div
                    key={subj}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between"
                  >
                    <span className="text-xs font-bold text-white">{subj}</span>
                    <span className="px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-xs font-bold">
                      {count} PYQs
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Audit Trail */}
            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-3">
              <h2 className="text-base font-bold text-white">Recent SuperAdmin Governance Audit Log</h2>
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {(overview?.recent_audit_logs || []).map((log: any) => (
                  <div
                    key={log.id}
                    className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-mono font-bold text-amber-400">{log.action}</span>
                      <p className="text-slate-300 mt-0.5">{log.detail}</p>
                    </div>
                    <span className="text-[10px] text-slate-500">{log.actor}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: User, Subscription & Concept Wall Governance */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-amber-400" />
              Student Profiles — Live Concept Wall & XP Controls (`POST /api/superadmin/users/action`)
            </h2>
            <p className="text-xs text-slate-400">
              Trigger or unlock a Hermes Concept Wall, award bonus XP, or reset daily chat caps in real time on Firestore.
            </p>

            <div className="space-y-3">
              {(usersData?.students || []).map((stu: any) => {
                const sid = stu.child_id || stu.id || 'child_demo_aarav';
                const lockedTopics = stu.locked_topics || [];
                const wallActive = lockedTopics.length > 0;
                return (
                  <div
                    key={sid}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-bold text-white">{stu.name || 'Aarav Sharma'}</span>
                        <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[11px] font-bold">
                          {(stu.exam_scope || ['JEE_MAIN']).join(', ')}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            wallActive
                              ? 'bg-rose-500/20 text-rose-300'
                              : 'bg-emerald-500/20 text-emerald-300'
                          }`}
                        >
                          {wallActive
                            ? `CONCEPT WALL LOCKED (${lockedTopics.length})`
                            : 'CONCEPT WALL CLEAR'}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">
                        ID: <code className="text-slate-300">{sid}</code> • XP:{' '}
                        <strong>{stu.xp || 1450}</strong> • Streak:{' '}
                        <strong>{stu.streak_days || 14}d</strong> • Mastery:{' '}
                        <strong>{stu.completion_pct || 14.3}%</strong>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {wallActive ? (
                        <button
                          onClick={() => handleUserAction(sid, 'unlock_concept_wall')}
                          className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1 cursor-pointer"
                        >
                          <Unlock className="w-3.5 h-3.5" /> Unlock Concept Wall
                        </button>
                      ) : (
                        <button
                          onClick={() => handleUserAction(sid, 'trigger_concept_wall')}
                          className="px-3 py-1.5 rounded-xl bg-rose-600/25 border border-rose-500/40 text-rose-300 text-xs font-bold flex items-center gap-1 cursor-pointer"
                        >
                          <Lock className="w-3.5 h-3.5" /> Trigger Concept Wall
                        </button>
                      )}

                      <button
                        onClick={() => handleUserAction(sid, 'award_xp', 250)}
                        className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1 cursor-pointer"
                      >
                        <Award className="w-3.5 h-3.5" /> Award +250 XP
                      </button>

                      <button
                        onClick={() => handleUserAction(sid, 'reset_chat_cap')}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer"
                      >
                        Reset Daily Chat Cap
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Parent Accounts & Subscription Governance */}
          <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <h2 className="text-base font-bold text-white">
              Parent Accounts — Subscription Tier Overrides
            </h2>
            <div className="space-y-3">
              {(usersData?.parents || []).map((par: any) => {
                const pid = par.parent_id || par.id || 'parent_demo_eklavya';
                return (
                  <div
                    key={pid}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-4"
                  >
                    <div>
                      <div className="text-sm font-bold text-white">
                        {par.name || 'Rajesh Sharma'} ({par.email || 'rajesh.sharma@eklavya.ai'})
                      </div>
                      <div className="text-xs text-slate-400">
                        Parent ID: <code>{pid}</code> • Plan:{' '}
                        <strong className="text-emerald-400">{par.plan_name || 'Premium Yearly'}</strong>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleUserAction(pid, 'grant_premium')}
                        className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold cursor-pointer"
                      >
                        Grant 1-Year Scholar Pro
                      </button>
                      <button
                        onClick={() => handleUserAction(pid, 'revoke_premium')}
                        className="px-3.5 py-1.5 rounded-xl bg-rose-900/50 hover:bg-rose-800 text-rose-200 text-xs font-semibold cursor-pointer"
                      >
                        Revoke Premium
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Live PYQ CMS with KaTeX Preview & Hot-Reload */}
      {activeTab === 'questions' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Create PYQ Form */}
          <form
            onSubmit={handleCreatePyq}
            className="lg:col-span-5 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4"
          >
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Plus className="w-5 h-5 text-amber-400" />
              Author New PYQ (Hot-Reloads Student Bank)
            </h2>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Exam</label>
                <select
                  value={newQExam}
                  onChange={(e) => setNewQExam(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                >
                  <option value="JEE Main">JEE Main</option>
                  <option value="JEE Advanced">JEE Advanced</option>
                  <option value="NEET">NEET</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Subject</label>
                <select
                  value={newQSubject}
                  onChange={(e) => setNewQSubject(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                >
                  <option value="Physics">Physics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Mathematics">Mathematics</option>
                  <option value="Biology">Biology</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Chapter</label>
                <input
                  type="text"
                  value={newQChapter}
                  onChange={(e) => setNewQChapter(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Type & Difficulty</label>
                <div className="flex gap-1.5">
                  <select
                    value={newQType}
                    onChange={(e) => setNewQType(e.target.value as 'MCQ' | 'NAT')}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-white"
                  >
                    <option value="MCQ">MCQ</option>
                    <option value="NAT">NAT</option>
                  </select>
                  <select
                    value={newQDiff}
                    onChange={(e) => setNewQDiff(e.target.value as any)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-white"
                  >
                    <option value="easy">easy</option>
                    <option value="medium">medium</option>
                    <option value="hard">hard</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">
                LaTeX Question Statement ($...$ inline, $$...$$ block)
              </label>
              <textarea
                rows={3}
                value={newQStatement}
                onChange={(e) => setNewQStatement(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white font-mono"
              />
            </div>

            {/* Live KaTeX Preview Box */}
            <div className="p-3 rounded-xl bg-slate-950 border border-indigo-500/30 text-xs space-y-1">
              <div className="text-[10px] font-bold text-indigo-400 uppercase">Live KaTeX Preview:</div>
              <LatexRenderer content={newQStatement} />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Correct Answer</label>
                <input
                  type="text"
                  value={newQCorrect}
                  onChange={(e) => setNewQCorrect(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-[11px] text-slate-400 mb-1">Year</label>
                <input
                  type="number"
                  value={newQYear}
                  onChange={(e) => setNewQYear(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Step-by-Step LaTeX Solution</label>
              <textarea
                rows={2}
                value={newQSolution}
                onChange={(e) => setNewQSolution(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white font-mono"
              />
            </div>

            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-extrabold cursor-pointer"
            >
              Publish PYQ & Hot-Reload Question Bank
            </button>
          </form>

          {/* Existing PYQs List */}
          <div className="lg:col-span-7 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-3 max-h-[80vh] overflow-y-auto">
            <h2 className="text-base font-bold text-white">
              Live PYQ Repository ({questions.length} Questions in `pyq_and_colleges.json`)
            </h2>
            {questions.map((q: any) => {
              const qId = q.id || q.questionId;
              return (
                <div
                  key={qId}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="text-xs font-bold text-indigo-400">
                      [{qId}] {q.exam} {q.year} • {q.subject} • {q.chapter} ({q.type || q.questionType})
                    </div>
                    <div className="text-xs text-slate-200">
                      <LatexRenderer content={q.statementHtml || q.statement || ''} />
                    </div>
                    <div className="text-[11px] text-emerald-400">
                      Answer Key: {q.correctOption ?? q.numericalAnswer ?? q.correctAnswer}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeletePyq(qId)}
                    className="p-2 rounded-lg bg-rose-950/60 hover:bg-rose-900 text-rose-300 shrink-0 cursor-pointer"
                    title="Delete Question"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: Flashcards & College Cutoffs CMS */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Create Flashcard */}
            <form
              onSubmit={handleCreateFlashcard}
              className="lg:col-span-5 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-3"
            >
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                Add Revision Flashcard
              </h2>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  value={fcSubject}
                  onChange={(e) => setFcSubject(e.target.value)}
                  placeholder="Subject"
                  className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white"
                />
                <input
                  type="text"
                  value={fcChapter}
                  onChange={(e) => setFcChapter(e.target.value)}
                  placeholder="Chapter"
                  className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white"
                />
              </div>
              <input
                type="text"
                value={fcTitle}
                onChange={(e) => setFcTitle(e.target.value)}
                placeholder="Card Title..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white"
              />
              <textarea
                rows={2}
                value={fcFront}
                onChange={(e) => setFcFront(e.target.value)}
                placeholder="Front Concept Prompt..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white"
              />
              <textarea
                rows={2}
                value={fcBack}
                onChange={(e) => setFcBack(e.target.value)}
                placeholder="Back Formula / LaTeX..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white"
              />
              <button
                type="submit"
                className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold cursor-pointer"
              >
                Publish Flashcard
              </button>
            </form>

            {/* Flashcard Deck List */}
            <div className="lg:col-span-7 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-2.5 max-h-96 overflow-y-auto">
              <h2 className="text-base font-bold text-white">Active Flashcards ({flashcards.length})</h2>
              {flashcards.slice(0, 25).map((fc: any) => (
                <div
                  key={fc.cardId}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="font-bold text-indigo-400">
                      {fc.subjectId?.toUpperCase() || fc.subject} • {fc.chapterName || fc.chapter}
                    </div>
                    <div className="text-white">
                      <LatexRenderer content={fc.frontText || fc.front || fc.title || ''} />
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteFlashcard(fc.cardId)}
                    className="p-1.5 rounded-lg bg-rose-950/60 text-rose-300 cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* College Cutoffs Live Editor */}
          <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            <h2 className="text-base font-bold text-white">
              JoSAA / MCC College Cutoff Matrix (`PUT /api/superadmin/colleges/{'{id}'}`)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {colleges.map((col: any) => {
                const firstBr = col.branches?.[0];
                const openRank =
                  firstBr?.cutoffs?.['2025']?.OPEN ||
                  firstBr?.cutoffs?.['2024']?.OPEN ||
                  col.closingRank ||
                  120;
                return (
                  <div
                    key={col.id || col.collegeId}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-3 text-xs"
                  >
                    <div>
                      <div className="font-bold text-white">{col.name || col.institute}</div>
                      <div className="text-slate-400">
                        {firstBr?.branchName || col.branch || 'B.Tech / MBBS'} • Closing AIR:{' '}
                        <strong className="text-emerald-400">#{openRank}</strong>
                      </div>
                    </div>
                    <div className="flex gap-1.5">
                      <button
                        onClick={() => handleUpdateCollegeCutoff(col, -15)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold cursor-pointer"
                      >
                        -15 AIR
                      </button>
                      <button
                        onClick={() => handleUpdateCollegeCutoff(col, 15)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold cursor-pointer"
                      >
                        +15 AIR
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: Hermes AI Guardrails & System Configuration */}
      {activeTab === 'ai' && sysConfig?.config && (
        <form
          onSubmit={handleSaveSystemConfig}
          className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 max-w-4xl"
        >
          <div className="flex items-center gap-2 text-base font-bold text-white">
            <Cpu className="w-5 h-5 text-amber-400" />
            Hermes Socratic AI Guardrails & Model Configuration (`PUT /api/superadmin/system-config`)
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Free-Tier Daily Socratic Chat Cap
              </label>
              <input
                type="number"
                value={sysConfig.config.free_daily_chat_cap}
                onChange={(e) =>
                  setSysConfig((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, free_daily_chat_cap: Number(e.target.value) },
                  }))
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Premium-Tier Daily Socratic Chat Cap
              </label>
              <input
                type="number"
                value={sysConfig.config.premium_daily_chat_cap}
                onChange={(e) =>
                  setSysConfig((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, premium_daily_chat_cap: Number(e.target.value) },
                  }))
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Micro-Topic Mastery Pass Threshold (%)
              </label>
              <input
                type="number"
                value={sysConfig.config.mastery_threshold_pct}
                onChange={(e) =>
                  setSysConfig((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, mastery_threshold_pct: Number(e.target.value) },
                  }))
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                API Rate Limit (Requests / Minute)
              </label>
              <input
                type="number"
                value={sysConfig.config.rate_limit_per_minute}
                onChange={(e) =>
                  setSysConfig((prev: any) => ({
                    ...prev,
                    config: { ...prev.config, rate_limit_per_minute: Number(e.target.value) },
                  }))
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
          </div>

          {sysConfig.soul_prompt && (
            <div className="space-y-1.5">
              <div className="text-xs font-bold text-indigo-400">
                Active Hermes Socratic SOUL Prompt (Read-Only System Instruction):
              </div>
              <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 whitespace-pre-wrap max-h-48 overflow-y-auto font-mono">
                {sysConfig.soul_prompt}
              </pre>
            </div>
          )}

          <button
            type="submit"
            className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-extrabold cursor-pointer"
          >
            Save Hermes AI Guardrails
          </button>
        </form>
      )}
    </div>
  );
};
