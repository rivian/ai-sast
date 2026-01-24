# AI-SAST Architecture

This document provides a detailed explanation of AI-SAST's architecture, components, and data flow.

## Architecture Diagram

![AI-SAST Architecture](images/architecture-dark.png)

> 📝 **Note**: Please save the architecture diagram as `docs/images/architecture-dark.png` in the repository.

## Overview

AI-SAST is an AI-powered static application security testing tool that integrates with GitHub to provide intelligent, context-aware vulnerability scanning. The system uses Google Cloud Vertex AI (Gemini models) to analyze source code and can optionally leverage historical vulnerability data to improve accuracy over time.

## Core Components

### 1. GitHub Integration
- **Trigger**: Pull requests and commits to main branch
- **Actions**: GitHub Actions workflow executes the scanner
- **Feedback**: PR comments with critical/high severity findings
- **Authentication**: Uses GitHub tokens for API access

### 2. AI-SAST Scanner
- **Core Engine**: Python-based security scanner
- **Entry Points**:
  - `pr_scan.py` - Scans only changed files in pull requests
  - `full_scan.py` - Scans entire repository on main branch
- **Analysis**: Parses code, applies exclusion rules, sends to Vertex AI
- **Output**: Structured vulnerability reports with CVSS scoring

### 3. Vertex AI (Gemini)
- **Model**: Gemini 2.0 Flash (configurable)
- **Input**: Source code with custom security analysis prompt
- **Processing**: 
  - Data flow analysis
  - Source/sink identification
  - Cross-file vulnerability tracing
  - Exploitability assessment
- **Output**: Structured vulnerability findings with severity, CVSS, and remediation guidance

### 4. Scan Modes

#### PR Diff Scanning
- **Trigger**: Pull request opened/updated
- **Scope**: Only files changed in the PR
- **Speed**: Fast (typically < 1 minute)
- **Output**: 
  - PR comment with critical/high findings
  - Markdown summary report
  - Full HTML report uploaded as artifact
- **Use Case**: Quick feedback during development

#### Full Repository Scanning
- **Trigger**: Push to main branch or manual workflow dispatch
- **Scope**: Entire repository (respects exclusion patterns)
- **Speed**: Slower (depends on repository size)
- **Output**: 
  - Comprehensive HTML report
  - Metrics for security dashboard
  - Historical baseline for trend analysis
- **Use Case**: Comprehensive security assessment, compliance, baseline

### 5. Historical Vulnerability Inventory (Optional)

**Component**: Databricks Integration

**Purpose**: Store and retrieve historical vulnerability data to provide context to the AI model

**Data Flow**:
1. Past scan results are stored in Databricks (false positives, confirmed vulnerabilities)
2. During scanning, relevant historical data is retrieved
3. Context is provided to Vertex AI to improve accuracy
4. Reduces false positives by learning from past feedback

**Configuration**:
```bash
AI_SAST_DATABRICKS_HOST=mycompany.cloud.databricks.com
AI_SAST_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
AI_SAST_DATABRICKS_TOKEN=dapi...
AI_SAST_DATABRICKS_CATALOG=security
AI_SAST_DATABRICKS_SCHEMA=sast
AI_SAST_DATABRICKS_TABLE=feedback
```

**Table Schema**:
- `file_path`: Path to the file
- `vulnerability_type`: Type of vulnerability
- `status`: confirmed_vulnerability | false_positive
- `feedback`: Developer comments
- `timestamp`: When the feedback was recorded

### 6. Jira Context (Optional)

**Component**: Jira Integration

**Purpose**: Provide additional context from existing security tickets

**Data Flow**:
1. Query Jira using JQL for relevant vulnerability tickets
2. Extract vulnerability patterns and descriptions
3. Provide context to Vertex AI for better detection
4. Helps identify organization-specific vulnerability patterns

**Configuration**:
```bash
JIRA_URL=https://mycompany.atlassian.net
JIRA_USERNAME=security-scanner@company.com
JIRA_API_TOKEN=ATATT3xFfGF0...
JIRA_JQL_QUERY="project = SEC AND status != Closed"
```

### 7. Results Processing

#### Metrics
- Total files scanned
- Vulnerabilities by severity (Critical, High, Medium, Low)
- Scan duration and performance metrics
- Trend analysis (when integrated with historical data)

#### Reports
- **HTML Report**: Rich, interactive report with:
  - Executive summary
  - Detailed findings with code snippets
  - CVSS scores and remediation guidance
  - Filterable by severity
  
- **Markdown Summary**: Concise summary for PR comments:
  - Critical and high severity issues only (configurable)
  - File locations and line numbers
  - Brief descriptions and CVSS scores
  - Links to full report

#### PR Comments
- Automated comments on pull requests
- Only critical/high severity findings (configurable via `AI_SAST_SEVERITY`)
- Formatted for readability
- Links to full HTML report in artifacts

### 8. Developer Feedback Loop

**Status**: ✅ **Implemented**

**Purpose**: Continuous improvement through developer feedback

**Process**:
1. Developer reviews findings in PR comment
2. Uses interactive checkboxes to mark issues as true/false positives:
   ```markdown
   - [ ] ✅ True Positive  [ ] ❌ False Positive
   ```
3. GitHub Actions workflow automatically captures the feedback
4. Feedback is stored in Databricks with metadata
5. Future scans leverage this feedback for improved accuracy

**Features**:
- ✅ **Interactive UI**: Checkbox-based feedback in PR comments
- ✅ **Automatic collection**: GitHub Actions workflow (`collect-feedback.yml`)
- ✅ **Databricks write-back**: Stores feedback automatically
- ✅ **Optional comments**: Developers can add explanations

**Implementation**:
- `src/main/collect_feedback.py` - Parses and stores feedback from PR comments
- `src/integrations/databricks.py` - `store_feedback()` and `store_batch_feedback()` methods
- `.github/workflows/collect-feedback.yml` - Triggered on PR comment events

**Benefits**:
- Reduces false positive rate over time
- Learns organization-specific patterns
- Improves developer trust and adoption
- Creates institutional security knowledge base

### 9. Vector/Log Aggregator (Optional)

**Component**: Vector Client

**Purpose**: Send security events to centralized logging/SIEM

**Events Logged**:
- Scan initiated/completed
- Vulnerabilities detected
- Critical findings
- System errors

**Configuration**:
```bash
AI_SAST_VECTOR_URL=https://splunk.company.com/services/collector
AI_SAST_VECTOR_TOKEN=Splunk ABC-123-XYZ
```

### 10. Webhook Notifications

**Status**: ✅ **Implemented**

**Purpose**: Send scan results and alerts to external systems

**Use Cases**:
- Notify Slack/Teams channels of critical findings
- Trigger additional security workflows
- Integration with ticketing systems
- Custom dashboards and monitoring

**Supported Platforms**:
- Slack (rich formatting with blocks and buttons)
- Microsoft Teams (adaptive cards)
- Discord (embeds)
- Generic webhooks (JSON payload)

**Webhook Events**:
```python
# Scan completed
webhook.send_scan_completed(repository, pr_number, scan_summary, report_url, duration)

# Critical vulnerability detected
webhook.send_critical_alert(repository, pr_number, vulnerability_details)

# Scan failed
webhook.send_scan_failed(repository, pr_number, error_message)

# Feedback received
webhook.send_feedback_received(repository, pr_number, feedback_summary)
```

**Configuration**:
```bash
AI_SAST_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
AI_SAST_WEBHOOK_SECRET=your-secret-key  # Optional, for signature verification
AI_SAST_WEBHOOK_TYPE=slack  # slack, teams, discord, or generic
```

**Security**:
- Optional HMAC signature (SHA-256) for webhook verification
- Configurable via `AI_SAST_WEBHOOK_SECRET`
- Signature sent in `X-AI-SAST-Signature` header

**Implementation**:
- `src/integrations/notifications.py` - Notification client for Slack, Teams, Discord, and generic webhooks
- Integrated into `pr_scan.py` and `full_scan.py`
- Platform-specific message formatting

## Current Implementation Status

### ✅ Fully Implemented
- Core AI scanning engine with Vertex AI
- GitHub Actions integration (PR diff & full scans)
- HTML and Markdown report generation
- CVSS scoring and severity classification
- Jira integration (read-only, for context)
- Databricks integration (read + write for feedback)
- Vector/log aggregator client
- Custom AI prompts (external file support)
- Configurable exclusion patterns
- **Notification system** (Slack, Teams, Discord, generic webhooks) - `src/core/notifications.py`
- **GitHub webhook listener** for capturing developer feedback
- **Interactive feedback collection** via PR comment checkboxes
- **Automated feedback storage** to Databricks
- **AWS infrastructure** (Terraform) for webhook deployment
- **Gitleaks integration** for secret detection in CI/CD

### 🚧 Planned for Future Releases
- **SARIF format** - GitHub Advanced Security integration (v1.2.0)
- **Additional AI models** - Claude, GPT-4 support (v1.2.0)
- **GitLab CI/CD** - GitLab integration (v1.2.0)
- **Custom rules engine** - User-defined security rules (v1.3.0)

### 💡 Future Enhancements
- IDE extensions (VS Code, IntelliJ)
- Multi-repository scanning
- Real-time scanning
- Machine learning model fine-tuning

### Pull Request Scan Flow

```
1. Developer opens PR
   ↓
2. GitHub Actions triggers workflow
   ↓
3. pr_scan.py executes
   ↓
4. Git diff identifies changed files
   ↓
5. Exclusion rules filter files
   ↓
6. [Optional] Query Databricks for historical context
   ↓
7. [Optional] Query Jira for vulnerability patterns
   ↓
8. For each file:
   - Load source code
   - Build prompt with context
   - Send to Vertex AI
   - Parse response
   ↓
9. Generate reports
   ↓
10. Post PR comment with checkboxes (critical/high only)
    ↓
11. Upload HTML report as artifact
    ↓
12. [Optional] Log events to Vector
    ↓
13. [Optional] Send webhook notifications
    ↓
14. Developer reviews findings and checks feedback boxes
    ↓
15. GitHub sends webhook event to AI-SAST webhook listener
    ↓
16. Webhook listener processes feedback and stores in Databricks
    ↓
17. Future scans use feedback to improve accuracy
```

### Developer Feedback Loop Flow

```
1. AI-SAST posts PR comment with findings
   - Each finding includes interactive checkboxes:
     [ ] ✅ True Positive
     [ ] ❌ False Positive
   ↓
2. Developer reviews findings and checks appropriate box
   ↓
3. GitHub sends "issue_comment" webhook to webhook listener endpoint
   ↓
4. Webhook listener (Flask app on AWS ECS):
   a. Verifies GitHub signature (HMAC-SHA256)
   b. Parses comment body for checked boxes
   c. Extracts vulnerability details
   d. Generates unique vulnerability ID
   ↓
5. Feedback stored in Databricks:
   - vulnerability_id
   - status (true_positive / false_positive)
   - file_path
   - severity
   - cvss_vector
   - user_info
   - timestamp
   ↓
6. [Optional] SNS notification sent for confirmed vulnerabilities
   ↓
7. Future scans query Databricks for historical feedback
   ↓
8. AI model learns from feedback to reduce false positives
```

### Full Repository Scan Flow

```
1. Push to main branch or manual trigger
   ↓
2. GitHub Actions triggers workflow
   ↓
3. full_scan.py executes
   ↓
4. Traverse repository directories
   ↓
5. Apply exclusion patterns
   ↓
6. [Optional] Retrieve historical context
   ↓
7. Scan all matching files (parallel processing)
   ↓
8. Aggregate results
   ↓
9. Generate comprehensive HTML report
   ↓
10. Store metrics
    ↓
11. Upload report as artifact
    ↓
12. [Optional] Update historical inventory
    ↓
13. [Optional] Send webhook notifications
```

## Security & Privacy

### Data Security
- **No Code Storage**: Source code is not stored permanently
- **Encrypted Transit**: All API calls use HTTPS/TLS
- **Credential Management**: Secrets stored in GitHub Secrets or environment variables
- **Access Control**: Service accounts with minimal required permissions

### Privacy Considerations
- **Google Cloud**: Code is sent to Vertex AI for analysis
  - Subject to Google Cloud's data processing agreement
  - Data residency configurable via region selection
  - Not used for model training (per Google Cloud terms)
- **Optional Integrations**: Only enabled if explicitly configured
- **Audit Trail**: All scans logged (if Vector integration enabled)

## Performance & Scalability

### Performance Characteristics
- **PR Scans**: Typically < 1 minute for small PRs
- **Full Scans**: Depends on repository size
  - 100 files: ~5-10 minutes
  - 1000 files: ~30-60 minutes
- **Parallel Processing**: Configurable worker count
- **Rate Limiting**: Automatic retry with exponential backoff

### Scalability
- **Horizontal**: Multiple workers process files in parallel
- **Vertical**: Configurable via `--max-workers` flag
- **Cost Optimization**:
  - PR scans minimize API calls by scanning only changed files
  - Exclusion patterns reduce unnecessary scans
  - Caching possible (future enhancement)

## Configuration

### Minimal Configuration
```bash
GOOGLE_CLOUD_PROJECT=my-project
VERTEX_AI_LOCATION=us-central1
```

### Full Configuration with All Features
```bash
# Core
GOOGLE_CLOUD_PROJECT=my-project
VERTEX_AI_LOCATION=us-central1

# Scanning
AI_SAST_EXCLUDE_PATHS=dist,build,vendor
AI_SAST_CUSTOM_PROMPT="Focus on authentication and authorization"
AI_SAST_SEVERITY=critical,high

# Jira Context
JIRA_URL=https://mycompany.atlassian.net
JIRA_USERNAME=scanner@company.com
JIRA_API_TOKEN=ATATT3xFfGF0...
JIRA_JQL_QUERY="project = SEC AND status != Closed"

# Historical Data
AI_SAST_DATABRICKS_HOST=company.databricks.com
AI_SAST_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/xyz
AI_SAST_DATABRICKS_TOKEN=dapi...
AI_SAST_DATABRICKS_CATALOG=security
AI_SAST_DATABRICKS_SCHEMA=sast
AI_SAST_DATABRICKS_TABLE=feedback

# Logging
AI_SAST_VECTOR_URL=https://splunk.company.com/services/collector
AI_SAST_VECTOR_TOKEN=Splunk ABC-123-XYZ

# Webhooks
AI_SAST_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
AI_SAST_WEBHOOK_SECRET=your-signing-secret  # Optional
AI_SAST_WEBHOOK_TYPE=slack  # slack, teams, discord, or generic
```

## Extensibility

### Custom Prompts
- Base prompt stored in `prompts/default_prompt.txt`
- Custom instructions via `AI_SAST_CUSTOM_PROMPT` environment variable
- Modify base prompt for organization-specific requirements

### Additional Integrations
The architecture supports adding new integrations:
- **Webhooks**: ✅ Implemented (Slack, Teams, Discord, custom endpoints)
- **Issue Trackers**: GitHub Issues, GitLab, etc.
- **Notification Systems**: PagerDuty, OpsGenie
- **Security Platforms**: Snyk, Checkmarx, etc.
- **Data Warehouses**: Snowflake, BigQuery, etc.

### Future Enhancements
- SARIF format support for GitHub Advanced Security
- Additional AI model support (Claude, GPT-4)
- GitLab CI/CD integration
- Real-time scanning IDE extensions
- Custom rule definitions
- Multi-repository scanning

## Deployment Models

### Cloud (Recommended)
- GitHub Actions for compute
- Google Cloud Vertex AI for AI models
- Optional: Databricks Cloud for historical data
- Optional: Cloud-based SIEM for logging

### Hybrid
- GitHub Actions for orchestration
- On-premises Vertex AI endpoint (if available)
- On-premises Databricks
- Internal SIEM/logging

### Self-Hosted
- Self-hosted GitHub Actions runners
- Google Cloud Vertex AI (requires internet access)
- Local or on-premises integrations

## Troubleshooting

### Common Issues

**High False Positive Rate**
- Enable Databricks integration for feedback loop
- Adjust AI_SAST_CUSTOM_PROMPT to be more specific
- Use AI_SAST_SEVERITY to filter out low-confidence findings

**Slow Scans**
- Increase AI_SAST_EXCLUDE_PATHS to skip unnecessary files
- Reduce --max-workers if hitting rate limits
- Use PR scanning for faster feedback

**Missing Findings**
- Review AI_SAST_CUSTOM_PROMPT - may be too restrictive
- Check exclusion patterns - may be filtering important files
- Verify Vertex AI model has access (quota, permissions)

---

For more information, see:
- [README.md](../README.md) - Main documentation
- [INTEGRATIONS.md](../INTEGRATIONS.md) - Optional integrations setup
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guide

