# AI-SAST - AI-Powered Static Application Security Testing

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions)](https://github.com/features/actions)

AI-SAST is a powerful, AI-driven static application security testing tool that uses Google Cloud Vertex AI (Gemini models) to scan source code for security vulnerabilities. It provides intelligent, context-aware security analysis with detailed reports.

## ✨ Features

- 🤖 **AI-Powered Scanning**: Uses Google Cloud Vertex AI's Gemini models to analyze code for vulnerabilities
- 💬 **Detailed Reports**: Generates comprehensive HTML and text reports
- 🔄 **GitHub Actions Integration**: Automated scanning in GitHub CI/CD workflows
- ⚙️ **Configurable**: Easy to configure through environment variables
- 🌐 **Multi-Language Support**: Supports Python, JavaScript/TypeScript, Java, C/C++, PHP, Ruby, Go, Rust, C#, SQL, Shell, and more
- 🎯 **Smart Filtering**: Configurable exclusion patterns to focus on relevant code
- 📊 **CVSS Scoring**: Provides CVSS v3.1 vector strings for vulnerabilities
- 💾 **Local Database**: Built-in SQLite for storing scan results and feedback (no external services required)
- 🔌 **Optional Integrations**: Jira, Databricks, and Vector/Log aggregation support for enterprise deployments (see [INTEGRATIONS.md](INTEGRATIONS.md))

## 🏛️ Architecture

AI-SAST provides intelligent, AI-powered security scanning with an optional feedback loop for continuous improvement:

![AI-SAST Architecture](docs/images/architecture.png)

> 📝 **Note**: Please save the architecture diagram image as `docs/images/architecture.png` in the repository.

### How It Works

1. **GitHub Integration**: Pull requests trigger automated scans via GitHub Actions
2. **AI-Powered Analysis**: Code is analyzed by Google Vertex AI (Gemini) for security vulnerabilities
3. **Context-Aware Scanning**: 
   - **Local Database**: Scan results and feedback stored in SQLite for continuous learning
   - Jira integration for known vulnerability patterns (optional)
   - Databricks for enterprise multi-team deployments (optional)
4. **Smart Scanning Modes**:
   - **PR Diff Scanning**: Fast, targeted scanning of only changed files
   - **Full Repository Scanning**: Comprehensive scan of entire codebase on main branch
5. **Results & Reporting**:
   - HTML reports with detailed findings and CVSS scoring
   - PR comments with critical/high severity issues and interactive feedback checkboxes
   - Webhook notifications (Slack, Teams, Discord, generic)
   - Metrics and trends for security posture tracking
6. **Feedback Loop**:
   - Interactive checkboxes in PR comments
   - Automatic storage in local SQLite database
   - Databricks option for enterprise deployments
   - Reduces false positives over time

📖 **For detailed architecture documentation**, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Vertex AI API enabled
- Google Cloud CLI (optional, for easier authentication)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ai-sast.git
cd ai-sast
```

2. Run the setup script:
```bash
python setup.py
```

This will:
- Check your Python version
- Install required packages from `requirements.txt`
- Verify Google Cloud CLI installation (optional)
- Help you create an `env_config.txt` file

### Configuration

Set your Google Cloud project ID and location:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export VERTEX_AI_LOCATION="us-central1"
```

Or source the `env_config.txt` file:

```bash
source env_config.txt
```

📚 **See below for complete environment variable reference with examples**

### Authentication

#### Option 1: gcloud CLI (Recommended for Development)
```bash
gcloud auth application-default login
```

#### Option 2: Service Account Key
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

#### Option 3: GitHub Actions
For GitHub Actions, use the `google-github-actions/auth` action with a service account key stored in GitHub Secrets.

## 📖 Usage

### Local Scanning

#### Scan a single file
```bash
python -m src.core.scanner --file /path/to/file.py
```

#### Scan a directory
```bash
python -m src.core.scanner --directory /path/to/your/code
```

#### Scan a Git repository
```bash
python -m src.core.scanner --repo https://github.com/user/repo.git --branch main
```

#### Generate an output report
```bash
python -m src.core.scanner --directory /path/to/code --output security_report.txt
```

### GitHub Actions Integration

The project includes a GitHub Actions workflow for automated scanning. To use it:

1. **Set up GitHub Secrets**:
   - `GOOGLE_CREDENTIALS`: Your Google Cloud service account key (JSON)
   - `GOOGLE_PROJECT_ID`: Your Google Cloud Project ID
   - `GOOGLE_LOCATION` (optional): Vertex AI location (default: us-central1)

2. **Add the workflow** (already included in `.github/workflows/security-scan.yml`):
   - **On Pull Requests**: Scans only changed files (fast, targeted)
   - **On Push to Main**: Scans entire repository (comprehensive)
   - **Manual Trigger**: Can be triggered manually via workflow_dispatch
   - Posts scan results as PR comments (for Critical/High findings)
   - Uploads detailed reports as artifacts

3. **Workflow Features**:
   - Smart scanning: PR diffs vs full repository
   - Automatic report generation (HTML + Markdown)
   - PR comment integration with formatted results
   - Artifact uploads with 30-day retention
   - Configurable via secrets and environment variables

4. **Required Permissions**:
   - Ensure your service account has the "Vertex AI User" role
   - Enable Vertex AI API in your Google Cloud project
   - Workflow needs `pull-requests: write` for PR comments

### Setting Up Developer Feedback Collection (Optional)

By default, feedback is automatically stored in SQLite at `~/.ai-sast/scans.db`. 

For enterprise deployments with webhook integration:

1. **Deploy webhook listener** (optional):
   ```bash
   cd webhook/iac
   terraform init
   terraform apply
   ```

2. **Configure GitHub webhook**:
   - Payload URL: `https://your-webhook-url.com/webhook`
   - Content type: `application/json`
   - Events: Issue comments
   
3. **(Optional) Use Databricks** for centralized storage (see [INTEGRATIONS.md](INTEGRATIONS.md))

📚 **For detailed webhook setup instructions**, see [webhook/README.md](webhook/README.md)

## ⚙️ Configuration Options

### Environment Variables (Quick Reference)

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud Project ID | (required) |
| `GOOGLE_PROJECT_ID` | Alternative to GOOGLE_CLOUD_PROJECT | (required) |
| `VERTEX_AI_LOCATION` | Vertex AI location/region | `us-central1` |
| `GOOGLE_LOCATION` | Alternative to VERTEX_AI_LOCATION | `us-central1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | (optional) |
| `GOOGLE_TOKEN` | Google Cloud token (JSON or base64) | (optional) |
| `AI_SAST_EXCLUDE_PATHS` | Comma-separated paths to exclude | (see below) |
| `AI_SAST_CUSTOM_PROMPT` | Custom instructions to append to AI prompt | (optional) |
| `AI_SAST_SEVERITY` | Comma-separated severities for PR comments | `critical,high` |
| `AI_SAST_DB_PATH` | Path to SQLite database | `~/.ai-sast/scans.db` |

📚 **For optional integrations**, see **[INTEGRATIONS.md](INTEGRATIONS.md)**

### Default Exclusions

By default, AI-SAST excludes the following paths:
- `test` - Test files and directories
- `node_modules` - Node.js dependencies
- `e2e` - End-to-end test directories
- `cypress` - Cypress test files
- `jest` - Jest test files
- `mock` - Mock files
- `log` - Log files
- `.git` - Git directories

To add custom exclusions:
```bash
export AI_SAST_EXCLUDE_PATHS="dist,build,vendor,docs"
```

### Custom AI Instructions

You can provide custom instructions to the AI model using the `AI_SAST_CUSTOM_PROMPT` environment variable:

```bash
export AI_SAST_CUSTOM_PROMPT="Focus on SQL injection and XSS vulnerabilities. Ignore file upload issues."
```

The default scanning prompt is stored in `prompts/default_prompt.txt` for easy review and customization. Your custom instructions via `AI_SAST_CUSTOM_PROMPT` will be appended to this base prompt.

**Examples:**
```bash
# Focus on specific vulnerabilities
export AI_SAST_CUSTOM_PROMPT="Prioritize authentication and authorization issues"

# Adjust sensitivity
export AI_SAST_CUSTOM_PROMPT="Only report issues with direct exploit paths"

# Domain-specific guidance  
export AI_SAST_CUSTOM_PROMPT="Pay special attention to payment processing and PII handling"
```

### Complete Environment Variable Reference

#### Core Configuration

```bash
# GOOGLE_CLOUD_PROJECT or GOOGLE_PROJECT_ID (Required)
export GOOGLE_CLOUD_PROJECT="my-company-production"
# Or: export GOOGLE_PROJECT_ID="security-scanning-project"

# VERTEX_AI_LOCATION (Optional, default: us-central1)
export VERTEX_AI_LOCATION="us-central1"
# Other options: "us-east1", "europe-west1", "asia-southeast1"

# GOOGLE_APPLICATION_CREDENTIALS (Optional)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# GOOGLE_TOKEN (Optional)
export GOOGLE_TOKEN='{"type":"service_account","project_id":"my-project",...}'
```

#### Scanning Configuration

```bash
# AI_SAST_CUSTOM_PROMPT (Optional)
export AI_SAST_CUSTOM_PROMPT="Focus on SQL injection and XSS vulnerabilities"

# AI_SAST_EXCLUDE_PATHS (Optional)
export AI_SAST_EXCLUDE_PATHS="dist,build,vendor,docs,*.min.js"

# AI_SAST_SEVERITY (Optional, default: critical,high)
export AI_SAST_SEVERITY="critical,high"
# Options: "critical", "high", "medium", "low" (any combination)
```

#### Environment File Template

Create a `.env` file:

```bash
# .env - AI-SAST Configuration
# DO NOT COMMIT THIS FILE

# === Core Configuration (Required) ===
GOOGLE_CLOUD_PROJECT=
VERTEX_AI_LOCATION=us-central1

# === Scanning Configuration (Optional) ===
AI_SAST_EXCLUDE_PATHS=
AI_SAST_CUSTOM_PROMPT=
AI_SAST_SEVERITY=critical,high
```

Then load it:
```bash
source .env
```

## 📊 Report Format

AI-SAST generates reports with the following information for each vulnerability:

- **Vulnerability Level**: CRITICAL / HIGH / MEDIUM / LOW / INFO
- **Issue**: Brief description of the vulnerability
- **Location**: File name and line number
- **CVSS Vector**: Full CVSS v3.1 vector string
- **Risk**: Explanation of the security impact
- **Fix**: Specific remediation steps with secure code examples

### Example Output

```
# Security Vulnerability Analysis Report
==================================================

## Summary
- Total files scanned: 25
- Successful scans: 25
- Failed scans: 0

## File: src/api/users.py
**Language**: python
**Status**: success

### Analysis:
- **Vulnerability Level**: HIGH
- **Issue**: SQL Injection vulnerability in user query
- **Location**: Line 42
- **CVSS Vector**: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N
- **Risk**: Attacker could manipulate SQL queries to access or modify unauthorized data
- **Fix**: Use parameterized queries instead of string concatenation...
```

## 🏗️ Project Structure

```
ai-sast/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── scanner.py         # Main security scanner
│   │   ├── vertex.py          # Vertex AI client
│   │   └── report.py          # Report generation
│   ├── integrations/          # Optional integrations
│   │   ├── __init__.py
│   │   ├── jira.py            # Jira integration
│   │   ├── databricks.py      # Databricks integration
│   │   ├── vector.py          # Vector/log aggregation
│   │   └── notifications.py   # Slack/Teams/Discord notifications
│   └── main/
│       ├── __init__.py
│       ├── full_scan.py       # Full repository scan (CI/CD)
│       └── pr_scan.py         # Pull request diff scan (CI/CD)
├── webhook/                   # Webhook listener for feedback
│   ├── main.py               # Flask webhook application
│   ├── Dockerfile            # Container image
│   ├── requirements.txt      # Python dependencies
│   ├── README.md            # Webhook setup guide
│   └── iac/                 # Terraform infrastructure
│       ├── main.tf
│       ├── variables.tf
│       └── modules/         # Terraform modules
├── .github/
│   └── workflows/
│       └── security-scan.yml  # GitHub Actions workflow with Gitleaks
├── prompts/
│   └── default_prompt.txt     # Default AI scanning prompt
├── docs/
│   ├── ARCHITECTURE.md        # Architecture documentation
│   └── images/
│       └── architecture.png   # Architecture diagram
├── examples/                  # Example usage scripts
├── tests/                     # Unit tests
├── .gitleaks.toml            # Gitleaks configuration
├── requirements.txt           # Python dependencies
├── setup.py                   # Setup script
├── LICENSE                    # Apache License 2.0
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guidelines
├── INTEGRATIONS.md            # Optional integrations guide
└── README.md                  # This file
```

## 🔒 Security Best Practices

This project follows OWASP security guidelines:
- ✅ No hardcoded secrets (use environment variables)
- ✅ Input validation and sanitization
- ✅ Secure credential handling
- ✅ Minimal logging of sensitive data

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Authentication Errors
- Verify you're authenticated with `gcloud` or have set credentials
- Check service account has "Vertex AI User" role
- Ensure `GOOGLE_PROJECT_ID` is correct

### Model Not Available (404 Error)
- AI-SAST uses `gemini-2.0-flash-exp` model by default
- Ensure your project has access to this model
- Contact Google Cloud support if needed

### API Not Enabled
- Enable Vertex AI API: `aiplatform.googleapis.com`
- Enable in Google Cloud Console under APIs & Services:
  ```bash
  gcloud services enable aiplatform.googleapis.com
  ```

### Rate Limiting
- The scanner implements automatic retry with exponential backoff
- If you hit rate limits frequently, consider:
  - Reducing parallel workers with `--max-workers` flag
  - Excluding more test files
  - Spreading scans across multiple time periods

## 🙏 Acknowledgments

- Google Cloud Vertex AI for providing powerful AI models
- OWASP for security testing guidelines
- The open-source community for continuous inspiration

## 📧 Support

- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/ai-sast/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/YOUR_USERNAME/ai-sast/discussions)
- 📖 Documentation: [Wiki](https://github.com/YOUR_USERNAME/ai-sast/wiki)

## 🗺️ Roadmap

- [ ] Support for additional AI models (Claude, GPT-4, etc.)
- [ ] Integration with SARIF format for GitHub Code Scanning
- [ ] Support for GitLab CI/CD
- [ ] Web dashboard for report visualization
- [ ] Custom rule definitions
- [ ] Integration with issue trackers (GitHub Issues, Jira)
- [ ] Incremental scanning (only changed files)
- [ ] False positive feedback loop

---

Made with ❤️ by the AI-SAST community

