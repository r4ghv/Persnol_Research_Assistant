export interface Paper {
  title: string;
  authors: string[];
  abstract: string;
  published: string;
  pdf_url?: string;
  doi?: string;
  source: string;
  source_id?: string;
  citation_count?: number;
  url?: string;
  entry_id?: string;
  _rank?: number;
  _rank_score?: number;
  primary_category?: string;
}

export interface SummaryItem {
  paper: Paper;
  summary: string;
  critique?: string;
  revised_summary?: string;
  rating?: number | null;
  content?: string;
}

export interface ResearchReport {
  path: string;
  json_path: string;
  markdown: string;
}

export interface ResearchResult {
  topic: string;
  papers: Paper[];
  summaries: SummaryItem[];
  chunks_stored: number;
  report: ResearchReport;
  average_rating?: number | null;
  sources_used: string[];
  workspace_report?: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface SourceCitation {
  title: string;
  source: string;
  url?: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  chunks: number;
  citations?: SourceCitation[];
  history: ChatMessage[];
  session_id: string;
}

export interface CompareResponse {
  answer: string;
  sources: SourceCitation[];
  chunks: number;
  citations?: SourceCitation[];
}

export interface StoredPaper {
  paper_id: string;
  title: string;
  source: string;
  authors?: string;
  url?: string;
  added_at?: string;
}

export interface WorkspaceCounts {
  papers: number;
  notes: number;
  chats: number;
  highlights: number;
  reports: number;
  citations: number;
  chunks: number;
}

export interface WorkspaceSummary {
  markdown: string;
  counts: WorkspaceCounts;
}

export interface SearchChunkResult {
  id: string;
  document: string;
  metadata: Record<string, unknown>;
  distance?: number;
}
