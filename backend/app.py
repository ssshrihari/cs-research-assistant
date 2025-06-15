from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import logging
from backend.utils.arxiv_client import ArxivClient
from backend.utils.pdf_processor_resilient import PDFProcessor  
from backend.models.summarizer import PaperSummarizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize components
try:
    arxiv_client = ArxivClient()
    pdf_processor = PDFProcessor()
    summarizer = PaperSummarizer()
    logger.info("All components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    arxiv_client = None
    pdf_processor = None
    summarizer = None

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'components': {
            'arxiv_client': arxiv_client is not None,
            'pdf_processor': pdf_processor is not None,
            'summarizer': summarizer is not None
        }
    })

@app.route('/api/search', methods=['POST'])
def search_papers():
    try:
        if not arxiv_client:
            return jsonify({
                'success': False,
                'error': 'ArXiv client not initialized'
            }), 500
            
        data = request.json
        query = data.get('query', '')
        max_results = data.get('max_results', 10)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        logger.info(f"Searching for papers with query: {query}")
        papers = arxiv_client.search_papers(query, max_results)
        
        return jsonify({
            'success': True,
            'papers': papers,
            'count': len(papers)
        })
        
    except Exception as e:
        logger.error(f"Error in search_papers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/summarize', methods=['POST'])
def summarize_paper():
    try:
        if not summarizer or not pdf_processor:
            return jsonify({
                'success': False,
                'error': 'Summarizer not initialized'
            }), 500
            
        data = request.json
        paper_url = data.get('paper_url', '')
        paper_text = data.get('paper_text', '')
        
        if not paper_url and not paper_text:
            return jsonify({
                'success': False,
                'error': 'Either paper_url or paper_text is required'
            }), 400
        
        # Extract text from PDF if URL provided
        if paper_url and not paper_text:
            logger.info(f"Extracting text from PDF: {paper_url}")
            paper_text = pdf_processor.extract_text_from_url(paper_url)
            
            if not paper_text:
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract text from PDF'
                }), 500
        
        logger.info("Generating summary...")
        summary = summarizer.generate_summary(paper_text)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error in summarize_paper: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    try:
        if not summarizer:
            return jsonify({
                'success': False,
                'error': 'Summarizer not initialized'
            }), 500
            
        data = request.json
        question = data.get('question', '')
        paper_text = data.get('paper_text', '')
        paper_url = data.get('paper_url', '')
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        # Extract text from PDF if URL provided and no text given
        if paper_url and not paper_text and pdf_processor:
            logger.info(f"Extracting text from PDF for Q&A: {paper_url}")
            paper_text = pdf_processor.extract_text_from_url(paper_url)
        
        if not paper_text:
            return jsonify({
                'success': False,
                'error': 'Paper text is required for Q&A'
            }), 400
        
        logger.info(f"Answering question: {question}")
        answer = summarizer.answer_question(question, paper_text)
        
        return jsonify({
            'success': True,
            'answer': answer
        })
        
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)# Ensure proper port handling for deployment
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
