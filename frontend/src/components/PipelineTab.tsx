import { useState } from 'react';
import {
  Search,
  Sparkles,
  Layers,
  Star,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  Download,
  CheckCircle2,
  AlertCircle,
  Clock,
  Quote,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';
import type { ResearchResult, SummaryItem } from '../types';

export const PipelineTab = () => {
  const [topic, setTopic] = useState('');
  const [maxPapers, setMaxPapers] = useState(5);
  const [summaryStyle, setSummaryStyle] = useState('bullet_points');
  const [sources, setSources] = useState({
    arXiv: true,
    PubMed: true,
    'Semantic Scholar': true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [activeReportTab, setActiveReportTab] = useState<'summaries' | 'report'>('summaries');
  const [expandedPapers, setExpandedPapers] = useState<Record<number, boolean>>({});

  const toggleSource = (sourceName: keyof typeof sources) => {
    setSources((prev) => ({
      ...prev,
      [sourceName]: !prev[sourceName],
    }));
  };

  const handleRunPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError('Please enter a research topic.');
      return;
    }

    const selectedSources = Object.entries(sources)
      .filter(([_, enabled]) => enabled)
      .map(([name]) => name);

    if (selectedSources.length === 0) {
      setError('Please select at least one academic source.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.runResearch({
        topic: topic.trim(),
        max_papers: maxPapers,
        summary_style: summaryStyle,
        sources: selectedSources,
      });
      setResult(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Research pipeline execution failed.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpandPaper = (index: number) => {
    setExpandedPapers((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const downloadMarkdown = () => {
    if (!result?.report?.markdown) return;
    const blob = new Blob([result.report.markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.topic.toLowerCase().replace(/[^a-z0-9]+/g, '_')}_report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Search Header and Input Form */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm sm:p-8">
        <div className="mb-6">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
            <Sparkles className="h-4 w-4" />
            <span>Autonomous 6-Stage Literature Review</span>
          </div>
          <h2 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
            Deep Academic Research Pipeline
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Searches arXiv, PubMed, and Semantic Scholar concurrently, extracts full PDF texts, chunks & embeds into ChromaDB, and runs an adversarial summarizer-critic workflow.
          </p>
        </div>

        <form onSubmit={handleRunPipeline} className="space-y-6">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Research Topic / Query
            </label>
            <div className="relative mt-2">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Constitutional AI and RLHF alignment mechanisms in LLMs"
                disabled={loading}
                className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3.5 pl-11 text-sm text-white placeholder-slate-500 shadow-inner outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
              />
              <Search className="absolute left-3.5 top-3.5 h-5 w-5 text-slate-500" />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* Max Papers */}
            <div>
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Max Papers ({maxPapers})
                </label>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={maxPapers}
                onChange={(e) => setMaxPapers(parseInt(e.target.value))}
                disabled={loading}
                className="mt-3 h-2 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-indigo-500"
              />
              <div className="mt-1 flex justify-between text-[11px] text-slate-500">
                <span>1 paper</span>
                <span>10 papers</span>
                <span>20 papers</span>
              </div>
            </div>

            {/* Summary Style */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Synthesis Format
              </label>
              <div className="mt-2 flex rounded-lg bg-slate-950/80 p-1 border border-slate-800">
                {[
                  { id: 'bullet_points', label: 'Bullets' },
                  { id: 'paragraph', label: 'Paragraph' },
                  { id: 'technical', label: 'Technical' },
                ].map((style) => (
                  <button
                    key={style.id}
                    type="button"
                    onClick={() => setSummaryStyle(style.id)}
                    disabled={loading}
                    className={`flex-1 rounded-md py-1.5 text-xs font-medium transition ${
                      summaryStyle === style.id
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {style.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Academic Sources */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Data Sources
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                {(['arXiv', 'PubMed', 'Semantic Scholar'] as const).map((sourceName) => (
                  <button
                    key={sourceName}
                    type="button"
                    onClick={() => toggleSource(sourceName)}
                    disabled={loading}
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium border transition ${
                      sources[sourceName]
                        ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
                        : 'bg-slate-950/40 border-slate-800 text-slate-500 hover:border-slate-700'
                    }`}
                  >
                    {sources[sourceName] ? '✓ ' : '+ '}
                    {sourceName}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:from-indigo-500 hover:to-violet-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Orchestrating 6-Agent Pipeline...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Execute Research Pipeline</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-6 flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-300">
            <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-rose-400" />
            <div>
              <p className="font-semibold">Pipeline Error</p>
              <p className="mt-0.5 text-xs text-rose-200/80">{error}</p>
            </div>
          </div>
        )}
      </section>

      {/* Loading Skeleton & Progress Tracker */}
      {loading && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-8 text-center backdrop-blur-sm">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          </div>
          <h3 className="mt-4 text-lg font-bold text-white">Running Multi-Agent Research Workflow</h3>
          <p className="mx-auto mt-1 max-w-md text-xs text-slate-400">
            Executing parallel search, PDF downloads, section chunking, vector embedding, summarizer synthesis, and adversarial critic validation.
          </p>

          <div className="mx-auto mt-6 grid max-w-2xl grid-cols-2 gap-3 text-left sm:grid-cols-3">
            {[
              { title: '1. SearchAgent', desc: 'Parallel source discovery' },
              { title: '2. ReaderAgent', desc: 'Concurrent PyMuPDF parse' },
              { title: '3. RetrieverAgent', desc: 'Vectorize & ChromaDB' },
              { title: '4. SummarizerAgent', desc: 'Context synthesis' },
              { title: '5. CriticAgent', desc: 'Adversarial fact-check' },
              { title: '6. ReportAgent', desc: 'Cross-paper comparison' },
            ].map((step, i) => (
              <div
                key={i}
                className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-3 shadow-inner"
              >
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 animate-ping rounded-full bg-indigo-400" />
                  <span className="text-xs font-semibold text-slate-200">{step.title}</span>
                </div>
                <p className="mt-1 text-[11px] text-slate-500">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results View */}
      {result && (
        <section className="space-y-6">
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
                <FileText className="h-4 w-4 text-indigo-400" />
                <span>Papers Analyzed</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-white">{result.papers.length}</p>
              <p className="text-[11px] text-slate-500">From {result.sources_used.join(', ')}</p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
                <Layers className="h-4 w-4 text-cyan-400" />
                <span>Vector Chunks</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-white">{result.chunks_stored}</p>
              <p className="text-[11px] text-slate-500">Indexed into ChromaDB</p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
                <Star className="h-4 w-4 text-amber-400" />
                <span>Critic Score</span>
              </div>
              <div className="mt-2 flex items-baseline gap-1">
                <p className="text-2xl font-bold text-white">
                  {result.average_rating ? result.average_rating.toFixed(1) : 'N/A'}
                </p>
                <span className="text-xs text-slate-500">/ 10</span>
              </div>
              <p className="text-[11px] text-slate-500">Average adversarial score</p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span>Workflow Status</span>
              </div>
              <p className="mt-2 text-2xl font-bold text-emerald-400">Success</p>
              <p className="text-[11px] text-slate-500">Report synthesized</p>
            </div>
          </div>

          {/* Navigation View (Summaries Cards vs Full Report Markdown) */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveReportTab('summaries')}
                className={`rounded-lg px-4 py-2 text-xs font-semibold transition ${
                  activeReportTab === 'summaries'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                }`}
              >
                Paper Summaries ({result.summaries.length})
              </button>
              <button
                onClick={() => setActiveReportTab('report')}
                className={`rounded-lg px-4 py-2 text-xs font-semibold transition ${
                  activeReportTab === 'report'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                }`}
              >
                Comparative Report (Markdown)
              </button>
            </div>

            {activeReportTab === 'report' && (
              <button
                onClick={downloadMarkdown}
                className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:bg-slate-700"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Export .md</span>
              </button>
            )}
          </div>

          {/* Tab 1: Detailed Summaries Cards */}
          {activeReportTab === 'summaries' && (
            <div className="space-y-4">
              {result.summaries.map((item: SummaryItem, index: number) => {
                const isExpanded = expandedPapers[index];
                const paper = item.paper;
                const score = paper._rank_score;
                const rank = paper._rank || index + 1;
                const directUrl = paper.pdf_url || paper.url;

                return (
                  <article
                    key={index}
                    className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-md transition hover:border-slate-700"
                  >
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-md bg-indigo-500/20 px-2 py-0.5 text-xs font-bold text-indigo-400">
                            #{rank}
                          </span>
                          <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300">
                            {paper.source}
                          </span>
                          {score && (
                            <span className="rounded-md bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 text-xs font-semibold text-cyan-400">
                              Score: {score}
                            </span>
                          )}
                          {item.rating && (
                            <span className="flex items-center gap-1 rounded-md bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-xs font-semibold text-amber-400">
                              <Star className="h-3 w-3 fill-amber-400" />
                              Critic: {item.rating}/10
                            </span>
                          )}
                        </div>

                        <h3 className="text-lg font-bold text-white">{paper.title}</h3>

                        <div className="flex flex-wrap gap-y-1 gap-x-4 text-xs text-slate-400">
                          <span>
                            <strong>Authors:</strong> {paper.authors?.join(', ') || 'Unknown'}
                          </span>
                          {paper.published && (
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3 text-slate-500" />
                              {paper.published.slice(0, 10)}
                            </span>
                          )}
                        </div>
                      </div>

                      {directUrl && (
                        <a
                          href={directUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="flex flex-shrink-0 items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white"
                        >
                          <span>Original Paper</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>

                    {/* Summary Content */}
                    <div className="mt-4 rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 text-sm text-slate-200">
                      <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>
                          {item.revised_summary || item.summary}
                        </ReactMarkdown>
                      </div>
                    </div>

                    {/* Expandable Critique & Notes */}
                    {item.critique && (
                      <div className="mt-3">
                        <button
                          onClick={() => toggleExpandPaper(index)}
                          className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300"
                        >
                          <Quote className="h-3.5 w-3.5" />
                          <span>{isExpanded ? 'Hide Critic Review' : 'View Adversarial Critic Review'}</span>
                          {isExpanded ? (
                            <ChevronUp className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5" />
                          )}
                        </button>

                        {isExpanded && (
                          <div className="mt-2 rounded-lg border border-indigo-500/20 bg-indigo-950/30 p-3.5 text-xs text-indigo-200/90">
                            <p className="font-semibold text-indigo-300">Critic Review Analysis:</p>
                            <p className="mt-1 whitespace-pre-wrap leading-relaxed">{item.critique}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}

          {/* Tab 2: Full Synthesized Report Markdown */}
          {activeReportTab === 'report' && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-md">
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown>{result.report.markdown}</ReactMarkdown>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};
