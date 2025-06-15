import fitz  # PyMuPDF
import requests
import tempfile
import os
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        """Initialize PDF processor"""
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.timeout = 60  # 60 seconds timeout
        logger.info("PDF processor initialized")
    
    def extract_text_from_url(self, pdf_url):
        """
        Download PDF from URL and extract text
        
        Args:
            pdf_url (str): URL to the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        try:
            logger.info(f"Starting PDF download from: {pdf_url}")
            
            # Validate URL
            if not self._is_valid_url(pdf_url):
                logger.error(f"Invalid URL: {pdf_url}")
                return ""
            
            # Download PDF with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
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
                return ""
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                # Download in chunks to handle large files
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            logger.info(f"PDF downloaded successfully to: {tmp_file_path}")
            
            # Extract text
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
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error processing PDF from URL: {e}")
            return ""
    
    def extract_text_from_file(self, file_path):
        """
        Extract text from a local PDF file
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        try:
            logger.info(f"Extracting text from: {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return ""
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes")
                return ""
            
            doc = fitz.open(file_path)
            text = ""
            
            # Extract text from each page
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
            
            # Clean and process the text
            text = self.clean_text(text)
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF file: {e}")
            return ""
    
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
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newline
        text = re.sub(r'[ \t]+', ' ', text)      # Replace multiple spaces/tabs with single space
        
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # Remove standalone page numbers
        text = re.sub(r'\n\s*Page \d+.*?\n', '\n', text)  # Remove "Page X" lines
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        
        # Remove URLs and email addresses for cleaner text
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up excessive whitespace again
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_sections(self, text):
        """
        Extract common academic paper sections
        
        Args:
            text (str): Full paper text
            
        Returns:
            dict: Dictionary containing extracted sections
        """
        sections = {}
        
        # Define section patterns (case-insensitive)
        section_patterns = {
            'abstract': [
                r'(?i)\babstract\b\s*\n(.*?)(?=\n\s*(?:introduction|1\.|keywords|index terms))',
                r'(?i)\babstract\b[:\s]+(.*?)(?=\n\s*[A-Z][a-z]+:|\n\s*\d+\.)',
            ],
            'introduction': [
                r'(?i)(?:1\.|introduction)\s*\n(.*?)(?=\n\s*(?:2\.|related work|background|methodology))',
                r'(?i)\bintroduction\b\s*\n(.*?)(?=\n\s*[A-Z][a-z]+|\n\s*\d+\.)',
            ],
            'methodology': [
                r'(?i)(?:methodology|method|approach|algorithm)\s*\n(.*?)(?=\n\s*(?:\d+\.|results|experiments|evaluation))',
            ],
            'results': [
                r'(?i)(?:results|experiments|evaluation|experimental results)\s*\n(.*?)(?=\n\s*(?:\d+\.|conclusion|discussion|related work))',
            ],
            'conclusion': [
                r'(?i)(?:conclusion|conclusions|summary)\s*\n(.*?)(?=\n\s*(?:references|bibliography|acknowledgment|\Z))',
            ],
            'related_work': [
                r'(?i)(?:related work|literature review|background)\s*\n(.*?)(?=\n\s*(?:\d+\.|methodology|approach))',
            ]
        }
        
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    section_text = match.group(1).strip()
                    # Clean up the section text
                    section_text = re.sub(r'\n+', ' ', section_text)
                    section_text = re.sub(r'\s+', ' ', section_text)
                    
                    # Limit section length
                    if len(section_text) > 2000:
                        section_text = section_text[:2000] + "..."
                    
                    sections[section_name] = section_text
                    logger.info(f"Extracted {section_name} section ({len(section_text)} chars)")
                    break
        
        return sections
    
    def extract_metadata(self, file_path):
        """
        Extract metadata from PDF file
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: PDF metadata
        """
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            doc.close()
            
            # Clean and format metadata
            cleaned_metadata = {}
            for key, value in metadata.items():
                if value:
                    cleaned_metadata[key.lower()] = str(value).strip()
            
            return cleaned_metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def _is_valid_url(self, url):
        """
        Validate if the URL is properly formatted and accessible
        
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
    
    def count_pages_from_url(self, pdf_url):
        """
        Get the number of pages in a PDF without extracting all text
        
        Args:
            pdf_url (str): URL to the PDF file
            
        Returns:
            int: Number of pages, or 0 if error
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(pdf_url, timeout=30, headers=headers, stream=True)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            doc = fitz.open(tmp_file_path)
            page_count = doc.page_count
            doc.close()
            
            os.unlink(tmp_file_path)
            
            return page_count
            
        except Exception as e:
            logger.error(f"Error counting pages: {e}")
            return 0