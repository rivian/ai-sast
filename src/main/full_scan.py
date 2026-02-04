#!/usr/bin/env python3
"""
Full Repository Security Scanner

This script is designed to run in GitHub Actions or locally to scan
an entire repository for security vulnerabilities.
"""

import sys
import os
import argparse
import hashlib
import re
from datetime import datetime
from typing import Optional, List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.scanner import SecurityScanner
from src.core.report import HTMLReportGenerator


def _generate_vuln_id(file_path: str, issue: str, location: str) -> str:
    """Generates a unique and stable ID for a vulnerability."""
    unique_string = f"{file_path}-{issue}-{location}"
    return hashlib.sha1(unique_string.encode()).hexdigest()[:8]


def _store_scan_findings(scan_results: List[Dict], repo_url: str, scan_id: str):
    """
    Store scan findings in database if AI_SAST_STORE_FINDINGS is enabled.
    
    Args:
        scan_results: List of scan result dictionaries
        repo_url: Repository URL
        scan_id: Unique identifier for this scan
    """
    # Check if storage is enabled (default: false)
    store_findings = os.environ.get('AI_SAST_STORE_FINDINGS', 'false').lower() in ['true', '1', 'yes']
    
    if not store_findings:
        return
    
    try:
        from src.integrations.scan_database import ScanDatabase
        
        print(f"\n💾 Storing scan findings in database (AI_SAST_STORE_FINDINGS=true)...")
        db = ScanDatabase()
        
        stored_count = 0
        for result in scan_results:
            file_path = result.get('file_path', 'unknown')
            analysis = result.get('analysis', '')
            
            # Parse vulnerabilities from analysis
            vuln_pattern = re.compile(
                r"-\s*\*\*Vulnerability Level\*\*:\s*(CRITICAL|HIGH|MEDIUM|LOW|INFO)\s*\n"
                r"-\s*\*\*Issue\*\*:\s*(.*?)\n"
                r"-\s*\*\*Location\*\*:\s*(.*?)\n"
                r"(?:-\s*\*\*CVSS Vector\*\*:\s*(.*?)\n)?"
                r"-\s*\*\*Risk\*\*:\s*(.*?)\n"
                r"-\s*\*\*Fix\*\*:\s*(.*?)(?:\n-|\n\n|$)",
                re.DOTALL | re.IGNORECASE
            )
            
            for match in vuln_pattern.finditer(analysis):
                severity = match.group(1).strip()
                issue = match.group(2).strip()
                location = match.group(3).strip()
                cvss_vector = match.group(4).strip() if match.group(4) else None
                risk = match.group(5).strip()
                fix = match.group(6).strip()
                
                # Generate vulnerability ID
                vuln_id = _generate_vuln_id(file_path, issue, location)
                
                # Store in database
                success = db.store_scan_result(
                    scan_id=scan_id,
                    repo_url=repo_url,
                    pr_number=None,
                    file_path=file_path,
                    vulnerability_id=vuln_id,
                    issue=issue,
                    severity=severity,
                    cvss_vector=cvss_vector,
                    location=location,
                    description=risk,
                    risk=risk,
                    fix=fix,
                    scan_type="full"
                )
                
                if success:
                    stored_count += 1
        
        db.close()
        print(f"✅ Stored {stored_count} finding(s) in database")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not store findings in database: {e}")
        # Don't fail the scan if storage fails


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
        github_sha = os.environ.get('GITHUB_SHA', 'unknown')
        scan_id = f"full-{github_sha[:7]}-{timestamp}"
        
        # Store scan findings in database (if enabled)
        _store_scan_findings(results, repo_url or os.path.abspath(scan_dir), scan_id)
        
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

