#!/usr/bin/env python3
"""
Notifications Client for AI-SAST

Sends scan results and notifications to external systems like Slack, Microsoft Teams, 
Discord, or custom webhooks.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import urllib.request
import urllib.error
import hmac
import hashlib

logger = logging.getLogger(__name__)


class WebhookClient:
    """
    Client for sending notifications about scan results to external systems
    
    Supports Slack, Microsoft Teams, Discord, and generic webhooks
    """
    
    def __init__(self):
        """
        Initialize webhook client
        
        Environment Variables:
            AI_SAST_WEBHOOK_URL: Webhook endpoint URL
            AI_SAST_WEBHOOK_SECRET: Optional secret for HMAC signature
            AI_SAST_WEBHOOK_TYPE: Type of webhook (slack, teams, discord, generic)
        """
        # AI_SAST_WEBHOOK_URL: Webhook endpoint URL
        # Example: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        # Example: "https://your-system.com/api/scan-results"
        self.webhook_url = os.environ.get('AI_SAST_WEBHOOK_URL')
        
        # AI_SAST_WEBHOOK_SECRET: Secret for HMAC signature (optional)
        # Example: "your-secret-key-for-verification"
        self.webhook_secret = os.environ.get('AI_SAST_WEBHOOK_SECRET')
        
        # AI_SAST_WEBHOOK_TYPE: Type of webhook formatting
        # Options: "slack", "teams", "discord", "generic" (default)
        self.webhook_type = os.environ.get('AI_SAST_WEBHOOK_TYPE', 'generic').lower()
        
        self.is_configured = bool(self.webhook_url)
        
        if not self.is_configured:
            logger.info("Webhook not configured - skipping webhook notifications")
    
    def send_scan_completed(
        self,
        repository: str,
        pr_number: Optional[int],
        scan_summary: Dict[str, int],
        report_url: Optional[str] = None,
        scan_duration: Optional[float] = None
    ) -> bool:
        """
        Send notification when scan is completed
        
        Args:
            repository: Repository name (e.g., "myorg/myapp")
            pr_number: Pull request number (None for full scans)
            scan_summary: Dictionary with counts by severity (critical, high, medium, low)
            report_url: URL to the full report
            scan_duration: Scan duration in seconds
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.is_configured:
            return False
        
        event_data = {
            "event": "scan_completed",
            "repository": repository,
            "pr_number": pr_number,
            "scan_type": "pr_diff" if pr_number else "full_repository",
            "scan_summary": scan_summary,
            "report_url": report_url,
            "scan_duration_seconds": scan_duration,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        total_issues = sum(scan_summary.values())
        critical_high = scan_summary.get('critical', 0) + scan_summary.get('high', 0)
        
        # Format message based on webhook type
        if self.webhook_type == 'slack':
            payload = self._format_slack_message(event_data, total_issues, critical_high)
        elif self.webhook_type == 'teams':
            payload = self._format_teams_message(event_data, total_issues, critical_high)
        elif self.webhook_type == 'discord':
            payload = self._format_discord_message(event_data, total_issues, critical_high)
        else:
            payload = event_data
        
        return self._send_webhook(payload)
    
    def send_critical_alert(
        self,
        repository: str,
        pr_number: Optional[int],
        vulnerability: Dict[str, Any]
    ) -> bool:
        """
        Send immediate alert for critical vulnerability
        
        Args:
            repository: Repository name
            pr_number: Pull request number
            vulnerability: Vulnerability details
            
        Returns:
            True if notification sent successfully
        """
        if not self.is_configured:
            return False
        
        event_data = {
            "event": "critical_vulnerability_detected",
            "repository": repository,
            "pr_number": pr_number,
            "vulnerability": {
                "severity": vulnerability.get('severity'),
                "issue": vulnerability.get('issue'),
                "file": vulnerability.get('file'),
                "location": vulnerability.get('location'),
                "cvss_vector": vulnerability.get('cvss_vector')
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if self.webhook_type == 'slack':
            payload = self._format_slack_alert(event_data)
        elif self.webhook_type == 'teams':
            payload = self._format_teams_alert(event_data)
        elif self.webhook_type == 'discord':
            payload = self._format_discord_alert(event_data)
        else:
            payload = event_data
        
        return self._send_webhook(payload)
    
    def send_scan_failed(
        self,
        repository: str,
        pr_number: Optional[int],
        error_message: str
    ) -> bool:
        """
        Send notification when scan fails
        
        Args:
            repository: Repository name
            pr_number: Pull request number
            error_message: Error details
            
        Returns:
            True if notification sent successfully
        """
        if not self.is_configured:
            return False
        
        event_data = {
            "event": "scan_failed",
            "repository": repository,
            "pr_number": pr_number,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return self._send_webhook(event_data)
    
    def send_feedback_received(
        self,
        repository: str,
        pr_number: int,
        feedback_summary: Dict[str, int]
    ) -> bool:
        """
        Send notification when developer feedback is received
        
        Args:
            repository: Repository name
            pr_number: Pull request number
            feedback_summary: Dictionary with feedback counts (true_positives, false_positives)
            
        Returns:
            True if notification sent successfully
        """
        if not self.is_configured:
            return False
        
        event_data = {
            "event": "feedback_received",
            "repository": repository,
            "pr_number": pr_number,
            "feedback_summary": feedback_summary,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return self._send_webhook(event_data)
    
    def _format_slack_message(self, event_data: Dict, total_issues: int, critical_high: int) -> Dict:
        """Format message for Slack"""
        repo = event_data['repository']
        pr_num = event_data['pr_number']
        summary = event_data['scan_summary']
        
        color = "danger" if critical_high > 0 else "warning" if total_issues > 0 else "good"
        
        pr_text = f"PR #{pr_num}" if pr_num else "Full Repository Scan"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 AI-SAST Scan Complete: {repo}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{pr_text}*\n{total_issues} security issue(s) found"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Critical:* {summary.get('critical', 0)}"},
                    {"type": "mrkdwn", "text": f"*High:* {summary.get('high', 0)}"},
                    {"type": "mrkdwn", "text": f"*Medium:* {summary.get('medium', 0)}"},
                    {"type": "mrkdwn", "text": f"*Low:* {summary.get('low', 0)}"}
                ]
            }
        ]
        
        if event_data.get('report_url'):
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Full Report"},
                        "url": event_data['report_url']
                    }
                ]
            })
        
        return {"blocks": blocks, "attachments": [{"color": color}]}
    
    def _format_slack_alert(self, event_data: Dict) -> Dict:
        """Format critical alert for Slack"""
        vuln = event_data['vulnerability']
        repo = event_data['repository']
        pr_num = event_data['pr_number']
        
        pr_text = f"PR #{pr_num}" if pr_num else "Repository"
        
        return {
            "text": f":rotating_light: *CRITICAL VULNERABILITY DETECTED* :rotating_light:",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Critical Security Alert"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Repository:* {repo}\n*{pr_text}*\n*Severity:* {vuln['severity']}\n*Issue:* {vuln['issue']}\n*File:* {vuln['file']}"
                    }
                }
            ],
            "attachments": [{"color": "danger"}]
        }
    
    def _format_teams_message(self, event_data: Dict, total_issues: int, critical_high: int) -> Dict:
        """Format message for Microsoft Teams"""
        repo = event_data['repository']
        pr_num = event_data['pr_number']
        summary = event_data['scan_summary']
        
        theme_color = "FF0000" if critical_high > 0 else "FFA500" if total_issues > 0 else "00FF00"
        pr_text = f"PR #{pr_num}" if pr_num else "Full Repository Scan"
        
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": f"AI-SAST Scan: {repo}",
            "sections": [{
                "activityTitle": f"🤖 AI-SAST Scan Complete",
                "activitySubtitle": f"{repo} - {pr_text}",
                "facts": [
                    {"name": "Critical", "value": str(summary.get('critical', 0))},
                    {"name": "High", "value": str(summary.get('high', 0))},
                    {"name": "Medium", "value": str(summary.get('medium', 0))},
                    {"name": "Low", "value": str(summary.get('low', 0))},
                    {"name": "Total Issues", "value": str(total_issues)}
                ],
                "markdown": True
            }]
        }
        
        if event_data.get('report_url'):
            card["potentialAction"] = [{
                "@type": "OpenUri",
                "name": "View Full Report",
                "targets": [{"os": "default", "uri": event_data['report_url']}]
            }]
        
        return card
    
    def _format_teams_alert(self, event_data: Dict) -> Dict:
        """Format critical alert for Teams"""
        vuln = event_data['vulnerability']
        repo = event_data['repository']
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": "Critical Vulnerability Detected",
            "sections": [{
                "activityTitle": "🚨 CRITICAL SECURITY ALERT",
                "activitySubtitle": repo,
                "facts": [
                    {"name": "Severity", "value": vuln['severity']},
                    {"name": "Issue", "value": vuln['issue']},
                    {"name": "File", "value": vuln['file']},
                    {"name": "CVSS", "value": vuln.get('cvss_vector', 'N/A')}
                ]
            }]
        }
    
    def _format_discord_message(self, event_data: Dict, total_issues: int, critical_high: int) -> Dict:
        """Format message for Discord"""
        repo = event_data['repository']
        pr_num = event_data['pr_number']
        summary = event_data['scan_summary']
        
        color = 0xFF0000 if critical_high > 0 else 0xFFA500 if total_issues > 0 else 0x00FF00
        pr_text = f"PR #{pr_num}" if pr_num else "Full Repository Scan"
        
        embed = {
            "embeds": [{
                "title": f"🤖 AI-SAST Scan Complete",
                "description": f"**{repo}** - {pr_text}",
                "color": color,
                "fields": [
                    {"name": "Critical", "value": str(summary.get('critical', 0)), "inline": True},
                    {"name": "High", "value": str(summary.get('high', 0)), "inline": True},
                    {"name": "Medium", "value": str(summary.get('medium', 0)), "inline": True},
                    {"name": "Low", "value": str(summary.get('low', 0)), "inline": True},
                    {"name": "Total Issues", "value": str(total_issues), "inline": False}
                ],
                "timestamp": event_data['timestamp']
            }]
        }
        
        if event_data.get('report_url'):
            embed["embeds"][0]["url"] = event_data['report_url']
        
        return embed
    
    def _format_discord_alert(self, event_data: Dict) -> Dict:
        """Format critical alert for Discord"""
        vuln = event_data['vulnerability']
        repo = event_data['repository']
        
        return {
            "embeds": [{
                "title": "🚨 CRITICAL SECURITY ALERT",
                "description": repo,
                "color": 0xFF0000,
                "fields": [
                    {"name": "Severity", "value": vuln['severity'], "inline": True},
                    {"name": "Issue", "value": vuln['issue'], "inline": False},
                    {"name": "File", "value": vuln['file'], "inline": False}
                ],
                "timestamp": event_data['timestamp']
            }]
        }
    
    def _send_webhook(self, payload: Dict) -> bool:
        """
        Send webhook request with optional HMAC signature
        
        Args:
            payload: JSON payload to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Add HMAC signature if secret is configured
            if self.webhook_secret:
                signature = hmac.new(
                    self.webhook_secret.encode('utf-8'),
                    data,
                    hashlib.sha256
                ).hexdigest()
                req.add_header('X-AI-SAST-Signature', f'sha256={signature}')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"✅ Webhook notification sent successfully")
                    return True
                else:
                    logger.warning(f"⚠️ Webhook returned status {response.status}")
                    return False
                    
        except urllib.error.HTTPError as e:
            logger.error(f"❌ Webhook HTTP error: {e.code} - {e.reason}")
            return False
        except urllib.error.URLError as e:
            logger.error(f"❌ Webhook URL error: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"❌ Webhook error: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    # Test webhook
    client = WebhookClient()
    
    if client.is_configured:
        success = client.send_scan_completed(
            repository="myorg/myapp",
            pr_number=123,
            scan_summary={"critical": 2, "high": 5, "medium": 10, "low": 3},
            report_url="https://github.com/myorg/myapp/actions/runs/123",
            scan_duration=45.2
        )
        print(f"Webhook test: {'Success' if success else 'Failed'}")
    else:
        print("Webhook not configured. Set AI_SAST_WEBHOOK_URL to test.")

