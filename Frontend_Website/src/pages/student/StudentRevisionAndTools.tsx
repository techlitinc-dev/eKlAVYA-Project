import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Layers,
  BookMarked,
  AlertOctagon,
  TrendingUp,
  Building2,
  ScanLine,
  RotateCw,
  CheckCircle2,
  Plus,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiFetch } from '../../lib/api';
import { LatexRenderer } from '../../components/LatexRenderer';

export const StudentRevisionAndTools: React.FC = () => {
  const { session } = useAuth();
  const location = useLocation();
  const studentId = session?.studentId || 'child_demo_aarav';

  const isToolsRoute = location.pathname.includes('/tools');
  const [activeTab, setActiveTab] = useState<
    'flashcards' | 'notebooks' | 'errors' | 'predictor' | 'colleges' | 'omr'
  >(isToolsRoute ? 'predictor' : 'flashcards');

  useEffect(() => {
    setActiveTab(isToolsRoute ? 'predictor' : 'flashcards');
  }, [isToolsRoute]);

  // 3D Flashcards State
  const [fcSubject, setFcSubject] = useState<string>('Physics');
  const [fcChapter, setFcChapter] = useState<string>('all');
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [flippedCardIds, setFlippedCardIds] = useState<Record<string, boolean>>({});
  const [masteryStatus, setMasteryStatus] = useState<Record<string, string>>({});

  // Smart Notebooks & Error Notebook State
  const [notebooks, setNotebooks] = useState<any[]>([]);
  const [newNotebookTitle, setNewNotebookTitle] = useState<string>('');
  const [errorsList, setErrorsList] = useState<any[]>([]);

  // AI Rank Predictor State
  const [predExam, setPredExam] = useState<string>('JEE_MAIN');
  const [predScore, setPredScore] = useState<number>(218);
  const [predMaxScore, setPredMaxScore] = useState<number>(300);
  const [predCategory, setPredCategory] = useState<string>('GEN');
  const [predResult, setPredResult] = useState<any>(null);

  // College Cutoffs State
  const [collegeExam, setCollegeExam] = useState<string>('');
  const [colleges, setColleges] = useState<any[]>([]);

  // Physical OMR Grader State
  const [omrSheetText, setOmrSheetText] = useState<string>('1:A, 2:C, 3:B, 4:D, 5:A');
  const [omrKeyText, setOmrKeyText] = useState<string>('1:A, 2:B, 3:B, 4:D, 5:A');
  const [omrResult, setOmrResult] = useState<any>(null);

  const loadFlashcards = async () => {
    try {
      const res = await apiFetch(
        `/api/rfc/subject/${encodeURIComponent(fcSubject)}/chapter/${encodeURIComponent(fcChapter)}/cards`
      );
      setFlashcards(res?.cards || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadNotebooksAndErrors = async () => {
    try {
      const [nbRes, errRes] = await Promise.all([
        apiFetch(`/api/notebook?studentId=${encodeURIComponent(studentId)}`),
        apiFetch(`/api/notebook/errors?studentId=${encodeURIComponent(studentId)}`),
      ]);
      setNotebooks(nbRes?.notebooks || []);
      setErrorsList(errRes?.errors || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadColleges = async () => {
    try {
      const q = collegeExam ? `?exam=${encodeURIComponent(collegeExam)}` : '';
      const res = await apiFetch(`/api/ai-hub/colleges/cutoffs${q}`);
      setColleges(res?.colleges || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadFlashcards();
  }, [fcSubject, fcChapter]);

  useEffect(() => {
    loadNotebooksAndErrors();
  }, [studentId]);

  useEffect(() => {
    loadColleges();
  }, [collegeExam]);

  const handleMarkFlashcard = async (cardId: string, status: 'KNOWN' | 'REVIEW_AGAIN') => {
    setMasteryStatus((prev) => ({ ...prev, [cardId]: status }));
    try {
      await apiFetch(`/api/rfc/mastery`, {
        method: 'POST',
        body: JSON.stringify({ studentId, cardId, status }),
      });
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateNotebook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNotebookTitle.trim()) return;
    await apiFetch(`/api/notebook`, {
      method: 'POST',
      body: JSON.stringify({
        studentId,
        title: newNotebookTitle.trim(),
        subject: 'Physics',
        colorHex: '#6366F1',
      }),
    });
    setNewNotebookTitle('');
    loadNotebooksAndErrors();
  };

  const handleResolveError = async (errorId: string) => {
    await apiFetch(
      `/api/notebook/errors/${encodeURIComponent(errorId)}/resolve?studentId=${encodeURIComponent(studentId)}`,
      { method: 'POST' }
    );
    loadNotebooksAndErrors();
  };

  const handlePredictRank = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch(`/api/ai-hub/rank/predict`, {
      method: 'POST',
      body: JSON.stringify({
        exam: predExam,
        expectedScore: Number(predScore),
        maxScore: Number(predMaxScore),
        category: predCategory,
        homeState: 'Maharashtra',
      }),
    });
    setPredResult(res);
  };

  const parsePairString = (raw: string) => {
    const out: Record<string, string> = {};
    raw.split(',').forEach((part) => {
      const [k, v] = part.split(':').map((s) => s.trim());
      if (k && v) out[k] = v.toUpperCase();
    });
    return out;
  };

  const handleEvaluateOmr = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch(`/api/ai-hub/omr/evaluate`, {
      method: 'POST',
      body: JSON.stringify({
        studentId,
        exam: 'JEE_MAIN',
        detectedBubbles: parsePairString(omrSheetText),
        answerKey: parsePairString(omrKeyText),
      }),
    });
    setOmrResult(res);
  };

  return (
    <div className="space-y-6">
      {/* Header & 6-Tab Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-indigo-400" />
            3D Flashcards, Smart & Error Notebooks, Rank Predictor & OMR Tools
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Active spaced-repetition flashcards, automated mistake ledger, JoSAA/MCC cutoff intelligence, and physical OMR sheet grader
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('flashcards')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'flashcards' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            3D Flashcards ({flashcards.length})
          </button>
          <button
            onClick={() => setActiveTab('notebooks')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'notebooks' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Smart Notebooks ({notebooks.length})
          </button>
          <button
            onClick={() => setActiveTab('errors')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'errors' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Error Notebook ({errorsList.length})
          </button>
          <button
            onClick={() => setActiveTab('predictor')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'predictor' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            AI Rank Predictor
          </button>
          <button
            onClick={() => setActiveTab('colleges')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'colleges' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            IIT/NIT/AIIMS Cutoffs
          </button>
          <button
            onClick={() => setActiveTab('omr')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
              activeTab === 'omr' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            OMR Sheet Grader
          </button>
        </div>
      </div>

      {/* TAB 1: Interactive 3D Flip Revision Flashcards */}
      {activeTab === 'flashcards' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {['Physics', 'Chemistry', 'Mathematics', 'Biology'].map((subj) => (
              <button
                key={subj}
                onClick={() => setFcSubject(subj)}
                className={`px-4 py-2 rounded-xl text-xs font-bold cursor-pointer ${
                  fcSubject === subj
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {subj} Deck
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {flashcards.map((card: any) => {
              const isFlipped = Boolean(flippedCardIds[card.cardId]);
              const status = masteryStatus[card.cardId];
              return (
                <div
                  key={card.cardId}
                  className="rounded-2xl bg-slate-900 border border-slate-800 p-5 flex flex-col justify-between min-h-[240px]"
                >
                  <div>
                    <div className="flex items-center justify-between text-[11px] mb-3">
                      <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold">
                        {card.subject} • {card.chapter}
                      </span>
                      <button
                        type="button"
                        onClick={() =>
                          setFlippedCardIds((prev) => ({ ...prev, [card.cardId]: !prev[card.cardId] }))
                        }
                        className="text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer"
                      >
                        <RotateCw className="w-3.5 h-3.5" /> Flip Card
                      </button>
                    </div>

                    <div
                      onClick={() =>
                        setFlippedCardIds((prev) => ({ ...prev, [card.cardId]: !prev[card.cardId] }))
                      }
                      className={`p-4 rounded-xl border cursor-pointer transition-all min-h-[115px] flex flex-col justify-center ${
                        isFlipped
                          ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-100'
                          : 'bg-slate-950 border-slate-800 text-white'
                      }`}
                    >
                      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                        {isFlipped ? 'Back (Formula / Derivation)' : 'Front (Concept Prompt — Click to Flip)'}
                      </div>
                      <div className="text-sm leading-relaxed">
                        <LatexRenderer content={isFlipped ? card.back : card.front} />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-4 mt-3 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => handleMarkFlashcard(card.cardId, 'KNOWN')}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
                        status === 'KNOWN'
                          ? 'bg-emerald-600 text-white'
                          : 'bg-slate-800 text-emerald-400 hover:bg-slate-700'
                      }`}
                    >
                      ✓ Got It (Known)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleMarkFlashcard(card.cardId, 'REVIEW_AGAIN')}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
                        status === 'REVIEW_AGAIN'
                          ? 'bg-amber-600 text-white'
                          : 'bg-slate-800 text-amber-400 hover:bg-slate-700'
                      }`}
                    >
                      ↻ Review Again
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: Smart Notebooks */}
      {activeTab === 'notebooks' && (
        <div className="space-y-5">
          <form onSubmit={handleCreateNotebook} className="flex flex-wrap gap-2 max-w-lg">
            <input
              type="text"
              value={newNotebookTitle}
              onChange={(e) => setNewNotebookTitle(e.target.value)}
              placeholder="Create custom Smart Notebook (e.g., Organic Named Reactions)..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white"
            />
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1 cursor-pointer"
            >
              <Plus className="w-4 h-4" /> Create Notebook
            </button>
          </form>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {notebooks.map((nb: any) => (
              <div key={nb.notebookId} className="rounded-2xl bg-slate-900 border border-slate-800 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <BookMarked className="w-4 h-4 text-indigo-400" />
                    {nb.title}
                  </h3>
                  <span className="text-xs text-slate-400">
                    {(nb.savedQuestions || []).length} Saved Questions
                  </span>
                </div>

                <div className="space-y-2">
                  {(nb.savedQuestions || []).map((sq: any) => (
                    <div key={sq.questionId} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                      <div className="font-bold text-indigo-400">
                        {sq.question?.subject || 'PYQ'} • {sq.question?.chapter || sq.questionId}
                      </div>
                      {sq.question?.statement && (
                        <div className="text-slate-200">
                          <LatexRenderer content={sq.question.statement} />
                        </div>
                      )}
                      <div className="text-[11px] text-amber-300">Note: {sq.personalNote}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Automated Error Notebook */}
      {activeTab === 'errors' && (
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 space-y-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <AlertOctagon className="w-5 h-5 text-rose-400" />
              Automated Mistake & Negative-Marking Ledger
            </h2>
            <p className="text-xs text-slate-400">
              Every wrong or unattempted question in Custom Tests is automatically captured here until you resolve it.
            </p>

            <div className="space-y-3 pt-2">
              {errorsList.map((err: any) => (
                <div
                  key={err.errorId}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span
                        className={`px-2 py-0.5 rounded font-bold ${
                          err.resolved
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : 'bg-rose-500/20 text-rose-300'
                        }`}
                      >
                        {err.resolved ? 'RESOLVED' : err.errorType || 'CONCEPTUAL_ERROR'}
                      </span>
                      <span className="text-slate-400">
                        {err.subject} • {err.chapter}
                      </span>
                    </div>
                    <div className="text-sm text-white">
                      <LatexRenderer content={err.statement} />
                    </div>
                    <div className="text-xs text-slate-400">
                      Your Answer: <strong className="text-rose-400">{err.selectedAnswer}</strong> • Official Key:{' '}
                      <strong className="text-emerald-400">{err.correctAnswer}</strong>
                    </div>
                  </div>

                  {!err.resolved ? (
                    <button
                      onClick={() => handleResolveError(err.errorId)}
                      className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shrink-0 cursor-pointer"
                    >
                      Mark Mastered & Resolved
                    </button>
                  ) : (
                    <span className="text-xs font-bold text-emerald-400 flex items-center gap-1 shrink-0">
                      <CheckCircle2 className="w-4 h-4" /> Remediated
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: AI Rank & Percentile Predictor */}
      {activeTab === 'predictor' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <form
            onSubmit={handlePredictRank}
            className="lg:col-span-5 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4"
          >
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              AI Rank & College Predictor (`POST /api/ai-hub/rank/predict`)
            </h2>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Exam</label>
              <select
                value={predExam}
                onChange={(e) => {
                  setPredExam(e.target.value);
                  setPredMaxScore(e.target.value === 'NEET' ? 720 : 300);
                  setPredScore(e.target.value === 'NEET' ? 655 : 218);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              >
                <option value="JEE_MAIN">JEE Main (Out of 300)</option>
                <option value="JEE_ADVANCED">JEE Advanced (Out of 360)</option>
                <option value="NEET">NEET-UG (Out of 720)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Expected Score</label>
                <input
                  type="number"
                  value={predScore}
                  onChange={(e) => setPredScore(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Category</label>
                <select
                  value={predCategory}
                  onChange={(e) => setPredCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                >
                  <option value="GEN">OPEN / General</option>
                  <option value="OBC">OBC-NCL</option>
                  <option value="EWS">Gen-EWS</option>
                  <option value="SC">SC</option>
                  <option value="ST">ST</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold cursor-pointer"
            >
              Predict All-India Rank & Eligible Colleges
            </button>
          </form>

          <div className="lg:col-span-7 rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4">
            {predResult ? (
              <>
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs text-slate-400">Predicted Percentile</div>
                    <div className="text-xl font-black text-emerald-400 mt-1">
                      {predResult.predictedPercentile}%ile
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs text-slate-400">Expected AIR Band</div>
                    <div className="text-xl font-black text-white mt-1">
                      #{predResult.predictedRankRange?.min} – #{predResult.predictedRankRange?.max}
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs text-slate-400">Eligible Institutes</div>
                    <div className="text-xl font-black text-indigo-400 mt-1">
                      {(predResult.eligibleColleges || []).length} Matched
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-300">Top Eligible JoSAA / MCC Institutes:</div>
                  {(predResult.eligibleColleges || []).map((c: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="font-bold text-white">{c.institute}</div>
                        <div className="text-slate-400">{c.branch}</div>
                      </div>
                      <span className="px-2.5 py-1 rounded bg-emerald-500/15 text-emerald-300 font-bold">
                        Closing AIR #{c.closingRank}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-xs text-slate-400">
                Submit your expected mock score on the left to compute All-India Rank and institute eligibility.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: IIT / NIT / AIIMS Cutoff Explorer */}
      {activeTab === 'colleges' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            {[
              { code: '', label: 'All Institutes' },
              { code: 'JEE_ADVANCED', label: 'IITs (JEE Advanced)' },
              { code: 'JEE_MAIN', label: 'NITs / IIITs (JEE Main)' },
              { code: 'NEET', label: 'AIIMS / Medical (NEET-UG)' },
            ].map((item) => (
              <button
                key={item.code}
                onClick={() => setCollegeExam(item.code)}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold cursor-pointer ${
                  collegeExam === item.code
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {colleges.map((col: any) => (
              <div key={col.collegeId} className="rounded-2xl bg-slate-900 border border-slate-800 p-5 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-bold">
                    {col.exam} • {col.category || 'OPEN'}
                  </span>
                  <span className="text-emerald-400 font-bold">Closing AIR #{col.closingRank}</span>
                </div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-purple-400" />
                  {col.institute}
                </h3>
                <p className="text-xs text-slate-300">{col.branch}</p>
                <div className="text-[11px] text-slate-400 pt-1">
                  Opening Rank: #{col.openingRank} • Closing Rank: #{col.closingRank} • State: {col.state}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: Physical OMR Sheet Grader */}
      {activeTab === 'omr' && (
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 max-w-3xl">
          <div className="flex items-center gap-2 text-sm font-bold text-amber-400">
            <ScanLine className="w-5 h-5" /> Physical OMR Bubble Sheet Evaluator (`POST /api/ai-hub/omr/evaluate`)
          </div>
          <form onSubmit={handleEvaluateOmr} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-300 mb-1">
                Detected Student OMR Bubbles (Question:Option pairs)
              </label>
              <input
                type="text"
                value={omrSheetText}
                onChange={(e) => setOmrSheetText(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs font-mono text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-300 mb-1">Official Answer Key</label>
              <input
                type="text"
                value={omrKeyText}
                onChange={(e) => setOmrKeyText(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs font-mono text-white"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold cursor-pointer"
            >
              Grade OMR Sheet (+4 / -1 Marking)
            </button>
          </form>

          {omrResult && (
            <div className="p-4 rounded-xl bg-slate-950 border border-amber-500/30 text-xs space-y-2">
              <div className="text-sm font-bold text-white">
                Final OMR Score: {omrResult.totalScore} / {omrResult.maxScore} • Accuracy: {omrResult.accuracy}%
              </div>
              <div className="text-slate-300">
                Correct: <strong className="text-emerald-400">{omrResult.correctCount}</strong> • Wrong:{' '}
                <strong className="text-rose-400">{omrResult.incorrectCount}</strong> • Unattempted:{' '}
                <strong>{omrResult.unattemptedCount}</strong>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
