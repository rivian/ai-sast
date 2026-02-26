# AI-SAST Architecture

## Overview

AI-SAST is an AI-powered static application security testing tool that combines traditional security scanning with large language models for intelligent vulnerability detection.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │  Gitleaks    │  │   PR Scan    │  │   Full Scan         │  │
│  │  (Secrets)   │  │  (Changed)   │  │   (All Files)       │  │
│  └──────────────┘  └──────────────┘  └─────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI-SAST Scanner                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  1. File Collection & Filtering                        │    │
│  │     - Load file extensions from ai-sast-extensions.txt │    │
│  │     - Apply exclusion patterns                         │    │
│  │     - Filter test files, dependencies, etc.            │    │
│  └────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  2. LLM Backend Selection                              │    │
│  │     ┌─────────────────┐      ┌──────────────────┐     │    │
│  │     │   Vertex AI     │  OR  │     Ollama       │     │    │
│  │     │   (Cloud)       │      │     (Local)      │     │    │
│  │     └─────────────────┘      └──────────────────┘     │    │
│  └────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  3. Code Analysis                                       │    │
│  │     - Load security scanning prompt                     │    │
│  │     - Send code + context to LLM                        │    │
│  │     - Parse vulnerability findings                      │    │
│  │     - Calculate CVSS scores                             │    │
│  │     - Generate unique vuln IDs                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  4. Report Generation                                   │    │
│  │     - HTML report (all severities)                      │    │
│  │     - Markdown PR comment (critical/high)               │    │
│  │     - Filter by AI_SAST_SEVERITY                        │    │
│  │     - Add interactive checkboxes                        │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌──────────────────┐                  ┌──────────────────────┐
│  SQLite Database │                  │  GitHub PR Comment   │
│  ~/.ai-sast/     │                  │  (with checkboxes)   │
│  - Scan results  │                  └──────────┬───────────┘
│  - Feedback      │                             │
└──────────────────┘                             │
                                                  │
                                    ┌─────────────▼─────────────┐
                                    │  Developer Reviews        │
                                    │  ☑ True Positive          │
                                    │  ☐ False Positive         │
                                    └─────────────┬─────────────┘
                                                  │
                                                  ▼
                                    ┌─────────────────────────┐
                                    │  Feedback Collection    │
                                    │  (GitHub Actions)       │
                                    └─────────────┬───────────┘
                                                  │
                                                  ▼
                                    ┌─────────────────────────┐
                                    │  Feedback Storage       │
                                    │  - SQLite (default)     │
                                    │  - Databricks (optional)│
                                    └─────────────────────────┘
```

## Core Components

### 1. Scanner Engine (`src/core/scanner.py`)

**Responsibilities:**
- File discovery and filtering
- Code content extraction
- LLM client initialization
- Parallel/sequential processing
- Retry logic with exponential backoff

**Key Features:**
- Configurable file extensions via `ai-sast-extensions.txt`
- Smart exclusion patterns (test files, dependencies, etc.)
- Rate limit handling
- Support for both Vertex AI and Ollama backends

### 2. LLM Backends

#### Vertex AI (Google Cloud)
- **Location:** `src/core/vertex.py`
- **Models:** Gemini 2.0 Flash, Gemini 2.5 Pro
- **Use Case:** Production, cloud-based scanning
- **Authentication:** Google Cloud credentials

#### Ollama (Local)
- **Location:** `src/integrations/ollama.py`
- **Models:** Qwen2.5-Coder, CodeLlama, Llama 3.1, DeepSeek
- **Use Case:** Privacy-first, local scanning
- **Requirements:** Ollama service running locally

### 3. Report Generator (`src/core/report.py`)

**Responsibilities:**
- HTML report generation with all severities
- Markdown PR comment generation (filtered by severity)
- CVSS vector string formatting
- Unique vulnerability ID generation (SHA-1 hash)
- Interactive checkbox creation

**Severity Filtering:**
- Controlled by `AI_SAST_SEVERITY` environment variable
- Options: `critical`, `high`, `medium`, `low`
- Default: `critical,high`

### 4. Feedback System

#### Storage Layer (`src/integrations/scan_database.py`)
- **Primary:** SQLite at `~/.ai-sast/scans.db`
- **Schema:**
  - `scan_results` table: Initial findings with vuln_id
  - `feedback` table: Developer feedback (true/false positive)

#### Feedback Collection (`.github/workflows/collect-feedback.yml`)
- **Trigger:** GitHub issue_comment events (PR comments)
- **Action:** Parse checkbox changes, store feedback in SQLite
- **Deployment:** Runs automatically in GitHub Actions

### 5. GitHub Actions Workflows

#### PR Scan (`.github/workflows/pr-scan.yml`)
- **Trigger:** Pull requests to main/dev, manual dispatch
- **Scope:** Only changed files (fast)
- **Output:** PR comment with critical/high findings, HTML report artifact

#### Full Scan (`.github/workflows/full-scan.yml`)
- **Trigger:** Manual dispatch only
- **Scope:** Entire repository
- **Output:** HTML report artifact
- **Configuration:** Sequential scanning (`--max-workers 1`)

#### Gitleaks (`.github/workflows/gitleaks.yml`)
- **Trigger:** Push, manual dispatch
- **Purpose:** Secret detection
- **Tool:** Open-source Gitleaks

## Data Flow

### 1. Pull Request Scan Flow

```
Developer creates PR
    │
    ├─> GitHub Actions triggered
    │
    ├─> Fetch changed files (git diff)
    │
    ├─> Filter by extensions & exclusions
    │
    ├─> For each file:
    │   ├─> Load prompt from prompts/default_prompt.txt
    │   ├─> Add custom prompt if AI_SAST_CUSTOM_PROMPT set
    │   ├─> Send to LLM (Vertex AI or Ollama)
    │   ├─> Parse JSON response
    │   └─> Generate vuln_id (SHA-1 hash)
    │
    ├─> Generate HTML report (all severities)
    │
    ├─> Generate PR comment markdown (filtered by AI_SAST_SEVERITY)
    │
    ├─> Post comment to PR
    │
    └─> Store results in SQLite
```

### 2. Feedback Loop Flow

```
Developer reviews PR comment
    │
    ├─> Checks ☑ True Positive or ☑ False Positive
    │
    ├─> Saves comment
    │
    ├─> GitHub Actions workflow triggered
    │
    ├─> Extract vuln_id and parse checkbox state
    │
    ├─> Store feedback in SQLite (or Databricks)
    │
    └─> Future scans include this feedback
```

## Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AI_SAST_LLM` | Choose `vertex`, `bedrock`, or `ollama` | `vertex` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | (required for vertex) |
| `GOOGLE_LOCATION` | GCP region | `us-central1` |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash-exp` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5-coder:14b` |
| `AI_SAST_SEVERITY` | PR comment severity filter | `critical,high` |
| `AI_SAST_EXCLUDE_PATHS` | Additional exclusion patterns | - |
| `AI_SAST_CUSTOM_PROMPT` | Append to scanning prompt | - |
| `AI_SAST_DB_PATH` | SQLite database location | `~/.ai-sast/scans.db` |

### File Configuration

**`ai-sast-extensions.txt`**
- Defines supported file types for scanning
- One pattern per line (e.g., `*.py`, `*.js`)
- Easily customizable by users

**`prompts/default_prompt.txt`**
- Base security scanning prompt sent to LLM
- Includes instructions for JSON formatting
- Users can append custom instructions via `AI_SAST_CUSTOM_PROMPT`

## Security Considerations

### Authentication
- **Local Development:** `gcloud auth application-default login`
- **GitHub Actions:** Service account JSON via `GOOGLE_CREDENTIALS` repository secret (workflow auth step)
- **Ollama:** No authentication (local only)

### Secrets Management
- All sensitive data in environment variables
- GitHub Secrets for CI/CD
- No hardcoded credentials
- Gitleaks integrated for secret detection

### Rate Limiting
- Exponential backoff (3^attempt seconds)
- Configurable max workers (`--max-workers`)
- Sleep delays between parallel file processing
- Recommended: `--max-workers 1` for full scans

## Deployment Options

### Local Development
```bash
# Vertex AI
export AI_SAST_LLM="vertex"
export GOOGLE_CLOUD_PROJECT="my-project"
gcloud auth application-default login
python -m src.main.pr_scan

# Ollama
export AI_SAST_LLM="ollama"
ollama serve
python -m src.main.pr_scan
```

### GitHub Actions (CI/CD)
- Secrets configured in repository settings
- Workflows run on `ubuntu-latest`
- Artifacts stored for 30 days
- PR comments and feedback collection automated

## Performance

### Scanning Speed
- **PR Scan:** ~5-30 seconds (depends on changed files)
- **Full Scan:** Minutes to hours (depends on codebase size)
- **Bottleneck:** LLM API calls (rate limits)

### Optimization Strategies
1. **Sequential scanning:** `--max-workers 1` (avoids rate limits)
2. **Exclusion patterns:** Skip test files, dependencies
3. **File type filtering:** Only scan relevant languages
4. **Local LLMs:** Ollama for unlimited requests
5. **Smaller models:** Use `qwen2.5-coder:7b` for faster inference

## Extensibility

### Adding New LLM Backends
1. Create client class in `src/integrations/`
2. Implement `generate()` method
3. Add to `src/core/scanner.py` backend selection
4. Update configuration documentation

### Custom Prompts
- Modify `prompts/default_prompt.txt` for base changes
- Use `AI_SAST_CUSTOM_PROMPT` for runtime additions
- Format: Append to base prompt with newline

### Additional Integrations
- **Jira:** Uncomment in `requirements.txt`, set env vars
- **Databricks:** Uncomment in `requirements.txt`, configure credentials
- **Notifications:** Set webhook URLs for Slack/Teams/Discord

## Debugging

```bash
# Enable verbose logging
export LOG_LEVEL="DEBUG"

# Test specific file
python -m src.core.scanner --file path/to/file.py

# Check database
sqlite3 ~/.ai-sast/scans.db "SELECT * FROM scan_results LIMIT 5;"
```
