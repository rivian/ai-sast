from flask import Flask, request, abort
import os
import hmac
import hashlib
import re
import boto3
import json
import logging
import time
from typing import Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# AWS SNS for notifications (optional)
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
sns_client = boto3.client('sns') if SNS_TOPIC_ARN else None

# Deduplication cache
processed_events = {}
DEDUP_WINDOW_SECONDS = 60


def sanitize_for_logging(value: str) -> str:
    """Sanitize string for safe logging by removing newlines and control characters."""
    if not value:
        return ""
    sanitized = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    sanitized = re.sub(r'[\x00-\x1F\x7F]', '', sanitized)
    return sanitized


def get_secret_from_aws(secret_id: str, key: str = None) -> Optional[str]:
    """Get a secret value from AWS Secrets Manager."""
    try:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_id)
        secret_string = response['SecretString']
        return json.loads(secret_string)[key] if key else secret_string
    except Exception as e:
        logger.error(f"❌ Failed to retrieve secret {secret_id}: {e}")
        return None


def verify_github_signature(request) -> bool:
    """Verify the request signature to ensure it's from GitHub."""
    github_webhook_secret = get_secret_from_aws('github-webhook-secret', 'github-webhook-secret')
    if not github_webhook_secret:
        logger.error("❌ Failed to retrieve GitHub webhook secret")
        return False
    
    signature_header = request.headers.get('X-Hub-Signature-256')
    if not signature_header:
        logger.error("❌ Missing X-Hub-Signature-256 header")
        return False
    
    # GitHub sends signature as "sha256=<hash>"
    expected_signature = 'sha256=' + hmac.new(
        github_webhook_secret.encode('utf-8'),
        request.data,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature_header, expected_signature):
        logger.error("❌ Invalid GitHub signature")
        return False
    
    return True


def store_feedback_in_database(
    repo_url: str,
    pr_number: int,
    file_path: str,
    vuln_id: str,
    issue: str,
    severity: str,
    status: str,
    cvss_vector: str = "",
    location: str = "",
    user_name: str = "",
    user_username: str = "",
    updated_timestamp: str = ""
) -> bool:
    """
    Store feedback in the configured backend (SQLite or Databricks).
    
    Args:
        repo_url: Repository URL
        pr_number: Pull request number
        file_path: Path to the file
        vuln_id: Vulnerability ID
        issue: Issue description
        severity: Severity level
        status: confirmed_vulnerability or false_positive
        cvss_vector: CVSS vector string
        location: Location in file
        user_name: User who provided feedback
        user_username: Username
        updated_timestamp: When feedback was given
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import feedback client
        import sys
        sys.path.insert(0, '/app/src')  # Adjust path based on Docker container structure
        from integrations.feedback import get_feedback_client
        
        feedback_client = get_feedback_client()
        
        if not feedback_client.is_configured:
            logger.warning("⚠️ Feedback system not configured, cannot store feedback")
            return False
        
        success = feedback_client.store_feedback(
            repo_url=repo_url,
            pr_number=pr_number,
            file_path=file_path,
            vulnerability_id=vuln_id,
            issue=issue,
            severity=severity,
            status=status,
            feedback=f"Provided by {user_name} ({user_username})",
            cvss_vector=cvss_vector,
            location=location
        )
        
        feedback_client.close()
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to store feedback: {e}")
        return False


def handle_feedback(
    vuln_id: str,
    new_status: str,
    pr_url: str,
    comment_body: str = "",
    user_name: str = "",
    user_username: str = "",
    updated_timestamp: str = ""
) -> None:
    """
    Handles developer feedback from GitHub PR comments.
    
    Args:
        vuln_id: Vulnerability ID (extracted from checkbox)
        new_status: 'true_positive' or 'false_positive'
        pr_url: Pull request URL
        comment_body: Full comment text
        user_name: User who provided feedback
        user_username: GitHub username
        updated_timestamp: ISO timestamp
    """
    # Deduplication
    event_key = f"{vuln_id}:{new_status}:{pr_url}:{updated_timestamp}"
    current_time = time.time()
    
    # Clean up expired cache entries
    expired_keys = [k for k, v in processed_events.items() if current_time - v > DEDUP_WINDOW_SECONDS]
    for k in expired_keys:
        del processed_events[k]
    
    if event_key in processed_events:
        logger.warning(f"⚠️ Duplicate event for {vuln_id}, skipping")
        return
    
    processed_events[event_key] = current_time
    
    # Extract vulnerability details from comment
    severity = ""
    issue = ""
    file_path = ""
    cvss_vector = ""
    location = ""
    
    if comment_body:
        lines = comment_body.split('\n')
        for line in lines:
            if '**Severity**:' in line:
                severity = line.split('**Severity**:')[1].strip()
            elif '**Issue**:' in line:
                issue = line.split('**Issue**:')[1].strip()
            elif '**Location**:' in line:
                location_match = line.split('**Location**:')[1].strip()
                # Extract file path from markdown link or plain text
                file_match = re.search(r'\[`([^`]+)`\]', location_match)
                if file_match:
                    file_path = file_match.group(1).split(':')[0]  # Remove line number
                    location = location_match
            elif '**CVSS Vector**:' in line:
                cvss_match = re.search(r'`([^`]+)`', line)
                if cvss_match:
                    cvss_vector = cvss_match.group(1)
    
    # Map status
    db_status = "confirmed_vulnerability" if new_status == "true_positive" else "false_positive"
    
    # Extract PR number from URL
    pr_number_match = re.search(r'/pull/(\d+)', pr_url)
    pr_number = int(pr_number_match.group(1)) if pr_number_match else 0
    
    # Store in feedback database
    success = store_feedback_in_database(
        repo_url=pr_url.rsplit('/pull/', 1)[0],  # Get repo URL without PR path
        pr_number=pr_number,
        file_path=file_path,
        vuln_id=vuln_id,
        issue=issue,
        severity=severity,
        status=db_status,
        cvss_vector=cvss_vector,
        location=location,
        user_name=user_name,
        user_username=user_username,
        updated_timestamp=updated_timestamp
    )
    
    if success:
        logger.info(f"✅ Stored feedback for {vuln_id}: {new_status}")
    
    # Send SNS notification if configured
    if sns_client and SNS_TOPIC_ARN and new_status == "true_positive":
        try:
            response = sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps({
                    'vuln_id': vuln_id,
                    'status': new_status,
                    'pr_url': pr_url,
                    'severity': severity,
                    'user': user_username
                }),
                Subject="AI-SAST Confirmed Vulnerability"
            )
            logger.info(f"✅ SNS published: {response['MessageId']}")
        except Exception as e:
            logger.error(f"❌ SNS publish failed: {e}")


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint that returns 200 OK."""
    return "AI-SAST Webhook Listener - OK", 200


@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint to handle events from GitHub."""
    
    # Verify GitHub signature
    if not verify_github_signature(request):
        abort(401, "Signature verification failed.")
    
    # Get event type
    event_type = request.headers.get('X-GitHub-Event')
    
    # We only care about issue_comment events (PR comments)
    if event_type != 'issue_comment':
        return "Event not supported", 200
    
    payload = request.json
    
    # Only process if it's a PR comment (not an issue comment)
    if not payload.get('issue', {}).get('pull_request'):
        return "Not a pull request comment", 200
    
    # Get action (created, edited, deleted)
    action = payload.get('action')
    if action not in ['created', 'edited']:
        return "Action not supported", 200
    
    # Get comment body
    comment_body = payload.get('comment', {}).get('body', '')
    
    # Check if it's an AI-SAST comment (contains our marker)
    if '🤖 AI-SAST Security Scan' not in comment_body:
        return "Not an AI-SAST comment", 200
    
    # Extract checkbox patterns (each on separate line)
    # Looking for:
    # - [x] ✅ True Positive
    # - [ ] ❌ False Positive
    checkbox_pattern = re.compile(r'- \[([ x])\] ✅ True Positive')
    
    if not checkbox_pattern.search(comment_body):
        return "No feedback checkboxes found", 200
    
    # Get user who made the comment/edit
    user = payload.get('comment', {}).get('user', {})
    user_name = user.get('name', user.get('login', ''))
    user_username = user.get('login', '')
    
    # Get PR URL
    pr_url = payload.get('issue', {}).get('html_url', '')
    
    # Get timestamp
    updated_timestamp = payload.get('comment', {}).get('updated_at', '')
    
    # Find all checked boxes (on separate lines)
    checked_pattern = re.compile(r'- \[x\] ✅ True Positive')
    false_positive_pattern = re.compile(r'- \[x\] ❌ False Positive')
    
    # Split comment into sections and process each vulnerability
    sections = comment_body.split('---')
    
    feedback_count = 0
    for section in sections:
        # Check if this section has a checked box
        is_true_positive = checked_pattern.search(section)
        is_false_positive = false_positive_pattern.search(section)
        
        if not (is_true_positive or is_false_positive):
            continue
        
        # Extract vulnerability ID from hidden comment or ID field
        vuln_id = None
        
        # Try to extract from HTML comment first (<!-- vuln-id: abc123 -->)
        id_comment_match = re.search(r'<!--\s*vuln-id:\s*([a-f0-9]+)\s*-->', section)
        if id_comment_match:
            vuln_id = id_comment_match.group(1)
        else:
            # Try to extract from visible ID field (**ID**: `abc123`)
            id_field_match = re.search(r'\*\*ID\*\*:\s*`([a-f0-9]+)`', section)
            if id_field_match:
                vuln_id = id_field_match.group(1)
            else:
                # Fallback: generate from section hash (for backwards compatibility)
                vuln_id = f"legacy-{hash(section) % 100000000:08x}"
                logger.warning(f"⚠️ No vuln_id found in section, using fallback: {vuln_id}")
        
        status = 'true_positive' if is_true_positive else 'false_positive'
        
        handle_feedback(
            vuln_id=vuln_id,
            new_status=status,
            pr_url=pr_url,
            comment_body=section,
            user_name=user_name,
            user_username=user_username,
            updated_timestamp=updated_timestamp
        )
        
        feedback_count += 1
    
    if feedback_count > 0:
        logger.info(f"✅ Processed {feedback_count} feedback item(s) from {pr_url}")
        return {"status": "success", "processed": feedback_count}, 200
    else:
        return "No checked feedback found", 200


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

