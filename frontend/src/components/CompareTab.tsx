import { useState, useEffect } from 'react';
import { Scale, RefreshCw, AlertCircle, ExternalLink, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';
import type { StoredPaper, CompareResponse } from '../types';

export const CompareTab = () => {
  const [papers, setPapers] = useState<StoredPaper[]>([]);
  const [selectedPaperIds, setSelectedPaperIds] = useState<string[]>([]);
  const [question, setQuestion] = useState(
    'Compare the methodologies, empirical findings, benchmark datasets, and limitations of these papers. Highlight key agreements and contradictions.'
  );
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);

  const fetchPapers = async () => {
    setRefreshing(true);
    try {
      const res = await api.listPapers();
      setPapers(res.papers || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stored papers.');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPapers();
  }, []);

  const togglePaperSelection = (id: string) => {
    setSelectedPaperIds((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedPaperIds.length < 2) {
      setError('Please select at least 2 papers to compare.');
      return;
    }
    if (!question.trim()) {
      setError('Please enter a comparison prompt or question.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.comparePapers({
        paper_ids: selectedPaperIds,
        question: question.trim(),
        k_per_paper: 3,
      });
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Comparison failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Configuration & Selection Card */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm sm:p-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
            <Scale className="h-4 w-4" />
            <span>Cross-Document Matrix Analysis</span>
          </div>

          <button
            type="button"
            onClick={fetchPapers}
            disabled={refreshing}
            className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-1.5 text-xs font-medium text-slate-300 hover:border-slate-700"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh Vector Store</span>
          </button>
        </div>

        <h2 className="mt-2 text-2xl font-bold text-white">Compare Ingested Academic Papers</h2>
        <p className="mt-1 text-sm text-slate-400">
          Select two or more papers stored in ChromaDB to perform side-by-side comparative analysis of methods, results, and limitations.
        </p>

        <form onSubmit={handleCompare} className="mt-6 space-y-6">
          {/* Papers Selection */}
          <div>
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-300">
              <span>Select Papers ({selectedPaperIds.length} selected)</span>
              <span className="text-slate-500">Requires min 2 papers</span>
            </div>

            {papers.length === 0 ? (
              <div className="mt-3 rounded-xl border border-dashed border-slate-800 p-6 text-center text-xs text-slate-500">
                No papers found in ChromaDB vector store. Run a query in the Autonomous Research tab first to populate papers.
              </div>
            ) : (
              <div className="mt-3 grid max-h-60 grid-cols-1 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
                {papers.map((paper) => {
                  const isSelected = selectedPaperIds.includes(paper.paper_id);
                  return (
                    <button
                      key={paper.paper_id}
                      type="button"
                      onClick={() => togglePaperSelection(paper.paper_id)}
                      className={`flex items-start gap-3 rounded-xl border p-3 text-left transition ${
                        isSelected
                          ? 'border-indigo-500/40 bg-indigo-500/10 text-white shadow-inner'
                          : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}} // handled by button
                        className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                      />
                      <div className="flex-1 overflow-hidden">
                        <p className="text-xs font-semibold leading-snug line-clamp-2 text-slate-200">
                          {paper.title}
                        </p>
                        <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-500">
                          <span className="rounded bg-slate-800 px-1.5 py-0.5">{paper.source}</span>
                          {paper.authors && <span className="truncate">{paper.authors}</span>}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Comparison Prompt */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Comparison Prompt / Directive
            </label>
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/80 p-3.5 text-sm text-white placeholder-slate-500 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
            />
          </div>

          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-300">
              <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || selectedPaperIds.length < 2}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Synthesizing Comparative Analysis...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Execute Comparison</span>
                </>
              )}
            </button>
          </div>
        </form>
      </section>

      {/* Comparison Result */}
      {result && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm sm:p-8 space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h3 className="text-xl font-bold text-white">Comparative Synthesis</h3>
            <p className="text-xs text-slate-400">
              Grounded in {result.chunks} retrieved chunks across {selectedPaperIds.length} papers
            </p>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-6 text-slate-200">
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown>{result.answer}</ReactMarkdown>
            </div>
          </div>

          {result.sources && result.sources.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Referenced Sources in Context
              </h4>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {result.sources.map((s, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs"
                  >
                    <div className="flex-1 overflow-hidden pr-2">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-indigo-400">[{i + 1}]</span>
                        <span className="font-semibold text-slate-200 truncate">{s.title}</span>
                      </div>
                      <span className="text-[10px] text-slate-500">{s.source}</span>
                    </div>
                    {s.url && (
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex-shrink-0 text-slate-400 hover:text-indigo-400"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};
