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
os.environ['LLM_BACKEND'] = 'ollama'
os.environ['OLLAMA_MODEL'] = 'qwen2.5-coder:14b'  # or any other model
os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'  # default Ollama URL

def main():
    """Example scan using Ollama backend"""
    
    print("=" * 70)
    print("🔍 AI-SAST with Ollama - Local Security Scanning")
    print("=" * 70)
    print()
    
    # Example vulnerable code to scan
    code_sample = """
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result

def process_file(filepath):
    # Path traversal vulnerability
    with open(filepath, 'r') as f:
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
