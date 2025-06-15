#!/bin/bash

# CS Research Assistant Setup Script
# For macOS (M2 Pro optimized)

echo "🔬 Setting up CS Research Assistant..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9+ from https://python.org"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Found Python $PYTHON_VERSION"

# Create project structure
print_status "Creating project structure..."
mkdir -p backend/models backend/utils backend/templates
mkdir -p frontend/assets

# Create __init__.py files
touch backend/__init__.py
touch backend/models/__init__.py
touch backend/utils/__init__.py

print_success "Project structure created"

# Create virtual environment
print_status "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
echo "This may take several minutes for AI models..."

# Install core dependencies first
pip install Flask==3.0.0 Flask-CORS==4.0.0 requests==2.31.0 arxiv==1.4.8

# Install PyTorch with MPS support for M2 Pro
print_status "Installing PyTorch with Apple Silicon support..."
pip install torch torchvision torchaudio

# Install transformers and other ML libraries
print_status "Installing AI/ML libraries..."
pip install transformers==4.35.2 sentence-transformers==2.2.2 faiss-cpu==1.7.4

# Install PDF processing
print_status "Installing PDF processing libraries..."
pip install PyMuPDF==1.23.8 nltk==3.8.1

# Install deployment dependencies
pip install gunicorn==21.2.0 python-dotenv==1.0.0

# Generate requirements.txt
print_status "Generating requirements.txt..."
pip freeze > requirements.txt

print_success "Dependencies installed successfully"

# Download NLTK data
print_status "Downloading NLTK data..."
python3 -c "
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    print('NLTK data downloaded successfully')
except Exception as e:
    print(f'Warning: Could not download NLTK data: {e}')
"

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5001
EOF

# Create .gitignore
print_status "Creating .gitignore..."
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.temp
temp/

# Model cache
transformers_cache/
.cache/
EOF

# Create Procfile for deployment
print_status "Creating deployment files..."
echo "web: gunicorn backend.app:app" > Procfile
echo "python-3.11.7" > runtime.txt

# Create a simple test script
print_status "Creating test script..."
cat > test_setup.py << EOF
#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly
"""
import sys

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import flask
        print("✅ Flask imported successfully")
        
        import arxiv
        print("✅ ArXiv client imported successfully")
        
        import fitz  # PyMuPDF
        print("✅ PDF processor imported successfully")
        
        import transformers
        print("✅ Transformers imported successfully")
        
        import torch
        print("✅ PyTorch imported successfully")
        
        # Test MPS availability on M2 Pro
        if torch.backends.mps.is_available():
            print("✅ Apple Silicon MPS acceleration available")
        else:
            print("⚠️  MPS not available, using CPU")
        
        import nltk
        print("✅ NLTK imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_nltk_data():
    """Test NLTK data availability"""
    try:
        import nltk
        from nltk.tokenize import sent_tokenize
        
        # Test tokenization
        test_text = "This is a test sentence. This is another sentence."
        sentences = sent_tokenize(test_text)
        
        if len(sentences) == 2:
            print("✅ NLTK sentence tokenization working")
            return True
        else:
            print("⚠️  NLTK tokenization may have issues")
            return False
            
    except Exception as e:
        print(f"❌ NLTK test failed: {e}")
        return False

def main():
    print("🧪 Testing CS Research Assistant setup...")
    print("=" * 50)
    
    import_success = test_imports()
    nltk_success = test_nltk_data()
    
    print("=" * 50)
    
    if import_success and nltk_success:
        print("🎉 Setup test completed successfully!")
        print("You can now run: python backend/app.py")
        return 0
    else:
        print("❌ Setup test failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

# Make the test script executable
chmod +x test_setup.py

# Create README
print_status "Creating README..."
cat > README.md << EOF
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
   \`\`\`bash
   chmod +x setup.sh
   ./setup.sh
   \`\`\`

2. Activate the virtual environment:
   \`\`\`bash
   source venv/bin/activate
   \`\`\`

3. Test the setup:
   \`\`\`bash
   python test_setup.py
   \`\`\`

4. Run the application:
   \`\`\`bash
   python backend/app.py
   \`\`\`

5. Open your browser to: http://localhost:5001

## Deployment

### Heroku
\`\`\`bash
heroku create your-app-name
git push heroku main
\`\`\`

### Railway
\`\`\`bash
railway login
railway init
railway up
\`\`\`

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

EOF

print_success "Setup completed successfully!"
print_status "Next steps:"
echo "1. Run: source venv/bin/activate"
echo "2. Test: python test_setup.py"
echo "3. Start: python backend/app.py"
echo "4. Open: http://localhost:5001"
echo ""
print_warning "Note: First run may take longer as AI models download (~1-2GB)"
echo ""
print_success "Happy researching! 🔬"