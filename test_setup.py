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
