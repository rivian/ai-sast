# AI-SAST - AI-Powered Static Application Security Testing

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions)](https://github.com/features/actions)

AI-SAST is a powerful, AI-driven static application security testing tool that supports **both cloud-based (Google Vertex AI)** and **local open-source (Ollama)** LLM backends. It provides intelligent, context-aware security analysis with detailed reports.

## ✨ Features

- 🤖 **Flexible LLM Backends**: 
  - **Vertex AI** (Google Cloud Gemini models) - Production-grade, cloud-based
  - **Ollama** (Local open-source models) - Privacy-first, runs on your machine
- 💬 **Detailed Reports**: Generates comprehensive HTML and text reports
- 🔄 **GitHub Actions Integration**: Automated scanning in GitHub CI/CD workflows
- ⚙️ **Configurable**: Easy to configure through environment variables
- 🌐 **Multi-Language Support**: Supports Python, JavaScript/TypeScript, Java, C/C++, PHP, Ruby, Go, Rust, C#, SQL, Shell, and more (see `ai-sast-extensions.txt`)
- 🎯 **Smart Filtering**: Configurable exclusion patterns to focus on relevant code
- 📊 **CVSS Scoring**: Provides CVSS v3.1 vector strings for vulnerabilities
- 💾 **Feedback Loop**: Built-in SQLite for storing scan results and feedback (no external services required)
- 🔒 **Privacy Options**: Keep your code on-premise with Ollama backend
- 🎯 **Context-Aware**: Jira integration provides LLM with historical vulnerability patterns for improved accuracy
- 🔌 **Enterprise Ready**: Optional Databricks/Vector storage for organization-wide learning and analytics

## 🏛️ Architecture

AI-SAST provides intelligent, AI-powered security scanning with an optional feedback loop for continuous improvement:

![AI-SAST Architecture](docs/images/architecture.png)

> 📝 **Note**: Please save the architecture diagram image as `docs/images/architecture.png` in the repository.

### How It Works

1. **Scan Trigger**: Pull requests or manual triggers start a scan
2. **AI Analysis**: Code is analyzed by Vertex AI (Gemini) or Ollama for vulnerabilities
3. **Results**: Get HTML reports and PR comments with findings
4. **Feedback Loop** (Optional): Developers mark findings as true/false positives for continuous improvement

📖 **For detailed architecture**, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🚀 Quick Start

### Vertex AI (Cloud) - Recommended for CI/CD

**Prerequisites:**
- Python 3.8+
- Google Cloud account with Vertex AI API enabled

**Setup:**
```bash
# Install dependencies
pip install -r requirements.txt

# Configure (only 2 required variables!)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_TOKEN="your-service-account-json"

# Run a scan
python -m src.main.pr_scan
```

**For GitHub Actions:** Add these as repository secrets:
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID  
- `GOOGLE_TOKEN`: Service account JSON

That's it! Workflows in `.github/workflows/` will run automatically.

---

### Ollama (Local) - For Development

**Quick Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5-coder:14b

# Configure
export LLM_BACKEND="ollama"

# Run
python examples/ollama_scan.py
```

**Benefits:** Free, private, offline, no rate limits

📚 **Detailed Ollama guide:** [docs/OLLAMA.md](docs/OLLAMA.md)

---

## 📖 Usage

### Local Scanning

```bash
# Scan a file
python -m src.core.scanner --file /path/to/file.py

# Scan a directory
python -m src.core.scanner --directory /path/to/your/code

# Scan a Git repository
python -m src.core.scanner --repo https://github.com/user/repo.git --branch main
```

### GitHub Actions (CI/CD)

**Setup:**

1. Add repository secrets (Settings → Secrets → Actions):
   - `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
   - `GOOGLE_TOKEN`: Service account JSON

2. Workflows run automatically:
   - **PR Scan**: Scans changed files on pull requests
   - **Full Scan**: Manual trigger for complete repository scan
   - **Gitleaks**: Secret detection on every push

**That's it!** Results appear as PR comments and artifacts.

### Optional: Feedback Loop & Webhooks

Developers can mark findings as true/false positives to improve accuracy over time.

📚 **Setup guide:** [docs/WEBHOOKS.md](docs/WEBHOOKS.md)

---

## 💡 Highly Recommended

### Jira Integration (Improves Accuracy)

Integrating with Jira provides context to the LLM about known vulnerability patterns, significantly improving finding accuracy:

```bash
export JIRA_SERVER="https://your-company.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your-jira-api-token"
export JIRA_PROJECT_KEY="SEC"  # Your security project key
```

**Why it helps:**
- LLM learns from historical security tickets
- Reduces false positives by understanding your codebase patterns
- Prioritizes findings based on real vulnerabilities found in the past

### Feedback Storage (Continuous Improvement)

Choose a storage backend to capture developer feedback and improve over time:

**SQLite (Default - Included)**
- ✅ Zero configuration
- ✅ Stored locally at `~/.ai-sast/scans.db`
- ✅ Perfect for single teams/repositories

**Vector/Databricks (Enterprise)**
- ✅ Centralized storage across all teams
- ✅ Organization-wide learning
- ✅ Advanced analytics and trends
- ✅ Scales to 1000+ repositories

```bash
# Databricks example
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="your-access-token"
```

**Why it matters:**
- Developers mark findings as true/false positives
- System learns from feedback to reduce false positives
- Accuracy improves continuously with each scan

📚 **Full setup guide:** [docs/WEBHOOKS.md](docs/WEBHOOKS.md)

### Customization (Fine-tune Scanning)

**Filter PR comment severities:**
```bash
# Default: Show only Critical and High in PR comments
export AI_SAST_SEVERITY="critical,high"

# Show all severities (more verbose)
export AI_SAST_SEVERITY="critical,high,medium,low"

# Show only Critical (very strict)
export AI_SAST_SEVERITY="critical"
```

**Note:** Full HTML reports always include all severities. This only affects PR comments.

**For GitHub Actions:** Set as repository variable at Settings → Actions → Variables:
- Name: `AI_SAST_SEVERITY`
- Value: `critical,high,medium` (or your preference)

**Exclude paths from scanning:**
```bash
export AI_SAST_EXCLUDE_PATHS="dist,build,vendor,docs"
```

**Custom AI instructions:**
```bash
export AI_SAST_CUSTOM_PROMPT="Focus on authentication and SQL injection vulnerabilities"
```

**Supported languages:** Python, JavaScript/TypeScript, Java, C/C++, PHP, Ruby, Go, Rust, C#, SQL, Shell, GraphQL
*(Edit `ai-sast-extensions.txt` to customize)*

---

## ⚙️ Configuration

### Required Environment Variables (Vertex AI)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_TOKEN` | Service account JSON (for GitHub Actions) |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_LOCATION` | GCP region | `us-central1` |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash-exp` |
| `LLM_BACKEND` | `vertex` or `ollama` | `vertex` |
| `OLLAMA_MODEL` | Ollama model (if using Ollama) | `qwen2.5-coder:14b` |

**For customization options (severity, exclusions, prompts)**, see "💡 Highly Recommended" section above.

**For webhook/enterprise features**, see [docs/WEBHOOKS.md](docs/WEBHOOKS.md)

**For feedback loop setup**, see [docs/FEEDBACK-LOOP.md](docs/FEEDBACK-LOOP.md)

---

## 🔄 Feedback Loop (Continuous Improvement)

AI-SAST includes a built-in feedback loop that learns from developer input to improve scan accuracy over time:

### How It Works

1. **Scan Results**: AI-SAST posts findings as PR comments with checkboxes
2. **Developer Feedback**: Check boxes to mark findings as ✅ True Positive or ❌ False Positive
3. **Learning**: Feedback is stored in SQLite (or Databricks)
4. **Improvement**: Future scans include historical feedback in AI prompts to avoid false positives

### Quick Setup

The feedback workflow is already configured! When developers check boxes in PR comments, the system:

1. Automatically collects feedback via GitHub Actions
2. Stores it in `~/.ai-sast/scans.db` (SQLite)
3. Includes it in future scan prompts

**Example PR Comment:**
```markdown
<!-- vuln-id: abc12345 -->

- [ ] ✅ True Positive
- [ ] ❌ False Positive

**ID**: `abc12345`
**Severity**: High
**Issue**: SQL Injection
**Location**: user_query.py:42
```

**After checking a box**, the feedback is stored and future scans will:
- ✅ Avoid similar false positives
- ✅ Be more vigilant about confirmed patterns

📖 **Complete guide**: [docs/FEEDBACK-LOOP.md](docs/FEEDBACK-LOOP.md)

---

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
│   ├── ARCHITECTURE.md        # System architecture
│   ├── OLLAMA.md              # Ollama setup guide
│   ├── WEBHOOKS.md            # Webhook integration
│   ├── FEEDBACK-LOOP.md       # Feedback loop guide
│   └── images/
│       └── architecture.png   # Architecture diagram
├── examples/                  # Example usage scripts
├── tests/                     # Unit tests
├── .gitleaks.toml            # Gitleaks configuration
├── requirements.txt           # Python dependencies
├── setup.py                   # Setup script
├── LICENSE                    # Apache License 2.0
├── CONTRIBUTING.md            # Contribution guidelines
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
- Ensure `GOOGLE_CLOUD_PROJECT` is correct

### Model Not Available (404 Error)
- AI-SAST uses `gemini-2.0-flash-exp` model by default
- You can change it with: `export GEMINI_MODEL="gemini-1.5-pro"`
- Ensure your project has access to the model
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

- [ ] Parallel file scanning for faster scans

---

Made with ❤️ by the AI-SAST community

