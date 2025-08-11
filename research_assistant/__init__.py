# Research Assistant Package
"""Personal Research Assistant using OpenAI and Gradio"""

__version__ = "1.0.0"
__author__ = "Research Assistant Team"

# Import main components
from .agents import Scraper, Researcher, Summarizer, Organizer
from .utils import Logger, Config

__all__ = [
    'Scraper',
    'Researcher', 
    'Summarizer',
    'Organizer',
    'Logger',
    'Config'
]
