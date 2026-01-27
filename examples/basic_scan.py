#!/usr/bin/env python3
"""
Example: Basic usage of AI-SAST scanner

This example demonstrates how to use the SecurityScanner class to scan
a single Python file for security vulnerabilities.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.scanner import SecurityScanner

def main():
    """Run a basic security scan example."""
    
    # Example vulnerable code
    vulnerable_code = """
def login_user(username, password):
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return execute_query(query)

def fetch_data(url):
    # SSRF vulnerability
    import requests
    user_input = input("Enter URL: ")
    response = requests.get(user_input)
    return response.text
"""
    
    print("=" * 60)
    print("AI-SAST Security Scanner - Basic Example")
    print("=" * 60)
    print("\n🔍 Scanning sample vulnerable code...\n")
    
    # Initialize scanner
    scanner = SecurityScanner()
    
    # Scan the code content
    result = scanner.scan_code_content(
        code_content=vulnerable_code,
        file_path="example_vulnerable.py",
        language="python"
    )
    
    # Display results
    print("📊 Scan Results:")
    print("-" * 60)
    print(f"File: {result['file_path']}")
    print(f"Language: {result['language']}")
    print(f"Status: {result['status']}")
    print("\n🔒 Security Analysis:")
    print("-" * 60)
    print(result['analysis'])
    print("\n" + "=" * 60)
    print("✅ Scan completed!")

if __name__ == "__main__":
    main()

