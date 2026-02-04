# Feedback Loop

Learn how AI-SAST continuously improves through developer feedback.

## Overview

The feedback loop allows developers to mark security findings as **true positives** (✅) or **false positives** (❌) directly in GitHub PR comments. This feedback is stored in a database and used to improve future scans.

## How It Works

### 1. Scan & Report
```
PR Created → AI-SAST Scans → Posts Comment with Findings
```

Each finding includes:
- ✅ True Positive checkbox
- ❌ False Positive checkbox
- Vulnerability details (severity, location, fix)

### 2. Developer Feedback
```
Developer Reviews → Checks Boxes → Optionally Adds Comments
```

Example:
```markdown
<!-- vuln-id: abc12345 -->

- [x] ✅ True Positive
- [ ] ❌ False Positive

**Issue**: SQL Injection
**Location**: user_query.py:42
```

### 3. Automatic Collection
```
Comment Edited → Workflow Triggers → Feedback Stored in Database
```

The `collect-feedback.yml` workflow:
- Detects checked boxes
- Parses vulnerability details
- Stores in SQLite (or Databricks)

### 4. Future Scans Use Feedback
```
Next Scan → Retrieve Feedback → Include in AI Prompt → Improved Accuracy
```

The AI receives context like:
```markdown
## Historical False Positives
Avoid reporting similar issues:

1. **Issue**: SQL Injection
   - **File**: user_query.py
   - **Reason**: Uses parameterized queries
```

## Setup

### Step 1: Verify Workflow Exists

The feedback collection workflow should already be in your repository:
```
.github/workflows/collect-feedback.yml
```

### Step 2: Test It

1. **Create a test PR**
2. **Let AI-SAST scan and comment**
3. **Check a box** (✅ or ❌)
4. **Watch the workflow run** in Actions tab
5. **Verify storage**:
   ```bash
   python3 -m src.integrations.scan_database --stats
   ```

### Step 3: Monitor Feedback

```bash
# View statistics
python3 -m src.integrations.scan_database --stats --repo-url https://github.com/org/repo

# Query database directly
sqlite3 ~/.ai-sast/scans.db "SELECT * FROM feedback ORDER BY timestamp DESC LIMIT 10;"
```

## Architecture

```
┌─────────────────┐
│  PR Scan        │
│  (retrieves     │
│   feedback)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post Comment   │
│  with Checkboxes│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Developer      │
│  Checks Boxes   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Collect        │
│  Feedback       │
│  Workflow       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite         │
│  Database       │
│  ~/.ai-sast/    │
│  scans.db       │
└─────────────────┘
```

## Database Storage

### SQLite (Default)

**Location**: `~/.ai-sast/scans.db`

**Features**:
- ✅ No setup required
- ✅ Works locally and in GitHub Actions
- ✅ Lightweight (~100KB per 50 feedbacks)
- ✅ Zero maintenance

**Limitations**:
- ❌ GitHub Actions runners start fresh (use artifacts to persist)
- ❌ Not shared across repositories

### Databricks (Enterprise)

**For teams wanting centralized feedback across repositories**

Set environment variables:
```bash
export AI_SAST_DATABRICKS_HOST="your-workspace.databricks.com"
export AI_SAST_DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/..."
export AI_SAST_DATABRICKS_TOKEN="your-token"
export AI_SAST_DATABRICKS_CATALOG="your_catalog"
export AI_SAST_DATABRICKS_SCHEMA="ai_sast"
export AI_SAST_DATABRICKS_TABLE="feedback"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_SAST_FEEDBACK_BACKEND` | `auto` | Backend: `sqlite`, `databricks`, or `auto` |
| `AI_SAST_DB_PATH` | `~/.ai-sast/scans.db` | SQLite database path |
| `AI_SAST_STORE_FINDINGS` | `false` | Store original findings (not just feedback) |

### Store Original Findings (Optional)

By default, only **feedback** is stored. To also store **scan findings**:

```bash
export AI_SAST_STORE_FINDINGS=true
```

**When to enable**:
- ✅ Need vulnerability trend analysis
- ✅ Want to calculate false positive rates
- ✅ Compliance requires full audit trail

**Keep disabled when**:
- ✅ Only need feedback for improvement
- ✅ Want minimal database size

See [Optional Findings Storage](Optional-Findings-Storage) for details.

## Impact

### False Positive Rate Over Time

```
100% │ ███
     │ ███
 80% │ ███
     │ ███  ██
 60% │ ███  ██
     │ ███  ██  █
 40% │ ███  ██  █
     │ ███  ██  █  ▓
 20% │ ███  ██  █  ▓  ░
     │ ███  ██  █  ▓  ░
  0% └─────────────────
      W1   W2   W3   W4   W5

After 5 weeks: ~70% reduction in false positives!
```

## Best Practices

### For Developers

1. ✅ **Review carefully** before marking false positives
2. ✅ **Add comments** explaining your reasoning
3. ✅ **Check only one box** per finding
4. ✅ **Update as needed** (e.g., when fixing issues)

### For Security Teams

1. ✅ **Monitor statistics** regularly
2. ✅ **Review false positives** to identify patterns
3. ✅ **Share feedback** across teams (use Databricks)
4. ✅ **Adjust severity filters** based on false positive rates

## Troubleshooting

### Feedback not being collected

**Check**:
1. Workflow exists: `.github/workflows/collect-feedback.yml`
2. Workflow has permissions: `pull-requests: read`, `issues: read`
3. Comment contains marker: `🤖 AI-SAST Security Scan`
4. Checkbox format is correct: `- [x]` (lowercase x)

**Debug**:
```bash
# Check workflow runs
# Go to Actions tab in GitHub

# Check database
python3 -m src.integrations.scan_database --stats
```

### Feedback not appearing in scans

**Check**:
1. Database exists: `ls -la ~/.ai-sast/scans.db`
2. Feedback present: `python3 -m src.integrations.scan_database --stats`
3. Repository URL matches exactly
4. Feedback is recent (only last 90 days included)

**Debug**:
```bash
# View feedback
sqlite3 ~/.ai-sast/scans.db "SELECT * FROM feedback;"

# Check scanner logs
python3 -m src.main.pr_scan  # Look for "Loaded X feedback records"
```

## API Reference

### Store Feedback

```python
from src.integrations.feedback import get_feedback_client

client = get_feedback_client()

client.store_feedback(
    repo_url="https://github.com/org/repo",
    pr_number=123,
    file_path="src/app.py",
    vulnerability_id="abc12345",
    issue="SQL Injection",
    severity="HIGH",
    status="false_positive",  # or "confirmed_vulnerability"
    feedback="Uses parameterized queries",
    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    location="Line 42"
)

client.close()
```

### Retrieve Feedback

```python
# Get false positives
false_positives = client.get_false_positives_for_project(
    repo_url="https://github.com/org/repo",
    days_back=90,
    limit=100
)

# Get confirmed vulnerabilities
confirmed = client.get_confirmed_vulnerabilities_for_project(
    repo_url="https://github.com/org/repo",
    days_back=90,
    limit=100
)

# Format for AI context
context = client.format_feedback_for_context(
    false_positives=false_positives,
    confirmed_vulnerabilities=confirmed
)
```

## Related Pages

- [**Optional Findings Storage**](Optional-Findings-Storage) - Store scan findings for analytics
- [**Configuration**](Configuration) - Environment variables
- [**Databricks Integration**](Databricks-Integration) - Enterprise feedback storage
- [**Troubleshooting**](Troubleshooting) - Common issues

---

[← Back to Home](Home)
