from transformers import pipeline, AutoTokenizer
import re
import torch
import logging

logger = logging.getLogger(__name__)

# Try to import NLTK safely
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
    
    # Try to ensure NLTK data is available
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            pass
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available, using basic text processing")

def safe_sentence_tokenize(text):
    """Safely tokenize sentences with fallback"""
    if NLTK_AVAILABLE:
        try:
            return sent_tokenize(text)
        except:
            pass
    
    # Fallback: split by periods, exclamation marks, and question marks
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() + '.' for s in sentences if len(s.strip()) > 10]

class PaperSummarizer:
    def __init__(self):
        """Initialize the summarization and Q&A models"""
        self.device = -1  # Use CPU for stability
        logger.info("Initializing PaperSummarizer...")
        
        # Initialize models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize all required models"""
        try:
            logger.info("Loading AI models... This may take a moment...")
            
            # Summarization model
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=self.device
            )
            
            # Q&A model
            self.qa_pipeline = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=self.device
            )
            
            logger.info("✅ All AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading AI models: {e}")
            logger.info("�� Falling back to rule-based methods")
            self.summarizer = None
            self.qa_pipeline = None
    
    def generate_summary(self, paper_text):
        """Generate a comprehensive summary of the research paper"""
        try:
            if not paper_text or len(paper_text.strip()) < 100:
                return "Unable to generate summary: insufficient text content."
            
            logger.info(f"Generating summary for text of length: {len(paper_text)}")
            
            if self.summarizer:
                return self._generate_ai_summary(paper_text)
            else:
                return self._generate_rule_based_summary(paper_text)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error generating summary. Please try again."
    
    def _generate_ai_summary(self, paper_text):
        """Generate summary using AI models"""
        try:
            # Split into chunks
            chunks = self._split_text_into_chunks(paper_text, 1000)
            summaries = []
            
            for i, chunk in enumerate(chunks[:3]):  # Process first 3 chunks
                if len(chunk.strip()) > 200:
                    logger.info(f"Processing chunk {i+1}/{min(3, len(chunks))}")
                    summary = self.summarizer(
                        chunk,
                        max_length=100,
                        min_length=30,
                        do_sample=False,
                        truncation=True
                    )
                    summaries.append(summary[0]['summary_text'])
            
            combined = ' '.join(summaries)
            return self._format_summary(combined)
            
        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            return self._generate_rule_based_summary(paper_text)
    
    def _generate_rule_based_summary(self, paper_text):
        """Generate summary using rule-based extraction"""
        try:
            sentences = safe_sentence_tokenize(paper_text)
            
            # Score sentences
            important_keywords = [
                'propose', 'present', 'introduce', 'develop', 'algorithm',
                'method', 'approach', 'results', 'performance', 'evaluation',
                'novel', 'new', 'contribution', 'significant', 'improvement'
            ]
            
            scored_sentences = []
            for i, sentence in enumerate(sentences[:30]):
                score = 0
                sentence_lower = sentence.lower()
                
                # Position bonus (earlier = more important)
                if i < 5:
                    score += 3
                elif i < 15:
                    score += 2
                
                # Keyword bonus
                for keyword in important_keywords:
                    if keyword in sentence_lower:
                        score += 2
                
                # Length bonus (prefer medium sentences)
                word_count = len(sentence.split())
                if 15 <= word_count <= 40:
                    score += 1
                
                scored_sentences.append((sentence, score))
            
            # Get top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [sent[0] for sent in scored_sentences[:4]]
            
            summary = ' '.join(top_sentences)
            return self._format_summary(summary)
            
        except Exception as e:
            logger.error(f"Rule-based summarization failed: {e}")
            return "Unable to generate summary at this time."
    
    def _format_summary(self, summary_text):
        """Format the summary nicely"""
        formatted = f"""**📝 Paper Summary:**

**Key Points:**
{summary_text}

**Note:** This summary was generated using AI analysis of the paper content.
        """
        return formatted.strip()
    
    def _split_text_into_chunks(self, text, chunk_size):
        """Split text into chunks"""
        sentences = safe_sentence_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def answer_question(self, question, paper_text):
        """Answer a question about the paper"""
        try:
            if not question or not paper_text:
                return "Please provide both a question and paper text."
            
            logger.info(f"Answering question: {question[:50]}...")
            
            if self.qa_pipeline:
                return self._answer_with_ai(question, paper_text)
            else:
                return self._answer_with_rules(question, paper_text)
                
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return "I'm unable to answer that question at the moment."
    
    def _answer_with_ai(self, question, paper_text):
        """Answer using AI Q&A"""
        try:
            # Limit text length
            if len(paper_text) > 3000:
                paper_text = paper_text[:3000]
            
            result = self.qa_pipeline(
                question=question,
                context=paper_text
            )
            
            return result['answer']
            
        except Exception as e:
            logger.error(f"AI Q&A failed: {e}")
            return self._answer_with_rules(question, paper_text)
    
    def _answer_with_rules(self, question, paper_text):
        """Answer using simple keyword matching"""
        try:
            sentences = safe_sentence_tokenize(paper_text)
            question_words = set(question.lower().split())
            
            best_sentence = ""
            best_score = 0
            
            for sentence in sentences[:50]:
                sentence_words = set(sentence.lower().split())
                overlap = len(question_words.intersection(sentence_words))
                
                if overlap > best_score:
                    best_score = overlap
                    best_sentence = sentence
            
            if best_score > 1:
                return best_sentence
            else:
                return "I couldn't find specific information to answer your question."
                
        except Exception as e:
            logger.error(f"Rule-based Q&A failed: {e}")
            return "I'm having trouble processing your question."
