# CS Research Assistant

An AI-powered tool for discovering, summarizing, and exploring computer science research papers.

## Features

- 🔍 Search ArXiv for CS papers
- 📝 AI-powered paper summarization
- 💬 Interactive Q&A about papers
- 📄 PDF processing and analysis
- 🎯 CS-focused with domain expertise

## Setup

1. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Test the setup:
   ```bash
   python test_setup.py
   ```

4. Run the application:
   ```bash
   python backend/app.py
   ```

5. Open your browser to: http://localhost:5001

## Deployment

### Heroku
```bash
heroku create your-app-name
git push heroku main
```

### Railway
```bash
railway login
railway init
railway up
```

## Requirements

- Python 3.9+
- macOS with Apple Silicon (M1/M2) recommended
- 4GB+ RAM for AI models
- Internet connection for ArXiv API

## Technology Stack

- **Backend**: Flask, PyTorch, Transformers
- **Frontend**: Vanilla JavaScript, Modern CSS
- **AI Models**: BART, DistilBERT
- **Data**: ArXiv API, PyMuPDF

