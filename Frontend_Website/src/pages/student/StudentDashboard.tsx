import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Flame,
  Trophy,
  Target,
  Zap,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Brain,
  Award,
  Calendar,
  BookOpen,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../lib/api';
import { LatexRenderer } from '../../components/LatexRenderer';

export const StudentDashboard: React.FC = () => {
  const { session } = useAuth();
  const studentId = session?.studentId || 'child_demo_aarav';
  const examType = session?.examType || 'JEE_MAIN';

  const [todayData, setTodayData] = useState<any>(null);
  const [scorePrediction, setScorePrediction] = useState<any>(null);
  const [dailyDose, setDailyDose] = useState<any>(null);
  const [heatmap, setHeatmap] = useState<any>(null);
  const [leaderboard, setLeaderboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Daily Dose Interactive Modal State
  const [showDoseModal, setShowDoseModal] = useState(false);
  const [doseAnswers, setDoseAnswers] = useState<Record<string, string>>({});
  const [doseSubmitted, setDoseSubmitted] = useState(false);

  // Target Goal Update State
  const [goalType, setGoalType] = useState<'questions' | 'minutes'>('questions');
  const [goalTarget, setGoalTarget] = useState<number>(25);
  const [goalSavedMsg, setGoalSavedMsg] = useState<string>('');

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const now = new Date();
      const [todayRes, predRes, doseRes, heatRes, leadRes] = await Promise.all([
        apiFetch(`/api/hermes/today`).catch(() => null),
        apiFetch(`/api/hermes/score-prediction`).catch(() => null),
        apiFetch(`/api/targets/daily-dose?studentId=${encodeURIComponent(studentId)}`).catch(() => null),
        apiFetch(
          `/api/targets/heatmap?studentId=${encodeURIComponent(studentId)}&month=${now.getMonth() + 1}&year=${now.getFullYear()}`
        ).catch(() => null),
        apiFetch(`/api/leaderboard/achievements?examType=${encodeURIComponent(examType)}&timeframe=weekly`).catch(
          () => null
        ),
      ]);

      setTodayData(todayRes);
      setScorePrediction(predRes);
      setDailyDose(doseRes);
      setHeatmap(heatRes);
      setLeaderboard(leadRes);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [studentId, examType]);

  const handleCompleteDailyDose = async () => {
    if (!dailyDose?.questions) return;
    let correct = 0;
    dailyDose.questions.forEach((q: any) => {
      if ((doseAnswers[q.questionId] || '').trim().toUpperCase() === String(q.correctAnswer).trim().toUpperCase()) {
        correct++;
      }
    });
    const accuracy = Math.round((correct / dailyDose.questions.length) * 100);
    setDoseSubmitted(true);

    try {
      const updated = await apiFetch(`/api/targets/daily-dose/complete`, {
        method: 'POST',
        body: JSON.stringify({
          studentId,
          completedCount: dailyDose.questions.length,
          accuracy,
        }),
      });
      setDailyDose(updated);
      const now = new Date();
      const heatRes = await apiFetch(
        `/api/targets/heatmap?studentId=${encodeURIComponent(studentId)}&month=${now.getMonth() + 1}&year=${now.getFullYear()}`
      );
      setHeatmap(heatRes);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch(`/api/targets/update`, {
        method: 'POST',
        body: JSON.stringify({
          studentId,
          type: goalType,
          targetCount: Number(goalTarget),
          currentProgress: dailyDose?.completedCount || 4,
        }),
      });
      setGoalSavedMsg(`Target updated to ${goalTarget} ${goalType}/day!`);
      setTimeout(() => setGoalSavedMsg(''), 3000);
    } catch (err: any) {
      setGoalSavedMsg(`Error: ${err.message}`);
    }
  };

  const conceptWallActive = todayData?.concept_wall_active || false;
  const streakDays = todayData?.streak || heatmap?.currentStreak || 14;
  const xpPoints = todayData?.xp || 1450;

  return (
    <div className="space-y-6">
      {/* Concept Wall Banner if active */}
      {conceptWallActive && (
        <div className="rounded-2xl bg-rose-950/70 border border-rose-500/40 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 mt-0.5">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-rose-200">
                Concept Wall Active: {todayData?.concept_wall_topic || 'Prerequisite Remediation Required'}
              </h3>
              <p className="text-xs text-rose-300/80 mt-0.5">
                Hermes AI detected a foundational gap. Complete a 5-minute Socratic Remediation chat to unlock new advanced topics.
              </p>
            </div>
          </div>
          <Link
            to="/student/mentor"
            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold whitespace-nowrap transition-colors"
          >
            Resolve with Hermes AI →
          </Link>
        </div>
      )}

      {/* Top Hero Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Welcome & Today's Plan Card */}
        <div className="lg:col-span-2 rounded-2xl bg-gradient-to-br from-indigo-950/90 via-slate-900 to-slate-900 border border-indigo-500/30 p-6 flex flex-col justify-between">
          <div>
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5" /> Hermes Adaptive Study Engine
              </span>
              <button
                onClick={loadDashboard}
                className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
              </button>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Welcome back, {session?.name || 'Aarav Sharma'}
            </h1>
            <p className="text-sm text-slate-300 mt-1">
              {todayData?.greeting ||
                'Your syllabus mastery graph is synced. Complete your 5-Q Daily Dose and continue Socratic tutoring on Rotational Mechanics.'}
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
            <div className="rounded-xl bg-slate-950/60 border border-slate-800/80 p-3.5">
              <div className="flex items-center gap-1.5 text-amber-400 text-xs font-semibold">
                <Flame className="w-4 h-4 fill-amber-400" /> Active Streak
              </div>
              <div className="text-2xl font-black text-white mt-1">{streakDays} Days</div>
              <div className="text-[11px] text-slate-400">Best: {heatmap?.longestStreak || 18} days</div>
            </div>

            <div className="rounded-xl bg-slate-950/60 border border-slate-800/80 p-3.5">
              <div className="flex items-center gap-1.5 text-indigo-400 text-xs font-semibold">
                <Zap className="w-4 h-4" /> Total XP
              </div>
              <div className="text-2xl font-black text-white mt-1">{xpPoints.toLocaleString()}</div>
              <div className="text-[11px] text-slate-400">Scholar League #1</div>
            </div>

            <div className="rounded-xl bg-slate-950/60 border border-slate-800/80 p-3.5">
              <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-semibold">
                <CheckCircle2 className="w-4 h-4" /> Topics Mastered
              </div>
              <div className="text-2xl font-black text-white mt-1">
                {todayData?.mastered_count ?? 18} / {todayData?.total_topics ?? 126}
              </div>
              <div className="text-[11px] text-slate-400">Micro-topics verified</div>
            </div>

            <div className="rounded-xl bg-slate-950/60 border border-slate-800/80 p-3.5">
              <div className="flex items-center gap-1.5 text-purple-400 text-xs font-semibold">
                <Target className="w-4 h-4" /> Predicted Score
              </div>
              <div className="text-2xl font-black text-white mt-1">
                {scorePrediction?.predicted_score || '218 / 300'}
              </div>
              <div className="text-[11px] text-slate-400">
                Percentile: {scorePrediction?.predicted_percentile || '99.18%ile'}
              </div>
            </div>
          </div>
        </div>

        {/* Daily Dose 5-Question Sprint Card */}
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="px-2.5 py-1 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-semibold">
                Daily Dose Sprint
              </span>
              <span className="text-xs font-bold text-emerald-400">+{dailyDose?.xpReward || 50} XP</span>
            </div>
            <h2 className="text-lg font-bold text-white">5 High-Yield Questions Today</h2>
            <p className="text-xs text-slate-400 mt-1">
              Curated daily mix across Physics, Chemistry & Mathematics to lock in your streak.
            </p>

            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Today's Progress</span>
                <span className="font-semibold text-white">
                  {dailyDose?.isCompleted ? '5 / 5 Completed' : `${dailyDose?.completedCount || 0} / 5 Solved`}
                </span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-500 to-emerald-400 transition-all duration-500"
                  style={{
                    width: `${dailyDose?.isCompleted ? 100 : ((dailyDose?.completedCount || 0) / 5) * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-slate-800 flex flex-col gap-2">
            <button
              onClick={() => {
                setDoseSubmitted(false);
                setShowDoseModal(true);
              }}
              className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              {dailyDose?.isCompleted ? 'Review Today’s 5-Q Sprint' : 'Start 5-Question Sprint Now'}
              <ArrowRight className="w-4 h-4" />
            </button>
            <div className="flex gap-2">
              <Link
                to="/student/mentor"
                className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium text-center transition-colors"
              >
                Hermes AI Tutor
              </Link>
              <Link
                to="/student/pyq"
                className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium text-center transition-colors"
              >
                Solve PYQs
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Second Row: Recommended Micro-Topics + Monthly Consistency Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Today's Hermes Recommended Micro-Topics */}
        <div className="lg:col-span-2 rounded-2xl bg-slate-900 border border-slate-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Brain className="w-5 h-5 text-indigo-400" />
                Hermes Priority Micro-Topics for Today
              </h2>
              <p className="text-xs text-slate-400">
                Selected based on your spaced-repetition decay curve and exam weightage
              </p>
            </div>
            <Link
              to="/student/mentor"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              Open Full Syllabus Tree <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {(
              todayData?.recommended_topics || [
                {
                  topic_id: 'phy_rotational_moi',
                  name: 'Moment of Inertia & Parallel Axis Theorem',
                  subject: 'Physics',
                  chapter: 'Rotational Motion',
                  state: 'IN_PROGRESS',
                  mastery_score: 68,
                },
                {
                  topic_id: 'chem_electro_nernst',
                  name: 'Nernst Equation & Gibbs Free Energy',
                  subject: 'Chemistry',
                  chapter: 'Electrochemistry',
                  state: 'NEEDS_REMEDIATION',
                  mastery_score: 42,
                },
                {
                  topic_id: 'math_calc_definite',
                  name: 'Definite Integration — King’s Property',
                  subject: 'Mathematics',
                  chapter: 'Integral Calculus',
                  state: 'MASTERED',
                  mastery_score: 88,
                },
                {
                  topic_id: 'phy_modern_debroglie',
                  name: 'de Broglie Wavelength & Photoelectric Effect',
                  subject: 'Physics',
                  chapter: 'Modern Physics',
                  state: 'IN_PROGRESS',
                  mastery_score: 74,
                },
              ]
            )
              .slice(0, 4)
              .map((topic: any, idx: number) => (
                <div
                  key={topic.topic_id || idx}
                  className="rounded-xl bg-slate-950/70 border border-slate-800/90 p-4 flex flex-col justify-between hover:border-indigo-500/40 transition-colors"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300">
                        {topic.subject || 'Physics'}
                      </span>
                      <span
                        className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                          topic.state === 'MASTERED'
                            ? 'bg-emerald-500/15 text-emerald-300'
                            : topic.state === 'NEEDS_REMEDIATION'
                            ? 'bg-rose-500/15 text-rose-300'
                            : 'bg-amber-500/15 text-amber-300'
                        }`}
                      >
                        {topic.state || 'IN_PROGRESS'}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-white">{topic.name || topic.title}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">{topic.chapter || 'Core JEE/NEET Module'}</p>
                  </div>

                  <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800/80">
                    <span className="text-xs text-slate-400">
                      Mastery: <strong className="text-white">{topic.mastery_score ?? 65}%</strong>
                    </span>
                    <Link
                      to={`/student/mentor?topic=${encodeURIComponent(topic.topic_id || topic.name)}`}
                      className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
                    >
                      Start Socratic Session →
                    </Link>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Monthly Consistency Heatmap & Daily Goal Editor */}
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Calendar className="w-4 h-4 text-emerald-400" />
                Consistency Heatmap
              </h2>
              <span className="text-xs text-slate-400">
                {heatmap?.month || new Date().getMonth() + 1}/{heatmap?.year || new Date().getFullYear()}
              </span>
            </div>

            <div className="grid grid-cols-7 gap-1.5 my-3">
              {(heatmap?.days || Array.from({ length: 28 }, (_, i) => ({ date: `Day ${i + 1}`, intensity: (i % 4) + 1 }))).map(
                (d: any, idx: number) => {
                  const colors = [
                    'bg-slate-800 text-slate-500',
                    'bg-emerald-950 text-emerald-400 border border-emerald-800/50',
                    'bg-emerald-800/70 text-emerald-200',
                    'bg-emerald-600 text-white',
                    'bg-emerald-400 text-slate-950 font-bold',
                  ];
                  const level = Math.min(4, Math.max(0, d.intensity ?? 0));
                  return (
                    <div
                      key={d.date || idx}
                      title={`${d.date}: ${d.questionsSolved ?? level * 6} Qs solved (${d.minutesSpent ?? level * 20} mins)`}
                      className={`h-7 rounded-md flex items-center justify-center text-[10px] ${colors[level]}`}
                    >
                      {idx + 1}
                    </div>
                  );
                }
              )}
            </div>
          </div>

          {/* Daily Target Editor */}
          <form onSubmit={handleSaveGoal} className="mt-4 pt-4 border-t border-slate-800 space-y-2.5">
            <div className="text-xs font-semibold text-slate-300">Customize Daily Study Target</div>
            <div className="flex gap-2">
              <select
                value={goalType}
                onChange={(e) => setGoalType(e.target.value as 'questions' | 'minutes')}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
              >
                <option value="questions">Questions / Day</option>
                <option value="minutes">Minutes / Day</option>
              </select>
              <input
                type="number"
                min={5}
                max={300}
                value={goalTarget}
                onChange={(e) => setGoalTarget(Number(e.target.value))}
                className="w-20 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
              />
              <button
                type="submit"
                className="flex-1 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg px-3 py-1.5 transition-colors cursor-pointer"
              >
                Save Goal
              </button>
            </div>
            {goalSavedMsg && <p className="text-[11px] text-emerald-400">{goalSavedMsg}</p>}
          </form>
        </div>
      </div>

      {/* Third Row: Weekly Leaderboard & Unlocked Badges */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Weekly League Leaderboard */}
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Trophy className="w-5 h-5 text-amber-400" />
                Weekly {examType.replace('_', ' ')} Scholar League
              </h2>
              <p className="text-xs text-slate-400">Live national XP standings</p>
            </div>
            <span className="px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300 text-xs font-bold">
              Top 1% Tier
            </span>
          </div>

          <div className="space-y-2">
            {(leaderboard?.leaderboard || [
              { rank: 1, name: 'Aarav Sharma (You)', xp: 1450, streak: 14, badge: 'Grandmaster' },
              { rank: 2, name: 'Diya Nair', xp: 1390, streak: 19, badge: 'Scholar' },
              { rank: 3, name: 'Rohan Kulkarni', xp: 1280, streak: 11, badge: 'Scholar' },
              { rank: 4, name: 'Kabir Verma', xp: 1140, streak: 8, badge: 'Rising Star' },
            ]).map((entry: any) => (
              <div
                key={entry.rank}
                className={`flex items-center justify-between p-3 rounded-xl border ${
                  entry.rank === 1
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-slate-950/60 border-slate-800/80'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-black ${
                      entry.rank === 1
                        ? 'bg-amber-400 text-slate-950'
                        : entry.rank === 2
                        ? 'bg-slate-300 text-slate-950'
                        : entry.rank === 3
                        ? 'bg-amber-700 text-white'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {entry.rank}
                  </span>
                  <div>
                    <div className="text-xs font-bold text-white">{entry.name}</div>
                    <div className="text-[11px] text-slate-400">
                      {entry.badge} • {entry.streak}d streak
                    </div>
                  </div>
                </div>
                <div className="text-xs font-extrabold text-indigo-400">{entry.xp} XP</div>
              </div>
            ))}
          </div>
        </div>

        {/* Gamified Achievements & Quick Exam Shortcuts */}
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2 mb-4">
              <Award className="w-5 h-5 text-purple-400" />
              Unlocked Achievements & Badges
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(leaderboard?.unlockedBadges || [
                {
                  id: 'b_streak_7',
                  title: '7-Day Consistency Streak',
                  description: 'Completed Daily Dose 7 days in a row',
                  icon: 'flame',
                },
                {
                  id: 'b_pyq_100',
                  title: 'PYQ Centurion',
                  description: 'Solved 100+ authentic JEE/NEET PYQs',
                  icon: 'trophy',
                },
                {
                  id: 'b_socratic',
                  title: 'First Principles Thinker',
                  description: 'Cleared 5 Hermes Socratic Concept Walls',
                  icon: 'brain',
                },
                {
                  id: 'b_cbt_ace',
                  title: 'NTA CBT Ace',
                  description: 'Scored >98%ile in a full-length mock test',
                  icon: 'award',
                },
              ]).map((b: any) => (
                <div
                  key={b.id}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start gap-2.5"
                >
                  <div className="p-2 rounded-lg bg-purple-500/15 text-purple-300">
                    <Award className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">{b.title}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{b.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-3 gap-2">
            <Link
              to="/student/tests"
              className="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-center text-xs font-semibold text-slate-200 transition-colors"
            >
              Build Custom Test
            </Link>
            <Link
              to="/student/revision"
              className="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-center text-xs font-semibold text-slate-200 transition-colors"
            >
              3D Flashcards
            </Link>
            <Link
              to="/student/tools"
              className="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-center text-xs font-semibold text-slate-200 transition-colors"
            >
              AI Rank Predictor
            </Link>
          </div>
        </div>
      </div>

      {/* Daily Dose 5-Question Sprint Modal */}
      {showDoseModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 max-h-[90vh] overflow-y-auto space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-amber-400" />
                  Daily Dose — 5 High-Yield Questions
                </h3>
                <p className="text-xs text-slate-400">
                  Solve all 5 questions to earn +{dailyDose?.xpReward || 50} XP and update your monthly heatmap.
                </p>
              </div>
              <button
                onClick={() => setShowDoseModal(false)}
                className="text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded-lg bg-slate-800"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              {(dailyDose?.questions || []).map((q: any, i: number) => (
                <div key={q.questionId || i} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-indigo-400">
                      Q{i + 1}. {q.subject} • {q.chapter}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {q.questionType} ({q.difficulty})
                    </span>
                  </div>

                  <div className="text-sm text-slate-100">
                    <LatexRenderer content={q.statement} />
                  </div>

                  {q.questionType === 'MCQ' && q.options ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {q.options.map((opt: any) => {
                        const selected = doseAnswers[q.questionId] === opt.id;
                        return (
                          <button
                            key={opt.id}
                            type="button"
                            onClick={() => setDoseAnswers((prev) => ({ ...prev, [q.questionId]: opt.id }))}
                            className={`text-left p-2.5 rounded-lg border text-xs flex items-center gap-2 transition-colors ${
                              selected
                                ? 'bg-indigo-600/20 border-indigo-500 text-white'
                                : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                            }`}
                          >
                            <span className="font-bold">{opt.id}.</span>
                            <LatexRenderer content={opt.text} />
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <input
                      type="text"
                      placeholder="Enter numerical value..."
                      value={doseAnswers[q.questionId] || ''}
                      onChange={(e) => setDoseAnswers((prev) => ({ ...prev, [q.questionId]: e.target.value }))}
                      className="w-full sm:w-64 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
                    />
                  )}

                  {doseSubmitted && (
                    <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-xs space-y-1">
                      <div className="font-bold text-emerald-300">
                        Correct Answer: {q.correctAnswer}
                      </div>
                      <div className="text-slate-300">
                        <LatexRenderer content={q.solution || 'Verified via NCERT & NTA solution key.'} />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowDoseModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Close
              </button>
              {!doseSubmitted && (
                <button
                  type="button"
                  onClick={handleCompleteDailyDose}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold cursor-pointer"
                >
                  Submit Daily Sprint & Claim +50 XP
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
