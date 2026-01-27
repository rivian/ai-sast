#!/usr/bin/env python3
"""
Example: Scanning a directory

This example demonstrates how to scan an entire directory for security vulnerabilities.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.scanner import SecurityScanner
from src.core.report import HTMLReportGenerator

def main():
    """Run a directory scan example."""
    
    print("=" * 60)
    print("AI-SAST Security Scanner - Directory Scan Example")
    print("=" * 60)
    
    # Get directory to scan (default to current directory)
    scan_dir = input("\nEnter directory to scan (default: current): ").strip() or "."
    
    if not os.path.exists(scan_dir):
        print(f"❌ Error: Directory '{scan_dir}' does not exist!")
        return
    
    print(f"\n🔍 Scanning directory: {os.path.abspath(scan_dir)}\n")
    
    # Initialize scanner
    scanner = SecurityScanner()
    
    # Scan directory
    results = scanner.scan_directory(
        directory_path=scan_dir,
        max_workers=5  # Use 5 parallel workers
    )
    
    # Generate text report
    print("\n📄 Generating text report...")
    text_report = scanner.generate_report(results)
    
    # Save text report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_file = f"ai_sast_report_{timestamp}.txt"
    with open(text_file, 'w') as f:
        f.write(text_report)
    print(f"✅ Text report saved: {text_file}")
    
    # Generate HTML report
    print("\n📊 Generating HTML report...")
    html_generator = HTMLReportGenerator()
    html_file = f"ai_sast_report_{timestamp}.html"
    html_generator.generate_report(
        results=results,
        repo_url=os.path.abspath(scan_dir),
        ref_name="main",
        output_file=html_file
    )
    print(f"✅ HTML report saved: {html_file}")
    
    # Display summary
    vulnerabilities = html_generator._process_results_by_severity(results)
    total_vulns = sum(len(v) for v in vulnerabilities.values())
    
    print("\n" + "=" * 60)
    print("📊 SCAN SUMMARY")
    print("=" * 60)
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

