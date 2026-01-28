# Integrations Guide

AI-SAST supports multiple backends and integrations:

## Core: LLM Backends

### Vertex AI (Google Cloud) - Default

**Purpose:** Production-grade AI analysis using Google's Gemini models

**Setup:**
```bash
export LLM_BACKEND="vertex"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export VERTEX_AI_LOCATION="us-central1"
export GEMINI_MODEL="gemini-2.0-flash-exp"
```

**Pros:**
- Production-ready, highly reliable
- Latest Gemini models
- Automatic scaling

**Cons:**
- Requires Google Cloud account
- API costs apply
- Code sent to cloud

---

### Ollama (Local Open-Source) - New! ⭐

**Purpose:** Run security scans completely locally using open-source models

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull qwen2.5-coder:14b

# Configure AI-SAST
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"
export OLLAMA_BASE_URL="http://localhost:11434"
```

**Recommended Models:**
- `qwen2.5-coder:14b` - **Recommended** - Best balance (8GB RAM)
- `qwen2.5-coder:7b` - Fast, code-focused (4GB RAM)
- `qwen2.5-coder:32b` - Most accurate (20GB RAM)
- `codellama:13b` - Meta's code model (8GB RAM)
- `llama3.1:8b` - Latest Llama (5GB RAM)
- `deepseek-coder:33b` - Alternative, very capable (20GB RAM)

**Pros:**
- ✅ 100% free and open-source
- ✅ Complete privacy (code never leaves your machine)
- ✅ No rate limits or API costs
- ✅ Works offline

**Cons:**
- Requires local resources (4-40GB RAM depending on model)
- Slower than cloud models (depends on hardware)
- Need to manage models yourself

**Example:**
```python
# See examples/ollama_scan.py
export LLM_BACKEND="ollama"
python -m src.main.pr_scan
```

---

## Built-in SQLite Database

**Default location:** `~/.ai-sast/scans.db`

**Stores:**
- Scan results (vulnerabilities found)
- Developer feedback (true/false positives)

**Configuration:**
```bash
# Optional: Custom location
export AI_SAST_DB_PATH="/path/to/scans.db"
```

**No setup required** - works automatically!

---

## 1. Jira Integration (Optional)

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

## 2. Databricks Integration (Optional - Enterprise Only)

For enterprises needing centralized storage across multiple teams.

**When to use:** Large teams, centralized analytics, existing Databricks infrastructure

### Setup

```bash
pip install databricks-sql-connector>=2.9.0

export AI_SAST_FEEDBACK_BACKEND="databricks"
export AI_SAST_DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export AI_SAST_DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
export AI_SAST_DATABRICKS_TOKEN="your-token"
export AI_SAST_DATABRICKS_CATALOG="security"
export AI_SAST_DATABRICKS_SCHEMA="sast"
export AI_SAST_DATABRICKS_TABLE="feedback"
```

### Table Schema

```sql
CREATE TABLE feedback (
    timestamp TIMESTAMP,
    repository STRING,
    vuln_id STRING,
    issue STRING,
    severity STRING,
    file_path STRING,
    status STRING,  -- 'False Positive' or 'Confirmed'
    comments STRING,
    user STRING
);
```

---

## 3. Vector/Log Aggregation (Optional)

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

| Integration | Purpose | Default |
|-------------|---------|---------|
| SQLite | Scan results & feedback storage | ✅ Built-in |
| Jira | Vulnerability context | Optional |
| Databricks | Enterprise centralized storage | Optional |
| Vector | Centralized logging (Splunk, etc.) | Optional |

