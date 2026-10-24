import { useState } from 'react';
import { Navbar, type TabType } from './components/Navbar';
import { PipelineTab } from './components/PipelineTab';
import { ChatTab } from './components/ChatTab';
import { CompareTab } from './components/CompareTab';
import { WorkspaceTab } from './components/WorkspaceTab';

export function App() {
    const [activeTab, setActiveTab] = useState<TabType>('pipeline');
    return (
      <div className="min-h0screen bg slate-950 text-slate-100">
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className = "mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
                {activeTab === 'pipeline' && <PipelineTab />}
                {activeTab === 'chat' && <ChatTab />}
                {activeTab === 'compare' && <CompareTab />}
                {activeTab === 'workspace' && <WorkspaceTab />}
        </main>
          </div>
    );
}
export default App;