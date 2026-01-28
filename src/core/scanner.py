#!/usr/bin/env python3
"""
Security vulnerability scanner using Vertex AI

This module provides functionality to scan source code for security vulnerabilities
using Google Cloud Vertex AI models.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import subprocess
import tempfile
import shutil
import time
import logging

from .vertex import VertexAIClient
from .config import PROJECT_ID, LOCATION

# Optional integrations - import only if available
try:
    from ..integrations.jira import JiraClient
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    JiraClient = None

try:
    from ..integrations.feedback import get_feedback_client
    FEEDBACK_AVAILABLE = True
except ImportError:
    FEEDBACK_AVAILABLE = False
    get_feedback_client = None


class SecurityScanner:
    """
    Security vulnerability scanner using Vertex AI
    """

    @staticmethod
    def _load_file_extensions() -> List[str]:
        """Load file extensions from ai-sast-extensions.txt file"""
        try:
            # Get the project root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            extensions_file = os.path.join(project_root, 'ai-sast-extensions.txt')
            
            if os.path.exists(extensions_file):
                with open(extensions_file, 'r') as f:
                    patterns = []
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            patterns.append(line)
                    if patterns:
                        return patterns
        except Exception as e:
            logging.warning(f"Could not load file extensions from ai-sast-extensions.txt: {e}")
        
        # Fallback patterns if file doesn't exist or has issues
        return [
            '*.py', '*.js', '*.ts', '*.java', '*.cpp', '*.c', '*.h',
            '*.php', '*.rb', '*.go', '*.rs', '*.cs', '*.sql', '*.sh', '*.graphql'
        ]

    @staticmethod
    def _load_default_prompt() -> str:
        """Load the default prompt from the prompts directory"""
        try:
            # Get the project root directory (2 levels up from this file)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            prompt_path = os.path.join(project_root, 'prompts', 'default_prompt.txt')
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logging.warning(f"Could not load default prompt from file: {e}. Using fallback.")
            # Fallback prompt in case file is not found
            return """As a cybersecurity expert, analyze the following source code for security vulnerabilities.

File: {file_path}
Language: {language}

Code:
```{language}
{code_content}
```

Format your response for each finding as:
- **Vulnerability Level**: [CRITICAL/HIGH/MEDIUM/LOW/INFO]
- **Issue**: Brief description of the vulnerability.
- **Location**: File name which the vulnerability exists.
- **CVSS Vector**: The full CVSS v3.1 vector string.
- **Risk**: A brief explanation of the security impact.
- **Fix**: Specific remediation steps.

{custom_instructions}"""

    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None, repo_url: Optional[str] = None):
        """
        Initialize the security scanner
        
        Args:
            project_id: Google Cloud Project ID
            location: GCP region
            repo_url: Repository URL for reference
        """
        self.client = VertexAIClient(
            project_id or PROJECT_ID,
            location or LOCATION
        )
        print(f"🤖 Using Gemini 2.0 Flash model for security analysis")
        
        # CI_PROJECT_URL (GitLab) or GITHUB_REPOSITORY (GitHub): Repository identifier
        # Example GitLab: "https://gitlab.com/myorg/myproject"
        # Example GitHub: "myorg/myproject" (will be converted to full URL)
        self.repo_url = repo_url or os.environ.get('CI_PROJECT_URL', '') or os.environ.get('GITHUB_REPOSITORY', '')
        
        # Optional Jira integration
        self.jira_client: Optional[JiraClient] = None
        self.jira_context = ""
        if JIRA_AVAILABLE:
            self._init_jira_client()
        
        # Feedback system (SQLite or Databricks)
        self.feedback_client = None
        self.feedback_context = ""
        if FEEDBACK_AVAILABLE:
            self._init_feedback_client()
        
        # Load default prompt from file
        self.DEFAULT_PROMPT = self._load_default_prompt()
        
        # AI_SAST_CUSTOM_PROMPT: Custom instructions to append to AI scanning prompt (optional)
        # Example: "Focus on SQL injection and XSS vulnerabilities"
        # Example: "Ignore issues in legacy code, prioritize new API endpoints"
        self.custom_instructions = os.environ.get('AI_SAST_CUSTOM_PROMPT', '')
        if self.custom_instructions:
            print("ℹ️ Appending custom instructions from AI_SAST_CUSTOM_PROMPT environment variable.")
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def _init_jira_client(self):
        """Initializes the Jira client if configuration is provided."""
        # JIRA_URL: Your Jira instance URL
        # Example: "https://mycompany.atlassian.net" or "https://jira.mycompany.com"
        jira_url = os.environ.get('JIRA_URL')
        
        # JIRA_USERNAME: Your Jira account email
        # Example: "security-scanner@mycompany.com" or "john.doe@company.com"
        jira_user = os.environ.get('JIRA_USERNAME')
        
        # JIRA_API_TOKEN: Your Jira API token (generate at id.atlassian.com)
        # Example: "ATATT3xFfGF0..." (long alphanumeric string)
        jira_token = os.environ.get('JIRA_API_TOKEN')
        
        if jira_user and jira_token:
            print("Jira configuration found. Initializing Jira client...")
            try:
                self.jira_client = JiraClient(jira_url, jira_user, jira_token)
                if self.jira_client.is_connected():
                    self.jira_context = self._get_vulnerability_context_from_jira()
            except Exception as e:
                print(f"⚠️ Warning: Failed to initialize Jira client: {e}")
        else:
            print("No Jira configuration found. Skipping Jira integration.")

    def _get_vulnerability_context_from_jira(self) -> str:
        """Fetches and formats vulnerability context from Jira."""
        if not self.jira_client or not self.jira_client.is_connected():
            return ""

        # JIRA_JQL_QUERY: JQL query to fetch vulnerability tickets
        # Example: "project = SECURITY AND status IN (Open, 'In Progress') AND type = Bug"
        # Example: "project = MYAPP AND labels = vulnerability AND priority IN (High, Critical)"
        # Example: "assignee = currentUser() AND status != Closed AND type = 'Security Bug'"
        jql_query = os.environ.get('JIRA_JQL_QUERY')
        
        if not jql_query:
            print("ℹ️ JIRA_JQL_QUERY not set. Please configure a JQL query to fetch vulnerabilities.")
            print("   Example: export JIRA_JQL_QUERY=\"project = SECURITY AND status != Closed\"")
            return ""
        
        try:
            tickets = self.jira_client.get_vulnerability_tickets(jql_query=jql_query)
            
            if not tickets:
                return ""

            context_parts = ["Here is a list of known, open vulnerabilities. Use this context to inform your analysis:\n"]
            for ticket in tickets[:20]:  # Limit to 20 to avoid prompt bloat
                context_parts.append(f"- **{ticket['key']}**: {ticket['summary']}")
                if ticket['description']:
                    desc_snippet = (ticket['description'][:150] + '...') if len(ticket['description']) > 150 else ticket['description']
                    context_parts.append(f"  - *Details*: {desc_snippet}")
            
            return "\n".join(context_parts)
        except Exception as e:
            print(f"⚠️ Warning: Failed to fetch Jira context: {e}")
            return ""

    def _init_feedback_client(self):
        """Initializes the feedback client (SQLite or Databricks)."""
        try:
            self.feedback_client = get_feedback_client()
            if self.feedback_client and self.feedback_client.is_configured:
                self.feedback_context = self._get_feedback_context()
            else:
                print("ℹ️ Feedback system not configured - skipping feedback retrieval")
        except Exception as e:
            print(f"⚠️ Warning: Failed to initialize feedback client: {e}")
            self.feedback_client = None

    def _get_feedback_context(self) -> str:
        """Fetches and formats feedback context from the feedback system."""
        if not self.feedback_client or not self.feedback_client.is_configured:
            return ""
        
        if not self.repo_url:
            print("ℹ️ No repository URL provided. Skipping feedback fetch.")
            return ""
        
        try:
            print(f"Fetching feedback for: {self.repo_url}")
            
            # Fetch false positives
            false_positives = self.feedback_client.get_false_positives_for_project(
                self.repo_url,
                days_back=90,
                limit=50
            )
            
            # Fetch confirmed vulnerabilities
            confirmed_vulnerabilities = self.feedback_client.get_confirmed_vulnerabilities_for_project(
                self.repo_url,
                days_back=90,
                limit=50
            )
            
            # Format context
            context = self.feedback_client.format_feedback_for_context(
                false_positives,
                confirmed_vulnerabilities
            )
            
            if context:
                total = len(false_positives) + len(confirmed_vulnerabilities)
                backend_name = type(self.feedback_client).__name__
                print(f"✅ Loaded {total} feedback record(s) from {backend_name}")
            
            return context
            
        except Exception as e:
            print(f"⚠️ Warning: Error fetching feedback: {e}")
            return ""

    def scan_code_content(self, code_content: str, file_path: str = "", language: str = "") -> Dict:
        """
        Scan source code content for security vulnerabilities
        
        Args:
            code_content: The source code to analyze
            file_path: Path/name of the file being analyzed
            language: Programming language (e.g., python, javascript, java)
            
        Returns:
            Dictionary containing vulnerability analysis results
        """
        
        # Format Jira context if it exists
        jira_context_formatted = ""
        if self.jira_context:
            jira_context_formatted = f"\n\nConsider the following context from the vulnerability database:\n\n---\n{self.jira_context}\n---"
        
        # Format Databricks feedback context if it exists
        feedback_context_formatted = ""
        if self.feedback_context:
            feedback_context_formatted = f"\n\n## Feedback from Past Scans\n\n{self.feedback_context}\n\nPlease use this feedback to improve accuracy. Avoid reporting issues similar to the false positives listed above, and pay special attention to patterns similar to confirmed vulnerabilities.\n\n---"

        # Combine contexts
        combined_context = jira_context_formatted + feedback_context_formatted
        
        # Create the final prompt using the custom instructions from the instance
        custom_instructions_formatted = f"\n\n{self.custom_instructions}" if self.custom_instructions else ""
        
        # Update the prompt to include combined context
        prompt_with_context = self.DEFAULT_PROMPT.replace(
            "{custom_instructions}",
            f"{combined_context}{custom_instructions_formatted}"
        )
        
        prompt = prompt_with_context.format(
            file_path=file_path,
            language=language,
            code_content=code_content,
            custom_instructions=""  # Already included above
        )
        
        max_retries = 5
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                # Use Gemini 2.0 Flash model
                analysis = self.client.generate_with_gemini(prompt, model_name="gemini-2.0-flash-exp")
                
                return {
                    "file_path": file_path,
                    "language": language,
                    "analysis": analysis,
                    "status": "success"
                }
            except Exception as e:
                error_message = str(e)
                # Check for rate limit error (429)
                if "429" in error_message and "Resource exhausted" in error_message:
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        print(f"⚠️ Rate limit hit for {file_path}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Gemini model failed after {max_retries} retries for {file_path}: {error_message}")
                        # Fail the job if all retries are exhausted
                        sys.exit(1)
                
                # If it's a different error, fail immediately
                if "404" in error_message and "Publisher Model" in error_message:
                    print(f"❌ Gemini model failed: {error_message}")
                    print("Failing job because the required Gemini model was not found (404).")
                else:
                    print(f"❌ An unexpected error occurred with the Gemini model: {error_message}")
                sys.exit(1)
        
        # This line should not be reachable if the loop exhausts
        return {
            "file_path": file_path, 
            "language": language, 
            "analysis": "Failed to get analysis after multiple retries.", 
            "status": "error"
        }
    
    def scan_file(self, file_path: str) -> Dict:
        """
        Scan a single file for security vulnerabilities
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            Dictionary containing vulnerability analysis results
        """
        
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file content with better encoding handling
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                self.logger.warning(f"Used fallback encoding for {file_path}")
            
            # Determine language from file extension
            language = self._detect_language(file_path)
            
            return self.scan_code_content(content, file_path, language)
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return {
                "file_path": file_path,
                "language": "unknown",
                "analysis": f"Error reading file: {str(e)}",
                "status": "error"
            }
    
    def scan_directory(self, directory_path: str, file_patterns: Optional[List[str]] = None, max_workers: int = 10) -> List[Dict]:
        """
        Scan all source files in a directory for vulnerabilities using parallel processing.
        
        Args:
            directory_path: Path to the directory to scan
            file_patterns: List of file patterns to include (e.g., ['*.py', '*.js'])
            max_workers: Maximum number of concurrent threads to use
            
        Returns:
            List of vulnerability analysis results
        """
        
        if file_patterns is None:
            file_patterns = self._load_file_extensions()
        
        # --- Exclusion Logic ---
        # AI_SAST_EXCLUDE_PATHS: Comma-separated paths to exclude from scanning (optional)
        # Example: "dist,build,vendor,docs,*.min.js"
        # Example: "node_modules,target,coverage,*.test.js"
        default_exclude_keywords = ['test', 'node_modules', 'e2e', 'cypress', 'local', 'jest', 'prettierrc', 'mock', 'log', 'png', 'script', 'mocks', '.git']
        exclude_paths_str = os.environ.get('AI_SAST_EXCLUDE_PATHS', '')
        custom_exclude_keywords = [path.strip() for path in exclude_paths_str.split(',') if path.strip()]
        
        all_exclude_keywords = default_exclude_keywords + custom_exclude_keywords

        if custom_exclude_keywords:
            print(f"ℹ️ Applying custom exclusion keywords: {', '.join(custom_exclude_keywords)}")
        print(f"ℹ️ Full list of exclusion keywords: {', '.join(all_exclude_keywords)}")

        def should_be_excluded(file_path: str) -> bool:
            """Check if a file path should be excluded based on keywords."""
            path_lower = file_path.lower()
            for keyword in all_exclude_keywords:
                if keyword.lower() in path_lower:
                    return True
            return False
        # --- End of Exclusion Logic ---

        all_files: List[str] = []
        excluded_files: List[str] = []
        for pattern in file_patterns:
            try:
                cmd = f"find {directory_path} -type f -name '{pattern}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                found_files = [os.path.relpath(p, directory_path) for p in result.stdout.strip().split('\n') if p]
                
                for f in found_files:
                    if should_be_excluded(f):
                        excluded_files.append(f)
                    else:
                        all_files.append(f)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Command failed for pattern '{pattern}': {e}")
        
        if excluded_files:
            print("\n--- Excluded Files & Folders ---")
            # Use set to get unique files and then sort for consistent output
            for file in sorted(list(set(excluded_files))):
                 print(f"- {file}")
            print("--------------------------------\n")

        print(f"Found {len(all_files)} files to scan.")
        
        scan_results: List[Dict] = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # We submit full paths to `scan_file`, but keep track of the relative path
            future_to_relpath = {
                executor.submit(self.scan_file, os.path.join(directory_path, rel_path)): rel_path 
                for rel_path in all_files
            }
            
            for future in as_completed(future_to_relpath):
                rel_path = future_to_relpath[future]
                try:
                    result = future.result()
                    # Override the absolute path with the correct relative path for reporting
                    result['file_path'] = rel_path
                    scan_results.append(result)
                except Exception as e:
                    print(f"Error scanning file {rel_path}: {e}")
                    scan_results.append({
                        "file_path": rel_path,
                        "language": "unknown",
                        "analysis": f"Failed to scan file: {e}",
                        "status": "error"
                    })
        
        return scan_results
    
    def scan_git_repository(self, repo_url: str, branch: str = "main") -> List[Dict]:
        """
        Clone and scan a Git repository for vulnerabilities
        
        Args:
            repo_url: URL of the Git repository
            branch: Branch to scan (default: main)
            
        Returns:
            List of vulnerability analysis results
        """
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repository
                print(f"🔄 Cloning repository: {repo_url}")
                clone_cmd = f"git clone --depth 1 --branch {branch} {repo_url} {temp_dir}/repo"
                result = subprocess.run(clone_cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    return [{
                        "file_path": repo_url,
                        "language": "git",
                        "analysis": f"Error cloning repository: {result.stderr}",
                        "status": "error"
                    }]
                
                # Scan the cloned repository
                repo_path = os.path.join(temp_dir, "repo")
                return self.scan_directory(repo_path)
                
            except Exception as e:
                return [{
                    "file_path": repo_url,
                    "language": "git",
                    "analysis": f"Error processing repository: {str(e)}",
                    "status": "error"
                }]
    
    def _detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Programming language name
        """
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.cs': 'csharp',
            '.sql': 'sql',
            '.sh': 'bash',
            '.graphql': 'graphql',
            '.ps1': 'powershell'
        }
        
        _, ext = os.path.splitext(file_path.lower())
        return extension_map.get(ext, 'text')
    
    def generate_report(self, scan_results: List[Dict], output_file: Optional[str] = None) -> str:
        """
        Generate a comprehensive security report
        
        Args:
            scan_results: List of scan results
            output_file: Optional output file path
            
        Returns:
            Formatted security report
        """
        
        report = []
        report.append("# Security Vulnerability Analysis Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary
        total_files = len(scan_results)
        successful_scans = sum(1 for r in scan_results if r['status'] == 'success')
        failed_scans = total_files - successful_scans
        
        report.append(f"## Summary")
        report.append(f"- Total files scanned: {total_files}")
        report.append(f"- Successful scans: {successful_scans}")
        report.append(f"- Failed scans: {failed_scans}")
        report.append("")
        
        # Individual file results
        for result in scan_results:
            report.append(f"## File: {result['file_path']}")
            report.append(f"**Language**: {result['language']}")
            report.append(f"**Status**: {result['status']}")
            report.append("")
            report.append("### Analysis:")
            report.append(result['analysis'])
            report.append("")
            report.append("-" * 50)
            report.append("")
        
        report_content = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📄 Report saved to: {output_file}")
        
        return report_content
    
    def _get_source_files(self, directory_path: str, file_patterns: Optional[List[str]] = None) -> List[str]:
        """
        Get all source files in a directory
        
        Args:
            directory_path: Path to the directory to scan
            file_patterns: List of file patterns to include
            
        Returns:
            List of file paths
        """
        if file_patterns is None:
            file_patterns = self._load_file_extensions()
        
        # Exclusion logic
        default_exclude_keywords = ['test', 'node_modules', '.git']
        exclude_paths_str = os.environ.get('AI_SAST_EXCLUDE_PATHS', '')
        custom_exclude_keywords = [path.strip() for path in exclude_paths_str.split(',') if path.strip()]
        all_exclude_keywords = default_exclude_keywords + custom_exclude_keywords

        def should_be_excluded(file_path: str) -> bool:
            path_lower = file_path.lower()
            for keyword in all_exclude_keywords:
                if keyword.lower() in path_lower:
                    return True
            return False

        all_files: List[str] = []
        for pattern in file_patterns:
            try:
                cmd = f"find {directory_path} -type f -name '{pattern}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                found_files = [p for p in result.stdout.strip().split('\n') if p]
                
                for f in found_files:
                    if not should_be_excluded(f):
                        all_files.append(f)
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Command failed for pattern '{pattern}': {e}")
        
        return all_files


def main():
    """
    Main function for command-line usage
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Security vulnerability scanner using Vertex AI")
    parser.add_argument("--file", type=str, help="Scan a single file")
    parser.add_argument("--directory", type=str, help="Scan all files in a directory")
    parser.add_argument("--repo", type=str, help="Scan a Git repository (requires proper access)")
    parser.add_argument("--branch", type=str, default="main", help="Git branch to scan (default: main)")
    parser.add_argument("--output", type=str, help="Output file for the report")
    parser.add_argument("--max-workers", type=int, default=10, help="Number of parallel threads for directory scanning")
    
    args = parser.parse_args()
    
    scanner = SecurityScanner()
    results: List[Dict] = []
    
    if args.file:
        print(f"🔍 Scanning file: {args.file}")
        results = [scanner.scan_file(args.file)]
    elif args.directory:
        print(f"🔍 Scanning directory: {args.directory}")
        results = scanner.scan_directory(args.directory, max_workers=args.max_workers)
    elif args.repo:
        print(f"🔍 Scanning repository: {args.repo}")
        results = scanner.scan_git_repository(args.repo, args.branch)
    else:
        print("❌ Please specify --file, --directory, or --repo")
        return
    
    # Generate report
    report = scanner.generate_report(results, args.output)
    
    if not args.output:
        print("\n" + report)


if __name__ == "__main__":
    main()

