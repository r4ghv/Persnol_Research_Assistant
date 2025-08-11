import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any

class Config:
    """Central configuration class for the Research Assistant application"""
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Directory configurations
        self.BASE_DIR = Path(__file__).parent.parent
        self.OUTPUT_DIR = self.BASE_DIR / "research_output"
        
        # API configurations
        self.OPENAI_API_KEY = self._get_env_var("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
        
        # Research parameters
        self.MAX_PAPERS = int(os.getenv("MAX_PAPERS", 5))
        self.MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", 10))
        
        # Network settings
        self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
        self.RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", 3))
        self.RETRY_DELAY = float(os.getenv("RETRY_DELAY", 2.0))
        
        # Initialize directories
        self._init_directories()
        self._validate_config()

    def _get_env_var(self, var_name: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Missing required environment variable: {var_name}")
        return value

    def _init_directories(self):
        """Create necessary directories if they don't exist"""
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        (self.OUTPUT_DIR / "papers").mkdir(exist_ok=True)
        (self.OUTPUT_DIR / "summaries").mkdir(exist_ok=True)
        (self.OUTPUT_DIR / "reports").mkdir(exist_ok=True)
        (self.BASE_DIR / "logs").mkdir(exist_ok=True)

    def _validate_config(self):
        """Validate configuration values"""
        if self.MAX_TOKENS > 4000:
            raise ValueError("MAX_TOKENS cannot exceed 4000 for GPT-3.5-turbo")
        if not self.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")

    def get_logging_config(self) -> Dict[str, Any]:
        """Return logging configuration"""
        return {
            "log_file": self.BASE_DIR / "logs" / "research_assistant.log",
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Return caching configuration"""
        return {
            "cache_dir": self.BASE_DIR / ".cache",
            "max_cache_size": int(os.getenv("MAX_CACHE_SIZE", 100))  # MB
        }
