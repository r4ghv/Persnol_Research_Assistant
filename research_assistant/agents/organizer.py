import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


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
    
    @staticmethod
    def _sanitize_filename(name: str, max_length: int = 50) -> str:
        """Sanitize a string for use as a filename"""
        safe = re.sub(r'[^\w\-]', '_', name[:max_length])
        # Collapse multiple underscores
        safe = re.sub(r'_+', '_', safe).strip('_')
        return safe
    
    def save_paper(self, paper: Dict, content: str, summary: str, pdf_data: bytes = None) -> Dict:
        """Save paper resources and return paths.
        
        Args:
            paper: Paper metadata dict.
            content: Extracted text content.
            summary: AI-generated summary.
            pdf_data: Raw PDF bytes (optional). If provided, avoids re-downloading.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self._sanitize_filename(paper['title'])}_{timestamp}"
        
        saved_files = {
            "text_path": self._save_text(content, filename),
            "summary_path": self._save_summary(summary, filename)
        }
        
        # Only save PDF if data is provided (avoids double-download)
        if pdf_data:
            saved_files["pdf_path"] = self._save_pdf_from_bytes(pdf_data, filename)
        
        return saved_files
    
    def _save_pdf_from_bytes(self, data: bytes, filename: str) -> str:
        """Save PDF from already-downloaded bytes"""
        path = os.path.join(self.output_dir, "papers/pdf", f"{filename}.pdf")
        try:
            with open(path, 'wb') as f:
                f.write(data)
        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            path = "PDF save failed"
        return path
    
    def _save_text(self, content: str, filename: str) -> str:
        """Save extracted text"""
        path = os.path.join(self.output_dir, "papers/text", f"{filename}.txt")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error saving text: {e}")
            path = "Text save failed"
        return path
    
    def _save_summary(self, summary: str, filename: str) -> str:
        """Save paper summary"""
        path = os.path.join(self.output_dir, "summaries", f"{filename}_summary.md")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# Summary\n\n{summary}")
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            path = "Summary save failed"
        return path
    
    def save_report(self, report_data: Dict) -> str:
        """Save final research report"""
        topic_slug = self._sanitize_filename(report_data['topic'])
        filename = f"{topic_slug}_report.json"
        path = os.path.join(self.output_dir, "reports", filename)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            path = "Report save failed"
        return path
