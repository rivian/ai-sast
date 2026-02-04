# GitHub Wiki Setup

This folder contains wiki documentation for AI-SAST. Here's how to publish it to your GitHub repository's wiki.

## Quick Publish to GitHub Wiki

### Option 1: Using GitHub Web Interface (Easiest)

1. **Enable Wiki** for your repository:
   - Go to your repository on GitHub
   - Click "Settings"
   - Scroll to "Features" section
   - Check "Wikis"

2. **Create Initial Wiki Page**:
   - Go to "Wiki" tab
   - Click "Create the first page"
   - Title: "Home"
   - Paste content from `wiki/Home.md`
   - Click "Save Page"

3. **Add More Pages**:
   - Click "New Page"
   - Copy/paste content from each `.md` file
   - Use the filename without `.md` as the page title
   - Example: `Installation-and-Setup.md` → Title: "Installation and Setup"

### Option 2: Using Git (Advanced)

GitHub wikis are actually Git repositories! You can clone and push to them.

1. **Clone the Wiki Repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-sast.wiki.git
   ```

2. **Copy Wiki Files**:
   ```bash
   cp wiki/*.md ai-sast.wiki/
   ```

3. **Commit and Push**:
   ```bash
   cd ai-sast.wiki
   git add .
   git commit -m "Add comprehensive documentation"
   git push
   ```

## Wiki Pages to Create

Based on the files in this folder, create these pages in your GitHub Wiki:

| File | Wiki Page Title | Description |
|------|----------------|-------------|
| `Home.md` | Home | Main wiki landing page |
| `Installation-and-Setup.md` | Installation and Setup | Setup instructions |
| `Feedback-Loop.md` | Feedback Loop | Feedback system documentation |

## Adding More Documentation

Convert existing docs from `docs/` folder to wiki format:

### Architecture Overview
- Source: `docs/ARCHITECTURE.md`
- Wiki Title: "Architecture Overview"
- Create in wiki with same content

### Ollama Setup
- Source: `docs/OLLAMA.md`
- Wiki Title: "Ollama Setup"
- Create in wiki with same content

### Webhook Integration
- Source: `docs/WEBHOOKS.md`
- Wiki Title: "Webhook Integration"
- Create in wiki with same content

### Optional Findings Storage
- Source: `docs/OPTIONAL-FINDINGS-STORAGE.md`
- Wiki Title: "Optional Findings Storage"
- Create in wiki with same content

## Wiki Navigation Tips

GitHub wikis automatically create a sidebar with all your pages. To customize the sidebar:

1. **Create `_Sidebar.md` in wiki**:
   ```markdown
   **Getting Started**
   - [Home](Home)
   - [Installation & Setup](Installation-and-Setup)
   - [Quick Start](Quick-Start-Guide)
   
   **Features**
   - [Architecture](Architecture-Overview)
   - [PR Scanning](PR-Scanning)
   - [Feedback Loop](Feedback-Loop)
   
   **Advanced**
   - [Ollama Setup](Ollama-Setup)
   - [Webhooks](Webhook-Integration)
   - [Optional Findings Storage](Optional-Findings-Storage)
   ```

2. **Create `_Footer.md` for footer**:
   ```markdown
   Made with ❤️ by AI-SAST Community | [Report Issue](../../issues)
   ```

## Benefits of GitHub Wiki

✅ **Easy to Edit** - Edit directly in browser
✅ **Version Controlled** - Full Git history
✅ **Searchable** - Built-in search
✅ **No Build Process** - Instant updates
✅ **Collaborative** - Anyone with access can contribute
✅ **Discoverable** - Shows up in "Wiki" tab

## After Publishing

1. **Update README.md** - Point to wiki:
   ```markdown
   - 📖 **Documentation**: [Browse the Wiki](../../wiki)
   ```

2. **Add Wiki Link** to repository description

3. **Keep docs/ folder** for reference or archive

## Maintenance

- **Update wiki** when features change
- **Keep synced** with code changes
- **Accept contributions** via pull requests
- **Review periodically** for accuracy

---

**Ready to publish?** Follow Option 1 above to get started!
