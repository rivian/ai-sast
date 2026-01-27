# Changelog

All notable changes to AI-SAST will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub webhook listener for capturing developer feedback from PR comments
- AWS infrastructure (Terraform) for deploying webhook listener on ECS Fargate
- Flask application for processing GitHub webhook events
- Automated feedback collection and storage in Databricks
- SNS notifications for confirmed vulnerabilities (optional)
- Interactive checkbox format in PR comments for true/false positive marking
- Feedback write functionality in Databricks client
- Webhook documentation and deployment guide (`webhook/README.md`)
- Enhanced architecture documentation with feedback loop details
- Gitleaks integration in GitHub Actions to detect secrets in commits
- `.gitleaks.toml` configuration file for secret scanning

### Changed
- Updated project structure to include `webhook/` directory
- Enhanced Databricks client with write capabilities
- Updated documentation to reflect webhook availability
- Renamed `webhook_client.py` to `notifications.py` for clarity
- Moved default AI prompt from hardcoded string to external file (`prompts/default_prompt.txt`)
- Scanner now loads prompt from file with fallback for missing file
- **Reorganized all integration modules** into `src/integrations/` directory
- Moved `jira_client.py`, `databricks_client.py`, `vector_client.py`, and `notifications.py` to `src/integrations/`
- **Simplified file naming**: Removed redundant `_client` suffix from integration files
  - `jira_client.py` → `jira.py`
  - `databricks_client.py` → `databricks.py`
  - `vector_client.py` → `vector.py`
- Renamed `WebhookClient` to `NotificationClient` for clarity in public API
- **Renamed environment variable**: `AI_SAST_PROMPT` → `AI_SAST_CUSTOM_PROMPT` for clarity

### Fixed
- Removed all "beacon" references from webhook infrastructure
- Removed all "rivian" references from webhook infrastructure
- Updated Terraform module names to be generic (ai-sast instead of beacon)
- Updated secret names in AWS Secrets Manager (github-webhook-secret instead of beacon-gitlab-secret-token)

---

## [1.0.0] - 2026-01-23

### Added
- Initial release of AI-SAST
- AI-powered security scanning using Google Cloud Vertex AI (Gemini 2.0 Flash)
- Support for multiple programming languages (Python, JavaScript/TypeScript, Java, C/C++, PHP, Ruby, Go, Rust, C#, SQL, Shell)
- GitHub Actions integration for CI/CD
  - Pull request scanning (scans only changed files)
  - Full repository scanning on push to main
  - Automated PR comments with findings
- Local scanning capabilities
  - Single file scanning
  - Directory scanning
  - Git repository scanning
- Comprehensive reporting
  - HTML report generation
  - Markdown report generation
  - CVSS v3.1 scoring
  - Severity-based filtering (Critical, High, Medium, Low)
- Optional integrations
  - Jira integration for vulnerability context
  - Databricks integration for historical feedback
  - Vector/Log aggregator support for security event logging
  - Webhook notifications (Slack, Teams, Discord, generic)
- Configurable exclusion patterns
- Custom AI prompt instructions (external file support)
- Environment variable configuration
- Apache License 2.0

### Security
- No hardcoded credentials
- Secure environment variable handling
- Input validation and sanitization
- OWASP security best practices
- GitHub webhook signature verification (HMAC-SHA256)
- AWS IAM roles with least privilege

---

## Release Notes

### What's New in 1.0.0

This is the initial open-source release of AI-SAST, an AI-powered static application security testing tool that leverages Google Cloud's Vertex AI to provide intelligent, context-aware security analysis.

**Key Features:**
- 🤖 **AI-Powered Analysis**: Uses Gemini 2.0 Flash for intelligent vulnerability detection
- 🔄 **CI/CD Integration**: Native GitHub Actions support with automated PR comments
- 🎯 **Smart Scanning**: Differential scanning for PRs, full scanning for main branch
- 📊 **Comprehensive Reports**: HTML and Markdown reports with CVSS scoring
- 🔌 **Extensible**: Optional Jira, Databricks, and logging integrations
- 📬 **Webhook Notifications**: Slack, Teams, Discord, and generic webhook support

**Getting Started:**
```bash
git clone https://github.com/YOUR_USERNAME/ai-sast.git
cd ai-sast
python setup.py
```

See [README.md](README.md) for complete documentation.

---

## Future Releases

### Planned for 1.2.0
- [ ] SARIF format support for GitHub Code Scanning
- [ ] Additional AI model support (Claude, GPT-4)
- [ ] GitLab CI/CD integration
- [ ] Custom rule definitions

### Under Consideration
- [ ] Web dashboard for report visualization
- [ ] IDE extensions (VS Code, IntelliJ)
- [ ] Incremental scanning improvements
- [ ] Multi-repository scanning
- [ ] API for programmatic access

---

For detailed changes and migration guides for future versions, see individual release notes.