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
import time
import fnmatch
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.scanner import SecurityScanner
from src.core.report import HTMLReportGenerator
from src.core.validator import validate_findings

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
        with open(github_event_path, 'r') as f:
            event = json.load(f)
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


def _store_scan_findings(scan_results: List[Dict], repo_url: str, pr_number: Optional[int], scan_id: str):
    """
    Store scan findings in database if AI_SAST_STORE_FINDINGS is enabled.
    
    Args:
        scan_results: List of scan result dictionaries
        repo_url: Repository URL
        pr_number: Pull request number (optional)
        scan_id: Unique identifier for this scan
    """
    # Check if storage is enabled (default: false)
    store_findings = os.environ.get('AI_SAST_STORE_FINDINGS', 'false').lower() in ['true', '1', 'yes']
    
    if not store_findings:
        return
    
    try:
        from ..integrations.scan_database import ScanDatabase
        
        print(f"\n💾 Storing scan findings in database (AI_SAST_STORE_FINDINGS=true)...")
        db = ScanDatabase()
        
        stored_count = 0
        for result in scan_results:
            file_path = result.get('file_path', 'unknown')
            analysis = result.get('analysis', '')
            
            # Parse vulnerabilities from analysis
            import re
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
                    pr_number=pr_number,
                    file_path=file_path,
                    vulnerability_id=vuln_id,
                    issue=issue,
                    severity=severity,
                    cvss_vector=cvss_vector,
                    location=location,
                    description=risk,
                    risk=risk,
                    fix=fix,
                    scan_type="pr"
                )
                
                if success:
                    stored_count += 1
        
        db.close()
        print(f"✅ Stored {stored_count} finding(s) in database")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not store findings in database: {e}")
        # Don't fail the scan if storage fails


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
    
    # GITHUB_EVENT_PATH: Path to event payload file
    # Example: "/home/runner/work/_temp/_github_workflow/event.json"
    github_event_path = os.environ.get('GITHUB_EVENT_PATH', '')
    
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

    # --- DoS protection: file count and size limits ---
    # AI_SAST_PR_SCAN_MAX_FILES: max number of files to scan per PR (0 = no limit)
    # AI_SAST_PR_SCAN_MAX_FILE_SIZE: max size in bytes of added lines per file (0 = no limit)
    # AI_SAST_PR_SCAN_MAX_TOTAL_SIZE: max total bytes of added lines per PR (0 = no limit)
    max_files = int(os.environ.get('AI_SAST_PR_SCAN_MAX_FILES', '100'))
    max_file_size = int(os.environ.get('AI_SAST_PR_SCAN_MAX_FILE_SIZE', '500000'))   # 500 KB default
    max_total_size = int(os.environ.get('AI_SAST_PR_SCAN_MAX_TOTAL_SIZE', '5242880'))  # 5 MB default
    max_files = max(0, max_files)
    max_file_size = max(0, max_file_size)
    max_total_size = max(0, max_total_size)
    # --- End DoS protection ---

    scan_results = []
    excluded_files = []
    skipped_file_size: List[str] = []
    skipped_total_cap: List[str] = []
    skipped_file_cap: List[str] = []
    
    # Initialize scanner
    scanner = SecurityScanner(repo_url=repo_url)
    file_patterns = scanner._load_file_extensions()

    total_added_bytes = 0

    # Collect (added_code, file_path, language) for each file that needs scanning
    tasks: List[Tuple[str, str, str]] = []
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
            # DoS: cap number of files
            if max_files > 0 and len(tasks) >= max_files:
                skipped_file_cap.append(file_path)
                continue
            size = len(added_code.encode('utf-8'))
            if max_file_size > 0 and size > max_file_size:
                skipped_file_size.append(file_path)
                print(f"ℹ️  Skipping (added lines too large, {size} bytes): {file_path}")
                continue
            if max_total_size > 0 and (total_added_bytes + size) > max_total_size:
                skipped_total_cap.append(file_path)
                print(f"ℹ️  Skipping (PR total size limit would be exceeded): {file_path}")
                continue
            total_added_bytes += size
            language = scanner._detect_language(file_path)
            tasks.append((added_code, file_path, language))
        else:
            print(f"ℹ️  No added lines to scan in: {file_path}")

    if skipped_file_size or skipped_total_cap or skipped_file_cap:
        print("\n--- DoS limits (files/size caps) ---")
        if skipped_file_size:
            print(f"Skipped {len(skipped_file_size)} file(s) over max file size: {skipped_file_size[:5]}{'...' if len(skipped_file_size) > 5 else ''}")
        if skipped_total_cap:
            print(f"Skipped {len(skipped_total_cap)} file(s) due to PR total size limit: {skipped_total_cap[:5]}{'...' if len(skipped_total_cap) > 5 else ''}")
        if skipped_file_cap:
            print(f"Skipped {len(skipped_file_cap)} file(s) due to max files per PR limit: {skipped_file_cap[:5]}{'...' if len(skipped_file_cap) > 5 else ''}")
        print("------------------------------------\n")

    # Batching: send multiple files per Vertex call for more context and fewer API calls
    batch_size = int(os.environ.get('AI_SAST_PR_SCAN_BATCH_SIZE', '10'))
    batch_size = max(1, min(batch_size, 50))
    max_batch_bytes = int(os.environ.get('AI_SAST_PR_SCAN_BATCH_MAX_BYTES', '0'))  # 0 = no per-batch cap
    if max_batch_bytes <= 0:
        max_batch_bytes = 2 * 1024 * 1024  # 2 MB default cap per batch

    if batch_size > 1:
        # Build batches: each batch has up to batch_size files and up to max_batch_bytes total
        batches: List[List[Tuple[str, str, str]]] = []
        current_batch: List[Tuple[str, str, str]] = []
        current_bytes = 0
        for (code, path, lang) in tasks:
            size = len(code.encode('utf-8'))
            if current_batch and (len(current_batch) >= batch_size or (max_batch_bytes > 0 and current_bytes + size > max_batch_bytes)):
                batches.append(current_batch)
                current_batch = []
                current_bytes = 0
            current_batch.append((code, path, lang))
            current_bytes += size
        if current_batch:
            batches.append(current_batch)
        print(f"\nScanning {len(tasks)} changed file(s) in {len(batches)} batch/batches (batch_size={batch_size})...")
        for i, batch in enumerate(batches):
            paths = [p for (_, p, _) in batch]
            print(f"🔍 Batch {i + 1}/{len(batches)}: {len(batch)} file(s)")
            try:
                batch_results = scanner.scan_code_content_batch(batch, batch_descriptor=f"batch {i + 1}/{len(batches)}")
                scan_results.extend(batch_results)
                for p in paths:
                    print(f"   Scanned: {p}")
            except Exception as e:
                print(f"❌ Batch failed: {e}")
                for (_, path, lang) in batch:
                    scan_results.append({
                        "file_path": path,
                        "language": lang,
                        "analysis": f"Failed to scan (batch error): {str(e)}",
                        "status": "error"
                    })
            if i < len(batches) - 1 and len(batches) > 1:
                time.sleep(1)
    else:
        # Per-file parallel scan (original behavior)
        max_workers = int(os.environ.get('AI_SAST_PR_SCAN_MAX_WORKERS', '5'))
        max_workers = max(1, min(max_workers, 20))
        print(f"\nScanning {len(tasks)} changed file(s) with {max_workers} parallel worker(s)...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(scanner.scan_code_content, code, path, lang): path
                for (code, path, lang) in tasks
            }
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    result = future.result()
                    scan_results.append(result)
                    print(f"🔍 Scanned: {file_path}")
                    if max_workers > 1:
                        time.sleep(1)
                except Exception as e:
                    print(f"❌ Error scanning {file_path}: {e}")
                    scan_results.append({
                        "file_path": file_path,
                        "language": "unknown",
                        "analysis": f"Failed to scan: {str(e)}",
                        "status": "error"
                    })

    if excluded_files:
        print("\n--- Excluded Files in this PR ---")
        for file in sorted(list(set(excluded_files))):
            print(f"- {file}")
        print("---------------------------------\n")

    # Generate reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    scan_id = f"pr-{github_sha[:7] if github_sha else 'unknown'}-{timestamp}"
    
    if not scan_results:
        print("✅ No new code changes to scan (or all files excluded).")
        print("PR scan completed successfully!")
        return
    
    # Store scan findings in database (if enabled)
    pr_number = None
    if github_event_path and os.path.exists(github_event_path):
        try:
            with open(github_event_path, 'r') as f:
                event = json.load(f)
            pr_number = event.get('pull_request', {}).get('number') or event.get('number')
        except:
            pass
    
    _store_scan_findings(scan_results, repo_url, pr_number, scan_id)

    html_generator = HTMLReportGenerator()
    vulnerabilities_by_severity = html_generator._process_results_by_severity(scan_results)
    allowed_severities = html_generator._get_allowed_severities()
    # Only validate findings that can appear in the PR comment (per AI_SAST_SEVERITY)
    findings_to_validate = {
        sev: vulns for sev, vulns in vulnerabilities_by_severity.items()
        if sev in allowed_severities
    }
    total_vulns = sum(len(v) for v in vulnerabilities_by_severity.values())
    vulns_to_validate_count = sum(len(v) for v in findings_to_validate.values())

    # Validate findings with validator LLM; only validated (true positive) go to PR comment and HTML report
    validated_vuln_ids = None
    validator_reasoning = None  # vuln_id -> 1-2 line proof for PR / HTML "Validator proof" section
    validator_llm_and_results = None  # (validator_llm_str, all_results_by_id) for DB
    if vulns_to_validate_count > 0:
        try:
            if vulns_to_validate_count < total_vulns:
                print(f"🔧 Validator: validating {vulns_to_validate_count} finding(s) in severities {allowed_severities} (AI_SAST_SEVERITY); skipping {total_vulns - vulns_to_validate_count} outside scope.")
            validator_result = validate_findings(findings_to_validate, repo_url=repo_url)
            if validator_result is None:
                print("🔧 Validator: disabled (not configured or error). Posting all findings in PR comment and HTML report.")
            else:
                validated_vuln_ids, reasoning_by_id, all_results_by_id, validator_llm_label = validator_result
                validator_reasoning = reasoning_by_id
                validator_llm_and_results = (validator_llm_label, all_results_by_id)
                print(f"🔧 Validator: kept {len(validated_vuln_ids)} finding(s) as true positive for PR comment and HTML report.")
        except Exception as e:
            print(f"⚠️ Validator failed: {e}. Posting all findings in PR comment and HTML report.")
            validated_vuln_ids = None

    # Persist validator LLM and result to DB for each finding (when storage enabled)
    if validator_llm_and_results and os.environ.get('AI_SAST_STORE_FINDINGS', 'false').lower() in ['true', '1', 'yes']:
        try:
            from src.integrations.scan_database import ScanDatabase
            validator_llm_label, all_results_by_id = validator_llm_and_results
            db = ScanDatabase()
            for vid, result_text in all_results_by_id.items():
                db.update_validator_result(scan_id=scan_id, repo_url=repo_url, vuln_id=vid, validator_llm=validator_llm_label, validator_result=result_text)
            db.close()
            print(f"✅ Updated {len(all_results_by_id)} finding(s) with validator results in database.")
        except Exception as e:
            print(f"⚠️ Could not update validator results in database: {e}")

    # Generate HTML report (same filter as PR comment: validated only when validator ran)
    html_report_file = f'ai_sast_pr_scan_report_{timestamp}.html'
    print(f"\n📊 Generating HTML report: {html_report_file}")
    html_generator.generate_report(
        results=scan_results,
        repo_url=repo_url,
        ref_name=github_ref_name,
        output_file=html_report_file,
        validated_vuln_ids=validated_vuln_ids,
        validator_reasoning=validator_reasoning,
    )

    # Generate markdown report for PR comment (optional)
    # Decide whether to post comment: if validator ran, post if any validated; else post if any finding in AI_SAST_SEVERITY
    if validated_vuln_ids is not None:
        should_post_comment = len(validated_vuln_ids) > 0
    else:
        should_post_comment = vulns_to_validate_count > 0

    if should_post_comment:
        print("\n💬 Generating markdown report for PR comment...")
        markdown_report = html_generator.generate_markdown_report(
            scan_results,
            report_title="🤖 AI-SAST Security Scan",
            repo_url=repo_url,
            ref_name=github_ref_name,
            report_context_text="PR changes",
            validated_vuln_ids=validated_vuln_ids,
            validator_reasoning=validator_reasoning,
        )
        
        # Save markdown report for GitHub Actions to use
        with open('pr_comment.md', 'w') as f:
            f.write(markdown_report)
        print("✅ Markdown report saved to pr_comment.md")
        print("   Use this file to post a PR comment in your workflow")
    else:
        if validated_vuln_ids is not None and vulns_to_validate_count > 0:
            print("\nℹ️  No findings validated as true positive; skipping PR comment.")
        else:
            print(f"\nℹ️  No findings in configured severities ({', '.join(allowed_severities)}).")
    
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

