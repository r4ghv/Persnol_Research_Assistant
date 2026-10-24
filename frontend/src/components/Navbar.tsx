import { useState, useEffect } from 'react';
import { BookOpen, MessageSquareText, Scale, FolderKanban, Activity } from 'lucide-react';
import { api } from '../services/api';

export type TabType = 'pipeline' | 'chat' | 'compare' | 'workspace';

interface NavbarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

export const Navbar = ({ activeTab, setActiveTab }: NavbarProps) => {
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.health();
        setIsBackendHealthy(res.status === 'ok');
      } catch {
        setIsBackendHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const tabs: { id: TabType; label: string; icon: typeof BookOpen }[] = [
    { id: 'pipeline', label: 'Autonomous Research', icon: BookOpen },
    { id: 'chat', label: 'Grounded RAG Chat', icon: MessageSquareText },
    { id: 'compare', label: 'Paper Compare', icon: Scale },
    { id: 'workspace', label: 'Workspace & Vectors', icon: FolderKanban },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/25">
            <BookOpen className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">ResearchAssistant</h1>
              <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
                v1.0 React
              </span>
            </div>
            <p className="text-xs text-slate-400">Multi-Agent Academic Intelligence & RAG</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 rounded-xl bg-slate-900/80 p-1 border border-slate-800">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/30'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Backend Health Status */}
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border ${
              isBackendHealthy === true
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : isBackendHealthy === false
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}
          >
            <Activity
              className={`h-3 w-3 ${
                isBackendHealthy === true
                  ? 'animate-pulse text-emerald-400'
                  : isBackendHealthy === false
                  ? 'text-rose-400'
                  : 'text-amber-400'
              }`}
            />
            <span className="hidden md:inline">
              {isBackendHealthy === true
                ? 'FastAPI Connected'
                : isBackendHealthy === false
                ? 'Backend Offline'
                : 'Checking API...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
