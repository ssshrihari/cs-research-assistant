import arxiv
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ArxivClient:
    def __init__(self):
        """Initialize ArXiv client with optimized settings"""
        self.client = arxiv.Client(
            page_size=10,
            delay_seconds=2.0,  # Respectful delay between requests
            num_retries=3
        )
        logger.info("ArXiv client initialized")
    
    def search_papers(self, query, max_results=10):
        """
        Search ArXiv for papers related to the query, focusing on CS papers
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of paper dictionaries
        """
        try:
            # Enhance query to focus on computer science papers
            enhanced_query = self._enhance_cs_query(query)
            logger.info(f"Enhanced query: {enhanced_query}")
            
            search = arxiv.Search(
                query=enhanced_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                paper = self._format_paper(result)
                papers.append(paper)
                logger.info(f"Found paper: {paper['title'][:50]}...")
            
            logger.info(f"Successfully retrieved {len(papers)} papers")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching ArXiv: {e}")
            return []
    
    def _enhance_cs_query(self, query):
        """
        Enhance the search query to focus on computer science papers
        
        Args:
            query (str): Original query
            
        Returns:
            str: Enhanced query with CS categories
        """
        # CS categories in ArXiv
        cs_categories = [
            "cs.AI",      # Artificial Intelligence
            "cs.LG",      # Machine Learning
            "cs.DC",      # Distributed Computing
            "cs.DS",      # Data Structures and Algorithms
            "cs.SE",      # Software Engineering
            "cs.SY",      # Systems and Control
            "cs.CR",      # Cryptography and Security
            "cs.DB",      # Databases
            "cs.NI",      # Networking
            "cs.PL",      # Programming Languages
            "cs.CV",      # Computer Vision
            "cs.CL",      # Computation and Language
            "cs.IR",      # Information Retrieval
            "cs.HCI",     # Human-Computer Interaction
        ]
        
        # Create category filter
        cat_filter = " OR ".join([f"cat:{cat}" for cat in cs_categories])
        
        # Combine with original query
        enhanced_query = f"({cat_filter}) AND ({query})"
        
        return enhanced_query
    
    def _format_paper(self, result):
        """
        Format ArXiv result into a standardized paper dictionary
        
        Args:
            result: ArXiv result object
            
        Returns:
            dict: Formatted paper information
        """
        # Extract ArXiv ID from the full URL
        arxiv_id = result.entry_id.split('/')[-1]
        
        # Clean and format abstract
        abstract = self._clean_abstract(result.summary)
        
        paper = {
            'id': arxiv_id,
            'title': result.title.strip(),
            'authors': [str(author).strip() for author in result.authors],
            'authors_string': ', '.join([str(author) for author in result.authors[:3]]) + 
                            ('...' if len(result.authors) > 3 else ''),
            'abstract': abstract,
            'published': result.published.strftime('%Y-%m-%d'),
            'published_formatted': result.published.strftime('%B %d, %Y'),
            'pdf_url': result.pdf_url,
            'arxiv_url': result.entry_id,
            'categories': result.categories,
            'primary_category': result.primary_category,
            'category_description': self._get_category_description(result.primary_category)
        }
        
        return paper
    
    def _clean_abstract(self, abstract):
        """
        Clean and format the abstract text
        
        Args:
            abstract (str): Raw abstract text
            
        Returns:
            str: Cleaned abstract
        """
        # Remove excessive whitespace and newlines
        abstract = re.sub(r'\s+', ' ', abstract)
        
        # Remove common LaTeX artifacts
        abstract = re.sub(r'\$.*?\$', '', abstract)  # Remove LaTeX math
        abstract = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', abstract)  # Remove LaTeX commands
        
        # Truncate if too long (for UI purposes)
        if len(abstract) > 500:
            abstract = abstract[:497] + "..."
        
        return abstract.strip()
    
    def _get_category_description(self, category):
        """
        Get human-readable description for ArXiv category
        
        Args:
            category (str): ArXiv category code
            
        Returns:
            str: Human-readable description
        """
        descriptions = {
            'cs.AI': 'Artificial Intelligence',
            'cs.LG': 'Machine Learning',
            'cs.DC': 'Distributed Computing',
            'cs.DS': 'Data Structures and Algorithms',
            'cs.SE': 'Software Engineering',
            'cs.SY': 'Systems and Control',
            'cs.CR': 'Cryptography and Security',
            'cs.DB': 'Databases',
            'cs.NI': 'Networking',
            'cs.PL': 'Programming Languages',
            'cs.CV': 'Computer Vision',
            'cs.CL': 'Natural Language Processing',
            'cs.IR': 'Information Retrieval',
            'cs.HCI': 'Human-Computer Interaction',
            'cs.RO': 'Robotics',
            'cs.GT': 'Computer Science and Game Theory',
            'cs.CC': 'Computational Complexity',
            'cs.CG': 'Computational Geometry',
            'cs.ET': 'Emerging Technologies',
            'cs.FL': 'Formal Languages and Automata',
            'cs.GL': 'General Literature',
            'cs.GR': 'Graphics',
            'cs.HC': 'Human-Computer Interaction',
            'cs.IT': 'Information Theory',
            'cs.LO': 'Logic in Computer Science',
            'cs.MA': 'Multiagent Systems',
            'cs.MM': 'Multimedia',
            'cs.MS': 'Mathematical Software',
            'cs.NA': 'Numerical Analysis',
            'cs.NE': 'Neural and Evolutionary Computing',
            'cs.OH': 'Other Computer Science',
            'cs.OS': 'Operating Systems',
            'cs.PF': 'Performance',
            'cs.SC': 'Symbolic Computation',
            'cs.SD': 'Sound'
        }
        
        return descriptions.get(category, category)
    
    def get_paper_by_id(self, paper_id):
        """
        Get a specific paper by its ArXiv ID
        
        Args:
            paper_id (str): ArXiv paper ID
            
        Returns:
            dict or None: Paper information or None if not found
        """
        try:
            search = arxiv.Search(id_list=[paper_id])
            
            for result in self.client.results(search):
                paper = self._format_paper(result)
                logger.info(f"Retrieved paper by ID: {paper['title']}")
                return paper
                
            logger.warning(f"No paper found with ID: {paper_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching paper by ID {paper_id}: {e}")
            return None
    
    def search_by_author(self, author_name, max_results=10):
        """
        Search for papers by a specific author
        
        Args:
            author_name (str): Author name to search for
            max_results (int): Maximum number of results
            
        Returns:
            list: List of papers by the author
        """
        try:
            query = f"au:{author_name}"
            enhanced_query = self._enhance_cs_query(query)
            
            search = arxiv.Search(
                query=enhanced_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            papers = []
            for result in self.client.results(search):
                paper = self._format_paper(result)
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers by author: {author_name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching by author {author_name}: {e}")
            return []