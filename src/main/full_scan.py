#!/usr/bin/env python3
"""
Full Repository Security Scanner

This script is designed to run in GitHub Actions or locally to scan
an entire repository for security vulnerabilities.
"""

import sys
import os
import argparse
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.scanner import SecurityScanner
from src.core.report import HTMLReportGenerator


def main():
    """Main function to run full repository security scan."""
    
    parser = argparse.ArgumentParser(description="Full repository security scan")
    parser.add_argument("--directory", type=str, default=".", help="Directory to scan (default: current)")
    parser.add_argument("--output-prefix", type=str, default="ai_sast_full_scan", help="Output file prefix")
    parser.add_argument("--max-workers", type=int, default=10, help="Max parallel workers (default: 10, set to 1 to avoid rate limits)")
    args = parser.parse_args()
    
    # Get repository information from environment or arguments
    # GITHUB_REPOSITORY: Repository name in format "owner/repo"
    # Example: "myorg/myapp" or "company/backend-services"
    repo_url = os.environ.get('GITHUB_REPOSITORY', '')
    if repo_url:
        repo_url = f"https://github.com/{repo_url}"
    
    # GITHUB_REF_NAME: Branch or tag name
    # Example: "main", "develop", "feature/new-api", "v1.2.3"
    ref_name = os.environ.get('GITHUB_REF_NAME', 'main')
    scan_dir = args.directory
    
    print("=" * 60)
    print("🔍 AI-SAST Full Repository Scan")
    print("=" * 60)
    print(f"Repository: {repo_url or 'Local scan'}")
    print(f"Branch/Ref: {ref_name}")
    print(f"Scan Directory: {os.path.abspath(scan_dir)}")
    print("=" * 60)
    print()
    
    if not os.path.exists(scan_dir):
        print(f"❌ ERROR: Scan directory {scan_dir} does not exist")
        sys.exit(1)
    
    try:
        print("Initializing AI-SAST Security Scanner...")
        scanner = SecurityScanner(repo_url=repo_url)
        
        print(f"Scanning directory: {scan_dir}")
        print("Applying default and custom exclusion rules from AI_SAST_EXCLUDE_PATHS...")
        results = scanner.scan_directory(scan_dir, max_workers=args.max_workers)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate text report
        text_report_file = f'{args.output_prefix}_report_{timestamp}.txt'
        print(f"\n📄 Generating text report: {text_report_file}")
        text_report = scanner.generate_report(results, text_report_file)
        
        # Generate HTML report
        html_report_file = f'{args.output_prefix}_report_{timestamp}.html'
        print(f"📊 Generating HTML report: {html_report_file}")
        
        html_generator = HTMLReportGenerator()
        html_generator.generate_report(
            results=results,
            repo_url=repo_url or os.path.abspath(scan_dir),
            ref_name=ref_name,
            output_file=html_report_file
        )
        
        # Generate summary
        vulnerabilities_by_severity = html_generator._process_results_by_severity(results)
        total_vulns = sum(len(v) for v in vulnerabilities_by_severity.values())
        vulnerable_files = {
            vuln['file_path'] 
            for sev in vulnerabilities_by_severity 
            for vuln in vulnerabilities_by_severity[sev]
        }
        
        # Print summary to console
        print('\n' + '=' * 60)
        print('📊 SECURITY SCAN SUMMARY')
        print('=' * 60)
        print(f'Scanned Directory: {os.path.abspath(scan_dir)}')
        print(f'Total files scanned: {len(results)}')
        print(f'Files with vulnerabilities: {len(vulnerable_files)}')
        print(f'Total vulnerabilities found: {total_vulns}')
        print(f'  - Critical: {len(vulnerabilities_by_severity.get("Critical", []))}')
        print(f'  - High: {len(vulnerabilities_by_severity.get("High", []))}')
        print(f'  - Medium: {len(vulnerabilities_by_severity.get("Medium", []))}')
        print(f'  - Low: {len(vulnerabilities_by_severity.get("Low", []))}')
        print('=' * 60)
        
        if total_vulns > 0:
            print("\n⚠️  Security vulnerabilities detected!")
            print(f"📄 Text report: {text_report_file}")
            print(f"📊 HTML report: {html_report_file}")
        else:
            print("\n✅ No vulnerabilities detected.")
        
        print('\n🎉 Security scan completed successfully!')
        
        # Exit with appropriate code
        # Don't fail the build, just report findings
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ ERROR: Security scan failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

