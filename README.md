# 🔬 Personal Research Assistant

A comprehensive research assistant that uses OpenAI GPT and Gradio to fetch academic papers, generate summaries, and organize research notes.

## Features

- **Web Scraping**: Fetches research papers from arXiv
- **AI Summarization**: Uses OpenAI GPT to generate intelligent summaries
- **File Organization**: Automatically organizes papers, summaries, and reports
- **Modern UI**: Beautiful Gradio-based interface
- **PDF Processing**: Extracts text content from PDF papers
- **Caching**: Intelligent caching to avoid re-downloading papers

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory with your OpenAI API key:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# OpenAI Model Configuration
OPENAI_MODEL=gpt-4o-mini
MAX_TOKENS=8000

# Research Parameters
MAX_PAPERS=5
MAX_PDF_PAGES=10

# Network Settings
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=2.0

# Logging
LOG_LEVEL=INFO

# Cache Settings
MAX_CACHE_SIZE=100
```

### 3. Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and paste it in your `.env` file

## Usage

### Running the Application

```bash
python main.py
```

The application will start and open in your browser at `http://localhost:7860`

### Using the Interface

1. **Enter Research Topic**: Type your research topic (e.g., "machine learning", "quantum computing")
2. **Set Parameters**: Choose the number of papers to analyze and summary style
3. **Start Research**: Click the "Start Research" button
4. **View Results**: The system will fetch papers, generate summaries, and organize files

### Summary Styles

- **Bullet Points**: Concise key findings
- **Paragraph**: 150-word summary
- **Technical**: Detailed technical analysis

## Project Structure

```
ResearchAssistant/
├── main.py                          # Main Gradio application
├── config.py                        # Configuration management
├── requirements.txt                 # Python dependencies
├── research_assistant/
│   ├── agents/                     # AI agents for different tasks
│   │   ├── scraper.py             # Paper fetching from arXiv
│   │   ├── summarizer.py          # OpenAI-based summarization
│   │   ├── organizer.py           # File organization
│   │   └── researcher.py          # Research coordination
│   └── utils/                      # Utility functions
│       ├── file_utils.py          # File operations
│       └── logger.py              # Logging utilities
└── research_output/                 # Generated research files
    ├── papers/                     # Downloaded papers
    ├── summaries/                  # Generated summaries
    ├── reports/                    # Research reports
    └── notes/                      # Research notes
```

## Example Research Topics

- **Machine Learning**: Recent advances in deep learning
- **Quantum Computing**: Quantum algorithms and applications
- **Climate Science**: Impact of climate change on ecosystems
- **Biotechnology**: CRISPR gene editing technology
- **Astrophysics**: Dark matter and dark energy research

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Ensure your API key is correctly set in the `.env` file
2. **PDF Download Issues**: Check your internet connection and firewall settings
3. **Memory Issues**: Reduce `MAX_PAPERS` and `MAX_PDF_PAGES` in your config
4. **Rate Limiting**: OpenAI has rate limits; wait between requests if needed

### Logs

Check the `logs/` directory for detailed error logs and debugging information.

## Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving the UI
- Adding new data sources
- Optimizing performance

## License

This project is open source and available under the MIT License.

## Acknowledgments

- OpenAI for providing the GPT API
- Gradio for the beautiful web interface
- arXiv for providing access to research papers
- PyMuPDF for PDF text extraction
