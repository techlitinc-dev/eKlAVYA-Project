import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Filter,
  Sparkles,
  Bookmark,
  CheckCircle2,
  XCircle,
  Layers,
  Calculator,
  HelpCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../lib/api';
import { LatexRenderer } from '../../components/LatexRenderer';

export const StudentPyqAndNcert: React.FC = () => {
  const { session } = useAuth();
  const studentId = session?.studentId || 'child_demo_aarav';

  const [activeTab, setActiveTab] = useState<'pyq' | 'ncert'>('pyq');

  // PYQ Filters
  const [examFilter, setExamFilter] = useState<string>('');
  const [subjectFilter, setSubjectFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [zoneFilter, setZoneFilter] = useState<string>('');
  const [questions, setQuestions] = useState<any[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<any>(null);
  const [userAnswer, setUserAnswer] = useState<string>('');
  const [showSolution, setShowSolution] = useState<boolean>(false);

  // Similar Questions & Bookmark State
  const [similarQuestions, setSimilarQuestions] = useState<any[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [bookmarkMsg, setBookmarkMsg] = useState<string>('');

  // NCERT Line-by-Line State
  const [ncertSubject, setNcertSubject] = useState<string>('Biology');
  const [ncertModules, setNcertModules] = useState<any[]>([]);

  const loadQuestions = async () => {
    const params = new URLSearchParams();
    if (examFilter) params.set('exam', examFilter);
    if (subjectFilter) params.set('subject', subjectFilter);
    if (typeFilter) params.set('questionType', typeFilter);
    if (zoneFilter) params.set('zone', zoneFilter);
    params.set('limit', '50');

    try {
      const res = await apiFetch(`/api/cpyqb/questions?${params.toString()}`);
      const list = res?.questions || [];
      setQuestions(list);
      if (list.length > 0 && (!selectedQuestion || !list.some((q: any) => q.questionId === selectedQuestion.questionId))) {
        setSelectedQuestion(list[0]);
        setUserAnswer('');
        setShowSolution(false);
        setSimilarQuestions([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadNcertModules = async (subj: string) => {
    try {
      const res = await apiFetch(`/api/neet/ncert/subject/${encodeURIComponent(subj)}/modules`);
      setNcertModules(res?.modules || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadQuestions();
  }, [examFilter, subjectFilter, typeFilter, zoneFilter]);

  useEffect(() => {
    loadNcertModules(ncertSubject);
  }, [ncertSubject]);

  const handleSelectQuestion = (q: any) => {
    setSelectedQuestion(q);
    setUserAnswer('');
    setShowSolution(false);
    setSimilarQuestions([]);
    setBookmarkMsg('');
  };

  const handleGenerateSimilar = async () => {
    if (!selectedQuestion) return;
    setLoadingSimilar(true);
    try {
      const res = await apiFetch(`/api/ai-hub/qa/generate-similar-questions`, {
        method: 'POST',
        body: JSON.stringify({
          questionId: selectedQuestion.questionId,
          statement: selectedQuestion.statement,
          subject: selectedQuestion.subject,
          chapter: selectedQuestion.chapter,
          difficulty: selectedQuestion.difficulty,
          count: 3,
        }),
      });
      setSimilarQuestions(res?.generatedQuestions || []);
    } finally {
      setLoadingSimilar(false);
    }
  };

  const handleBookmarkQuestion = async () => {
    if (!selectedQuestion) return;
    try {
      const nbRes = await apiFetch(`/api/notebook?studentId=${encodeURIComponent(studentId)}`);
      const defaultNotebookId = nbRes?.notebooks?.[0]?.notebookId || 'nb_default_physics';
      await apiFetch(`/api/notebook/question`, {
        method: 'POST',
        body: JSON.stringify({
          studentId,
          notebookId: defaultNotebookId,
          questionId: selectedQuestion.questionId,
          personalNote: `Saved from ${selectedQuestion.exam} (${selectedQuestion.year}) — ${selectedQuestion.chapter}`,
        }),
      });
      setBookmarkMsg('Saved to Smart Notebook!');
      setTimeout(() => setBookmarkMsg(''), 3000);
    } catch (err: any) {
      setBookmarkMsg(err.message || 'Already bookmarked');
    }
  };

  const isAnswerCorrect =
    selectedQuestion &&
    userAnswer.trim() !== '' &&
    userAnswer.trim().toUpperCase() === String(selectedQuestion.correctAnswer).trim().toUpperCase();

  return (
    <div className="space-y-6">
      {/* Header & Tab Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-indigo-400" />
            Chapter-wise PYQ Bank & NCERT Line-by-Line
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Authentic JEE Main, JEE Advanced & NEET-UG previous year questions with KaTeX solutions and NCERT page mapping
          </p>
        </div>

        <div className="flex gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('pyq')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
              activeTab === 'pyq' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            PYQ Question Bank ({questions.length})
          </button>
          <button
            onClick={() => setActiveTab('ncert')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
              activeTab === 'ncert' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            NEET NCERT Line-by-Line
          </button>
        </div>
      </div>

      {activeTab === 'pyq' ? (
        <>
          {/* Filter Bar */}
          <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300">
              <Filter className="w-4 h-4 text-indigo-400" /> Filters:
            </div>

            <select
              value={examFilter}
              onChange={(e) => setExamFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white"
            >
              <option value="">All Exams (JEE Main / Adv / NEET)</option>
              <option value="JEE_MAIN">JEE Main</option>
              <option value="JEE_ADVANCED">JEE Advanced</option>
              <option value="NEET">NEET-UG</option>
            </select>

            <select
              value={subjectFilter}
              onChange={(e) => setSubjectFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white"
            >
              <option value="">All Subjects</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
              <option value="Mathematics">Mathematics</option>
              <option value="Biology">Biology</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white"
            >
              <option value="">All Types (MCQ + NAT)</option>
              <option value="MCQ">Single Choice MCQ</option>
              <option value="NAT">Numerical Value (NAT)</option>
            </select>

            <select
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white"
            >
              <option value="">All Revision Zones</option>
              <option value="high_yield">High-Yield Zone</option>
              <option value="must_revise">Must-Revise Zone</option>
              <option value="trap_zone">Common Trap Zone</option>
            </select>
          </div>

          {/* Main Split View: Question List + Interactive Solver Workspace */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left List */}
            <div className="lg:col-span-5 rounded-2xl bg-slate-900 border border-slate-800 p-4 max-h-[75vh] overflow-y-auto space-y-2.5">
              {questions.map((q: any) => {
                const active = selectedQuestion?.questionId === q.questionId;
                return (
                  <button
                    key={q.questionId}
                    onClick={() => handleSelectQuestion(q)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                      active
                        ? 'bg-indigo-600/20 border-indigo-500 text-white'
                        : 'bg-slate-950/70 border-slate-800/80 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 text-[11px] mb-1">
                      <span className="font-bold text-indigo-400">
                        {q.exam} {q.year} • {q.subject}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                        {q.questionType} • {q.difficulty}
                      </span>
                    </div>
                    <div className="text-xs font-bold text-white mb-1">{q.chapter}</div>
                    <div className="text-xs text-slate-400 line-clamp-2">
                      <LatexRenderer content={q.statement} />
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Right Interactive Problem Workspace */}
            <div className="lg:col-span-7 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5">
              {selectedQuestion ? (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-4">
                    <div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold">
                          {selectedQuestion.exam} {selectedQuestion.year}
                        </span>
                        <span className="text-slate-400">
                          {selectedQuestion.subject} → {selectedQuestion.chapter}
                        </span>
                      </div>
                      <h2 className="text-sm font-bold text-white mt-1">
                        Topic: {selectedQuestion.topic} (NCERT Ref: {selectedQuestion.ncertReference || 'Standard'})
                      </h2>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleBookmarkQuestion}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                      >
                        <Bookmark className="w-3.5 h-3.5 text-amber-400" /> Bookmark
                      </button>
                      <button
                        onClick={handleGenerateSimilar}
                        disabled={loadingSimilar}
                        className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        {loadingSimilar ? 'Generating...' : '3 Similar Questions'}
                      </button>
                    </div>
                  </div>

                  {bookmarkMsg && (
                    <div className="text-xs text-emerald-400 font-semibold">{bookmarkMsg}</div>
                  )}

                  {/* Question Statement */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 leading-relaxed">
                    <LatexRenderer content={selectedQuestion.statement} />
                  </div>

                  {/* MCQ Options or Virtual Numeric Keypad (NAT) */}
                  {selectedQuestion.questionType === 'MCQ' && selectedQuestion.options ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {selectedQuestion.options.map((opt: any) => {
                        const chosen = userAnswer === opt.id;
                        return (
                          <button
                            key={opt.id}
                            onClick={() => setUserAnswer(opt.id)}
                            className={`text-left p-3.5 rounded-xl border text-xs flex items-center gap-2.5 transition-all cursor-pointer ${
                              chosen
                                ? 'bg-indigo-600/25 border-indigo-500 text-white'
                                : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                            }`}
                          >
                            <span className="w-6 h-6 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-white">
                              {opt.id}
                            </span>
                            <LatexRenderer content={opt.text} />
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-amber-400">
                        <Calculator className="w-4 h-4" /> NTA Virtual Numerical Value (NAT) Keypad
                      </div>
                      <input
                        type="text"
                        value={userAnswer}
                        onChange={(e) => setUserAnswer(e.target.value)}
                        placeholder="Type or click numeric keypad..."
                        className="w-full sm:w-64 bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-sm font-mono text-white"
                      />
                      <div className="flex flex-wrap gap-1.5 max-w-xs">
                        {['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.', '-'].map((digit) => (
                          <button
                            key={digit}
                            type="button"
                            onClick={() => setUserAnswer((prev) => prev + digit)}
                            className="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold cursor-pointer"
                          >
                            {digit}
                          </button>
                        ))}
                        <button
                          type="button"
                          onClick={() => setUserAnswer('')}
                          className="px-3 h-9 rounded-lg bg-rose-900/50 hover:bg-rose-800 text-rose-200 text-xs font-bold cursor-pointer"
                        >
                          Clear
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Check Answer & Step-by-Step Solution */}
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setShowSolution(true)}
                      className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold cursor-pointer"
                    >
                      Verify Answer & View Step-by-Step Solution
                    </button>
                  </div>

                  {showSolution && (
                    <div
                      className={`p-4 rounded-xl border text-xs space-y-2 ${
                        isAnswerCorrect
                          ? 'bg-emerald-950/40 border-emerald-500/40'
                          : 'bg-indigo-950/40 border-indigo-500/40'
                      }`}
                    >
                      <div className="flex items-center gap-2 font-bold">
                        {isAnswerCorrect ? (
                          <span className="text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4" /> Spot On! Correct Answer: {selectedQuestion.correctAnswer}
                          </span>
                        ) : (
                          <span className="text-amber-300 flex items-center gap-1">
                            <XCircle className="w-4 h-4" /> Official NTA Key: {selectedQuestion.correctAnswer} (Your input: {userAnswer || 'None'})
                          </span>
                        )}
                      </div>
                      <div className="text-slate-200 leading-relaxed pt-1">
                        <LatexRenderer content={selectedQuestion.solution} />
                      </div>
                    </div>
                  )}

                  {/* 3 AI Similar Questions Drawer */}
                  {similarQuestions.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-950 border border-indigo-500/30 space-y-3">
                      <div className="text-xs font-bold text-indigo-400 flex items-center gap-1.5">
                        <Sparkles className="w-4 h-4" /> 3 AI-Generated Twin Practice Questions
                      </div>
                      <div className="space-y-2.5">
                        {similarQuestions.map((sq: any, idx: number) => (
                          <div key={sq.questionId || idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
                            <div className="font-semibold text-white">
                              Twin Q{idx + 1} ({sq.difficulty}):
                            </div>
                            <div className="text-slate-300">
                              <LatexRenderer content={sq.statement} />
                            </div>
                            <div className="text-[11px] text-emerald-400 pt-1">
                              Answer: {sq.correctAnswer} — <LatexRenderer content={sq.hint || sq.solution || ''} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-xs text-slate-400">Select a question on the left to begin solving.</div>
              )}
            </div>
          </div>
        </>
      ) : (
        /* NEET NCERT Line-by-Line Module Explorer */
        <div className="space-y-4">
          <div className="flex gap-2">
            {['Biology', 'Chemistry', 'Physics'].map((subj) => (
              <button
                key={subj}
                onClick={() => setNcertSubject(subj)}
                className={`px-4 py-2 rounded-xl text-xs font-bold cursor-pointer ${
                  ncertSubject === subj
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                NCERT {subj}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ncertModules.map((mod: any) => (
              <div
                key={mod.moduleId}
                className="rounded-2xl bg-slate-900 border border-slate-800 p-5 space-y-3"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">
                    {mod.ncertPageRange || 'NCERT Core'}
                  </span>
                  <span className="text-slate-400">{mod.subject}</span>
                </div>
                <h3 className="text-base font-bold text-white">{mod.chapter}</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  <LatexRenderer content={mod.summary || mod.keyTakeaway || 'Direct NCERT line-by-line assertion & reason coverage.'} />
                </p>
                {mod.assertionReasonExamples && (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                    <div className="font-bold text-amber-400 flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5" /> High-Yield Assertion-Reason Highlight:
                    </div>
                    <div className="text-slate-300">
                      <LatexRenderer content={mod.assertionReasonExamples[0]} />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
