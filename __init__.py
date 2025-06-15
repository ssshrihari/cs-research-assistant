# Create __init__.py files
touch backend/__init__.py
touch backend/models/__init__.py
touch backend/utils/__init__.py

# Create Procfile for Heroku deployment
echo "web: gunicorn backend.app:app" > Procfile

# Create .env file for environment variables
cat > .env << EOF
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5001
EOF

# Create .gitignore
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

# Create runtime.txt for Heroku (Python version)
echo "python-3.11.7" > runtime.txt