#!/usr/bin/env python3
"""
GitHub PR Feedback Collector

This script processes PR comments with checkboxes to collect developer feedback
on security findings and stores them in Databricks for future scan improvements.

This runs as a GitHub Action triggered by PR comment events.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.feedback import get_feedback_client


def parse_feedback_from_comment(comment_body: str) -> List[Dict]:
    """
    Parse feedback checkboxes from PR comment
    
    Expected format in comment:
    - [x] ✅ True Positive  [ ] ❌ False Positive
      **Issue**: SQL Injection in user_query.py:42
      **CVSS**: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
      ...
    
    Args:
        comment_body: The PR comment text
        
    Returns:
        List of feedback dictionaries
    """
    feedback_list = []
    
    # Pattern to match feedback sections
    # Matches: - [x] ✅ True Positive  [ ] ❌ False Positive
    pattern = r'- \[([ x])\] ✅ True Positive\s+\[([ x])\] ❌ False Positive'
    
    # Split comment into sections by the feedback pattern
    sections = re.split(pattern, comment_body)
    
    # Process sections in groups of 3 (match, tp_checkbox, fp_checkbox, content)
    for i in range(1, len(sections), 3):
        if i + 2 >= len(sections):
            break
            
        tp_checked = sections[i].strip() == 'x'
        fp_checked = sections[i + 1].strip() == 'x'
        content = sections[i + 2] if i + 2 < len(sections) else ""
        
        # Only process if one checkbox is selected
        if not (tp_checked or fp_checked):
            continue
        
        status = "confirmed_vulnerability" if tp_checked else "false_positive"
        
        # Extract vulnerability details from content
        vuln_data = _extract_vulnerability_details(content)
        if vuln_data:
            vuln_data['status'] = status
            feedback_list.append(vuln_data)
    
    return feedback_list


def _extract_vulnerability_details(content: str) -> Optional[Dict]:
    """
    Extract vulnerability details from comment section
    
    Args:
        content: Section of comment with vulnerability details
        
    Returns:
        Dictionary with vulnerability data or None
    """
    details = {}
    
    # Extract severity
    severity_match = re.search(r'\*\*Severity\*\*:\s*(\w+)', content, re.IGNORECASE)
    if severity_match:
        details['severity'] = severity_match.group(1)
    
    # Extract issue description
    issue_match = re.search(r'\*\*Issue\*\*:\s*(.+?)(?:\n|$)', content)
    if issue_match:
        details['issue'] = issue_match.group(1).strip()
    
    # Extract file and location
    location_match = re.search(r'\*\*Location\*\*:\s*(.+?)(?:\n|$)', content)
    if location_match:
        location_str = location_match.group(1).strip()
        # Parse "file.py:42" or "file.py, Line 42"
        file_match = re.match(r'([^:,]+)', location_str)
        if file_match:
            details['file_path'] = file_match.group(1).strip()
            details['location'] = location_str
    
    # Extract CVSS vector
    cvss_match = re.search(r'\*\*CVSS Vector\*\*:\s*(CVSS:[^\n]+)', content)
    if cvss_match:
        details['cvss_vector'] = cvss_match.group(1).strip()
    
    # Extract developer feedback/comments (if any)
    feedback_match = re.search(r'\*\*Comment\*\*:\s*(.+?)(?:\n\n|\n-|\Z)', content, re.DOTALL)
    if feedback_match:
        details['feedback'] = feedback_match.group(1).strip()
    
    # Generate a unique ID from the content
    if 'file_path' in details and 'issue' in details:
        vuln_id = f"{details['file_path']}:{details.get('location', 'unknown')}:{details['issue'][:50]}"
        details['vuln_id'] = vuln_id
        return details
    
    return None


def main():
    """Main function to process PR feedback"""
    print("🔄 Processing PR feedback from comment...")
    
    # Get GitHub event data
    github_event_path = os.environ.get('GITHUB_EVENT_PATH')
    if not github_event_path:
        print("❌ Error: GITHUB_EVENT_PATH not set (not running in GitHub Actions)")
        sys.exit(1)
    
    try:
        with open(github_event_path, 'r') as f:
            event_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading GitHub event data: {e}")
        sys.exit(1)
    
    # Extract comment body
    comment_body = event_data.get('comment', {}).get('body', '')
    if not comment_body:
        print("ℹ️  No comment body found")
        sys.exit(0)
    
    # Check if comment is from AI-SAST (contains our marker)
    if '🤖 AI-SAST Security Scan' not in comment_body:
        print("ℹ️  Not an AI-SAST comment, skipping")
        sys.exit(0)
    
    # Parse feedback
    print("📝 Parsing feedback from comment...")
    feedback_list = parse_feedback_from_comment(comment_body)
    
    if not feedback_list:
        print("ℹ️  No feedback checkboxes found in comment")
        sys.exit(0)
    
    print(f"✅ Found {len(feedback_list)} feedback item(s)")
    
    # Get repository and PR information
    repo_url = event_data.get('repository', {}).get('html_url', '')
    pr_number = event_data.get('issue', {}).get('number')
    
    if not repo_url or not pr_number:
        print("❌ Error: Could not extract repository URL or PR number")
        sys.exit(1)
    
    print(f"📍 Repository: {repo_url}")
    print(f"📍 PR: #{pr_number}")
    
    # Initialize feedback client (SQLite or Databricks)
    print("\n🔌 Initializing feedback system...")
    feedback_client = get_feedback_client()
    
    if not feedback_client.is_configured:
        print("⚠️  Feedback system not configured - feedback will not be stored")
        print("   By default, feedback is stored in SQLite at ~/.ai-sast/feedback.db")
        print("   To use Databricks instead, set these environment variables:")
        print("   - AI_SAST_DATABRICKS_HOST")
        print("   - AI_SAST_DATABRICKS_HTTP_PATH")
        print("   - AI_SAST_DATABRICKS_TOKEN")
        print("   - AI_SAST_DATABRICKS_CATALOG")
        print("   - AI_SAST_DATABRICKS_SCHEMA")
        print("   - AI_SAST_DATABRICKS_TABLE")
        sys.exit(0)
    
    backend_name = type(feedback_client).__name__
    print(f"✅ Using {backend_name} for feedback storage")
    
    # Store feedback
    print("\n💾 Storing feedback...")
    success_count = feedback_client.store_batch_feedback(
        repo_url=repo_url,
        pr_number=pr_number,
        feedback_list=feedback_list
    )
    
    feedback_client.close()
    
    # Summary
    print(f"\n✅ Successfully stored {success_count}/{len(feedback_list)} feedback records")
    
    # Send webhook notification (optional)
    try:
        from core.webhook_client import WebhookClient
        webhook = WebhookClient()
        if webhook.is_configured:
            print("\n📡 Sending webhook notification...")
            true_positives = sum(1 for f in feedback_list if f.get('status') == 'confirmed_vulnerability')
            false_positives = sum(1 for f in feedback_list if f.get('status') == 'false_positive')
            
            webhook.send_feedback_received(
                repository=repo_url,
                pr_number=pr_number,
                feedback_summary={
                    'true_positives': true_positives,
                    'false_positives': false_positives,
                    'total': len(feedback_list)
                }
            )
    except Exception as e:
        print(f"⚠️  Webhook notification skipped: {e}")
    
    print("\n✨ Feedback processing complete!")


if __name__ == "__main__":
    main()

