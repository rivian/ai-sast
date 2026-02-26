#!/usr/bin/env python3
"""
Example: Using AI-SAST with Ollama (Local Open-Source LLM)

This example demonstrates how to use AI-SAST with Ollama instead of Vertex AI,
running completely locally without any cloud dependencies.

Prerequisites:
1. Install Ollama: https://ollama.com/
2. Pull a model: ollama pull qwen2.5-coder:14b
3. Ensure Ollama is running: ollama serve
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.scanner import SecurityScanner

# Configure AI-SAST to use Ollama
os.environ['AI_SAST_LLM'] = 'ollama'
os.environ['OLLAMA_MODEL'] = 'qwen2.5-coder:14b'  # or any other model
os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'  # default Ollama URL

def main():
    """Example scan using Ollama backend"""
    
    print("=" * 70)
    print("🔍 AI-SAST with Ollama - Local Security Scanning")
    print("=" * 70)
    print()
    
    # Example code to scan - demonstrating secure practices
    code_sample = """
import sqlite3
import os

def get_user(username):
    '''Secure database query using parameterized statements'''
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Use parameterized query to prevent SQL injection
    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def process_file(filepath):
    '''Read file with path validation to prevent path traversal'''
    # Validate filepath is within allowed directory
    base_dir = os.path.abspath('/allowed/directory')
    abs_path = os.path.abspath(filepath)
    
    if not abs_path.startswith(base_dir):
        raise ValueError("Invalid file path")
    
    with open(abs_path, 'r') as f:
        return f.read()
"""
    
    try:
        # Initialize scanner with Ollama backend
        print("Initializing AI-SAST with Ollama backend...")
        scanner = SecurityScanner()
        
        print("\n📝 Scanning example vulnerable code...")
        print("=" * 70)
        
        # Scan the code
        result = scanner.scan_code_content(
            code_content=code_sample,
            file_path="example_vulnerable.py",
            language="python"
        )
        
        print("\n📊 Scan Results:")
        print("=" * 70)
        print(result['analysis'])
        print("=" * 70)
        
        print("\n✅ Scan completed successfully!")
        print("\n💡 Tips:")
        print("   - Ollama runs completely locally (no cloud costs)")
        print("   - Your code never leaves your machine")
        print("   - Switch models anytime: export OLLAMA_MODEL='codellama:13b'")
        print("   - Available models: ollama list")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if Ollama is running: curl http://localhost:11434/api/tags")
        print("   2. Pull a model: ollama pull qwen2.5-coder:14b")
        print("   3. List models: ollama list")
        print("   4. Start Ollama: ollama serve")
        sys.exit(1)

if __name__ == "__main__":
    main()
