
import logging

import gradio as gr
import gradio_client.utils as _gcutils
import httpx

from research_assistant.utils.config import Config
from research_assistant.utils.logger import Logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- gradio 4.44.1 workaround ---------------------------------------------
# `gr.Chatbot(type="messages")` emits API schemas whose `additionalProperties`
# is the boolean `true`. gradio_client.utils._json_schema_to_python_type then
# recurses into it and crashes with `TypeError: 'bool' is not a container`
# while building `api_info` during `interface.launch()`. Guard all recursive
# entries: any non-dict schema node is a primitive/marker and maps to "Any".

_ORIG_JSON_SCHEMA_TO_PY = _gcutils._json_schema_to_python_type


def _safe_json_schema_to_python_type(schema, defs):
    if not isinstance(schema, dict):
        return "Any"
    return _ORIG_JSON_SCHEMA_TO_PY(schema, defs)


_gcutils._json_schema_to_python_type = _safe_json_schema_to_python_type
# ---------------------------------------------------------------------------

def _extract_detail(exc: httpx.HTTPStatusError) -> str:
    """Pull the FastAPI `detail` message out of an HTTP error response."""
    try:
        return str(exc.response.json().get("detail", str(exc)))
    except Exception:
        return str(exc)


class ResearchAssistantApp:
    """Thin Gradio client over the FastAPI backend.

    All business logic (pipeline, chat, compare, workspace archiving) lives in
    the backend; this class only renders UI state fetched over HTTP.
    """

    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        self.client = httpx.Client(
            base_url=self.config.API_BASE_URL,
            timeout=self.config.API_TIMEOUT,
        )
        self.current_research = None

    def research_topic(self, topic, max_papers, summary_style,
                       use_arxiv, use_pubmed, use_s2):
        """Main research function triggered by Gradio → POST /api/research."""
        try:
            if not topic or not topic.strip():
                return "Please enter a research topic.", "", []
            topic = topic.strip()
            max_papers = int(max_papers)
            if max_papers < 1 or max_papers > 20:
                return "Please select between 1 and 20 papers.", "", []

            sources = []
            if use_arxiv:
                sources.append("arXiv")
            if use_pubmed:
                sources.append("PubMed")
            if use_s2:
                sources.append("Semantic Scholar")
            if not sources:
                return "Please select at least one source.", "", []

            self.logger.log(f"Starting research on: {topic}")

            resp = self.client.post(
                "/api/research",
                json={
                    "topic": topic,
                    "max_papers": max_papers,
                    "summary_style": summary_style,
                    "sources": sources,
                },
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("error"):
                error_msg = result["error"] + ". Please try:\n"
                error_msg += "• Using different keywords (e.g., 'machine learning' instead of 'AI')\n"
                error_msg += "• Using broader terms (e.g., 'computer science' instead of 'quantum computing')\n"
                error_msg += "• Checking your internet connection\n"
                error_msg += "• Trying again later (arXiv may be temporarily unavailable)"
                return error_msg, "", []

            papers = result["papers"]
            summaries = result["summaries"]
            report = result["report"]
            ws_report_path = result.get("workspace_report")
            avg_rating = result.get("average_rating")

            # Format output for display
            sources_used = result.get("sources_used") or sorted(
                set(p.get("source", "?") for p in papers)
            )
            output_text = f"✅ Research completed on: {topic}\n\n"
            output_text += f"📊 Papers analyzed: {len(papers)}\n"
            output_text += f"🔍 Sources: {', '.join(sorted(sources_used))}\n"
            output_text += f"🧠 Chunks embedded: {result['chunks_stored']}\n"
            if avg_rating is not None:
                output_text += f"⭐ Average critic rating: {avg_rating:.1f}/10\n"
            output_text += f"📄 Markdown report: {report['path']}\n"
            output_text += f"📁 JSON report: {report['json_path']}\n"
            if ws_report_path:
                output_text += f"🗂️ Workspace report: {ws_report_path}\n"
            output_text += "\n"

            # Create interactive summary components
            summary_components = self._create_summary_components(summaries, summary_style)

            return output_text, summary_components, summaries

        except httpx.HTTPStatusError as e:
            error_msg = f"❌ Research failed: {_extract_detail(e)}"
            self.logger.log(error_msg)
            return error_msg, "", []
        except httpx.ConnectError:
            error_msg = (
                "❌ Cannot reach the research backend. "
                f"Is the API server running at {self.config.API_BASE_URL}? "
                "Start it with: python -m research_assistant.api"
            )
            self.logger.log(error_msg)
            return error_msg, "", []
        except Exception as e:
            error_msg = f"❌ Error during research: {str(e)}"
            self.logger.log(error_msg)
            return error_msg, "", []
    
    @staticmethod
    def _format_sources(sources):
        """Render retrieval sources as markdown with clickable links."""
        if not sources:
            return ""
        lines = ["### 📚 Sources"]
        for i, s in enumerate(sources, 1):
            if s.get("url"):
                lines.append(f"- [{i}] [{s['title']}]({s['url']}) — *{s['source']}*")
            else:
                lines.append(f"- [{i}] {s['title']} — *{s['source']}*")
        return "\n".join(lines)

    def chat_send(self, message, k, session_id):
        """Send a message in a conversational chat session (RAG + history)."""
        try:
            resp = self.client.post(
                "/api/chat/send",
                json={
                    "session_id": session_id or "default",
                    "question": message,
                    "k": int(k),
                },
            )
            resp.raise_for_status()
            result = resp.json()
            chatbot_messages = [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in result.get("history", [])
            ]
            sources_html = self._format_sources(result.get("sources", []))
            return chatbot_messages, sources_html, ""
        except httpx.HTTPStatusError as e:
            detail = _extract_detail(e)
            self.logger.log(f"❌ Error in chat: {detail}")
            return [], f"❌ Error in chat: {detail}", ""
        except httpx.ConnectError:
            return [], f"❌ Cannot reach the research backend at {self.config.API_BASE_URL}.", ""
        except Exception as e:
            self.logger.log(f"❌ Error in chat: {e}")
            return [], f"❌ Error in chat: {str(e)}", ""

    def chat_clear(self, session_id):
        """Clear the chat history for a session."""
        try:
            self.client.post(
                "/api/chat/clear", json={"session_id": session_id or "default"}
            )
        except Exception as e:
            self.logger.log(f"❌ Error clearing chat: {e}")
        return [], ""

    def compare_papers(self, paper_ids, question):
        """Compare multiple stored papers with a structured, sourced answer."""
        try:
            if not paper_ids or len(paper_ids) < 2:
                return "Please select at least two papers to compare.", ""
            resp = self.client.post(
                "/api/compare",
                json={
                    "paper_ids": list(paper_ids),
                    "question": question,
                    "k_per_paper": 3,
                },
            )
            resp.raise_for_status()
            result = resp.json()
            return result.get("answer", ""), self._format_sources(result.get("sources", []))
        except httpx.HTTPStatusError as e:
            detail = _extract_detail(e)
            self.logger.log(f"❌ Error comparing papers: {detail}")
            return f"❌ Error comparing papers: {detail}", ""
        except httpx.ConnectError:
            return (
                f"❌ Cannot reach the research backend at {self.config.API_BASE_URL}.",
                "",
            )
        except Exception as e:
            self.logger.log(f"❌ Error comparing papers: {e}")
            return f"❌ Error comparing papers: {str(e)}", ""

    def refresh_papers_list(self):
        """Reload the paper picker choices from the vector store."""
        choices = self._paper_choices()
        return gr.Dropdown(choices=choices)

    def _paper_choices(self):
        """[(label, paper_id), ...] for the compare dropdown."""
        try:
            resp = self.client.get("/api/papers")
            resp.raise_for_status()
            papers = resp.json().get("papers", [])
            return [(f"{p['title']} — {p['source']}", p["paper_id"]) for p in papers]
        except Exception:
            return []

    def _workspace_summary(self):
        """Markdown snapshot of the workspace directory contents."""
        try:
            resp = self.client.get("/api/workspace")
            resp.raise_for_status()
            return resp.json().get("markdown", "_(workspace unavailable)_")
        except Exception:
            return (
                f"_(Cannot reach the research backend at {self.config.API_BASE_URL}.)_"
            )
    
    def _create_summary_components(self, summaries, style):
        """Create interactive summary components for the interface"""
        components = []
        
        for i, summary_data in enumerate(summaries, 1):
            paper = summary_data['paper']
            summary = summary_data.get('revised_summary') or summary_data['summary']
            rank = paper.get("_rank", i)
            score = paper.get("_rank_score", "")
            source = paper.get("source", "?")
            score_display = f" ({score}/100)" if score else ""
            
            summary_html = f"""
            <div style="
                border: 2px solid #e0e0e0; 
                border-radius: 12px; 
                padding: 20px; 
                margin: 15px 0; 
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <div style="
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center; 
                    margin-bottom: 15px;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                ">
                    <h3 style="
                        margin: 0; 
                        color: #2c3e50; 
                        font-size: 18px; 
                        font-weight: 600;
                        flex: 1;
                    ">#{rank} {paper['title']}</h3>
                    <span style="
                        background: #6c757d; 
                        color: white; 
                        padding: 4px 10px; 
                        border-radius: 20px; 
                        font-size: 12px; 
                        font-weight: bold;
                        margin-right: 6px;
                    ">{source}</span>
                    <span style="
                        background: #007bff; 
                        color: white; 
                        padding: 4px 12px; 
                        border-radius: 20px; 
                        font-size: 12px; 
                        font-weight: bold;
                    ">{style.replace('_', ' ').title()}{score_display}</span>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <p style="
                        margin: 5px 0; 
                        color: #6c757d; 
                        font-size: 14px;
                    ">
                        <strong>👥 Authors:</strong> {', '.join(paper['authors'])}
                    </p>
                    <p style="
                        margin: 5px 0; 
                        color: #6c757d; 
                        font-size: 14px;
                    ">
                        <strong>📅 Published:</strong> {paper['published'][:10]}
                    </p>
                    <p style="
                        margin: 5px 0; 
                        color: #6c757d; 
                        font-size: 14px;
                    ">
                        <strong>🏷️ Category:</strong> {paper['primary_category']}
                    </p>
                </div>
                
                <div style="
                    background: #f8f9fa; 
                    border-left: 4px solid #28a745; 
                    padding: 15px; 
                    border-radius: 8px;
                    margin: 15px 0;
                ">
                    <h4 style="
                        margin: 0 0 10px 0; 
                        color: #28a745; 
                        font-size: 16px;
                    ">📋 Abstract</h4>
                    <p style="
                        margin: 0; 
                        color: #495057; 
                        font-size: 14px; 
                        line-height: 1.6;
                    ">{paper['abstract'][:300]}{'...' if len(paper['abstract']) > 300 else ''}</p>
                </div>
                
                <div style="
                    background: #fff3cd; 
                    border: 1px solid #ffeaa7; 
                    border-radius: 8px; 
                    padding: 15px;
                    margin: 15px 0;
                ">
                    <h4 style="
                        margin: 0 0 10px 0; 
                        color: #856404; 
                        font-size: 16px;
                    ">✨ AI Summary</h4>
                    <div style="
                        color: #495057; 
                        font-size: 14px; 
                        line-height: 1.6;
                        white-space: pre-wrap;
                    ">{summary}</div>
                </div>
                
                <div style="
                    display: flex; 
                    gap: 10px; 
                    margin-top: 15px;
                ">
                    <a href="{paper['pdf_url']}" target="_blank" style="
                        background: #dc3545; 
                        color: white; 
                        padding: 8px 16px; 
                        text-decoration: none; 
                        border-radius: 6px; 
                        font-size: 12px; 
                        font-weight: bold;
                        transition: background 0.3s ease;
                    ">📥 Download PDF</a>
                    <span style="
                        background: #6c757d; 
                        color: white; 
                        padding: 8px 16px; 
                        border-radius: 6px; 
                        font-size: 12px; 
                        font-weight: bold;
                    ">🔗 DOI: {paper['doi']}</span>
                </div>
            </div>
            """
            
            components.append(summary_html)
        
        return "\n".join(components)
    
    def create_interface(self):
        """Create and return the Gradio interface"""
        
        with gr.Blocks(title="Personal Research Assistant", theme=gr.themes.Soft()) as interface:
            gr.Markdown("""
            # 🔬 Personal Research Assistant
            
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            ">
                <h1 style="margin: 0; font-size: 2.5em;">🚀 AI-Powered Research</h1>
                <p style="font-size: 1.2em; margin: 10px 0;">Enter a research topic to fetch academic papers, generate intelligent summaries, and organize your research automatically.</p>
            </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    with gr.Group():
                        gr.Markdown("### 📝 Research Parameters")
                        topic_input = gr.Textbox(
                            label="Research Topic",
                            placeholder="e.g., machine learning, quantum computing, climate change",
                            lines=2
                        )
                        
                        with gr.Row():
                            max_papers = gr.Slider(
                                minimum=1,
                                maximum=10,
                                value=5,
                                step=1,
                                label="Maximum Papers to Analyze"
                            )
                            
                            summary_style = gr.Dropdown(
                                choices=["bullet_points", "paragraph", "technical"],
                                value="bullet_points",
                                label="Summary Style"
                            )
                        
                        with gr.Row():
                            source_arxiv = gr.Checkbox(value=True, label="arXiv")
                            source_pubmed = gr.Checkbox(value=True, label="PubMed")
                            source_s2 = gr.Checkbox(value=True, label="Semantic Scholar")
                        
                        research_btn = gr.Button(
                            "🔍 Start Research", 
                            variant="primary", 
                            size="lg"
                        )
                
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.Markdown("### 📊 Research Status")
                        status_output = gr.Textbox(
                            label="Status",
                            lines=8,
                            interactive=False
                        )
            
            # Research Results Section
            with gr.Group():
                gr.Markdown("""
                ### 📚 Research Results
                <div style="
                    background: #f8f9fa;
                    border-left: 4px solid #007bff;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                ">
                    <p style="margin: 0; color: #495057;">
                        <strong>💡 Tip:</strong> Each paper summary includes the abstract, AI-generated summary, and direct links to download the PDF and view the DOI.
                    </p>
                </div>
                """)
                
                # Dynamic summary components will be displayed here
                summary_output = gr.HTML(
                    label="Paper Summaries"
                )
            
            # Example topics with better styling
            with gr.Group():
                gr.Markdown("""
                ### 💡 Example Research Topics
                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                ">
                    <div style="
                        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
                        padding: 20px;
                        border-radius: 12px;
                        color: white;
                        text-align: center;
                    ">
                        <h4 style="margin: 0 0 10px 0;">🤖 Machine Learning</h4>
                        <p style="margin: 0; font-size: 14px;">Recent advances in deep learning</p>
                    </div>
                    <div style="
                        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                        padding: 20px;
                        border-radius: 12px;
                        color: white;
                        text-align: center;
                    ">
                        <h4 style="margin: 0 0 10px 0;">⚛️ Quantum Computing</h4>
                        <p style="margin: 0; font-size: 14px;">Quantum algorithms and applications</p>
                    </div>
                    <div style="
                        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
                        padding: 20px;
                        border-radius: 12px;
                        color: white;
                        text-align: center;
                    ">
                        <h4 style="margin: 0 0 10px 0;">🌍 Climate Science</h4>
                        <p style="margin: 0; font-size: 14px;">Impact of climate change on ecosystems</p>
                    </div>
                    <div style="
                        background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
                        padding: 20px;
                        border-radius: 12px;
                        color: white;
                        text-align: center;
                    ">
                        <h4 style="margin: 0 0 10px 0;">🧬 Biotechnology</h4>
                        <p style="margin: 0; font-size: 14px;">CRISPR gene editing technology</p>
                    </div>
                </div>
                """)
            
            # Conversational Chat, Compare, and Workspace Tabs
            with gr.Tabs():
                with gr.Tab("💬 Chat with Papers"):
                    with gr.Group():
                        gr.Markdown("""
                        ### 💬 Chat with Papers
                        <div style="
                            background: #e8f5e9;
                            border-left: 4px solid #28a745;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                        ">
                            <p style="margin: 0; color: #2e7d32;">
                                <strong>💡 Tip:</strong> Have a conversation with your stored papers. Every answer is grounded in the embedded chunks and always includes sources. Chat history persists in <strong>Workspace/Chat History</strong>.
                            </p>
                        </div>
                        """)
                        
                        with gr.Row():
                            chat_session_id = gr.Textbox(
                                label="Session ID",
                                value="default",
                                placeholder="e.g., thesis, literature-review",
                                scale=3
                            )
                            chat_k = gr.Slider(
                                minimum=1,
                                maximum=10,
                                value=5,
                                step=1,
                                label="Chunks to Retrieve",
                                scale=1
                            )
                        
                        chat_history = gr.Chatbot(
                            label="Conversation",
                            type="messages",
                            height=400
                        )
                        
                        with gr.Row():
                            chat_input = gr.Textbox(
                                label="Your Message",
                                placeholder="Ask anything about your stored papers...",
                                lines=2,
                                scale=4
                            )
                            chat_send_btn = gr.Button("➤ Send", variant="primary", size="lg", scale=1)
                            chat_clear_btn = gr.Button("🗑️ Clear Session", variant="secondary", size="lg", scale=1)
                        
                        chat_sources = gr.Markdown(label="Sources")
                
                with gr.Tab("⚖️ Compare Papers"):
                    with gr.Group():
                        gr.Markdown("""
                        ### ⚖️ Compare Papers
                        <div style="
                            background: #fff3e0;
                            border-left: 4px solid #ff9800;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                        ">
                            <p style="margin: 0; color: #e65100;">
                                <strong>💡 Tip:</strong> Select at least two papers stored in your vector database and ask a comparative question (methodology, findings, limitations). Answers are structured and cited.
                            </p>
                        </div>
                        """)
                        
                        with gr.Row():
                            compare_papers_dd = gr.Dropdown(
                                label="Papers to Compare",
                                multiselect=True,
                                choices=self._paper_choices(),
                                scale=3
                            )
                            refresh_papers_btn = gr.Button("🔄 Reload Papers", variant="secondary", scale=1)
                        
                        compare_question = gr.Textbox(
                            label="Comparison Question",
                            placeholder="e.g., How do these papers differ in methodology and findings?",
                            lines=2
                        )
                        compare_btn = gr.Button("⚖️ Compare", variant="primary", size="lg")
                        compare_answer = gr.Markdown(label="Comparison")
                        compare_sources = gr.Markdown(label="Sources")
                
                with gr.Tab("📂 Research Workspace"):
                    with gr.Group():
                        gr.Markdown("""
                        ### 📂 Research Workspace
                        <div style="
                            background: #e3f2fd;
                            border-left: 4px solid #2196f3;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                        ">
                            <p style="margin: 0; color: #0d47a1;">
                                <strong>Structure:</strong> Papers / Notes / Chat History / Highlights / Reports / Citations. All research artifacts are archived here automatically.
                            </p>
                        </div>
                        """)
                        workspace_status = gr.Markdown(value=self._workspace_summary())
                        refresh_workspace_btn = gr.Button("🔄 Refresh Workspace", variant="secondary")
            
            # Footer with better styling
            gr.Markdown("""
            ---
            <div style="
                text-align: center;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                margin-top: 30px;
            ">
                <p style="margin: 0; color: #6c757d;">
                    🚀 Built with <strong>OpenAI GPT-4o-mini</strong> and <strong>Gradio</strong> | 
                    📚 Sources: <strong>arXiv, PubMed, Semantic Scholar</strong> |
                    🎨 Ranked by relevance, recency & quality
                </p>
            </div>
            """)
            
            # Event handlers
            research_btn.click(
                fn=self.research_topic,
                inputs=[topic_input, max_papers, summary_style, source_arxiv, source_pubmed, source_s2],
                outputs=[status_output, summary_output, gr.State()]
            )
            
            chat_send_btn.click(
                fn=self.chat_send,
                inputs=[chat_input, chat_k, chat_session_id],
                outputs=[chat_history, chat_sources, chat_input]
            )
            chat_input.submit(
                fn=self.chat_send,
                inputs=[chat_input, chat_k, chat_session_id],
                outputs=[chat_history, chat_sources, chat_input]
            )
            chat_clear_btn.click(
                fn=self.chat_clear,
                inputs=[chat_session_id],
                outputs=[chat_history, chat_sources]
            )
            
            compare_btn.click(
                fn=self.compare_papers,
                inputs=[compare_papers_dd, compare_question],
                outputs=[compare_answer, compare_sources]
            )
            refresh_papers_btn.click(
                fn=self.refresh_papers_list,
                outputs=[compare_papers_dd]
            )
            
            refresh_workspace_btn.click(
                fn=self._workspace_summary,
                outputs=[workspace_status]
            )
        
        return interface

def main():
    """Main function to run the Gradio app"""
    try:
        app = ResearchAssistantApp()
        interface = app.create_interface()
        
        # Launch the interface
        interface.launch(
            server_name="127.0.0.1",
            server_port=7864,  # Use a different port
            show_error=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start Research Assistant: {e}")
        print(f"Error: {e}")
        print("Please check your configuration and OpenAI API key.")

if __name__ == "__main__":
    main()
