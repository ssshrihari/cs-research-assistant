// API Configuration
const API_BASE_URL = window.location.origin;

// Global state
let currentPaper = null;
let currentPaperText = null;

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const resultsSection = document.getElementById('resultsSection');
const papersContainer = document.getElementById('papersContainer');
const resultsCount = document.getElementById('resultsCount');
const summaryModal = document.getElementById('summaryModal');
const closeModal = document.getElementById('closeModal');
const summaryContent = document.getElementById('summaryContent');
const qaInput = document.getElementById('qaInput');
const qaBtn = document.getElementById('qaBtn');
const qaHistory = document.getElementById('qaHistory');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const statusIndicator = document.getElementById('statusIndicator');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const errorToast = document.getElementById('errorToast');
const successToast = document.getElementById('successToast');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkServerHealth();
});

function initializeApp() {
    // Set up suggestion tags
    const suggestionTags = document.querySelectorAll('.suggestion-tag');
    suggestionTags.forEach(tag => {
        tag.addEventListener('click', () => {
            const query = tag.dataset.query;
            searchInput.value = query;
            searchPapers();
        });
    });

    // Set up Q&A suggestion buttons
    const qaSuggestionBtns = document.querySelectorAll('.qa-suggestion-btn');
    qaSuggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.dataset.question;
            qaInput.value = question;
            askQuestion();
        });
    });

    // Set up modal tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            // Update active tab button
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update active tab content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetTab + 'Tab') {
                    content.classList.add('active');
                }
            });
        });
    });
}

function setupEventListeners() {
    // Search functionality
    searchBtn.addEventListener('click', searchPapers);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchPapers();
    });

    // Modal functionality
    closeModal.addEventListener('click', closeSummaryModal);
    summaryModal.addEventListener('click', (e) => {
        if (e.target === summaryModal) closeSummaryModal();
    });

    // Q&A functionality
    qaBtn.addEventListener('click', askQuestion);
    qaInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') askQuestion();
    });

    // File upload
    fileInput.addEventListener('change', handleFileUpload);

    // Toast close buttons
    document.getElementById('toastClose').addEventListener('click', () => {
        errorToast.classList.remove('show');
    });
    document.getElementById('successClose').addEventListener('click', () => {
        successToast.classList.remove('show');
    });

    // Auto-hide toasts
    setTimeout(() => {
        errorToast.classList.remove('show');
        successToast.classList.remove('show');
    }, 5001);
}

async function checkServerHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateStatus('connected', 'Connected to AI service');
        } else {
            updateStatus('error', 'Service partially available');
        }
    } catch (error) {
        updateStatus('error', 'Cannot connect to server');
        console.error('Health check failed:', error);
    }
}

function updateStatus(type, message) {
    statusDot.className = `status-dot ${type}`;
    statusText.textContent = message;
}

async function searchPapers() {
    const query = searchInput.value.trim();
    if (!query) {
        showError('Please enter a search query');
        return;
    }

    setSearchLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                max_results: 10
            })
        });

        const data = await response.json();

        if (data.success) {
            displayPapers(data.papers);
            showSuccess(`Found ${data.papers.length} papers`);
        } else {
            throw new Error(data.error || 'Search failed');
        }

    } catch (error) {
        console.error('Search error:', error);
        showError(`Search failed: ${error.message}`);
        // Show fallback message
        papersContainer.innerHTML = `
            <div class="error-message">
                <h3>Search temporarily unavailable</h3>
                <p>Please try again in a moment or check your connection.</p>
            </div>
        `;
        resultsSection.style.display = 'block';
    } finally {
        setSearchLoading(false);
    }
}

function setSearchLoading(loading) {
    const btnText = searchBtn.querySelector('.btn-text');
    const btnLoading = searchBtn.querySelector('.btn-loading');
    
    searchBtn.disabled = loading;
    btnText.style.display = loading ? 'none' : 'inline';
    btnLoading.style.display = loading ? 'flex' : 'none';
}

function displayPapers(papers) {
    if (!papers || papers.length === 0) {
        papersContainer.innerHTML = `
            <div class="no-results">
                <h3>No papers found</h3>
                <p>Try different keywords or check the suggested topics above.</p>
            </div>
        `;
        resultsSection.style.display = 'block';
        return;
    }

    resultsCount.textContent = `${papers.length} paper${papers.length !== 1 ? 's' : ''} found`;
    
    papersContainer.innerHTML = papers.map(paper => `
        <div class="paper-card" data-paper-id="${paper.id}">
            <div class="paper-title" onclick="window.open('${paper.arxiv_url}', '_blank')">
                ${paper.title}
            </div>
            <div class="paper-meta">
                <div class="paper-authors">${paper.authors_string}</div>
                <div class="paper-date">${paper.published_formatted}</div>
                <div class="paper-category">${paper.category_description}</div>
            </div>
            <div class="paper-abstract">${paper.abstract}</div>
            <div class="paper-actions">
                <button class="action-btn summarize-btn" onclick="summarizePaper('${paper.id}', '${paper.pdf_url}', '${escapeHtml(paper.title)}')">
                    📝 Summarize
                </button>
                <button class="action-btn ask-btn" onclick="openQA('${paper.id}', '${paper.pdf_url}', '${escapeHtml(paper.title)}')">
                    💬 Ask Questions
                </button>
                <button class="action-btn view-btn" onclick="window.open('${paper.pdf_url}', '_blank')">
                    📄 View PDF
                </button>
            </div>
        </div>
    `).join('');

    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, '&#39;');
}

async function summarizePaper(paperId, pdfUrl, title) {
    currentPaper = { id: paperId, url: pdfUrl, title: title };
    openModal('summary');
    
    // Reset content
    summaryContent.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Downloading and analyzing paper...</p>
            <small>This may take a moment for longer papers</small>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                paper_url: pdfUrl
            })
        });

        const data = await response.json();

        if (data.success) {
            summaryContent.innerHTML = `
                <div class="summary-text">
                    ${formatSummary(data.summary)}
                </div>
            `;
            showSuccess('Summary generated successfully');
        } else {
            throw new Error(data.error || 'Summarization failed');
        }

    } catch (error) {
        console.error('Summarization error:', error);
        summaryContent.innerHTML = `
            <div class="error-message">
                <h3>Unable to generate summary</h3>
                <p>Error: ${error.message}</p>
                <p>You can still ask questions about this paper in the Q&A tab.</p>
            </div>
        `;
        showError(`Summarization failed: ${error.message}`);
    }
}

function formatSummary(summaryText) {
    // Convert markdown-style formatting to HTML
    let formatted = summaryText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    return `<p>${formatted}</p>`;
}

async function openQA(paperId, pdfUrl, title) {
    currentPaper = { id: paperId, url: pdfUrl, title: title };
    openModal('qa');
    
    // Clear previous Q&A
    qaHistory.innerHTML = '';
    qaInput.value = '';
    qaInput.focus();
}

function openModal(tab = 'summary') {
    summaryModal.style.display = 'block';
    
    // Set active tab
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tab + 'Tab');
    });
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function closeSummaryModal() {
    summaryModal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

async function askQuestion() {
    const question = qaInput.value.trim();
    if (!question || !currentPaper) {
        showError('Please enter a question');
        return;
    }

    setQALoading(true);
    
    // Add question to history immediately
    addQuestionToHistory(question, 'Thinking...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                paper_url: currentPaper.url
            })
        });

        const data = await response.json();

        if (data.success) {
            updateLastAnswer(data.answer);
            qaInput.value = '';
        } else {
            throw new Error(data.error || 'Q&A failed');
        }

    } catch (error) {
        console.error('Q&A error:', error);
        updateLastAnswer(`Sorry, I couldn't answer that question. Error: ${error.message}`);
        showError(`Q&A failed: ${error.message}`);
    } finally {
        setQALoading(false);
    }
}

function setQALoading(loading) {
    const btnText = qaBtn.querySelector('.btn-text');
    const btnLoading = qaBtn.querySelector('.btn-loading');
    
    qaBtn.disabled = loading;
    btnText.style.display = loading ? 'none' : 'inline';
    btnLoading.style.display = loading ? 'flex' : 'none';
}

function addQuestionToHistory(question, answer) {
    const qaItem = document.createElement('div');
    qaItem.className = 'qa-item';
    qaItem.innerHTML = `
        <div class="qa-question">
            <span>❓</span>
            ${question}
        </div>
        <div class="qa-answer" data-answer-id="${Date.now()}">
            ${answer}
        </div>
    `;
    
    qaHistory.appendChild(qaItem);
    qaHistory.scrollTop = qaHistory.scrollHeight;
}

function updateLastAnswer(answer) {
    const lastAnswer = qaHistory.querySelector('.qa-answer:last-child');
    if (lastAnswer) {
        lastAnswer.innerHTML = answer;
    }
}

function handleFileUpload() {
    const file = fileInput.files[0];
    if (file) {
        if (file.type !== 'application/pdf') {
            showError('Please select a PDF file');
            fileInput.value = '';
            return;
        }
        
        if (file.size > 50 * 1024 * 1024) { // 50MB limit
            showError('File size must be less than 50MB');
            fileInput.value = '';
            return;
        }
        
        fileName.textContent = `Selected: ${file.name}`;
        showSuccess('PDF selected - upload functionality coming soon!');
        
        // TODO: Implement PDF upload and processing
        // This would involve sending the file to the backend for processing
    }
}

function showError(message) {
    document.getElementById('toastMessage').textContent = message;
    errorToast.classList.add('show');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorToast.classList.remove('show');
    }, 5001);
}

function showSuccess(message) {
    document.getElementById('successMessage').textContent = message;
    successToast.classList.add('show');
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        successToast.classList.remove('show');
    }, 3000);
}

// Utility function to handle API errors
function handleApiError(error, context) {
    console.error(`${context} error:`, error);
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return 'Network error - please check your connection';
    }
    
    if (error.message.includes('404')) {
        return 'Service not found - please check if the server is running';
    }
    
    if (error.message.includes('500')) {
        return 'Server error - please try again later';
    }
    
    return error.message || 'An unexpected error occurred';
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape key to close modal
    if (e.key === 'Escape' && summaryModal.style.display === 'block') {
        closeSummaryModal();
    }
    
    // Ctrl/Cmd + Enter to search
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && document.activeElement === searchInput) {
        searchPapers();
    }
    
    // Ctrl/Cmd + Enter to ask question
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && document.activeElement === qaInput) {
        askQuestion();
    }
});

// Auto-save search history (optional enhancement)
function saveSearchHistory(query) {
    try {
        let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        history = history.filter(item => item !== query); // Remove duplicates
        history.unshift(query);
        history = history.slice(0, 10); // Keep only last 10 searches
        localStorage.setItem('searchHistory', JSON.stringify(history));
    } catch (error) {
        console.warn('Could not save search history:', error);
    }
}

function loadSearchHistory() {
    try {
        return JSON.parse(localStorage.getItem('searchHistory') || '[]');
    } catch (error) {
        console.warn('Could not load search history:', error);
        return [];
    }
}

// Enhanced search with history
function enhancedSearch() {
    const query = searchInput.value.trim();
    if (query) {
        saveSearchHistory(query);
        searchPapers();
    }
}

// Add search history dropdown (optional)
function createSearchHistoryDropdown() {
    const history = loadSearchHistory();
    if (history.length === 0) return;
    
    const dropdown = document.createElement('div');
    dropdown.className = 'search-history-dropdown';
    dropdown.innerHTML = history.map(item => `
        <div class="history-item" onclick="selectHistoryItem('${escapeHtml(item)}')">
            ${item}
        </div>
    `).join('');
    
    // Position dropdown below search input
    const searchContainer = document.querySelector('.search-container');
    searchContainer.appendChild(dropdown);
}

function selectHistoryItem(query) {
    searchInput.value = query;
    removeSearchHistoryDropdown();
    searchPapers();
}

function removeSearchHistoryDropdown() {
    const dropdown = document.querySelector('.search-history-dropdown');
    if (dropdown) {
        dropdown.remove();
    }
}

// Focus management
searchInput.addEventListener('focus', function() {
    // Could show search history dropdown here
});

searchInput.addEventListener('blur', function() {
    // Hide search history dropdown after a delay
    setTimeout(removeSearchHistoryDropdown, 200);
});

// Performance optimization: debounce search suggestions
let searchSuggestionsTimeout;
searchInput.addEventListener('input', function() {
    clearTimeout(searchSuggestionsTimeout);
    searchSuggestionsTimeout = setTimeout(() => {
        // Could implement real-time search suggestions here
        const query = searchInput.value.trim();
        if (query.length > 2) {
            // Implement search suggestions
        }
    }, 300);
});

// Analytics and usage tracking (privacy-respecting)
function trackUsage(action, details = {}) {
    // This could be used for improving the service
    // Only track anonymous usage patterns, no personal data
    console.log('Usage:', action, details);
}

// Track when user performs actions
function trackSearch(query) {
    trackUsage('search', { queryLength: query.length });
}

function trackSummarization(paperId) {
    trackUsage('summarize', { paperId });
}

function trackQuestion(question) {
    trackUsage('question', { questionLength: question.length });
}

// Error recovery and retry logic
class APIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.retryCount = 3;
        this.retryDelay = 1000;
    }
    
    async request(endpoint, options = {}) {
        for (let attempt = 0; attempt < this.retryCount; attempt++) {
            try {
                const response = await fetch(`${this.baseUrl}${endpoint}`, {
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
                
            } catch (error) {
                if (attempt === this.retryCount - 1) {
                    throw error;
                }
                
                console.warn(`Request failed (attempt ${attempt + 1}), retrying...`, error);
                await this.sleep(this.retryDelay * Math.pow(2, attempt));
            }
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize API client
const apiClient = new APIClient(API_BASE_URL);

// Enhanced API methods using the client
async function enhancedSearchPapers() {
    const query = searchInput.value.trim();
    if (!query) {
        showError('Please enter a search query');
        return;
    }

    setSearchLoading(true);
    trackSearch(query);
    
    try {
        const data = await apiClient.request('/api/search', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                max_results: 10
            })
        });

        if (data.success) {
            displayPapers(data.papers);
            showSuccess(`Found ${data.papers.length} papers`);
            saveSearchHistory(query);
        } else {
            throw new Error(data.error || 'Search failed');
        }

    } catch (error) {
        const errorMessage = handleApiError(error, 'Search');
        showError(errorMessage);
        
        // Show offline fallback if available
        showOfflineFallback();
        
    } finally {
        setSearchLoading(false);
    }
}

function showOfflineFallback() {
    papersContainer.innerHTML = `
        <div class="offline-fallback">
            <h3>🔌 Connection Issues</h3>
            <p>We're having trouble connecting to our servers. Please check:</p>
            <ul>
                <li>Your internet connection</li>
                <li>That the backend server is running</li>
                <li>Try refreshing the page</li>
            </ul>
            <button onclick="checkServerHealth()" class="retry-btn">
                🔄 Retry Connection
            </button>
        </div>
    `;
    resultsSection.style.display = 'block';
}

// Enhanced error handling with user-friendly messages
const ERROR_MESSAGES = {
    'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection.',
    'SERVER_ERROR': 'Our servers are experiencing issues. Please try again later.',
    'RATE_LIMITED': 'Too many requests. Please wait a moment before trying again.',
    'INVALID_PDF': 'Unable to process this PDF. It may be corrupted or password-protected.',
    'PDF_TOO_LARGE': 'This PDF is too large to process. Please try a smaller file.',
    'SUMMARIZATION_FAILED': 'Unable to generate summary. The paper may be too complex or in an unsupported format.',
    'QA_FAILED': 'Unable to answer the question. Try rephrasing or asking about specific sections.'
};

function getErrorMessage(error) {
    if (error.message in ERROR_MESSAGES) {
        return ERROR_MESSAGES[error.message];
    }
    return error.message || 'An unexpected error occurred';
}

// Progressive enhancement: Add features if browser supports them
if ('serviceWorker' in navigator) {
    // Could register a service worker for offline functionality
    console.log('Service Worker support detected');
}

if ('clipboard' in navigator) {
    // Add copy-to-clipboard functionality for summaries and answers
    function addCopyButtons() {
        const summaryContent = document.getElementById('summaryContent');
        const qaItems = document.querySelectorAll('.qa-item');
        
        // Add copy button to summary
        if (summaryContent && !summaryContent.querySelector('.copy-btn')) {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-btn';
            copyBtn.innerHTML = '📋 Copy Summary';
            copyBtn.onclick = () => copyToClipboard(summaryContent.textContent);
            summaryContent.appendChild(copyBtn);
        }
        
        // Add copy buttons to Q&A items
        qaItems.forEach(item => {
            if (!item.querySelector('.copy-btn')) {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-btn';
                copyBtn.innerHTML = '📋 Copy';
                copyBtn.onclick = () => copyToClipboard(item.textContent);
                item.appendChild(copyBtn);
            }
        });
    }
    
    async function copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            showSuccess('Copied to clipboard!');
        } catch (error) {
            console.error('Copy failed:', error);
            showError('Failed to copy to clipboard');
        }
    }
}

// Accessibility improvements
function enhanceAccessibility() {
    // Add ARIA labels and roles
    searchInput.setAttribute('aria-label', 'Search research papers');
    searchBtn.setAttribute('aria-label', 'Search ArXiv for papers');
    
    // Add keyboard navigation for paper cards
    const paperCards = document.querySelectorAll('.paper-card');
    paperCards.forEach((card, index) => {
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'article');
        card.setAttribute('aria-label', `Paper ${index + 1}`);
        
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const titleElement = card.querySelector('.paper-title');
                if (titleElement) {
                    titleElement.click();
                }
            }
        });
    });
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', function() {
    // Replace basic search with enhanced version
    searchBtn.removeEventListener('click', searchPapers);
    searchBtn.addEventListener('click', enhancedSearchPapers);
    
    // Enhance accessibility
    enhanceAccessibility();
    
    // Add copy functionality observer
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && 'clipboard' in navigator) {
                addCopyButtons();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Export functions for global access (for onclick handlers)
window.summarizePaper = summarizePaper;
window.openQA = openQA;
window.escapeHtml = escapeHtml;