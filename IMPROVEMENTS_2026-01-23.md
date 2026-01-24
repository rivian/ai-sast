# Improvements Summary - 2026-01-23

This document summarizes the improvements made to the AI-SAST open-source project based on the review feedback.

## Issues Identified & Resolutions

### 1. ✅ Renamed `webhook_client.py` to `notifications.py`

**Issue**: The file name `webhook_client.py` was confusing because it handles sending notifications to external systems (Slack, Teams, Discord), not receiving webhooks.

**Resolution**:
- Renamed `src/core/webhook_client.py` → `src/core/notifications.py`
- Updated all imports in:
  - `src/core/__init__.py`
  - `src/main/pr_scan.py`
  - `docs/ARCHITECTURE.md`
- Updated docstrings to clarify it's a "Notifications Client"
- The actual webhook **listener** is in `webhook/main.py` (Flask app)

**Clarity**:
- `src/core/notifications.py` - Sends notifications OUT to external systems
- `webhook/main.py` - Receives webhook events IN from GitHub

---

### 2. ✅ Moved Default Prompt to External File

**Issue**: The default AI scanning prompt was hardcoded as a class variable in `scanner.py`, making it difficult to view and customize.

**Resolution**:
- Prompt already exists in `prompts/default_prompt.txt` (112 lines)
- Added `_load_default_prompt()` static method to load from file
- Scanner now loads prompt during initialization: `self.DEFAULT_PROMPT = self._load_default_prompt()`
- Includes fallback prompt in case file is missing (defensive programming)
- Users can now easily view and customize the prompt without touching code

**Benefits**:
- ✅ Prompt is visible and documented
- ✅ Can be customized without code changes
- ✅ Version controlled separately
- ✅ Graceful fallback if file is missing

---

### 3. ✅ Removed All Rivian/Beacon-Specific Code from Webhook Folder

**Issue**: Needed to ensure no proprietary or company-specific references in the webhook infrastructure.

**Findings & Fixes**:

#### Found & Fixed:
1. **`webhook/iac/modules/api-gateway/main.tf`**
   - Changed: `name = "beacon-webhook-api"` → `name = "ai-sast-webhook-api"`

2. **`webhook/iac/modules/secrets-manager/main.tf`**
   - Changed: `name = "beacon-gitlab-secret-token"` → `name = "github-webhook-secret"`

#### Verified Clean:
- ✅ No "rivian" references found in webhook folder
- ✅ No other "beacon" references found
- ✅ All environment variables are generic (`AI_SAST_*`)
- ✅ All configuration is user-provided

**Result**: Webhook infrastructure is 100% generic and ready for open-source use.

---

### 4. ✅ Added Gitleaks for Secret Detection

**Issue**: Need to prevent accidental commits of secrets, API keys, tokens, etc.

**Resolution**:

#### Added Gitleaks Job to GitHub Actions:
**File**: `.github/workflows/security-scan.yml`

```yaml
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Run Gitleaks
      uses: gitleaks/gitleaks-action@v2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        GITLEAKS_ENABLE_SUMMARY: true
  
  security-scan:
    runs-on: ubuntu-latest
    needs: gitleaks  # Only runs if gitleaks passes
```

#### Created Gitleaks Configuration:
**File**: `.gitleaks.toml`

```toml
title = "AI-SAST Gitleaks Configuration"

[extend]
useDefault = true

[allowlist]
paths = [
    '''README\.md$''',
    '''INTEGRATIONS\.md$''',
    '''docs/.*\.md$''',
    '''examples/.*''',
    '''\.github/workflows/.*\.yml$''',
]

regexes = [
    '''Example:.*''',
    '''example.*=.*''',
    '''\$\{\{ secrets\..*\}\}''',  # GitHub Actions secrets syntax
]

[allowlist.stopwords]
stopwords = [
    'your-project-id',
    'your-workspace',
    'your-token',
    'YOUR_',
    'EXAMPLE_',
]
```

**Features**:
- ✅ Scans for secrets in all commits
- ✅ Fails CI/CD pipeline if secrets detected
- ✅ Allowlists documentation examples
- ✅ Allowlists GitHub Actions secrets syntax (`${{ secrets.* }}`)
- ✅ Ignores example/placeholder values
- ✅ Runs before main security scan
- ✅ Provides summary in GitHub UI

**Benefits**:
- Prevents accidental exposure of credentials
- Catches secrets before they're pushed
- Educates developers on secure practices
- Complies with security best practices

---

## Additional Documentation Updates

### Updated Files:

1. **`README.md`**
   - Added `notifications.py` to project structure
   - Added `.gitleaks.toml` to project structure
   - Updated workflow description to mention Gitleaks

2. **`docs/ARCHITECTURE.md`**
   - Renamed webhook_client.py → notifications.py
   - Added Gitleaks to implemented features
   - Clarified external prompt file support

3. **`CHANGELOG.md`**
   - Documented all changes in [Unreleased] section
   - Added "Changed" and "Fixed" sections
   - Listed all improvements

---

## Summary of Changes

| Category | Change | Files Affected |
|----------|--------|----------------|
| **Rename** | webhook_client.py → notifications.py | 4 files |
| **Refactor** | Moved prompt to external file | scanner.py |
| **Cleanup** | Removed beacon/rivian references | 2 Terraform modules |
| **Security** | Added Gitleaks secret scanning | workflow + config |
| **Docs** | Updated all documentation | 4 docs files |

---

## Testing Recommendations

### 1. Test Prompt Loading
```bash
cd /path/to/ai-sast
python -c "from src.core.scanner import SecurityScanner; s = SecurityScanner(); print('✅ Prompt loaded successfully' if s.DEFAULT_PROMPT else '❌ Failed')"
```

### 2. Test Notifications Import
```bash
python -c "from src.core.notifications import WebhookClient; print('✅ Import successful')"
```

### 3. Test Gitleaks Locally
```bash
# Install gitleaks
brew install gitleaks  # macOS
# OR
docker pull zricethezav/gitleaks

# Run scan
gitleaks detect --config .gitleaks.toml --verbose
```

### 4. Test Webhook Infrastructure
```bash
# Check for any remaining proprietary references
cd webhook
grep -ri "rivian" . || echo "✅ No rivian references"
grep -ri "beacon" . || echo "⚠️ Found beacon references (check if generic context)"
```

---

## Security Improvements

1. **Secret Detection**: Gitleaks prevents accidental credential leaks
2. **Generic Infrastructure**: No company-specific hardcoded values
3. **Clear Separation**: Notifications (outbound) vs webhook listener (inbound)
4. **Visible Prompts**: Prompt engineering is transparent and auditable

---

## Migration Notes for Existing Users

### If using webhook_client:
```python
# OLD (will fail)
from src.core.webhook_client import WebhookClient

# NEW (correct)
from src.core.notifications import WebhookClient
```

### If customizing prompts:
```python
# OLD (editing scanner.py)
# Edit DEFAULT_PROMPT in scanner.py

# NEW (recommended)
# Edit prompts/default_prompt.txt
# No code changes needed!
```

---

## Compliance Checklist

- [x] No proprietary code in open-source version
- [x] No hardcoded company-specific values
- [x] All secrets managed via environment variables
- [x] Secret detection in CI/CD pipeline
- [x] Clear separation of concerns (naming)
- [x] Transparent AI prompts (external file)
- [x] Documentation updated
- [x] CHANGELOG updated

---

## Conclusion

All four issues have been addressed:

1. ✅ **webhook_client.py** renamed to **notifications.py** for clarity
2. ✅ **Default prompt** moved to external file (`prompts/default_prompt.txt`)
3. ✅ **All beacon/rivian references** removed from webhook infrastructure
4. ✅ **Gitleaks** integrated for automatic secret detection

The codebase is now cleaner, more secure, and ready for open-source distribution!

