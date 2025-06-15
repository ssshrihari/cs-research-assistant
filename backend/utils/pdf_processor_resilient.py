import requests
import tempfile
import os
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Try different PDF libraries in order of preference
PDF_LIBRARY = None

# Option 1: Try PyMuPDF
try:
    import fitz
    PDF_LIBRARY = "pymupdf"
    logger.info("Using PyMuPDF for PDF processing")
except ImportError:
    pass

# Option 2: Try pdfplumber
if PDF_LIBRARY is None:
    try:
        import pdfplumber
        PDF_LIBRARY = "pdfplumber"
        logger.info("Using pdfplumber for PDF processing")
    except ImportError:
        pass

# Option 3: Try PyPDF2
if PDF_LIBRARY is None:
    try:
        import PyPDF2
        PDF_LIBRARY = "pypdf2"
        logger.info("Using PyPDF2 for PDF processing")
    except ImportError:
        pass

if PDF_LIBRARY is None:
    logger.warning("No PDF library available - PDF processing will be disabled")

class PDFProcessor:
    def __init__(self):
        """Initialize PDF processor with available library"""
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.timeout = 60  # 60 seconds timeout
        self.library = PDF_LIBRARY
        logger.info(f"PDF processor initialized with library: {self.library}")
    
    def extract_text_from_url(self, pdf_url):
        """
        Download PDF from URL and extract text
        
        Args:
            pdf_url (str): URL to the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        if self.library is None:
            logger.error("No PDF library available")
            return "PDF processing not available - no PDF library installed."
        
        try:
            logger.info(f"Starting PDF download from: {pdf_url}")
            
            # Validate URL
            if not self._is_valid_url(pdf_url):
                logger.error(f"Invalid URL: {pdf_url}")
                return ""
            
            # Download PDF with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'
            }
            
            response = requests.get(
                pdf_url, 
                timeout=self.timeout,
                headers=headers,
                stream=True
            )
            response.raise_for_status()
            
            # Check file size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                logger.error(f"File too large: {content_length} bytes")
                return "File too large to process."
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                # Download in chunks
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            logger.info(f"PDF downloaded successfully to: {tmp_file_path}")
            
            # Extract text using available library
            text = self.extract_text_from_file(tmp_file_path)
            
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
                logger.info("Temporary file cleaned up")
            except OSError:
                logger.warning("Failed to delete temporary file")
            
            return text
            
        except requests.exceptions.Timeout:
            logger.error("PDF download timed out")
            return "PDF download timed out. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF: {e}")
            return "Error downloading PDF. Please check the URL."
        except Exception as e:
            logger.error(f"Unexpected error processing PDF from URL: {e}")
            return "Error processing PDF."
    
    def extract_text_from_file(self, file_path):
        """
        Extract text from a local PDF file using available library
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        if self.library is None:
            return "PDF processing not available."
        
        try:
            logger.info(f"Extracting text from: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return ""
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes")
                return "File too large to process."
            
            # Extract text based on available library
            if self.library == "pymupdf":
                text = self._extract_with_pymupdf(file_path)
            elif self.library == "pdfplumber":
                text = self._extract_with_pdfplumber(file_path)
            elif self.library == "pypdf2":
                text = self._extract_with_pypdf2(file_path)
            else:
                return "No PDF processing library available."
            
            # Clean and process the text
            text = self.clean_text(text)
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF file: {e}")
            return f"Error extracting text: {str(e)}"
    
    def _extract_with_pymupdf(self, file_path):
        """Extract text using PyMuPDF"""
        import fitz
        
        doc = fitz.open(file_path)
        text = ""
        
        for page_num in range(min(doc.page_count, 50)):  # Limit to first 50 pages
            try:
                page = doc[page_num]
                page_text = page.get_text()
                text += page_text + "\n"
                logger.debug(f"Extracted text from page {page_num + 1}")
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                continue
        
        doc.close()
        return text
    
    def _extract_with_pdfplumber(self, file_path):
        """Extract text using pdfplumber"""
        import pdfplumber
        
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages[:50]):  # Limit to first 50 pages
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    logger.debug(f"Extracted text from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                    continue
        
        return text
    
    def _extract_with_pypdf2(self, file_path):
        """Extract text using PyPDF2"""
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(min(len(pdf_reader.pages), 50)):  # Limit to first 50 pages
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text + "\n"
                    logger.debug(f"Extracted text from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                    continue
        
        return text
    
    def clean_text(self, text):
        """
        Clean and preprocess extracted text
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines
        text = re.sub(r'[ \t]+', ' ', text)      # Replace multiple spaces/tabs
        
        # Remove page numbers and headers/footers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # Remove standalone page numbers
        text = re.sub(r'\n\s*Page \d+.*?\n', '\n', text)  # Remove "Page X" lines
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        
        # Remove URLs and email addresses
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up excessive whitespace again
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _is_valid_url(self, url):
        """
        Validate if the URL is properly formatted
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def get_text_preview(self, text, max_length=500):
        """
        Get a preview of the extracted text
        
        Args:
            text (str): Full text
            max_length (int): Maximum length of preview
            
        Returns:
            str: Text preview
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # Try to break at sentence boundary
        preview = text[:max_length]
        last_period = preview.rfind('.')
        if last_period > max_length // 2:
            preview = preview[:last_period + 1]
        else:
            preview = preview + "..."
        
        return preview
    
    def is_available(self):
        """Check if PDF processing is available"""
        return self.library is not None
    
    def get_library_info(self):
        """Get information about the PDF library being used"""
        return {
            "library": self.library,
            "available": self.library is not None,
            "supported_formats": ["pdf"] if self.library else []
        }