import React, { useEffect, useState } from 'react';
import {
  ClipboardList,
  Play,
  Clock,
  CheckCircle2,
  BarChart3,
  KeyRound,
  Award,
  Sparkles,
  Flag,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../lib/api';
import { LatexRenderer } from '../../components/LatexRenderer';

export const StudentTestsAndCbt: React.FC = () => {
  const { session } = useAuth();
  const studentId = session?.studentId || 'child_demo_aarav';
  const examType = session?.examType || 'JEE_MAIN';

  const [activeTab, setActiveTab] = useState<'builder' | 'cbt' | 'analysis' | 'assignment'>('builder');

  // Step 1 & 2 Custom Test Builder State
  const [selectedExam, setSelectedExam] = useState<string>(examType);
  const [selectedSubjects, setSelectedSubjects] = useState<string[]>(['Physics', 'Chemistry', 'Mathematics']);
  const [difficulty, setDifficulty] = useState<string>('MEDIUM');
  const [questionCount, setQuestionCount] = useState<number>(6);
  const [durationMinutes, setDurationMinutes] = useState<number>(20);
  const [generating, setGenerating] = useState<boolean>(false);

  // Active CBT Exam State
  const [activeTest, setActiveTest] = useState<any>(null);
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [markedReview, setMarkedReview] = useState<Record<string, boolean>>({});
  const [visited, setVisited] = useState<Record<string, boolean>>({});
  const [secondsLeft, setSecondsLeft] = useState<number>(1200);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [analysisData, setAnalysisData] = useState<any>(null);

  // Classroom Homework Assignment Join State
  const [joinCode, setJoinCode] = useState<string>('6X9A21');
  const [assignment, setAssignment] = useState<any>(null);
  const [hwAnswers, setHwAnswers] = useState<Record<string, string>>({});
  const [hwSubmittedResult, setHwSubmittedResult] = useState<any>(null);

  // Timer countdown when CBT is active
  useEffect(() => {
    if (activeTab !== 'cbt' || !activeTest) return;
    const timer = setInterval(() => {
      setSecondsLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [activeTab, activeTest]);

  const handleToggleSubject = (subj: string) => {
    setSelectedSubjects((prev) =>
      prev.includes(subj) ? prev.filter((s) => s !== subj) : [...prev, subj]
    );
  };

  const handleGenerateTest = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const res = await apiFetch(`/api/custom-test/generate`, {
        method: 'POST',
        body: JSON.stringify({
          studentId,
          exam: selectedExam,
          subjects: selectedSubjects.length > 0 ? selectedSubjects : ['Physics'],
          chapters: [],
          difficulty,
          questionCount: Number(questionCount),
          durationMinutes: Number(durationMinutes),
          includeNAT: true,
        }),
      });
      setActiveTest(res);
      setCurrentIdx(0);
      setAnswers({});
      setMarkedReview({});
      if (res?.questions?.[0]?.questionId) {
        setVisited({ [res.questions[0].questionId]: true });
      }
      setSecondsLeft((res?.durationMinutes || durationMinutes) * 60);
      setActiveTab('cbt');
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleSelectCbtQuestion = (idx: number) => {
    setCurrentIdx(idx);
    const qId = activeTest?.questions?.[idx]?.questionId;
    if (qId) {
      setVisited((prev) => ({ ...prev, [qId]: true }));
    }
  };

  const handleSubmitCbt = async () => {
    if (!activeTest) return;
    setSubmitting(true);
    try {
      const payloadResponses = (activeTest.questions || []).map((q: any) => ({
        questionId: q.questionId,
        selectedAnswer: answers[q.questionId] || null,
        timeSpentSeconds: 48,
      }));
      await apiFetch(`/api/custom-test/submit`, {
        method: 'POST',
        body: JSON.stringify({
          testId: activeTest.testId,
          studentId,
          responses: payloadResponses,
        }),
      });
      const analysis = await apiFetch(`/api/custom-test/analysis/${encodeURIComponent(activeTest.testId)}`);
      setAnalysisData(analysis);
      setActiveTab('analysis');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleLoadAssignment = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      const res = await apiFetch(`/api/assignment/student/id/${encodeURIComponent(joinCode.trim().toUpperCase())}`);
      setAssignment(res);
      setHwAnswers({});
      setHwSubmittedResult(null);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    handleLoadAssignment();
  }, []);

  const handleSubmitAssignment = async () => {
    if (!assignment) return;
    const res = await apiFetch(
      `/api/assignment/student/id/${encodeURIComponent(assignment.joinCode)}/submit`,
      {
        method: 'POST',
        body: JSON.stringify({
          studentId,
          studentName: session?.name || 'Aarav Sharma',
          answers: hwAnswers,
          timeSpentSeconds: 320,
        }),
      }
    );
    setHwSubmittedResult(res);
  };

  const formatClock = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const currentQuestion = activeTest?.questions?.[currentIdx];

  return (
    <div className="space-y-6">
      {/* Top Sub-Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <ClipboardList className="w-6 h-6 text-indigo-400" />
            Custom Test Generator, NTA CBT Simulator & Classroom Assignments
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Build multi-chapter mocks, practice in an authentic NTA 4-state palette simulator, or join a teacher assignment code
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('builder')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'builder' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            1. Custom Test Builder
          </button>
          <button
            onClick={() => setActiveTab('cbt')}
            disabled={!activeTest}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'cbt'
                ? 'bg-emerald-600 text-white'
                : activeTest
                ? 'text-slate-300 hover:text-white'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            2. Live NTA CBT Simulator
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            disabled={!analysisData}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'analysis'
                ? 'bg-purple-600 text-white'
                : analysisData
                ? 'text-slate-300 hover:text-white'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            3. Diagnostic Report Card
          </button>
          <button
            onClick={() => setActiveTab('assignment')}
            className={`px-3.5 py-2 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'assignment' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            4. Join Homework Code ({joinCode})
          </button>
        </div>
      </div>

      {/* TAB 1: 2-Step Custom Test Generator Wizard */}
      {activeTab === 'builder' && (
        <form
          onSubmit={handleGenerateTest}
          className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-6 max-w-4xl"
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                2-Step Custom Mock Wizard
              </span>
              <h2 className="text-lg font-bold text-white mt-0.5">
                Configure Target Exam, Subjects & Difficulty Mix
              </h2>
            </div>
            <Sparkles className="w-6 h-6 text-indigo-400" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Step 1: Exam & Subjects */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-2">
                  Step 1A: Select Target Examination Pattern
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['JEE_MAIN', 'JEE_ADVANCED', 'NEET'].map((ex) => (
                    <button
                      type="button"
                      key={ex}
                      onClick={() => {
                        setSelectedExam(ex);
                        setSelectedSubjects(
                          ex === 'NEET'
                            ? ['Biology', 'Chemistry', 'Physics']
                            : ['Physics', 'Chemistry', 'Mathematics']
                        );
                      }}
                      className={`py-2.5 px-3 rounded-xl border text-xs font-bold cursor-pointer ${
                        selectedExam === ex
                          ? 'bg-indigo-600/25 border-indigo-500 text-white'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                      }`}
                    >
                      {ex.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-2">
                  Step 1B: Include Subjects (+4 / -1 NTA Marking)
                </label>
                <div className="flex flex-wrap gap-2">
                  {['Physics', 'Chemistry', 'Mathematics', 'Biology'].map((subj) => {
                    const checked = selectedSubjects.includes(subj);
                    return (
                      <button
                        type="button"
                        key={subj}
                        onClick={() => handleToggleSubject(subj)}
                        className={`px-3.5 py-2 rounded-xl border text-xs font-semibold cursor-pointer ${
                          checked
                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200'
                            : 'bg-slate-950 border-slate-800 text-slate-400'
                        }`}
                      >
                        {checked ? '✓ ' : '+ '}
                        {subj}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Step 2: Difficulty, Count & Duration */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-2">
                  Step 2A: Difficulty Distribution
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['EASY', 'MEDIUM', 'HARD'].map((diff) => (
                    <button
                      type="button"
                      key={diff}
                      onClick={() => setDifficulty(diff)}
                      className={`py-2 px-3 rounded-xl border text-xs font-bold cursor-pointer ${
                        difficulty === diff
                          ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                      }`}
                    >
                      {diff}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Number of Questions
                  </label>
                  <input
                    type="number"
                    min={3}
                    max={30}
                    value={questionCount}
                    onChange={(e) => setQuestionCount(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    min={5}
                    max={180}
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex justify-end">
            <button
              type="submit"
              disabled={generating}
              className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-extrabold flex items-center gap-2 cursor-pointer"
            >
              <Play className="w-4 h-4 fill-white" />
              {generating ? 'Assembling Authentic NTA Paper...' : 'Launch Fullscreen NTA CBT Exam'}
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: Live NTA CBT Exam Interface */}
      {activeTab === 'cbt' && activeTest && currentQuestion && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left 8 Cols: Active Question Canvas */}
          <div className="lg:col-span-8 rounded-2xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between min-h-[68vh]">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-4">
                <div>
                  <span className="text-xs font-bold text-indigo-400">
                    Question {currentIdx + 1} of {activeTest.questions.length} • {currentQuestion.subject}
                  </span>
                  <h3 className="text-sm font-bold text-white mt-0.5">
                    {currentQuestion.chapter} ({currentQuestion.questionType} • +4 / -1 Marks)
                  </h3>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs font-mono font-bold">
                  <Clock className="w-4 h-4" /> {formatClock(secondsLeft)}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 leading-relaxed">
                <LatexRenderer content={currentQuestion.statement} />
              </div>

              {currentQuestion.questionType === 'MCQ' && currentQuestion.options ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {currentQuestion.options.map((opt: any) => {
                    const selected = answers[currentQuestion.questionId] === opt.id;
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() =>
                          setAnswers((prev) => ({ ...prev, [currentQuestion.questionId]: opt.id }))
                        }
                        className={`text-left p-3.5 rounded-xl border text-xs flex items-center gap-2.5 cursor-pointer ${
                          selected
                            ? 'bg-emerald-600/25 border-emerald-500 text-white'
                            : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        <span className="w-6 h-6 rounded-lg bg-slate-800 flex items-center justify-center font-bold">
                          {opt.id}
                        </span>
                        <LatexRenderer content={opt.text} />
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-amber-300">
                    Numerical Value Answer (NAT):
                  </label>
                  <input
                    type="text"
                    value={answers[currentQuestion.questionId] || ''}
                    onChange={(e) =>
                      setAnswers((prev) => ({
                        ...prev,
                        [currentQuestion.questionId]: e.target.value,
                      }))
                    }
                    placeholder="Enter numeric value..."
                    className="w-64 bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white"
                  />
                </div>
              )}
            </div>

            {/* Bottom CBT Control Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800 mt-6">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setMarkedReview((prev) => ({
                      ...prev,
                      [currentQuestion.questionId]: !prev[currentQuestion.questionId],
                    }))
                  }
                  className="px-3.5 py-2 rounded-xl bg-purple-600/20 border border-purple-500/40 text-purple-300 text-xs font-bold flex items-center gap-1.5 cursor-pointer"
                >
                  <Flag className="w-3.5 h-3.5" />
                  {markedReview[currentQuestion.questionId] ? 'Unmark Review' : 'Mark for Review'}
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setAnswers((prev) => {
                      const next = { ...prev };
                      delete next[currentQuestion.questionId];
                      return next;
                    })
                  }
                  className="px-3.5 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold cursor-pointer"
                >
                  Clear Response
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={currentIdx === 0}
                  onClick={() => handleSelectCbtQuestion(currentIdx - 1)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-white text-xs font-bold disabled:opacity-40 cursor-pointer"
                >
                  ← Previous
                </button>
                {currentIdx < activeTest.questions.length - 1 ? (
                  <button
                    type="button"
                    onClick={() => handleSelectCbtQuestion(currentIdx + 1)}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold cursor-pointer"
                  >
                    Save & Next →
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSubmitCbt}
                    disabled={submitting}
                    className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold cursor-pointer"
                  >
                    {submitting ? 'Grading...' : 'Submit Final Paper'}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Right 4 Cols: Authentic NTA 4-State Question Palette */}
          <div className="lg:col-span-4 rounded-2xl bg-slate-900 border border-slate-800 p-5 flex flex-col justify-between">
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white">NTA Question Palette</h3>
              <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded bg-emerald-600 inline-block" /> Answered
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded bg-rose-600 inline-block" /> Visited / Unanswered
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded bg-purple-600 inline-block" /> Marked for Review
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 rounded bg-slate-800 inline-block" /> Not Visited
                </div>
              </div>

              <div className="grid grid-cols-5 gap-2 pt-2">
                {activeTest.questions.map((q: any, i: number) => {
                  const hasAns = Boolean(answers[q.questionId]);
                  const isRev = Boolean(markedReview[q.questionId]);
                  const isVis = Boolean(visited[q.questionId]);

                  let badgeStyle = 'bg-slate-800 text-slate-400';
                  if (isRev) badgeStyle = 'bg-purple-600 text-white';
                  else if (hasAns) badgeStyle = 'bg-emerald-600 text-white';
                  else if (isVis) badgeStyle = 'bg-rose-600/80 text-white';

                  return (
                    <button
                      key={q.questionId}
                      type="button"
                      onClick={() => handleSelectCbtQuestion(i)}
                      className={`h-10 rounded-xl font-bold text-xs transition-all cursor-pointer ${badgeStyle} ${
                        currentIdx === i ? 'ring-2 ring-white' : ''
                      }`}
                    >
                      {i + 1}
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              type="button"
              onClick={handleSubmitCbt}
              disabled={submitting}
              className="w-full mt-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold cursor-pointer"
            >
              {submitting ? 'Submitting CBT...' : 'Submit Exam & Generate Diagnostic Report'}
            </button>
          </div>
        </div>
      )}

      {/* TAB 3: Post-Test Diagnostic Report Card & Topper Comparison */}
      {activeTab === 'analysis' && analysisData && (
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-bold text-emerald-400">Official NTA CBT Post-Test Analysis</span>
              <h2 className="text-xl font-extrabold text-white">
                Score: {analysisData.totalScore} / {analysisData.maxScore} • Accuracy: {analysisData.accuracy}%
              </h2>
            </div>
            <div className="px-4 py-2 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-bold">
              Estimated Percentile: {analysisData.estimatedPercentile || 98.4}%ile
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs text-slate-400">Your Score vs Topper Score</div>
              <div className="text-lg font-black text-white mt-1">
                {analysisData.totalScore} vs {analysisData.topperComparison?.topperScore || analysisData.maxScore}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs text-slate-400">Avg Time / Question</div>
              <div className="text-lg font-black text-white mt-1">
                {analysisData.topperComparison?.studentAvgTimeSeconds || 48}s (Topper: 36s)
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs text-slate-400">Auto-Logged Mistakes</div>
              <div className="text-lg font-black text-emerald-400 mt-1">
                Synced to Error Notebook
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Classroom Homework Assignment Joiner (`6X9A21`) */}
      {activeTab === 'assignment' && (
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5">
          <form onSubmit={handleLoadAssignment} className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
              <KeyRound className="w-4 h-4" /> Enter 6-Character Teacher Assignment Code:
            </div>
            <input
              type="text"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              className="w-36 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono font-bold text-white uppercase"
            />
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold cursor-pointer"
            >
              Load Assignment
            </button>
          </form>

          {assignment && (
            <div className="space-y-4 pt-3 border-t border-slate-800">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-base font-bold text-white">{assignment.title}</h3>
                  <p className="text-xs text-slate-400">
                    Assigned by {assignment.teacherName} • Join Code: <strong className="text-amber-400">{assignment.joinCode}</strong>
                  </p>
                </div>
                <span className="text-xs text-slate-400">
                  {(assignment.questions || []).length} Questions
                </span>
              </div>

              <div className="space-y-3">
                {(assignment.questions || []).map((q: any, i: number) => (
                  <div key={q.questionId} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5">
                    <div className="text-xs font-bold text-indigo-400">
                      Q{i + 1}. {q.subject} • {q.chapter} ({q.questionType})
                    </div>
                    <div className="text-sm text-slate-100">
                      <LatexRenderer content={q.statement} />
                    </div>
                    {q.questionType === 'MCQ' && q.options ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {q.options.map((opt: any) => (
                          <button
                            key={opt.id}
                            type="button"
                            onClick={() => setHwAnswers((prev) => ({ ...prev, [q.questionId]: opt.id }))}
                            className={`text-left p-2.5 rounded-lg border text-xs flex items-center gap-2 cursor-pointer ${
                              hwAnswers[q.questionId] === opt.id
                                ? 'bg-amber-500/20 border-amber-500 text-white'
                                : 'bg-slate-900 border-slate-800 text-slate-300'
                            }`}
                          >
                            <span className="font-bold">{opt.id}.</span>
                            <LatexRenderer content={opt.text} />
                          </button>
                        ))}
                      </div>
                    ) : (
                      <input
                        type="text"
                        placeholder="Numerical answer..."
                        value={hwAnswers[q.questionId] || ''}
                        onChange={(e) => setHwAnswers((prev) => ({ ...prev, [q.questionId]: e.target.value }))}
                        className="w-56 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white"
                      />
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between pt-3">
                <button
                  type="button"
                  onClick={handleSubmitAssignment}
                  className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold cursor-pointer"
                >
                  Submit Homework to Teacher Portal
                </button>
                {hwSubmittedResult && (
                  <div className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    <Award className="w-4 h-4" />
                    Submitted! Score: {hwSubmittedResult.score} / {hwSubmittedResult.maxScore} ({hwSubmittedResult.accuracy}%)
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
