# Webhook & Feedback Features - Implementation Guide

This document explains how to use the newly implemented webhook notifications and developer feedback collection features in AI-SAST.

## 🎉 What's New

### 1. Webhook Notifications ✅

Send scan results and alerts to external systems like Slack, Teams, Discord, or custom endpoints.

### 2. Interactive Feedback Collection ✅

Collect developer feedback directly from PR comments using interactive checkboxes.

### 3. Automated Feedback Storage ✅

Automatically store developer feedback in Databricks for continuous improvement.

---

## 🔔 Webhook Notifications

### Supported Platforms

- **Slack** - Rich formatting with blocks, buttons, and colors
- **Microsoft Teams** - Adaptive cards with actions
- **Discord** - Rich embeds with formatting
- **Generic** - Standard JSON payload for custom integrations

### Setup

#### 1. Get Your Webhook URL

**Slack:**
1. Go to https://api.slack.com/apps
2. Create an app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to channel
5. Copy the webhook URL

**Microsoft Teams:**
1. Go to your Teams channel
2. Click "..." → Connectors
3. Search for "Incoming Webhook"
4. Configure and copy URL

**Discord:**
1. Go to Server Settings → Integrations
2. Create Webhook
3. Copy webhook URL

#### 2. Configure GitHub Secrets

Add these secrets to your repository (Settings → Secrets → Actions):

```
AI_SAST_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
AI_SAST_WEBHOOK_TYPE=slack  # or: teams, discord, generic
AI_SAST_WEBHOOK_SECRET=optional-signing-secret  # For HMAC verification
```

#### 3. Test It!

Webhooks are automatically triggered when scans complete. No additional configuration needed!

### Webhook Events

#### Scan Completed
Sent when a scan finishes successfully:
- Repository name
- PR number (if applicable)
- Vulnerability counts by severity
- Link to full report
- Scan duration

#### Critical Alert
Sent immediately when critical vulnerabilities are detected:
- Vulnerability details
- File and location
- CVSS vector
- Immediate action required

#### Scan Failed
Sent when a scan encounters errors:
- Error message
- Repository and PR information
- Timestamp

#### Feedback Received
Sent when developers provide feedback:
- Number of true positives marked
- Number of false positives marked
- PR information

### Example Slack Notification

```
🤖 AI-SAST Scan Complete: myorg/myapp
PR #123
5 security issue(s) found

Critical: 2
High: 3
Medium: 0
Low: 0

[View Full Report]
```

---

## 📝 Interactive Feedback Collection

### How It Works

1. **Scan runs** on your PR
2. **PR comment posted** with findings and checkboxes:
   ```markdown
   - [ ] ✅ True Positive  [ ] ❌ False Positive
   **Severity**: Critical
   **Issue**: SQL Injection in user_query.py:42
   ...
   ```
3. **Developer reviews** and checks appropriate box
4. **Feedback automatically collected** when comment is edited
5. **Stored in Databricks** for future scans
6. **AI learns** and improves accuracy over time

### Setup

#### 1. Configure Databricks (Optional but Recommended)

Add these secrets to your repository:

```
AI_SAST_DATABRICKS_HOST=your-workspace.cloud.databricks.com
AI_SAST_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
AI_SAST_DATABRICKS_TOKEN=dapi...
AI_SAST_DATABRICKS_CATALOG=security
AI_SAST_DATABRICKS_SCHEMA=sast
AI_SAST_DATABRICKS_TABLE=feedback
```

#### 2. Create Databricks Table

```sql
CREATE TABLE IF NOT EXISTS security.sast.feedback (
  repo_url STRING,
  pr_number INT,
  file_path STRING,
  vuln_id STRING,
  issue STRING,
  severity STRING,
  status STRING,  -- 'confirmed_vulnerability' or 'false_positive'
  feedback STRING,  -- Optional developer comment
  cvss_vector STRING,
  location STRING,
  timestamp TIMESTAMP,
  created_at TIMESTAMP
);
```

#### 3. Workflow is Auto-Configured

The `.github/workflows/collect-feedback.yml` workflow is already set up to:
- Trigger on PR comment creation/edit
- Parse feedback checkboxes
- Store in Databricks
- Send webhook notification

### Providing Feedback

As a developer, just:

1. **Review** the AI-SAST findings in your PR
2. **Check the appropriate box**:
   - ✅ True Positive - Confirm it's a real issue
   - ❌ False Positive - Mark it as incorrect
3. **Optionally add a comment** explaining your reasoning
4. **Done!** Feedback is automatically collected and stored

### Feedback Format

The system recognizes this format in PR comments:

```markdown
- [ ] ✅ True Positive  [ ] ❌ False Positive
**Severity**: Critical
**Issue**: SQL Injection vulnerability
**Location**: user_query.py:42
**CVSS Vector**: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
```

When you check one of the boxes:

```markdown
- [x] ✅ True Positive  [ ] ❌ False Positive
```

The feedback is captured and processed automatically!

---

## 🔄 How Feedback Improves Scanning

### Feedback Loop

```
1. Scan finds potential vulnerability
   ↓
2. Posted in PR comment with checkboxes
   ↓
3. Developer provides feedback
   ↓
4. Stored in Databricks
   ↓
5. Future scans use this as context
   ↓
6. AI avoids similar false positives
   ↓
7. Accuracy improves over time!
```

### What Gets Better

- **Fewer False Positives**: AI learns what your team considers false positives
- **Better Context**: AI understands your codebase patterns
- **Organizational Knowledge**: Build a database of security decisions
- **Team Alignment**: Security knowledge shared across team

---

## 🧪 Testing

### Test Webhooks

```python
# Test webhook locally
export AI_SAST_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export AI_SAST_WEBHOOK_TYPE="slack"

python -c "
from src.core.webhook_client import WebhookClient

webhook = WebhookClient()
webhook.send_scan_completed(
    repository='myorg/myapp',
    pr_number=123,
    scan_summary={'critical': 2, 'high': 3, 'medium': 5, 'low': 1},
    report_url='https://github.com/myorg/myapp/actions/runs/123'
)
"
```

### Test Feedback Collection

1. Create a test PR
2. Run a scan
3. Manually edit the PR comment
4. Check a feedback checkbox
5. Watch the `collect-feedback` workflow run
6. Verify data in Databricks

---

## 🔒 Security Considerations

### Webhook Security

- **HMAC Signatures**: Set `AI_SAST_WEBHOOK_SECRET` to enable HMAC-SHA256 signatures
- **Signature Header**: Sent as `X-AI-SAST-Signature: sha256=<hash>`
- **Verification**: Receiving endpoint should verify the signature

Example verification (Python):

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### Data Privacy

- **No Code Storage**: Only vulnerability metadata is stored in Databricks
- **Configurable**: All integrations are optional
- **Secure Secrets**: Use GitHub Secrets for all credentials
- **Access Control**: Configure Databricks table permissions appropriately

---

## 📊 Monitoring

### Check Feedback Collection

```sql
-- View recent feedback
SELECT * FROM security.sast.feedback
ORDER BY created_at DESC
LIMIT 100;

-- Feedback summary by repository
SELECT 
  repo_url,
  status,
  COUNT(*) as count
FROM security.sast.feedback
GROUP BY repo_url, status;

-- False positive trends
SELECT 
  DATE(created_at) as date,
  COUNT(*) as false_positive_count
FROM security.sast.feedback
WHERE status = 'false_positive'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Check Webhook Delivery

Check GitHub Actions logs for webhook workflow runs:
1. Go to Actions tab
2. Select "Collect Security Feedback" workflow
3. View logs for delivery status

---

## 🎯 Best Practices

### For Developers

1. **Review Carefully**: Take time to understand each finding
2. **Provide Context**: Add comments explaining false positives
3. **Be Consistent**: Use same criteria across the team
4. **Act Quickly**: Provide feedback while context is fresh

### For Security Teams

1. **Monitor Feedback**: Review false positives regularly
2. **Tune Prompts**: Adjust `AI_SAST_CUSTOM_PROMPT` based on feedback patterns
3. **Share Learnings**: Use feedback to improve security training
4. **Celebrate Wins**: Acknowledge when false positive rate decreases

### For Teams

1. **Set Expectations**: Document what constitutes a false positive
2. **Regular Reviews**: Discuss findings in security reviews
3. **Feedback Culture**: Encourage honest, constructive feedback
4. **Continuous Improvement**: Track metrics and celebrate progress

---

## 🐛 Troubleshooting

### Webhooks Not Working

**Check:**
- Webhook URL is correct and accessible
- Webhook type matches platform (`slack`, `teams`, `discord`)
- GitHub Secret is properly configured
- View workflow logs for error messages

**Test:**
```bash
curl -X POST $AI_SAST_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text": "Test from AI-SAST"}'
```

### Feedback Not Collected

**Check:**
- PR comment contains `🤖 AI-SAST Security Scan` marker
- Checkboxes are in correct format
- Databricks credentials are configured
- `collect-feedback` workflow has run permissions
- View workflow logs for errors

### Feedback Not Improving Results

**Check:**
- Enough feedback collected (need 10+ examples)
- Feedback is consistent across team
- Databricks table is accessible during scans
- Scanner is actually using feedback (check logs)

---

## 📚 Additional Resources

- [INTEGRATIONS.md](INTEGRATIONS.md) - Databricks, Jira, Vector setup
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture details
- [GitHub Actions Docs](https://docs.github.com/en/actions) - Workflow customization
- [Databricks SQL](https://docs.databricks.com/sql/) - Query and analyze feedback

---

**Need help?** Open an issue on GitHub or check the documentation!

