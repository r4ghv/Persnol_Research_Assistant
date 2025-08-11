import os
import json
from datetime import datetime
from typing import Dict, List
import requests

class Organizer:
    def __init__(self, output_dir: str = "research_output"):
        self.output_dir = os.path.abspath(output_dir)
        self._init_directory_structure()
    
    def _init_directory_structure(self):
        """Create required subdirectories"""
        subdirs = [
            "papers/pdf",
            "papers/text",
            "summaries",
            "notes",
            "reports"
        ]
        for subdir in subdirs:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
    
    def save_paper(self, paper: Dict, content: str, summary: str) -> Dict:
        """Save paper resources and return paths"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{paper['title'][:50].replace(' ', '_')}_{timestamp}"
        
        saved_files = {
            "pdf_path": self._save_pdf(paper['pdf_url'], filename),
            "text_path": self._save_text(content, filename),
            "summary_path": self._save_summary(summary, filename)
        }
        
        return saved_files
    
    def _save_pdf(self, url: str, filename: str) -> str:
        """Download and save PDF"""
        path = os.path.join(self.output_dir, "papers/pdf", f"{filename}.pdf")
        if not os.path.exists(path):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                with open(path, 'wb') as f:
                    f.write(response.content)
            except Exception as e:
                print(f"Error downloading PDF: {str(e)}")
                path = "PDF download failed"
        return path
    
    def _save_text(self, content: str, filename: str) -> str:
        """Save extracted text"""
        path = os.path.join(self.output_dir, "papers/text", f"{filename}.txt")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error saving text: {str(e)}")
            path = "Text save failed"
        return path
    
    def _save_summary(self, summary: str, filename: str) -> str:
        """Save paper summary"""
        path = os.path.join(self.output_dir, "summaries", f"{filename}_summary.md")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# Summary\n\n{summary}")
        except Exception as e:
            print(f"Error saving summary: {str(e)}")
            path = "Summary save failed"
        return path
    
    def save_report(self, report_data: Dict) -> str:
        """Save final research report"""
        filename = f"{report_data['topic'].replace(' ', '_')}_report.json"
        path = os.path.join(self.output_dir, "reports", filename)
        try:
            with open(path, 'w') as f:
                json.dump(report_data, f, indent=2)
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            path = "Report save failed"
        return path
    
    def organize(self, summaries: List[Dict]) -> None:
        """Legacy method for compatibility"""
        for summary in summaries:
            try:
                # This would organize summaries in a real implementation
                print(f"Organizing summary: {summary.get('title', 'Unknown')}")
            except Exception as e:
                print(f"Error organizing summary: {str(e)}")
