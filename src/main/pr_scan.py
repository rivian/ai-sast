#!/usr/bin/env python3
"""
GitHub Pull Request Diff Security Scanner

This script is designed to run in GitHub Actions on pull request events.
It fetches the diff of the pull request, scans only the added/modified lines
for security vulnerabilities, and can post results as a PR comment.
"""

import os
import sys
import json
import fnmatch
import hashlib
from datetime import datetime
from typing import Optional, List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.scanner import SecurityScanner
from src.core.report import HTMLReportGenerator

try:
    from src.integrations.notifications import WebhookClient
except ImportError:
    WebhookClient = None


def parse_added_lines_from_diff(diff: str) -> str:
    """Parses a unified diff string and extracts only the added lines."""
    added_lines = []
    for line in diff.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])  # Append line content without the '+'
    return '\n'.join(added_lines)


def get_pr_changes_from_github() -> List[Dict]:
    """
    Get PR changes from GitHub Actions environment.
    Uses GitHub's REST API or git diff depending on availability.
    """
    # Check if we're in GitHub Actions
    github_token = os.environ.get('GITHUB_TOKEN')
    github_repository = os.environ.get('GITHUB_REPOSITORY')
    github_event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    changes = []
    
    if github_event_path and os.path.exists(github_event_path):
        # Read the GitHub event payload
        with open(github_event_path, 'r') as f:
            event = json.load(f)
        
        # Get base and head SHAs
        base_sha = event.get('pull_request', {}).get('base', {}).get('sha')
        head_sha = event.get('pull_request', {}).get('head', {}).get('sha')
        
        if base_sha and head_sha:
            print(f"Comparing {base_sha[:7]}...{head_sha[:7]}")
            
            # Use git diff to get changes
            import subprocess
            try:
                # Get list of changed files
                result = subprocess.run(
                    ['git', 'diff', '--name-status', f'{base_sha}...{head_sha}'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 2:
                        continue
                    
                    status = parts[0]
                    file_path = parts[1]
                    
                    # Skip deleted files
                    if status == 'D':
                        continue
                    
                    # Get the diff for this file
                    diff_result = subprocess.run(
                        ['git', 'diff', f'{base_sha}...{head_sha}', '--', file_path],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    changes.append({
                        'new_path': file_path,
                        'deleted_file': False,
                        'diff': diff_result.stdout
                    })
                    
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Warning: Git diff failed: {e}")
                print("Falling back to full repository scan...")
                return []
    
    return changes


def _generate_vuln_id(file_path: str, issue: str, location: str) -> str:
    """Generates a unique and stable ID for a vulnerability."""
    unique_string = f"{file_path}-{issue}-{location}"
    return hashlib.sha1(unique_string.encode()).hexdigest()[:8]


def main():
    """Main function to run security scan on PR diffs."""
    
    # GitHub environment variables (automatically set by GitHub Actions)
    # GITHUB_REPOSITORY: Repository name in format "owner/repo"
    # Example: "myorg/myapp"
    github_repository = os.environ.get('GITHUB_REPOSITORY', '')
    
    # GITHUB_REF_NAME: Branch, tag, or PR reference name
    # Example: "feature/new-feature", "main", "123/merge"
    github_ref_name = os.environ.get('GITHUB_REF_NAME', '')
    
    # GITHUB_SHA: Commit SHA that triggered the workflow
    # Example: "abc123def456..."
    github_sha = os.environ.get('GITHUB_SHA', '')
    
    # GITHUB_EVENT_NAME: Name of the event that triggered the workflow
    # Example: "pull_request", "push", "workflow_dispatch"
    github_event_name = os.environ.get('GITHUB_EVENT_NAME', '')
    
    repo_url = f"https://github.com/{github_repository}" if github_repository else ""
    
    print("=" * 60)
    print("🔍 AI-SAST Pull Request Scan")
    print("=" * 60)
    print(f"Repository: {repo_url or 'Unknown'}")
    print(f"Event: {github_event_name}")
    print(f"Ref: {github_ref_name}")
    print(f"SHA: {github_sha[:7] if github_sha else 'Unknown'}")
    print("=" * 60)
    print()
    
    # Get PR changes
    print("Fetching PR changes...")
    changes = get_pr_changes_from_github()
    
    if not changes:
        print("⚠️  No changes detected or unable to fetch PR diff.")
        print("This may happen if:")
        print("  - Not running in a pull request context")
        print("  - Git history is not available")
        print("  - Running in a shallow clone")
        print("\nFalling back to full repository scan...")
        
        # Fall back to full scan
        from src.main.full_scan import main as full_scan_main
        full_scan_main()
        return
    
    print(f"✅ Found {len(changes)} changed file(s)")
    
    # --- Exclusion Logic ---
    # AI_SAST_EXCLUDE_PATHS: Comma-separated paths to exclude from PR scanning (optional)
    # Example: "dist,build,vendor,docs"
    default_exclude_keywords = ['test', 'node_modules', 'e2e', 'cypress', 'local', 'jest', 
                                 'prettierrc', 'mock', 'log', 'png', 'script']
    exclude_paths_str = os.environ.get('AI_SAST_EXCLUDE_PATHS', '')
    custom_exclude_keywords = [path.strip() for path in exclude_paths_str.split(',') if path.strip()]
    
    all_exclude_keywords = default_exclude_keywords + custom_exclude_keywords

    if custom_exclude_keywords:
        print(f"ℹ️  Applying custom exclusion keywords: {', '.join(custom_exclude_keywords)}")
    print(f"ℹ️  Full list of exclusion keywords: {', '.join(all_exclude_keywords)}")

    def should_be_excluded(file_path: str) -> bool:
        """Check if a file path should be excluded based on keywords."""
        path_lower = file_path.lower()
        for keyword in all_exclude_keywords:
            if keyword.lower() in path_lower:
                return True
        return False
    # --- End of Exclusion Logic ---

    scan_results = []
    excluded_files = []
    
    # Initialize scanner
    scanner = SecurityScanner(repo_url=repo_url)
    file_patterns = scanner._load_file_extensions()

    print("\nScanning changed files...")
    for change in changes:
        file_path = change.get('new_path')

        if should_be_excluded(file_path):
            excluded_files.append(file_path)
            continue
        
        # Check if the file matches any of the patterns
        if not any(fnmatch.fnmatch(file_path, pattern) for pattern in file_patterns):
            print(f"ℹ️  Skipping file with unsupported extension: {file_path}")
            continue

        if change.get('deleted_file'):
            continue

        diff = change.get('diff', '')
        added_code = parse_added_lines_from_diff(diff)

        if added_code:
            print(f"🔍 Scanning changes in: {file_path}")
            language = scanner._detect_language(file_path)
            
            result = scanner.scan_code_content(added_code, file_path, language)
            scan_results.append(result)
        else:
            print(f"ℹ️  No added lines to scan in: {file_path}")

    if excluded_files:
        print("\n--- Excluded Files in this PR ---")
        for file in sorted(list(set(excluded_files))):
            print(f"- {file}")
        print("---------------------------------\n")

    # Generate reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if not scan_results:
        print("✅ No new code changes to scan (or all files excluded).")
        print("PR scan completed successfully!")
        return

    # Generate HTML report
    html_report_file = f'ai_sast_pr_scan_report_{timestamp}.html'
    print(f"\n📊 Generating HTML report: {html_report_file}")
    
    html_generator = HTMLReportGenerator()
    html_generator.generate_report(
        results=scan_results,
        repo_url=repo_url,
        ref_name=github_ref_name,
        output_file=html_report_file
    )
    
    # Generate markdown report for PR comment (optional)
    vulnerabilities_by_severity = html_generator._process_results_by_severity(scan_results)
    total_vulns = sum(len(v) for v in vulnerabilities_by_severity.values())
    
    should_post_comment = bool(
        vulnerabilities_by_severity.get("Critical") or 
        vulnerabilities_by_severity.get("High")
    )
    
    if should_post_comment:
        print("\n💬 Generating markdown report for PR comment...")
        markdown_report = html_generator.generate_markdown_report(
            scan_results,
            report_title="🤖 AI-SAST Security Scan",
            repo_url=repo_url,
            ref_name=github_ref_name,
            report_context_text="PR changes"
        )
        
        # Save markdown report for GitHub Actions to use
        with open('pr_comment.md', 'w') as f:
            f.write(markdown_report)
        print("✅ Markdown report saved to pr_comment.md")
        print("   Use this file to post a PR comment in your workflow")
    else:
        print("\nℹ️  No critical or high severity issues found.")
    
    # Send webhook notification (optional)
    if WebhookClient:
        try:
            webhook = WebhookClient()
            if webhook.is_configured:
                print("\n📡 Sending webhook notification...")
                
                # Get PR number from event
                pr_number = None
                if github_event_path and os.path.exists(github_event_path):
                    with open(github_event_path, 'r') as f:
                        event = json.load(f)
                    pr_number = event.get('pull_request', {}).get('number') or event.get('number')
                
                scan_summary = {
                    'critical': len(vulnerabilities_by_severity.get('Critical', [])),
                    'high': len(vulnerabilities_by_severity.get('High', [])),
                    'medium': len(vulnerabilities_by_severity.get('Medium', [])),
                    'low': len(vulnerabilities_by_severity.get('Low', []))
                }
                
                webhook.send_scan_completed(
                    repository=github_repository or repo_url,
                    pr_number=pr_number,
                    scan_summary=scan_summary,
                    report_url=None,  # Can be set to GitHub Actions artifact URL
                    scan_duration=None
                )
                
                # Send critical alerts
                critical_vulns = vulnerabilities_by_severity.get('Critical', [])
                for vuln in critical_vulns[:3]:  # Limit to first 3 to avoid spam
                    webhook.send_critical_alert(
                        repository=github_repository or repo_url,
                        pr_number=pr_number,
                        vulnerability=vuln
                    )
        except Exception as e:
            print(f"⚠️  Webhook notification skipped: {e}")
    
    # Print summary
    vulnerable_files = {
        vuln['file_path'] 
        for sev in vulnerabilities_by_severity 
        for vuln in vulnerabilities_by_severity[sev]
    }
    
    print('\n' + '=' * 60)
    print('📊 SECURITY SCAN SUMMARY')
    print('=' * 60)
    print(f'Total files scanned in PR: {len(scan_results)}')
    print(f'Files with vulnerabilities: {len(vulnerable_files)}')
    print(f'Total vulnerabilities found: {total_vulns}')
    print(f'  - Critical: {len(vulnerabilities_by_severity.get("Critical", []))}')
    print(f'  - High: {len(vulnerabilities_by_severity.get("High", []))}')
    print(f'  - Medium: {len(vulnerabilities_by_severity.get("Medium", []))}')
    print(f'  - Low: {len(vulnerabilities_by_severity.get("Low", []))}')
    print('=' * 60)
    print(f'\n📄 Full report: {html_report_file}')
    print('\n🎉 PR scan completed successfully!')


if __name__ == "__main__":
    main()

