import { useState, useRef, useEffect } from 'react';
import {
  Send,
  Trash2,
  SlidersHorizontal,
  Bot,
  User,
  ExternalLink,
  BookOpen,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';
import type { ChatMessage, SourceCitation } from '../types';

export const ChatTab = () => {
  const [sessionId, setSessionId] = useState('default');
  const [k, setK] = useState(5);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeSources, setActiveSources] = useState<SourceCitation[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuestion = input.trim();
    setInput('');
    setError(null);

    // Optimistically update message history
    const updatedHistory: ChatMessage[] = [
      ...messages,
      { role: 'user', content: userQuestion },
    ];
    setMessages(updatedHistory);
    setLoading(true);

    try {
      const response = await api.sendChatMessage({
        session_id: sessionId,
        question: userQuestion,
        k: k,
      });

      setMessages(response.history || [
        ...updatedHistory,
        { role: 'assistant', content: response.answer },
      ]);
      setActiveSources(response.sources || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate grounded RAG answer.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (confirm('Clear chat history for this session?')) {
      try {
        await api.clearChat(sessionId);
        setMessages([]);
        setActiveSources([]);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to clear session.');
      }
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
      {/* Left / Main Chat Area (3 cols) */}
      <div className="flex h-[750px] flex-col rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-sm lg:col-span-3">
        {/* Chat Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Grounded Literature RAG</h2>
              <p className="text-xs text-slate-400">
                Answers derived exclusively from vector-embedded paper chunks
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClearChat}
              title="Clear Session History"
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-1.5 text-xs font-medium text-slate-400 hover:border-rose-500/30 hover:bg-rose-500/10 hover:text-rose-300"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-base font-bold text-white">Ask Questions About Ingested Papers</h3>
              <p className="mt-1 max-w-sm text-xs text-slate-400">
                Query research methodologies, compare findings across papers, or ask for specific experimental results.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2 max-w-lg">
                {[
                  'What are the primary datasets evaluated in the ingested papers?',
                  'Summarize the key mathematical formulations for loss functions.',
                  'What limitations and future directions do the authors highlight?',
                ].map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(prompt)}
                    className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-1.5 text-xs text-slate-300 hover:border-indigo-500/40 hover:bg-indigo-500/10"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={idx}
                  className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm shadow-indigo-500/20">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-2xl rounded-2xl px-4 py-3 text-sm shadow-sm ${
                      isUser
                        ? 'bg-indigo-600 text-white'
                        : 'border border-slate-800 bg-slate-950/80 text-slate-200'
                    }`}
                  >
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>

                  {isUser && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-slate-800 text-slate-300">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-3 text-sm text-slate-400">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-indigo-400" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 delay-100" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 delay-200" />
                  <span className="text-xs text-slate-500">Querying ChromaDB vector embeddings...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="border-t border-slate-800 p-4">
          {error && (
            <div className="mb-3 flex items-center gap-2 rounded-lg border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 flex-shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about the research papers..."
              disabled={loading}
              className="flex-1 rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="flex items-center justify-center rounded-xl bg-indigo-600 px-5 text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-500 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Right Sidebar: Context & Citations (1 col) */}
      <div className="space-y-6 lg:col-span-1">
        {/* RAG Settings Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
            <SlidersHorizontal className="h-4 w-4 text-indigo-400" />
            <span>Retrieval Settings</span>
          </div>

          <div className="mt-4 space-y-4">
            <div>
              <div className="flex justify-between text-xs text-slate-400">
                <span>Top-K Chunks ({k})</span>
                <span className="font-semibold text-slate-200">{k} Chunks</span>
              </div>
              <input
                type="range"
                min="1"
                max="15"
                value={k}
                onChange={(e) => setK(parseInt(e.target.value))}
                className="mt-2 h-2 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-indigo-500"
              />
              <p className="mt-1 text-[11px] text-slate-500">
                Number of semantic vector chunks retrieved per question
              </p>
            </div>

            <div>
              <label className="block text-xs text-slate-400">Session ID</label>
              <input
                type="text"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 text-xs text-white outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Retrieved Sources & Citations */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
            <BookOpen className="h-4 w-4 text-cyan-400" />
            <span>Retrieved Sources</span>
          </div>

          {activeSources.length === 0 ? (
            <p className="mt-3 text-xs text-slate-500">
              No sources in active context. Ask a question to trigger retrieval.
            </p>
          ) : (
            <div className="mt-3 space-y-2.5">
              {activeSources.map((s, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-3 text-xs shadow-inner"
                >
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[10px] font-bold text-indigo-400">
                      [{idx + 1}]
                    </span>
                    <span className="text-[10px] text-slate-500">{s.source}</span>
                  </div>
                  <p className="mt-1.5 font-semibold text-slate-200 line-clamp-2">{s.title}</p>
                  {s.url && (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300"
                    >
                      <span>View Source</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
