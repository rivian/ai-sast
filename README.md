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
- 💾 **Local Database**: Built-in SQLite for storing scan results and feedback (no external services required)
- 🔒 **Privacy Options**: Keep your code on-premise with Ollama backend
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

### Choose Your LLM Backend

AI-SAST supports two backends:

| Backend | Best For | Setup |
|---------|----------|-------|
| **Vertex AI** | Production, cloud, teams | Requires Google Cloud account |
| **Ollama** | Local, privacy, cost-free | Runs on your machine |

<details>
<summary><b>Option 1: Vertex AI (Cloud)</b></summary>

#### Prerequisites
- Python 3.8 or higher
- Google Cloud Platform account with Vertex AI API enabled
- Google Cloud CLI (optional, for easier authentication)

#### Setup
```bash
# Install dependencies
python setup.py

# Configure
export LLM_BACKEND="vertex"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export VERTEX_AI_LOCATION="us-central1"
export GEMINI_MODEL="gemini-2.0-flash-exp"  # or gemini-2.5-pro
```

See full Vertex AI setup below.
</details>

<details>
<summary><b>Option 2: Ollama (Local/Open-Source) ⭐ New!</b></summary>

#### Prerequisites
- Python 3.8 or higher
- [Ollama](https://ollama.com/) installed locally

#### Setup
```bash
# Install Ollama (Mac/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a code model
ollama pull qwen2.5-coder:14b

# Start Ollama (if not auto-started)
ollama serve

# Install AI-SAST dependencies
pip install -r requirements.txt

# Configure
export LLM_BACKEND="ollama"
export OLLAMA_MODEL="qwen2.5-coder:14b"
export OLLAMA_BASE_URL="http://localhost:11434"

# Run example
python examples/ollama_scan.py
```

**Recommended Models for Security Scanning:**
- `qwen2.5-coder:14b` - **Recommended** - Best balance (8GB RAM)
- `qwen2.5-coder:7b` - Fast, code-focused (4GB RAM)
- `qwen2.5-coder:32b` - Most accurate (20GB RAM)
- `codellama:13b` - Meta's code model (8GB RAM)
- `llama3.1:8b` - Latest Llama (5GB RAM)
- `deepseek-coder:33b` - Alternative, very capable (20GB RAM)

**Benefits:**
- ✅ 100% free and open-source
- ✅ Your code never leaves your machine
- ✅ No cloud costs or rate limits
- ✅ Works offline

</details>

---

## 🖥️ Running Ollama Locally (Open-Source Alternative)

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | macOS, Linux, Windows (WSL2) | macOS or Linux |
| **RAM** | 8GB (for 7B models) | 16GB+ (for 14B models) |
| **Disk Space** | 5GB free | 20GB+ free |
| **CPU** | Any modern CPU | Multi-core CPU |
| **GPU** | Not required | NVIDIA/AMD GPU (10x faster) |

### Installation Steps

#### 1. Install Ollama

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [https://ollama.com/download/windows](https://ollama.com/download/windows)

**Verify Installation:**
```bash
ollama --version
```

#### 2. Start Ollama Service

**macOS:**
Ollama starts automatically after installation.

**Linux:**
```bash
# Start service
ollama serve

# Or run in background
nohup ollama serve &
```

**Check if running:**
```bash
curl http://localhost:11434/api/tags
```

#### 3. Pull a Model

**Recommended for most users:**
```bash
ollama pull qwen2.5-coder:14b
```

**Other options:**
```bash
# Faster, smaller model (4GB RAM)
ollama pull qwen2.5-coder:7b

# Most accurate (20GB RAM)
ollama pull qwen2.5-coder:32b

# Alternatives
ollama pull codellama:13b
ollama pull llama3.1:8b
```

**List installed models:**
```bash
ollama list
```

#### 4. Install AI-SAST

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-sast.git
cd ai-sast

# Install Python dependencies
pip install -r requirements.txt
```

#### 5. Configure AI-SAST for Ollama

```bash
# Set backend to Ollama
export LLM_BACKEND="ollama"

# Optional: Change model (defaults to qwen2.5-coder:14b)
export OLLAMA_MODEL="qwen2.5-coder:14b"

# Optional: Change Ollama URL (defaults to http://localhost:11434)
export OLLAMA_BASE_URL="http://localhost:11434"
```

#### 6. Run Your First Scan

```bash
# Test with example
python examples/ollama_scan.py

# Scan a file
python -m src.core.scanner --file your_file.py

# Scan a directory
python -m src.core.scanner --directory ./your-code
```

### Quick Start (All-in-One)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5-coder:14b

# Verify
ollama list

# Configure
export LLM_BACKEND="ollama"

# Run example
cd ai-sast
python examples/ollama_scan.py
```

### Troubleshooting

**"Connection refused":**
```bash
# Make sure Ollama is running
ollama serve

# Or check status
curl http://localhost:11434/api/tags
```

**"Model not found":**
```bash
# List available models
ollama list

# Pull the model you want
ollama pull qwen2.5-coder:14b
```

**"Out of memory":**
```bash
# Use a smaller model
ollama pull qwen2.5-coder:7b
export OLLAMA_MODEL="qwen2.5-coder:7b"
```

**Slow performance:**
```bash
# Check if GPU is being used
ollama ps

# For NVIDIA GPUs, install CUDA drivers
# For AMD GPUs, install ROCm drivers
```

### Model Selection Guide

| Model | RAM | Speed | Accuracy | Best For |
|-------|-----|-------|----------|----------|
| `qwen2.5-coder:7b` | 4GB | Fast | ⭐⭐⭐⭐ | Quick scans, limited RAM |
| `qwen2.5-coder:14b` | 8GB | Medium | ⭐⭐⭐⭐⭐ | **Recommended default** |
| `qwen2.5-coder:32b` | 20GB | Slow | ⭐⭐⭐⭐⭐ | Maximum accuracy |
| `codellama:13b` | 8GB | Medium | ⭐⭐⭐⭐ | Alternative option |
| `llama3.1:8b` | 5GB | Medium | ⭐⭐⭐⭐ | General purpose |

### Switching Between Vertex AI and Ollama

**Use Vertex AI:**
```bash
unset LLM_BACKEND  # Uses default (vertex)
# or
export LLM_BACKEND="vertex"
```

**Use Ollama:**
```bash
export LLM_BACKEND="ollama"
```

### Performance Tips

1. **Use GPU**: Install NVIDIA CUDA or AMD ROCm for 5-10x speedup
2. **Smaller models**: Use `qwen2.5-coder:7b` for faster scans
3. **More RAM**: Close other applications to free memory
4. **SSD**: Store models on SSD for faster loading
5. **Keep models updated**: Run `ollama pull <model>` periodically

📚 **For detailed configuration**, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

---

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
| **LLM Backend** |
| `LLM_BACKEND` | Backend to use: `vertex` or `ollama` | `vertex` |
| **Vertex AI (Cloud)** |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud Project ID | (required for vertex) |
| `GOOGLE_PROJECT_ID` | Alternative to GOOGLE_CLOUD_PROJECT | (required for vertex) |
| `VERTEX_AI_LOCATION` | Vertex AI location/region | `us-central1` |
| `GOOGLE_LOCATION` | Alternative to VERTEX_AI_LOCATION | `us-central1` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash-exp` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | (optional) |
| `GOOGLE_TOKEN` | Google Cloud token (JSON or base64) | (optional) |
| **Ollama (Local)** |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model to use with Ollama | `qwen2.5-coder:14b` |
| **Scanning** |
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

### Supported File Extensions

AI-SAST scans specific file types for security vulnerabilities. The supported extensions are defined in `ai-sast-extensions.txt` file in the project root.

**Default supported languages:**
- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`, `.hpp`)
- PHP (`.php`)
- Ruby (`.rb`)
- Go (`.go`)
- Rust (`.rs`)
- C# (`.cs`)
- SQL (`.sql`)
- Shell (`.sh`, `.bash`)
- GraphQL (`.graphql`, `.gql`)

**To customize:**
Edit `ai-sast-extensions.txt` to add or remove file types:
```bash
# Add Swift files
echo "*.swift" >> ai-sast-extensions.txt

# Remove PHP files (comment out the line)
sed -i 's/^\*.php$/# *.php/' ai-sast-extensions.txt
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

# GEMINI_MODEL (Optional, default: gemini-2.0-flash-exp)
export GEMINI_MODEL="gemini-2.0-flash-exp"
# Other options: "gemini-1.5-pro", "gemini-2.5-pro" (requires higher quota)

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
# Controls which severity levels are posted as PR comments
export AI_SAST_SEVERITY="critical,high"
# Options:
#   - "critical,high" (default) - Only critical and high severity findings
#   - "critical,high,medium" - Include medium severity findings
#   - "critical,high,medium,low" - Include all findings except info
#   - "critical" - Only critical findings
# Note: Full scan reports always include all severities, this only affects PR comments
```

#### GitHub Actions Configuration

**To customize PR comment severities in GitHub Actions:**

1. Go to: **Repository Settings → Secrets and variables → Actions → Variables**
2. Click **New repository variable**
3. Set:
   - **Name**: `AI_SAST_SEVERITY`
   - **Value**: `critical,high,medium` (or your preferred severities)

**Examples:**
```bash
# Show only critical issues (very strict)
AI_SAST_SEVERITY=critical

# Show critical and high (default, recommended)
AI_SAST_SEVERITY=critical,high

# Show critical, high, and medium (more verbose)
AI_SAST_SEVERITY=critical,high,medium

# Show everything except info (very verbose)
AI_SAST_SEVERITY=critical,high,medium,low
```

#### Environment File Template

Create a `.env` file:

```bash
# .env - AI-SAST Configuration
# DO NOT COMMIT THIS FILE

# === Core Configuration (Required) ===
GOOGLE_CLOUD_PROJECT=
VERTEX_AI_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash-exp

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

