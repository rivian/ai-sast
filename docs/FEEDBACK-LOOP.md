# AI-SAST Feedback Loop

This document explains how the AI-SAST feedback system works to continuously improve scan accuracy based on developer feedback.

## Overview

The feedback loop allows developers to mark findings as **true positives** (✅) or **false positives** (❌) directly in GitHub PR comments. This feedback is then:

1. **Stored** in a database (SQLite by default, or Databricks)
2. **Retrieved** during future scans
3. **Included** in the AI prompt context to improve accuracy over time

## Architecture

```
┌─────────────────┐
│  PR Scan        │
│  (scan code)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Post Comment   │◄─────┤  Retrieve        │
│  with Checkboxes│      │  Historical      │
└────────┬────────┘      │  Feedback        │
         │               └──────────────────┘
         │                        ▲
         ▼                        │
┌─────────────────┐              │
│  Developer      │              │
│  Checks Boxes   │              │
└────────┬────────┘              │
         │                        │
         ▼                        │
┌─────────────────┐              │
│  Collect        │──────────────┘
│  Feedback       │
│  (GitHub Action)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Store in       │
│  Database       │
└─────────────────┘
```

## How It Works

### Step 1: Scan and Comment Generation

When a PR is created or updated:

1. **PR Scan Action** runs (`pr_scan.py`)
2. Scans only changed code in the PR
3. Generates a markdown report with:
   - Unique ID for each finding (8-char hash)
   - Interactive checkboxes for feedback
   - Complete vulnerability details
4. Posts the report as a PR comment

**Example Comment:**

```markdown
### 🤖 AI-SAST Security Scan
**2** potential issue(s) found.

> 💡 **Help us improve!** Use the checkboxes below to mark each finding...

---

<!-- vuln-id: abc12345 -->

- [ ] ✅ True Positive
- [ ] ❌ False Positive

**ID**: `abc12345`
**Severity**: High
**Issue**: SQL Injection
**Location**: [`user_query.py:42`](link-to-code)
**CVSS Vector**: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`

<details><summary>📋 Click to see details</summary>

**Risk:**
User input is directly concatenated into SQL query...

**Remediation:**
```
Use parameterized queries instead...
```
</details>

**💬 Optional Comment**: (Reply to this PR to explain your feedback)
```

### Step 2: Developer Provides Feedback

Developers review the findings and:

1. Check **one** box per finding (True Positive OR False Positive)
2. Optionally add comments explaining their decision
3. The comment edit triggers the feedback collection workflow

### Step 3: Feedback Collection

When a PR comment is edited:

1. **GitHub Actions** detects the comment edit
2. **collect-feedback.yml** workflow triggers
3. **collect_feedback.py** script:
   - Parses the edited comment
   - Extracts checked boxes and vulnerability details
   - Stores feedback in database with:
     - Repository URL
     - PR number
     - File path
     - Vulnerability ID
     - Issue type
     - Severity
     - Status (confirmed_vulnerability or false_positive)
     - CVSS vector
     - Location
     - Optional developer comments

### Step 4: Feedback Storage

Feedback is stored in one of two backends:

#### SQLite (Default)
- **Location**: `~/.ai-sast/scans.db`
- **Configuration**: None required (automatic)
- **Use Case**: Local development, single developer
- **Tables**:
  - `feedback`: Developer feedback on findings
  - `scan_results`: Historical scan results

#### Databricks (Optional)
- **Location**: Databricks SQL warehouse
- **Configuration**: Set environment variables:
  ```bash
  AI_SAST_DATABRICKS_HOST=...
  AI_SAST_DATABRICKS_HTTP_PATH=...
  AI_SAST_DATABRICKS_TOKEN=...
  AI_SAST_DATABRICKS_CATALOG=...
  AI_SAST_DATABRICKS_SCHEMA=...
  AI_SAST_DATABRICKS_TABLE=...
  ```
- **Use Case**: Enterprise, team-wide feedback sharing

### Step 5: Feedback Retrieval and Context

During future scans, the system:

1. **Queries** the database for historical feedback from the same repository
2. **Retrieves**:
   - False positives (last 90 days, max 100)
   - Confirmed vulnerabilities (last 90 days, max 100)
3. **Formats** the feedback into context text
4. **Includes** in the AI prompt

**Example Context Added to Prompt:**

```markdown
## Historical False Positives
Avoid reporting similar issues:

1. **Issue**: SQL Injection
   - **File**: user_query.py
   - **Severity**: HIGH
   - **Reason**: Uses parameterized queries - safe pattern

2. **Issue**: Missing Authentication
   - **File**: internal_api.py
   - **Severity**: HIGH
   - **Reason**: Internal API, behind VPN

## Previously Confirmed Vulnerabilities
Be vigilant about similar patterns:

1. **Issue**: Weak Password Hashing
   - **File**: auth.py
   - **Severity**: CRITICAL
```

This context helps the AI:
- ✅ Avoid reporting similar false positives
- ✅ Be more vigilant about confirmed vulnerability patterns
- ✅ Learn project-specific security patterns

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_SAST_FEEDBACK_BACKEND` | No | `auto` | Backend selection: `sqlite`, `databricks`, or `auto` |
| `AI_SAST_DB_PATH` | No | `~/.ai-sast/scans.db` | SQLite database path |
| `AI_SAST_STORE_FINDINGS` | No | `false` | Store scan findings in database (set to `true` to enable) |
| `AI_SAST_DATABRICKS_HOST` | For Databricks | - | Databricks workspace hostname |
| `AI_SAST_DATABRICKS_HTTP_PATH` | For Databricks | - | SQL warehouse HTTP path |
| `AI_SAST_DATABRICKS_TOKEN` | For Databricks | - | Personal access token |
| `AI_SAST_DATABRICKS_CATALOG` | For Databricks | - | Unity Catalog name |
| `AI_SAST_DATABRICKS_SCHEMA` | For Databricks | - | Schema name |
| `AI_SAST_DATABRICKS_TABLE` | For Databricks | - | Table name |

### Storing Scan Findings (Optional)

By default, only **feedback** is stored in the database to keep it lightweight. If you want to also store the **original scan findings** (for analytics, tracking, etc.), set:

```bash
export AI_SAST_STORE_FINDINGS=true
```

**When to enable:**
- ✅ You want to track all vulnerabilities found over time
- ✅ You need analytics on vulnerability trends
- ✅ You want to calculate false positive rates
- ✅ You want historical records of all scans

**When to keep disabled (default):**
- ✅ You only care about feedback for improving accuracy
- ✅ You want to minimize database size
- ✅ Findings are already visible in PR comments/reports

### Backend Selection Logic

1. If `AI_SAST_FEEDBACK_BACKEND=databricks` → Use Databricks
2. Else if all Databricks variables are set → Use Databricks
3. Otherwise → Use SQLite (default)

## 📊 Database Schema

### SQLite Tables

The database has two main tables:

#### `feedback` Table (Always Used)
Stores developer feedback on security findings. This is the core of the feedback loop.

```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    repository TEXT NOT NULL,
    pr_number INTEGER,
    file_path TEXT NOT NULL,
    vuln_id TEXT NOT NULL,
    issue TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,           -- 'confirmed_vulnerability' or 'false_positive'
    feedback_text TEXT,             -- Optional developer comment
    cvss_vector TEXT,
    location TEXT,
    user TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(repository, vuln_id, status)
);
```

#### `scan_results` Table (Optional - Only if `AI_SAST_STORE_FINDINGS=true`)
Stores original scan findings for analytics and tracking.

```sql
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    repository TEXT NOT NULL,
    pr_number INTEGER,
    file_path TEXT NOT NULL,
    vuln_id TEXT NOT NULL,
    issue TEXT NOT NULL,
    severity TEXT NOT NULL,
    cvss_vector TEXT,
    location TEXT,
    description TEXT,
    risk TEXT,
    fix TEXT,
    scan_type TEXT,                 -- 'pr' or 'full'
    created_at TEXT NOT NULL,
    UNIQUE(repository, vuln_id, scan_id)
);
```

**Note:** The `scan_results` table is only populated when `AI_SAST_STORE_FINDINGS=true` is set.

## API Reference

### Feedback Client

```python
from src.integrations.feedback import get_feedback_client

# Get appropriate client (SQLite or Databricks)
client = get_feedback_client()

# Store single feedback
client.store_feedback(
    repo_url="https://github.com/org/repo",
    pr_number=123,
    file_path="src/app.py",
    vulnerability_id="abc12345",
    issue="SQL Injection",
    severity="HIGH",
    status="false_positive",
    feedback="Uses parameterized queries",
    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    location="Line 42",
    user="developer@example.com"
)

# Store batch feedback
client.store_batch_feedback(
    repo_url="https://github.com/org/repo",
    pr_number=123,
    feedback_list=[
        {
            'vuln_id': 'abc12345',
            'file_path': 'src/app.py',
            'issue': 'SQL Injection',
            'severity': 'HIGH',
            'status': 'false_positive',
            'feedback': 'Uses parameterized queries',
            'location': 'Line 42'
        }
    ]
)

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

client.close()
```

## Testing the Feedback Loop

### 1. Test SQLite Storage

```bash
# Run the test suite
python tests/test_sqlite_feedback.py

# Test with actual repository
python -m src.integrations.scan_database --stats --repo-url https://github.com/org/repo
```

### 2. Test Feedback Collection

```bash
# Set up test environment
export GITHUB_EVENT_PATH=/path/to/test-event.json
export GITHUB_TOKEN=your-token

# Run feedback collector
python -m src.main.collect_feedback
```

### 3. Verify Feedback in Scan

```bash
# Run a scan and check logs for feedback context
python -m src.main.pr_scan

# Look for output:
# "✅ Loaded 5 historical feedback records for context"
```

## Monitoring and Statistics

### View Feedback Statistics

```bash
# Overall statistics
python -m src.integrations.scan_database --stats

# Repository-specific statistics
python -m src.integrations.scan_database --stats --repo-url https://github.com/org/repo
```

**Example Output:**
```
✅ Database: /Users/username/.ai-sast/scans.db

📊 Statistics:
  Scan results: 156
  Total feedback: 43
  False positives: 28
  Confirmed vulnerabilities: 15
```

## Troubleshooting

### Feedback not being collected

1. **Check workflow is enabled**: `.github/workflows/collect-feedback.yml`
2. **Verify permissions**: Workflow needs `pull-requests: read` and `issues: read`
3. **Check comment format**: Must contain `🤖 AI-SAST Security Scan` marker
4. **Verify checkbox format**: Must be `- [x]` or `- [ ]` (lowercase x)

### Feedback not appearing in scans

1. **Check database location**: Default is `~/.ai-sast/scans.db`
2. **Verify repository URL match**: Must match exactly
3. **Check feedback age**: Only last 90 days included by default
4. **Enable debug logging**: Set `LOGLEVEL=DEBUG`

### Database issues

```bash
# Check SQLite database
sqlite3 ~/.ai-sast/scans.db ".tables"
sqlite3 ~/.ai-sast/scans.db "SELECT COUNT(*) FROM feedback;"

# Reset database (caution: deletes all data)
rm ~/.ai-sast/scans.db
```

## Best Practices

### For Developers

1. ✅ **Review findings carefully** before marking as false positive
2. ✅ **Add comments** explaining your reasoning (helps future reviews)
3. ✅ **Check only one box** per finding (true positive OR false positive)
4. ✅ **Update checkboxes** as findings are fixed

### For Security Teams

1. ✅ **Monitor feedback statistics** regularly
2. ✅ **Review false positives** to identify AI tuning opportunities
3. ✅ **Share confirmed vulnerabilities** across teams (use Databricks)
4. ✅ **Adjust severity filters** based on false positive rates

### For Organizations

1. ✅ **Use Databricks** for centralized feedback across multiple repos
2. ✅ **Set up notifications** for critical confirmed vulnerabilities
3. ✅ **Export feedback** periodically for analysis
4. ✅ **Train developers** on using the feedback system

## See Also

- [Architecture Documentation](ARCHITECTURE.md)
- [Contributing Guide](../CONTRIBUTING.md)
