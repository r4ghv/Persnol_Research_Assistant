
import os
import logging
import gradio as gr
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from research_assistant.agents import Summarizer, Organizer, Scraper, DEFAULT_SOURCES
from research_assistant.utils.config import Config
from research_assistant.utils.logger import Logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchAssistantApp:
    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        
        # Initialize agents with config
        self.scraper = Scraper(config=self.config)
        self.summarizer = Summarizer(self.config.OPENAI_API_KEY, self.config.OPENAI_MODEL)
        self.organizer = Organizer(str(self.config.OUTPUT_DIR))
        
        self.current_research = None
        
    def research_topic(self, topic, max_papers, summary_style,
                       use_arxiv, use_pubmed, use_s2):
        """Main research function triggered by Gradio"""
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
            
            self.logger.log(f"Fetching papers from {', '.join(sources)} for: {topic}")
            papers = self.scraper.fetch_papers(topic, max_papers, sources=sources)
            
            if not papers:
                error_msg = f"No papers found for topic: '{topic}'. Please try:\n"
                error_msg += "• Using different keywords (e.g., 'machine learning' instead of 'AI')\n"
                error_msg += "• Using broader terms (e.g., 'computer science' instead of 'quantum computing')\n"
                error_msg += "• Checking your internet connection\n"
                error_msg += "• Trying again later (arXiv may be temporarily unavailable)"
                return error_msg, "", []
            
            # Step 2: Extract content from papers (parallel)
            self.logger.log(f"Extracting content from {len(papers)} papers...")
            paper_contents = [None] * len(papers)
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for i, paper in enumerate(papers):
                    future = executor.submit(self.scraper.extract_content, paper)
                    futures[future] = i
                for future in as_completed(futures):
                    i = futures[future]
                    content, pdf_data = future.result()
                    paper_contents[i] = {
                        'paper': papers[i],
                        'content': content,
                        'pdf_data': pdf_data
                    }
            
            # Step 3: Generate summaries (parallel)
            self.logger.log(f"Generating summaries for {len(papers)} papers...")
            summaries = [None] * len(paper_contents)
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for i, paper_data in enumerate(paper_contents):
                    future = executor.submit(
                        self.summarizer.summarize,
                        paper_data['paper']['title'],
                        paper_data['paper']['abstract'],
                        paper_data['content'],
                        summary_style
                    )
                    futures[future] = i
                for future in as_completed(futures):
                    i = futures[future]
                    paper_data = paper_contents[i]
                    summaries[i] = {
                        'paper': paper_data['paper'],
                        'summary': future.result(),
                        'content': paper_data['content'],
                        'pdf_data': paper_data['pdf_data']
                    }
            
            # Step 4: Organize files
            saved_files = []
            for summary_data in summaries:
                saved_paths = self.organizer.save_paper(
                    summary_data['paper'],
                    summary_data['content'],
                    summary_data['summary'],
                    pdf_data=summary_data.get('pdf_data')
                )
                saved_files.append(saved_paths)
            
            # Step 5: Generate research report
            report_data = {
                'topic': topic,
                'timestamp': datetime.now().isoformat(),
                'papers_analyzed': len(papers),
                'papers': summaries,
                'files_saved': saved_files
            }
            
            report_path = self.organizer.save_report(report_data)
            
            # Format output for display
            sources_used = set(p.get("source", "?") for p in papers)
            output_text = f"✅ Research completed on: {topic}\n\n"
            output_text += f"📊 Papers analyzed: {len(papers)}\n"
            output_text += f"🔍 Sources: {', '.join(sorted(sources_used))}\n"
            output_text += f"📁 Report saved to: {report_path}\n\n"
            
            # Create interactive summary components
            summary_components = self._create_summary_components(summaries, summary_style)
            
            return output_text, summary_components, summaries
            
        except Exception as e:
            error_msg = f"❌ Error during research: {str(e)}"
            self.logger.log(error_msg)
            return error_msg, "", []
    
    def _create_summary_components(self, summaries, style):
        """Create interactive summary components for the interface"""
        components = []
        
        for i, summary_data in enumerate(summaries, 1):
            paper = summary_data['paper']
            summary = summary_data['summary']
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
