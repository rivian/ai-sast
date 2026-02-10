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
- `GOOGLE_CREDENTIALS`: Service account JSON (used by the workflow’s Google auth step)

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
   - `GOOGLE_CREDENTIALS`: Service account JSON (required by the workflow’s Google Cloud auth step)

2. Workflows run automatically:
   - **PR Scan**: Scans changed files on pull requests
   - **Full Scan**: Manual trigger for complete repository scan
   - **Gitleaks**: Secret detection on every push

**That's it!** Results appear as PR comments and artifacts.

#### Using AI-SAST in another repository (runs in your repo, on your runners)

**Your code never runs on ai-sast infrastructure.** The workflow runs in your repo on your runners and checks out the ai-sast scanner at runtime—no submodule or copy required.

1. **Copy the workflow file** into your repo as `.github/workflows/ai-sast.yml`:  
   [`.github/workflows/ai-sast.yml`](.github/workflows/ai-sast.yml)

2. **Add repository secrets** (Settings → Secrets and variables → Actions):  
   `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CREDENTIALS`

The workflow checks out **`rivian/ai-sast`** by default. **Optional:** set `AI_SAST_REPO` (e.g. for a fork); `AI_SAST_BASE_BRANCH` (default `main`); `runs-on: self-hosted` for your own runners. **Full scan:** Actions → “AI-SAST” → “Run workflow”.

📚 **Full integration guide:** [docs/INTEGRATION.md](docs/INTEGRATION.md)

### Optional: Feedback Loop

Developers can mark findings as true/false positives to improve accuracy over time. Feedback is automatically stored in SQLite.

📚 **Setup guide:** [docs/FEEDBACK-LOOP.md](docs/FEEDBACK-LOOP.md)

---

## 💡 Configuration

### Jira Integration (Improves Accuracy)

Integrating with Jira provides context to the LLM about known vulnerability patterns:

```bash
export JIRA_SERVER="https://your-company.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your-jira-api-token"
export JIRA_PROJECT_KEY="SEC"
```

### Customize Scanning

**Filter PR comment severities:**
```bash
export AI_SAST_SEVERITY="critical,high"  # Default
```

**Exclude paths:**
```bash
export AI_SAST_EXCLUDE_PATHS="dist,build,vendor"
```

**Custom AI instructions:**
```bash
export AI_SAST_CUSTOM_PROMPT="Focus on authentication vulnerabilities"
```

---

## ⚙️ Configuration

### Required Environment Variables (Vertex AI)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_CREDENTIALS` | Repository secret: service account JSON (for GitHub Actions auth) |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_LOCATION` | GCP region | `us-central1` |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash-exp` |
| `LLM_BACKEND` | `vertex` or `ollama` | `vertex` |
| `OLLAMA_MODEL` | Ollama model (if using Ollama) | `qwen2.5-coder:14b` |
| `AI_SAST_STORE_FINDINGS` | Store scan findings in DB | `false` |

**Note on `AI_SAST_STORE_FINDINGS`:** Set to `true` to store all scan findings in the database for analytics. By default, only feedback is stored to keep the database lightweight.

**For customization options (severity, exclusions, prompts)**, see "💡 Highly Recommended" section above.

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

## 🔒 Security Best Practices

This project follows OWASP security guidelines:
- ✅ No hardcoded secrets (use environment variables)
- ✅ Input validation and sanitization
- ✅ Secure credential handling
- ✅ Minimal logging of sensitive data

## 🐛 Troubleshooting

**Authentication Errors:**
- Check service account has "Vertex AI User" role
- Verify `GOOGLE_CLOUD_PROJECT` is correct

**Model Not Available:**
- Try different model: `export GEMINI_MODEL="gemini-1.5-pro"`
- Enable Vertex AI API: `gcloud services enable aiplatform.googleapis.com`

**Rate Limiting:**
- Reduce parallel workers: `--max-workers 1`
- Exclude more files: `export AI_SAST_EXCLUDE_PATHS="dist,build,tests"`

## 📧 Support

- 🐛 **Issues**: [Report bugs](../../issues)
- 💬 **Discussions**: [Ask questions](../../discussions)
- 📖 **Documentation**: Browse the [docs/](docs/) folder

---

Made with ❤️ by the AI-SAST community

