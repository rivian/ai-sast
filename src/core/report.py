#!/usr/bin/env python3
"""
HTML Report Generator for Security Scan Results
Generates beautiful HTML reports that can be displayed in web browsers.
"""

import os
import re
import html
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import hashlib

class HTMLReportGenerator:
    """Generate HTML reports for security scan results."""
    
    SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]
    
    def __init__(self):
        self.template = self._get_html_template()
    
    def _get_allowed_severities(self) -> List[str]:
        """Gets the list of severities to include in the report from an env var."""
        # AI_SAST_SEVERITY: Comma-separated list of severities to include in PR comments
        # Example: "critical,high" (default - only show critical and high in PRs)
        # Example: "critical,high,medium,low" (show all severities)
        # Example: "critical" (only show critical issues)
        severities_str = os.environ.get('AI_SAST_SEVERITY', 'critical,high')
        allowed = [s.strip().capitalize() for s in severities_str.split(',') if s.strip()]
        # Ensure the order is correct
        return [s for s in self.SEVERITY_ORDER if s in allowed]

    def _parse_line_number(self, location_str: str) -> Optional[int]:
        """Extracts the first number from a location string like 'Line 25'."""
        if not location_str:
            return None
        match = re.search(r'(?:line|lines)\\s*(\\d+)', location_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _create_hyperlink(self, repo_url: str, ref_name: str, file_path: str, line_number: Optional[int]) -> Optional[str]:
        """Creates a link to a specific file and line (GitHub or GitLab compatible)."""
        if not all([repo_url, ref_name, file_path]):
            return None
        
        # Ensure repo_url ends with .git so we can strip it consistently
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        
        # Detect platform and create appropriate link
        if 'github.com' in repo_url:
            # GitHub format: /blob/{ref}/{path}#L{line}
            link = f"{repo_url}/blob/{ref_name}/{file_path}"
            if line_number:
                link += f"#L{line_number}"
        elif 'gitlab.com' in repo_url or '/-/' in repo_url:
            # GitLab format: /-/blob/{ref}/{path}#L{line}
            link = f"{repo_url}/-/blob/{ref_name}/{file_path}"
            if line_number:
                link += f"#L{line_number}"
        else:
            # Generic format (GitHub-style as default)
            link = f"{repo_url}/blob/{ref_name}/{file_path}"
            if line_number:
                link += f"#L{line_number}"
        
        return link

    def _generate_vuln_id(self, file_path: str, issue: str, location: str) -> str:
        """Generates a unique and stable ID for a vulnerability."""
        unique_string = f"{file_path}-{issue}-{location}"
        return hashlib.sha1(unique_string.encode()).hexdigest()[:8]

    def _parse_vulnerabilities(self, analysis_text: str) -> Dict[str, List[Dict]]:
        """Parse vulnerability details from the analysis text."""
        vulnerabilities = {
            "Critical": [], "High": [], "Medium": [], "Low": []
        }
        pattern = re.compile(
            r"-\s*\*\*Vulnerability Level\*\*:\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\n"
            r"-\s*\*\*Issue\*\*:\s*(.*?)\n"
            r"-\s*\*\*Location\*\*:\s*(.*?)\n"
            r"-\s*\*\*Risk\*\*:\s*(.*?)\n"
            r"-\s*\*\*Fix\*\*:\s*(.*?)\n",
            re.DOTALL | re.IGNORECASE
        )

        for match in pattern.finditer(analysis_text):
            level, issue, location, risk, fix = match.groups()
            level = level.strip().capitalize()
            
            vulnerabilities[level].append({
                "issue": issue.strip(),
                "location": location.strip(),
                "risk": risk.strip(),
                "fix": fix.strip(),
            })
        return vulnerabilities

    def _process_results_by_severity(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Processes raw scan results and groups them by severity."""
        vulnerabilities_by_severity = {
            "Critical": [], "High": [], "Medium": [], "Low": []
        }
        for result in results:
            analysis_text = result.get('analysis', '')
            parsed_vulns = self._parse_vulnerabilities(analysis_text)
            for severity, vulns in parsed_vulns.items():
                for vuln in vulns:
                    vuln['file_path'] = result.get('file_path', 'Unknown file')
                    vulnerabilities_by_severity[severity].append(vuln)
        return vulnerabilities_by_severity

    def generate_report(self, results: List[Dict[str, Any]], repo_url: str, 
                       ref_name: str, output_file: Optional[str] = None,
                       validated_vuln_ids: Optional[Set[str]] = None,
                       validator_reasoning: Optional[Dict[str, str]] = None) -> str:
        """
        Generate an HTML report from security scan results.
        
        Args:
            results: List of security scan results
            repo_url: Repository URL that was scanned
            ref_name: The branch name or commit SHA for generating links
            output_file: Output file path (optional)
            validated_vuln_ids: If set (e.g. from validator LLM), only include these findings in the report.
            validator_reasoning: Optional vuln_id -> proof text to show per finding.
            
        Returns:
            HTML content as string
        """
        
        if validated_vuln_ids is not None:
            print(f"ℹ️  Generating HTML report with validated findings only.")
        else:
            print(f"ℹ️  Generating full HTML report with all severities.")
        
        vulnerabilities_by_severity = self._process_results_by_severity(results)
        if validated_vuln_ids is not None:
            vulnerabilities_by_severity = {
                key: [v for v in vulns if self._generate_vuln_id(v.get('file_path', ''), v.get('issue', ''), v.get('location', '')) in validated_vuln_ids]
                for key, vulns in vulnerabilities_by_severity.items()
            }
            vulnerabilities_by_severity = {k: v for k, v in vulnerabilities_by_severity.items() if v}
        
        summary = {level: len(vulns) for level, vulns in vulnerabilities_by_severity.items()}
        summary["Total"] = sum(summary.values())
        
        results_html = self._generate_severity_results_html(vulnerabilities_by_severity, repo_url, ref_name, validator_reasoning=validator_reasoning)
        
        html_content = self.template.format(
            repo_url=html.escape(repo_url),
            scan_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_files=len(results),
            total_vulnerabilities=summary["Total"],
            critical_count=summary.get("Critical", 0),
            high_count=summary.get("High", 0),
            medium_count=summary.get("Medium", 0),
            low_count=summary.get("Low", 0),
            severity_results=results_html
        )
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
    def generate_markdown_report(self, results: List[Dict[str, Any]], report_title: str, repo_url: str, ref_name: str, report_context_text: Optional[str] = None, validated_vuln_ids: Optional[Set[str]] = None, validator_reasoning: Optional[Dict[str, str]] = None) -> str:
        """Generates a markdown-formatted report suitable for GitHub/GitLab comments.
        If validated_vuln_ids is provided, only findings whose vuln_id is in that set are included (e.g. validator true positives only).
        If validator_reasoning is provided (vuln_id -> proof text), adds a "Validator proof" line after Risk in the details section.
        """
        allowed_severities = self._get_allowed_severities()
        print(f"ℹ️  Generating markdown report for severities: {', '.join(allowed_severities)}")

        vulnerabilities_by_severity = self._process_results_by_severity(results)
        
        # Filter the vulnerabilities based on the allowed severities
        filtered_vulns = {
            key: vulns for key, vulns in vulnerabilities_by_severity.items() 
            if key in allowed_severities
        }

        # If validator was used, keep only findings that were validated as true positive
        if validated_vuln_ids is not None:
            filtered_vulns = {
                key: [v for v in vulns if self._generate_vuln_id(v.get('file_path', ''), v.get('issue', ''), v.get('location', '')) in validated_vuln_ids]
                for key, vulns in filtered_vulns.items()
            }
            filtered_vulns = {k: v for k, v in filtered_vulns.items() if v}

        summary = {level: len(vulns) for level, vulns in filtered_vulns.items()}
        summary["Total"] = sum(summary.values())

        if summary['Total'] == 0:
            original_total = sum(len(v) for v in vulnerabilities_by_severity.values())
            if original_total > 0 and validated_vuln_ids is not None:
                return f"✅ **{html.escape(report_title)}**: No findings were validated as true positive by the validator. All reported issues were filtered out."
            if original_total > 0:
                return f"✅ **{html.escape(report_title)}**: No vulnerabilities found matching the severity filter: `{os.environ.get('AI_SAST_SEVERITY', 'critical,high')}`."
            return f"✅ **{html.escape(report_title)}**: No new vulnerabilities were found."

        md_parts = [f"### {html.escape(report_title)}"]
        md_parts.append(f"**{summary.get('Total', 0)}** potential issue(s) found.")
        md_parts.append("\n> 💡 **Help us improve!** Use the checkboxes below to mark each finding as a true positive (✅) or false positive (❌).")
        md_parts.append("> Your feedback helps train the AI to be more accurate over time.\n")
        md_parts.append("| Severity | Count |")
        md_parts.append("|---|---|")
        if summary.get('Critical', 0) > 0: md_parts.append(f"| 🚨 Critical | {summary.get('Critical')} |")
        if summary.get('High', 0) > 0: md_parts.append(f"| 🔥 High | {summary.get('High')} |")
        if summary.get('Medium', 0) > 0: md_parts.append(f"| ⚠️ Medium | {summary.get('Medium')} |")
        if summary.get('Low', 0) > 0: md_parts.append(f"| ℹ️ Low | {summary.get('Low')} |")
        md_parts.append("\n---\n")
        
        for severity in self.SEVERITY_ORDER:
            vulns = filtered_vulns.get(severity, [])
            if not vulns: continue
            
            md_parts.append(f"\n<details><summary>📄 **{severity} Issues ({len(vulns)})**</summary>\n")

            for vuln in vulns:
                file_path_raw = vuln.get('file_path', 'Unknown File')
                location_raw = vuln.get('location', 'N/A')
                issue_raw = vuln.get('issue', 'N/A')
                line_num = self._parse_line_number(location_raw)
                
                # Generate unique ID for this finding
                vuln_id = self._generate_vuln_id(file_path_raw, issue_raw, location_raw)

                link = self._create_hyperlink(repo_url, ref_name, file_path_raw, line_num)
                
                file_display_text = f"{html.escape(file_path_raw)}:{line_num}" if line_num else html.escape(file_path_raw)
                file_display = f"[`{file_display_text}`]({link})" if link else f"`{html.escape(file_path_raw)}`"
                
                issue = html.escape(issue_raw)
                risk = html.escape(vuln.get('risk', 'N/A'))
                fix = html.escape(vuln.get('fix', 'N/A'))
                cvss_vector = vuln.get('cvss_vector', 'N/A')

                md_parts.append("\n---\n")
                
                # Add unique ID (hidden comment for tracking)
                md_parts.append(f"<!-- vuln-id: {vuln_id} -->\n")
                
                # Add interactive feedback checkboxes (each on separate line)
                md_parts.append(f"- [ ] ✅ True Positive\n")
                md_parts.append(f"- [ ] ❌ False Positive\n")
                
                md_parts.append(f"**ID**: `{vuln_id}`")
                md_parts.append(f"**Severity**: {severity}")
                md_parts.append(f"**Issue**: {issue}")
                md_parts.append(f"**Location**: {file_display}")
                md_parts.append(f"**CVSS Vector**: `{html.escape(cvss_vector)}`")
                
                details = f"<details><summary>📋 Click to see details, risk, and remediation</summary>"
                details += f"\n\n**Risk:**\n{risk}\n"
                if validator_reasoning and vuln_id in validator_reasoning and validator_reasoning[vuln_id]:
                    proof = html.escape(validator_reasoning[vuln_id].strip())
                    details += f"\n**Validator proof:** {proof}\n"
                details += f"\n**Remediation:**\n```\n{fix}\n```\n"
                details += "</details>"
                md_parts.append(details)
                
                md_parts.append("\n**💬 Optional Comment**: (Reply to this PR to explain your feedback)")
            
            md_parts.append("\n</details>\n")
            
        return '\n'.join(md_parts)
    
    def _generate_severity_results_html(self, vulnerabilities_by_severity: Dict[str, List[Dict]], repo_url: str, ref_name: str, validator_reasoning: Optional[Dict[str, str]] = None) -> str:
        """Generate HTML for results grouped by severity. Optionally show validator proof per finding."""
        html_parts = []
        
        severity_map = {
            "Critical": {"class": "critical", "icon": "fa-skull-crossbones"},
            "High": {"class": "high", "icon": "fa-exclamation-triangle"},
            "Medium": {"class": "medium", "icon": "fa-exclamation-circle"},
            "Low": {"class": "low", "icon": "fa-info-circle"},
        }

        for severity in self.SEVERITY_ORDER:
            vulns = vulnerabilities_by_severity.get(severity, [])
            if not vulns:
                continue

            map_info = severity_map[severity]
            
            vuln_details_html = ""
            for vuln in vulns:
                file_path_raw = vuln['file_path']
                location_raw = vuln['location']
                line_num = self._parse_line_number(location_raw)
                link = self._create_hyperlink(repo_url, ref_name, file_path_raw, line_num)
                
                file_display_text = f"{html.escape(file_path_raw)}:{line_num}" if line_num else html.escape(file_path_raw)
                file_display = f'<a href="{link}" target="_blank">{file_display_text}</a>' if link else html.escape(file_path_raw)
                location_display = html.escape(location_raw)
                proof_html = ""
                if validator_reasoning:
                    vuln_id = self._generate_vuln_id(file_path_raw, vuln.get('issue', ''), location_raw)
                    if vuln_id in validator_reasoning and validator_reasoning[vuln_id]:
                        proof_html = f"<p><strong>Validator proof:</strong> {html.escape(validator_reasoning[vuln_id].strip())}</p>"

                vuln_details_html += f"""
                    <div class="vuln-item">
                        <p><strong>File:</strong> {file_display}</p>
                        <p><strong>Issue:</strong> {html.escape(vuln['issue'])}</p>
                        <p><strong>Location:</strong> {location_display}</p>
                        <p><strong>Risk:</strong> {html.escape(vuln['risk'])}</p>
                        {proof_html}
                        <p><strong>Fix:</strong> <pre>{html.escape(vuln['fix'])}</pre></p>
                    </div>
                """
            
            html_parts.append(f"""
                <div class="severity-section">
                    <div class="severity-header {map_info['class']}">
                        <h3><i class="fas {map_info['icon']}"></i> {severity} ({len(vulns)})</h3>
                    </div>
                    <div class="analysis-content">
                        {vuln_details_html}
                    </div>
                </div>
            """)
        
        return '\n'.join(html_parts)
    
    def _get_html_template(self) -> str:
        """Get the HTML template for security reports."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Scan Report</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f7f6; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: #2c3e50; color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin-bottom: 10px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; padding: 20px; text-align: center; }}
        .summary-item {{ padding: 20px; border-radius: 10px; color: white; font-size: 1.2em; }}
        .summary-item span {{ display: block; font-size: 2em; font-weight: bold; }}
        .summary-item.critical {{ background: #dc3545; }}
        .summary-item.high {{ background: #fd7e14; }}
        .summary-item.medium {{ background: #ffc107; }}
        .summary-item.low {{ background: #17a2b8; }}
        .results-container {{ padding: 30px; }}
        .severity-section {{ background: #fff; margin-bottom: 20px; border-radius: 10px; overflow: hidden; border: 1px solid #e0e0e0; }}
        .severity-header {{ padding: 15px 20px; color: white; display: flex; align-items: center; }}
        .severity-header h3 {{ margin: 0; font-size: 1.4em; }}
        .severity-header .fas {{ margin-right: 10px; font-size: 1.2em; }}
        .severity-header.critical {{ background-color: #dc3545; }}
        .severity-header.high {{ background-color: #fd7e14; }}
        .severity-header.medium {{ background-color: #ffc107; }}
        .severity-header.low {{ background-color: #17a2b8; }}
        .analysis-content {{ padding: 20px; background: #fdfdfd; }}
        .vuln-item {{ border: 1px solid #eee; background: #fff; padding: 15px; margin-bottom: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .vuln-item p {{ margin-bottom: 8px; }}
        .vuln-item pre {{ background: #2d2d2d; color: #f2f2f2; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-family: 'Courier New', Courier, monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Security Scan Report</h1>
            <p>Repository: <a href="{repo_url}" style="color: #4db8ff;">{repo_url}</a></p>
            <p>Scan Date: {scan_date}</p>
        </div>
        <div class="summary-grid">
            <div class="summary-item critical"><span>{critical_count}</span> Critical</div>
            <div class="summary-item high"><span>{high_count}</span> High</div>
            <div class="summary-item medium"><span>{medium_count}</span> Medium</div>
            <div class="summary-item low"><span>{low_count}</span> Low</div>
        </div>
        <div class="results-container">
            {severity_results}
        </div>
    </div>
</body>
</html>
        """

def main():
    """Example usage for testing the report generator."""
    # Dummy data for testing
    mock_results = [
        {
            "file_path": "src/user_controller.py",
            "analysis": """
- **Vulnerability Level**: CRITICAL
- **Issue**: SQL Injection <script>alert('XSS on issue')</script>
- **Location**: Line 42
- **Risk**: Full database compromise.
- **Fix**: Use parameterized queries.

- **Vulnerability Level**: MEDIUM
- **Issue**: Hardcoded API Key
- **Location**: Line 15
- **Risk**: Key may be exposed.
- **Fix**: Use environment variables.
            """
        },
        {
            "file_path": "src/utils.js",
            "analysis": """
- **Vulnerability Level**: LOW
- **Issue**: Use of deprecated function `eval()`
- **Location**: Line 101
- **Risk**: Potential for code injection if input is not sanitized.
- **Fix**: Avoid `eval()` and use safer alternatives like `JSON.parse()`.
            """
        },
        {
            "file_path": "<script>alert('XSS on file path')</script>",
            "analysis": "File appears to be secure."
        }
    ]
    
    generator = HTMLReportGenerator()
    generator.generate_report(
        results=mock_results,
        repo_url="https://github.com/example/repo.git",
        ref_name="main",
        output_file="security_report.html"
    )
    
    print("HTML report generated successfully!")

if __name__ == "__main__":
    main() 