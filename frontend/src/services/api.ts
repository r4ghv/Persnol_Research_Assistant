import type {
  ResearchResult,
  ChatResponse,
  CompareResponse,
  StoredPaper,
  WorkspaceSummary,
  SearchChunkResult,
} from '../types';

const API_BASE = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) {
        errorMsg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  async health(): Promise<{ status: string; service: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },

  async runResearch(params: {
    topic: string;
    max_papers?: number;
    summary_style?: string;
    sources?: string[];
  }): Promise<ResearchResult> {
    const res = await fetch(`${API_BASE}/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: params.topic,
        max_papers: params.max_papers ?? 5,
        summary_style: params.summary_style ?? 'bullet_points',
        sources: params.sources ?? ['arXiv'],
      }),
    });
    return handleResponse(res);
  },

  async sendChatMessage(params: {
    session_id?: string;
    question: string;
    k?: number;
  }): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: params.session_id || 'default',
        question: params.question,
        k: params.k ?? 5,
      }),
    });
    return handleResponse(res);
  },

  async clearChat(sessionId: string = 'default'): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/chat/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    return handleResponse(res);
  },

  async getChatHistory(sessionId: string = 'default'): Promise<{ session_id: string; history: Array<{ role: 'user' | 'assistant'; content: string }> }> {
    const res = await fetch(`${API_BASE}/chat/${encodeURIComponent(sessionId)}/history`);
    return handleResponse(res);
  },

  async comparePapers(params: {
    paper_ids: string[];
    question: string;
    k_per_paper?: number;
  }): Promise<CompareResponse> {
    const res = await fetch(`${API_BASE}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_ids: params.paper_ids,
        question: params.question,
        k_per_paper: params.k_per_paper ?? 3,
      }),
    });
    return handleResponse(res);
  },

  async listPapers(): Promise<{ papers: StoredPaper[] }> {
    const res = await fetch(`${API_BASE}/papers`);
    return handleResponse(res);
  },

  async deletePaper(paperId: string): Promise<{ ok: boolean; paper_id: string }> {
    const res = await fetch(`${API_BASE}/papers/${encodeURIComponent(paperId)}`, {
      method: 'DELETE',
    });
    return handleResponse(res);
  },

  async getWorkspace(): Promise<WorkspaceSummary> {
    const res = await fetch(`${API_BASE}/workspace`);
    return handleResponse(res);
  },

  async searchChunks(query: string, k: number = 10): Promise<{ results: SearchChunkResult[] }> {
    const res = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, k }),
    });
    return handleResponse(res);
  },
};
