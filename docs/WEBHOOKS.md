# Webhook Integration & Feedback Loop

The webhook integration enables an automated feedback loop where developers can mark findings as true or false positives, and the system learns from this feedback over time.

## Overview

```
Developer reviews PR comment
    ↓
Checks ☑ True Positive or ☑ False Positive
    ↓
GitHub sends webhook event
    ↓
Webhook listener captures feedback
    ↓
Stored in SQLite or Databricks
    ↓
Future scans learn from feedback
```

## How It Works

### 1. AI-SAST Posts Findings

When a scan completes, AI-SAST posts a PR comment with:
- Vulnerability details (severity, issue, location, CVSS)
- Interactive checkboxes for feedback
- Unique vulnerability ID for tracking

Example:
```markdown
---

<!-- vuln-id: a7b3c9f2 -->

- [ ] ✅ True Positive
- [ ] ❌ False Positive

**ID**: `a7b3c9f2`
**Severity**: Critical
**Issue**: SQL Injection vulnerability
**Location**: `src/auth/login.py:45`
**CVSS Vector**: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
```

### 2. Developer Provides Feedback

Developer clicks "Edit" on the PR comment and checks a box:

**True Positive** (real vulnerability):
```markdown
- [x] ✅ True Positive
- [ ] ❌ False Positive
```

**False Positive** (false alarm):
```markdown
- [ ] ✅ True Positive
- [x] ❌ False Positive
```

### 3. Webhook Captures Feedback

When the comment is edited, GitHub sends a webhook event to the listener, which:
1. Extracts the vulnerability ID from the hidden HTML comment
2. Parses the checkbox state
3. Stores the feedback with developer name and timestamp

### 4. Feedback Storage

**SQLite (Default):**
- Stored locally at `~/.ai-sast/scans.db`
- Two tables: `scan_results` and `feedback`
- No setup required

**Databricks (Optional for Enterprise):**
- Centralized storage for multiple teams/repositories
- Requires Databricks workspace and credentials
- Enables organization-wide feedback learning

## Setup

### Option 1: Local Feedback (Default)

No setup required! Feedback is automatically stored in SQLite at `~/.ai-sast/scans.db`.

**Limitations:**
- Only captures feedback when webhook is deployed
- No automatic PR comment updates (developer must edit manually)
- Local to each repository

### Option 2: Deploy Webhook Listener

For automated feedback capture from PR comment edits.

#### Prerequisites

- AWS account (or other cloud provider)
- Terraform installed
- GitHub webhook secret (optional but recommended)

#### Deployment Steps

**1. Deploy Infrastructure**

```bash
cd webhook/iac

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy
terraform apply
```

This creates:
- ECS cluster and service
- Application Load Balancer
- API Gateway
- Security groups
- ECR repository for Docker image

**2. Build and Push Docker Image**

```bash
cd webhook

# Build image
docker build -t ai-sast-webhook .

# Tag for ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag ai-sast-webhook:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ai-sast-webhook:latest

# Push
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ai-sast-webhook:latest
```

**3. Configure GitHub Webhook**

Go to: **Repository Settings → Webhooks → Add webhook**

- **Payload URL**: `https://your-webhook-url.com/webhook` (from Terraform output)
- **Content type**: `application/json`
- **Secret**: Generate a secure secret (recommended)
- **Events**: Select "Issue comments"
- **Active**: ✓

**4. Set Environment Variables**

Update ECS task definition with:

```bash
# Required
GITHUB_WEBHOOK_SECRET=your-webhook-secret  # Same as GitHub webhook secret

# Optional (if using Databricks)
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ACCESS_TOKEN=your-access-token

# Optional
AI_SAST_DB_PATH=/data/scans.db  # Custom database path
```

**5. Test Webhook**

```bash
# Send test payload
curl -X POST https://your-webhook-url.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d @test-payload.json
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_WEBHOOK_SECRET` | Secret for validating webhook payloads | Recommended | - |
| `AI_SAST_DB_PATH` | Path to SQLite database | No | `~/.ai-sast/scans.db` |
| `DATABRICKS_SERVER_HOSTNAME` | Databricks workspace URL | No (for Databricks) | - |
| `DATABRICKS_HTTP_PATH` | Databricks SQL warehouse path | No (for Databricks) | - |
| `DATABRICKS_ACCESS_TOKEN` | Databricks access token | No (for Databricks) | - |

### Webhook Security

**HMAC Signature Verification:**

The webhook validates GitHub's HMAC signature to ensure requests are authentic:

```python
# Automatic validation in webhook/main.py
signature = request.headers.get('X-Hub-Signature-256')
if not verify_signature(payload, signature, GITHUB_WEBHOOK_SECRET):
    return "Invalid signature", 401
```

**Best Practices:**
1. Always set `GITHUB_WEBHOOK_SECRET`
2. Use HTTPS for webhook URL
3. Restrict webhook to specific events (Issue comments only)
4. Monitor webhook logs for suspicious activity

## Database Schema

### SQLite Schema

**scan_results table:**
```sql
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vuln_id TEXT UNIQUE NOT NULL,           -- Unique vulnerability ID
    file_path TEXT NOT NULL,                 -- File containing vulnerability
    severity TEXT NOT NULL,                  -- Critical/High/Medium/Low
    issue TEXT NOT NULL,                     -- Vulnerability description
    location TEXT,                           -- Line number or code location
    cvss_vector TEXT,                        -- CVSS v3.1 vector string
    risk TEXT,                               -- Risk explanation
    fix TEXT,                                -- Remediation steps
    repo_url TEXT,                           -- Repository URL
    pr_number INTEGER,                       -- Pull request number
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**feedback table:**
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vuln_id TEXT NOT NULL,                   -- Links to scan_results
    status TEXT NOT NULL,                    -- true_positive or false_positive
    developer_name TEXT,                     -- Developer who provided feedback
    developer_username TEXT,                 -- GitHub username
    pr_url TEXT,                             -- PR URL
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vuln_id) REFERENCES scan_results(vuln_id)
);
```

### Querying Feedback

**Get all feedback:**
```bash
sqlite3 ~/.ai-sast/scans.db "SELECT * FROM feedback;"
```

**Get false positive rate:**
```sql
SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM feedback
GROUP BY status;
```

**Get feedback by developer:**
```sql
SELECT developer_name, status, COUNT(*) as count
FROM feedback
GROUP BY developer_name, status;
```

## Databricks Integration (Optional)

For enterprise deployments with multiple teams and repositories.

### Benefits

- **Centralized Feedback**: All teams contribute to shared learning
- **Cross-Repository Learning**: Feedback from one repo helps others
- **Advanced Analytics**: Query feedback across organization
- **Data Warehouse**: Integrate with existing data pipelines

### Setup

**1. Create Databricks Tables**

```sql
-- In Databricks SQL editor
CREATE TABLE IF NOT EXISTS ai_sast_scan_results (
    vuln_id STRING,
    file_path STRING,
    severity STRING,
    issue STRING,
    location STRING,
    cvss_vector STRING,
    risk STRING,
    fix STRING,
    repo_url STRING,
    pr_number INT,
    scan_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_sast_feedback (
    vuln_id STRING,
    status STRING,
    developer_name STRING,
    developer_username STRING,
    pr_url STRING,
    feedback_date TIMESTAMP
);
```

**2. Configure Credentials**

```bash
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="your-access-token"
```

**3. Enable in Code**

The system automatically uses Databricks if credentials are set. No code changes needed.

### Querying Databricks Feedback

```sql
-- False positive rate by repository
SELECT 
    repo_url,
    status,
    COUNT(*) as count
FROM ai_sast_feedback
GROUP BY repo_url, status;

-- Top false positive patterns
SELECT 
    r.issue,
    COUNT(*) as fp_count
FROM ai_sast_feedback f
JOIN ai_sast_scan_results r ON f.vuln_id = r.vuln_id
WHERE f.status = 'false_positive'
GROUP BY r.issue
ORDER BY fp_count DESC
LIMIT 10;

-- Feedback trends over time
SELECT 
    DATE_TRUNC('week', feedback_date) as week,
    status,
    COUNT(*) as count
FROM ai_sast_feedback
GROUP BY week, status
ORDER BY week DESC;
```

## Optional Notifications

Send feedback notifications to team chat channels.

### Slack

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

When feedback is received, sends:
```
🔒 AI-SAST Feedback Received
Repository: org/repo
PR: #123
Vulnerability: SQL Injection (Critical)
Status: ✅ True Positive
Developer: @username
```

### Microsoft Teams

```bash
export TEAMS_WEBHOOK_URL="https://your-org.webhook.office.com/webhookb2/..."
```

### Discord

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

## Monitoring & Debugging

### Webhook Logs

**AWS CloudWatch:**
```bash
aws logs tail /ecs/ai-sast-webhook --follow
```

**Local Testing:**
```bash
# Run webhook locally
cd webhook
python main.py

# In another terminal, send test request
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d @test-payload.json
```

### Common Issues

**Webhook not receiving events:**
1. Check GitHub webhook settings (Settings → Webhooks)
2. Verify webhook URL is correct
3. Check "Recent Deliveries" in GitHub for errors
4. Ensure webhook is set to "Issue comments" event

**Invalid signature errors:**
1. Verify `GITHUB_WEBHOOK_SECRET` matches GitHub webhook secret
2. Check webhook secret was set when creating webhook
3. Ensure payload is raw bytes, not decoded JSON

**Database connection errors:**
1. Check database path exists and is writable
2. Verify Databricks credentials if using Databricks
3. Check network connectivity to Databricks

**Feedback not being stored:**
1. Check webhook logs for errors
2. Verify vuln_id exists in PR comment
3. Ensure checkbox format is correct (separate lines)

## Advanced Configuration

### Custom Webhook Port

```bash
# In webhook/main.py
app.run(host='0.0.0.0', port=8080)
```

### Custom Database Path

```bash
export AI_SAST_DB_PATH="/custom/path/scans.db"
```

### Rate Limiting

Add rate limiting to prevent abuse:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/webhook', methods=['POST'])
@limiter.limit("100 per hour")
def webhook():
    # ...
```

### Webhook Retry Logic

GitHub retries failed webhooks with exponential backoff. Ensure your webhook:
1. Responds within 10 seconds
2. Returns 2xx status code for success
3. Returns 4xx for client errors (won't retry)
4. Returns 5xx for server errors (will retry)

## Infrastructure as Code

All webhook infrastructure is defined in Terraform:

```
webhook/iac/
├── main.tf                # Main configuration
├── variables.tf           # Input variables
├── provider.tf            # AWS provider
└── modules/
    ├── ecr/              # Container registry
    ├── ecs_cluster/      # ECS cluster
    ├── ecs_service/      # ECS service
    ├── lb/               # Load balancer
    ├── security_group/   # Security groups
    └── task_definition/  # ECS task definition
```

### Customization

Edit `webhook/iac/variables.tf` to customize:
- AWS region
- Instance sizes
- Auto-scaling settings
- Network configuration

## Costs

### AWS (with webhook deployed)

Estimated monthly costs:
- **ECS Fargate**: $10-30 (depends on traffic)
- **Application Load Balancer**: $20-30
- **NAT Gateway**: $30-50 (if using private subnets)
- **Data transfer**: $5-10

**Total**: ~$65-120/month for webhook infrastructure

### SQLite (local)

**Cost**: $0 (runs locally)

**Limitation**: Feedback only captured when webhook service is running

## FAQ

**Q: Do I need to deploy the webhook?**
A: No, it's optional. Feedback is stored in SQLite by default, but webhook enables automatic capture from PR comment edits.

**Q: Can I use GitHub Actions instead of a webhook?**
A: Webhooks are needed for real-time feedback capture. GitHub Actions can't monitor comment edits effectively.

**Q: How do I migrate from SQLite to Databricks?**
A: Export SQLite data and import to Databricks using the provided schema. Set Databricks credentials and the system will use it automatically.

**Q: Can I self-host the webhook?**
A: Yes, run the Flask app on any server with Docker. Just ensure GitHub can reach your webhook URL.

**Q: Is the webhook secure?**
A: Yes, when configured with `GITHUB_WEBHOOK_SECRET`. It validates HMAC signatures on all requests.

**Q: Can I customize the feedback workflow?**
A: Yes, edit `webhook/main.py` to add custom logic, notifications, or integrations.

**Q: Does the webhook work with GitLab or Bitbucket?**
A: Currently GitHub only, but the code can be adapted for other platforms.

## Getting Help

- **Webhook Issues**: Check CloudWatch logs or run locally for debugging
- **Database Issues**: Verify SQLite file permissions or Databricks credentials
- **GitHub Webhook**: Check "Recent Deliveries" in GitHub webhook settings
- **General Support**: [Open an issue](https://github.com/YOUR_USERNAME/ai-sast/issues)
