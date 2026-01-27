#!/usr/bin/env python3
"""
Example: Scanning a Git repository

This example demonstrates how to scan a remote Git repository for security vulnerabilities.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.scanner import SecurityScanner
from src.core.report import HTMLReportGenerator

def main():
    """Run a Git repository scan example."""
    
    print("=" * 60)
    print("AI-SAST Security Scanner - Git Repository Scan Example")
    print("=" * 60)
    
    # Get repository URL
    repo_url = input("\nEnter Git repository URL: ").strip()
    if not repo_url:
        print("❌ Error: Repository URL is required!")
        return
    
    # Get branch (optional)
    branch = input("Enter branch to scan (default: main): ").strip() or "main"
    
    print(f"\n🔍 Scanning repository: {repo_url}")
    print(f"📌 Branch: {branch}\n")
    
    # Initialize scanner
    scanner = SecurityScanner(repo_url=repo_url)
    
    # Scan repository
    results = scanner.scan_git_repository(
        repo_url=repo_url,
        branch=branch
    )
    
    # Check if scan was successful
    if results and results[0].get('status') == 'error':
        print(f"❌ Error scanning repository: {results[0].get('analysis')}")
        return
    
    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n📄 Generating text report...")
    text_report = scanner.generate_report(results)
    text_file = f"ai_sast_repo_report_{timestamp}.txt"
    with open(text_file, 'w') as f:
        f.write(text_report)
    print(f"✅ Text report saved: {text_file}")
    
    print("\n📊 Generating HTML report...")
    html_generator = HTMLReportGenerator()
    html_file = f"ai_sast_repo_report_{timestamp}.html"
    html_generator.generate_report(
        results=results,
        repo_url=repo_url,
        ref_name=branch,
        output_file=html_file
    )
    print(f"✅ HTML report saved: {html_file}")
    
    # Display summary
    vulnerabilities = html_generator._process_results_by_severity(results)
    total_vulns = sum(len(v) for v in vulnerabilities.values())
    
    print("\n" + "=" * 60)
    print("📊 SCAN SUMMARY")
    print("=" * 60)
    print(f"Repository: {repo_url}")
    print(f"Branch: {branch}")
    print(f"Files scanned: {len(results)}")
    print(f"Total vulnerabilities found: {total_vulns}")
    print(f"  - Critical: {len(vulnerabilities.get('Critical', []))}")
    print(f"  - High: {len(vulnerabilities.get('High', []))}")
    print(f"  - Medium: {len(vulnerabilities.get('Medium', []))}")
    print(f"  - Low: {len(vulnerabilities.get('Low', []))}")
    print("=" * 60)
    print("\n✅ Scan completed! Check the report files for details.")

if __name__ == "__main__":
    main()

