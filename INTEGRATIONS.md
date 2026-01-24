# Optional Integrations Guide

AI-SAST supports optional integrations with external tools to enhance scanning capabilities. All integrations are **optional** and the scanner works perfectly fine without them.

## Available Integrations

### 1. Jira Integration
Fetch vulnerability context from your Jira instance to inform AI analysis.

### 2. Databricks Integration  
Use historical false positive and confirmed vulnerability data to improve scan accuracy over time.

### 3. Vector/Log Aggregator Integration
Send security scan events to your centralized logging system (Splunk HEC, Vector, etc.)

---

## 1. Jira Integration

### Purpose
- Fetch known vulnerabilities from your Jira tracking system
- Provide context to the AI model about existing security issues
- Avoid re-reporting already tracked vulnerabilities

### Setup

#### Install Jira dependency:
```bash
pip install jira>=3.10.5
```

#### Configure environment variables:
```bash
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_JQL_QUERY="project = SECURITY AND status != Closed"  # Required
```

#### Get Jira API Token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token

### Usage

The scanner automatically uses Jira if configured:

```python
from src.core.scanner import SecurityScanner

# Scanner will automatically fetch Jira context if configured
scanner = SecurityScanner()
results = scanner.scan_directory("./src")
```

### Customization

**Custom JQL Query** (Required):

You must define a JQL query to fetch relevant vulnerability tickets:

```bash
# Example: Fetch open security bugs in your project
export JIRA_JQL_QUERY="project = MYPROJECT AND type = 'Security Bug' AND status IN ('Open', 'In Progress')"

# Example: Fetch high-priority vulnerabilities
export JIRA_JQL_QUERY="project = SECURITY AND priority IN (High, Critical) AND status != Closed"

# Example: Fetch vulnerabilities for specific components
export JIRA_JQL_QUERY="project = SECURITY AND component = 'Backend' AND labels = 'vulnerability'"
```

The scanner will use this query to fetch context from Jira.

### Troubleshooting

**Connection fails:**
- Verify your Jira URL is correct
- Check API token is valid
- Ensure your account has access to query issues

**No context fetched:**
- Check your JQL query returns results in Jira web UI
- Verify the issue fields are accessible

---

## 2. Databricks Integration

### Purpose
- Learn from historical scan results
- Reduce false positives over time
- Highlight patterns similar to confirmed vulnerabilities
- Create a feedback loop for continuous improvement

### Setup

#### Install Databricks dependency:
```bash
pip install databricks-sql-connector>=2.9.0
```

#### Configure environment variables:
```bash
export AI_SAST_DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export AI_SAST_DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
export AI_SAST_DATABRICKS_TOKEN="your-databricks-token"
export AI_SAST_DATABRICKS_CATALOG="my_catalog"          # Required: Your catalog name
export AI_SAST_DATABRICKS_SCHEMA="my_schema"            # Required: Your schema name
export AI_SAST_DATABRICKS_TABLE="my_feedback_table"     # Required: Your table name
```

#### Get Databricks Token:
1. Go to your Databricks workspace
2. Click Settings > User Settings
3. Go to Access Tokens tab
4. Generate new token

### Database Schema

Create a table in your Databricks workspace to store feedback. You can customize the catalog, schema, and table names:

```sql
CREATE TABLE IF NOT EXISTS my_catalog.my_schema.my_feedback_table (
    timestamp TIMESTAMP,
    repository STRING,
    vuln_id STRING,
    issue STRING,
    severity STRING,
    file_path STRING,
    location STRING,
    status STRING,          -- 'False Positive', 'Confirmed', 'Needs Triage'
    comments STRING,
    user STRING
);
```

**Note**: Replace `my_catalog`, `my_schema`, and `my_feedback_table` with your actual names, then configure the environment variables accordingly.

### Usage

The scanner automatically fetches feedback if configured:

```python
from src.core.scanner import SecurityScanner

# Scanner will fetch historical feedback for the repository
scanner = SecurityScanner(repo_url="https://github.com/org/repo")
results = scanner.scan_directory("./src")
```

### How It Works

1. Scanner fetches last 90 days of feedback for the repository
2. False positives: AI learns to avoid similar patterns
3. Confirmed vulnerabilities: AI pays extra attention to similar code
4. Feedback is included in the AI prompt context

### Recording Feedback

Log feedback to Databricks when triaging scan results:

```sql
-- Mark as false positive (use your table name)
INSERT INTO my_catalog.my_schema.my_feedback_table VALUES (
    current_timestamp(),
    'https://github.com/org/repo',
    'abc12345',
    'SQL Injection in user_controller.py',
    'HIGH',
    'src/user_controller.py',
    'Line 42',
    'False Positive',
    'Uses parameterized queries - not exploitable',
    'security_team@company.com'
);

-- Confirm vulnerability (use your table name)
INSERT INTO my_catalog.my_schema.my_feedback_table VALUES (
    current_timestamp(),
    'https://github.com/org/repo',
    'def67890',
    'XSS in dashboard.js',
    'CRITICAL',
    'src/dashboard.js',
    'Line 108',
    'Confirmed',
    'Verified exploitable - fix required',
    'security_team@company.com'
);
```

---

## 3. Vector/Log Aggregator Integration

### Purpose
- Centralize security scan events
- Track findings over time
- Integrate with SIEM systems
- Create dashboards and alerts

### Setup

#### No additional dependencies needed (uses `requests`)

#### Configure environment variables:
```bash
export AI_SAST_VECTOR_URL="https://your-splunk-hec.company.com/services/collector"
export AI_SAST_VECTOR_TOKEN="your-hec-token"

# Or for raw host:port format:
export AI_SAST_VECTOR_URL="splunk.company.com"  # Will add http:// and :8088/services/collector
export AI_SAST_VECTOR_TOKEN="your-hec-token"
```

### Usage

#### Automatic logging in scans:
Events are automatically logged during scans if configured.

#### Manual logging:
```python
from src.integrations.vector import VectorClient

client = VectorClient()

# Log a vulnerability
client.log_vulnerability(
    repo_url="https://github.com/org/repo",
    file_path="src/app.py",
    severity="HIGH",
    issue="SQL Injection vulnerability",
    status="Needs Triage",
    vuln_id="vuln-123",
    location="Line 42",
    cvss_score="8.5"
)

# Log scan completion
client.log_scan_complete(
    repo_url="https://github.com/org/repo",
    total_files=150,
    vulnerabilities_found=3
)
```

### Event Format

Events are sent in Splunk HEC format:

```json
{
  "event": {
    "repo": "https://github.com/org/repo",
    "category": "AI-SAST",
    "timestamp": "2026-01-23 10:30:00",
    "severity": "HIGH",
    "issue": "SQL Injection",
    "file_path": "src/app.py",
    "location": "Line 42",
    "status": "Needs Triage",
    "vuln_id": "vuln-123",
    "cvss_score": "8.5"
  }
}
```

### Compatible Systems

- ✅ Splunk (HTTP Event Collector)
- ✅ Vector.dev
- ✅ Elastic Stack (with HEC-compatible endpoint)
- ✅ Any system accepting JSON over HTTP

---

## Testing Integrations

### Test Jira:
```bash
python -m src.core.jira_client \
  --url "https://company.atlassian.net" \
  --username "user@company.com" \
  --token "your-token" \
  --jql "project = SECURITY"
```

### Test Databricks:
```bash
python -m src.core.databricks_client \
  --repo-url "https://github.com/org/repo"
```

### Test Vector:
```bash
python -m src.core.vector_client \
  --endpoint "https://splunk.company.com/services/collector" \
  --token "your-token" \
  --test-event
```

---

## Disabling Integrations

All integrations are optional. Simply don't set the environment variables:

```bash
# Jira: Don't set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
# Databricks: Don't set AI_SAST_DATABRICKS_* variables
# Vector: Don't set AI_SAST_VECTOR_URL, AI_SAST_VECTOR_TOKEN
```

The scanner will work normally without any integrations!

---

## Security Notes

- 🔒 Store tokens in environment variables or secrets managers
- 🔒 Never commit tokens to version control
- 🔒 Use least-privilege access for all integrations
- 🔒 Rotate tokens regularly
- 🔒 Monitor integration access logs

---

## Summary

| Integration | Purpose | Required Packages | Optional |
|-------------|---------|-------------------|----------|
| Jira | Vulnerability context | `jira>=3.10.5` | ✅ Yes |
| Databricks | Historical feedback | `databricks-sql-connector>=2.9.0` | ✅ Yes |
| Vector | Centralized logging | Built-in (`requests`) | ✅ Yes |

All integrations enhance the scanner but are **completely optional**!

