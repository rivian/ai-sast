#!/usr/bin/env python3
"""
Vector Client for Security Event Logging

This is a generic client for sending security events to a vector/log aggregator endpoint.
Compatible with Splunk HEC, Vector, and other HTTP event collectors.

Configure via environment variables to connect to your log aggregation service.
"""

import requests
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union


def get_current_timestamp() -> str:
    """Get the current UTC timestamp in a formatted string."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def send_security_event(
    repo_url: str,
    target_url: str, 
    category: str,
    message: str,
    assertion_condition: Union[bool, str],
    vuln_id: str = "",
    status: str = "",
    issue: str = "",
    severity: str = "",
    file_path: str = "",
    location: str = "",
    cvss_score: str = "",
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Log security events to the configured vector endpoint.
    
    Args:
        repo_url: Repository URL being scanned
        target_url: Target URL or severity level
        category: Category of the security scan (e.g., "AI-SAST")
        message: Event message/description
        assertion_condition: Test result (True/False or 'Success'/'Fail')
        vuln_id: Vulnerability ID
        status: Vulnerability status (e.g., "Needs Triage", "False Positive", "Confirmed")
        issue: Issue description
        severity: Severity level (e.g., "CRITICAL", "HIGH", "MEDIUM", "LOW")
        file_path: Path to the file with the vulnerability
        location: Location in the file (e.g., "Line 42")
        cvss_score: Numeric CVSS score (e.g., "8.2")
        details: Additional custom fields as dictionary
    
    Returns:
        True if successfully sent, False otherwise
    """
    
    # AI_SAST_VECTOR_URL: Vector/log aggregator endpoint URL
    # Example: "https://splunk.company.com/services/collector"
    # Example: "vector.company.com" (will add http:// and port automatically)
    # Example: "https://logs.company.com:8088/collector"
    vector_endpoint = os.environ.get("AI_SAST_VECTOR_URL")
    
    # AI_SAST_VECTOR_TOKEN: Authentication token for the vector endpoint
    # Example: "Splunk ABC123-DEF456-GHI789" (Splunk HEC token)
    # Example: "Bearer eyJhbGciOiJIUzI1NiIs..." (JWT token)
    vector_token = os.environ.get("AI_SAST_VECTOR_TOKEN")
    
    if not vector_endpoint or not vector_token:
        # Silently skip if logging is not configured
        return False
    
    # Format the endpoint URL
    # Support both raw endpoint and host:port format
    if not vector_endpoint.startswith('http'):
        endpoint_url = f"http://{vector_endpoint}:8088/services/collector"
    else:
        endpoint_url = vector_endpoint
    
    # Convert boolean assertion to string
    if isinstance(assertion_condition, bool):
        assertion_result = 'Success' if assertion_condition else 'Fail'
    else:
        assertion_result = str(assertion_condition)
    
    # Prepare the payload - all data in main JSON structure
    event_data = {
        "repo": repo_url,
        "target": target_url,
        "category": category,
        "test": message,
        "assertion": assertion_result,
        "timestamp": get_current_timestamp()
    }

    # Add optional fields directly to the main JSON structure if provided
    if vuln_id:
        event_data['vuln_id'] = vuln_id
    if status:
        event_data['status'] = status
    if issue:
        event_data['issue'] = issue
    if severity:
        event_data['severity'] = severity
    if file_path:
        event_data['file_path'] = file_path
    if location:
        event_data['location'] = location
    if cvss_score:
        event_data['cvss_score'] = cvss_score
    
    # Include additional details if provided
    if details:
        for key, value in details.items():
            if key not in event_data:  # Don't override explicit parameters
                event_data[key] = value
    
    # Try both Splunk HEC format and direct format
    payload_splunk = {"event": event_data}
    payload_direct = event_data
    
    # Use the Splunk HEC format by default (most compatible)
    payload = payload_splunk
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Splunk {vector_token}"
    }
    
    try:
        # Send data to vector endpoint
        response = requests.post(
            endpoint_url, 
            json=payload, 
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        # Try direct format as fallback
        try:
            response = requests.post(
                endpoint_url, 
                json=payload_direct, 
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            # Silently fail - don't block scans due to logging issues
            return False


class VectorClient:
    """
    Client for sending security events to a vector/log aggregation endpoint.
    
    Example usage:
        client = VectorClient()
        client.log_vulnerability(
            repo_url="https://github.com/org/repo",
            file_path="src/app.py",
            severity="HIGH",
            issue="SQL Injection",
            status="Needs Triage"
        )
    """
    
    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize the Vector client.
        
        Args:
            endpoint: Vector endpoint URL (or set AI_SAST_VECTOR_URL env var)
            token: Authentication token (or set AI_SAST_VECTOR_TOKEN env var)
        """
        self.endpoint = endpoint or os.environ.get("AI_SAST_VECTOR_URL")
        self.token = token or os.environ.get("AI_SAST_VECTOR_TOKEN")
        self.is_configured = bool(self.endpoint and self.token)
    
    def log_vulnerability(
        self,
        repo_url: str,
        file_path: str,
        severity: str,
        issue: str,
        status: str = "Needs Triage",
        vuln_id: str = "",
        location: str = "",
        cvss_score: str = "",
        **kwargs
    ) -> bool:
        """
        Log a vulnerability finding.
        
        Args:
            repo_url: Repository URL
            file_path: File containing the vulnerability
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            issue: Description of the issue
            status: Status of the vulnerability
            vuln_id: Unique vulnerability identifier
            location: Location in file (e.g., "Line 42")
            cvss_score: CVSS score
            **kwargs: Additional custom fields
        
        Returns:
            True if logged successfully
        """
        return send_security_event(
            repo_url=repo_url,
            target_url=severity,
            category="AI-SAST",
            message=f"Vulnerability: {issue} in {file_path}",
            assertion_condition=False,  # Vulnerability found = test failed
            vuln_id=vuln_id,
            status=status,
            issue=issue,
            severity=severity,
            file_path=file_path,
            location=location,
            cvss_score=cvss_score,
            details=kwargs
        )
    
    def log_scan_complete(
        self,
        repo_url: str,
        total_files: int,
        vulnerabilities_found: int,
        **kwargs
    ) -> bool:
        """
        Log scan completion event.
        
        Args:
            repo_url: Repository URL
            total_files: Number of files scanned
            vulnerabilities_found: Number of vulnerabilities found
            **kwargs: Additional custom fields
        
        Returns:
            True if logged successfully
        """
        return send_security_event(
            repo_url=repo_url,
            target_url="scan_complete",
            category="AI-SAST",
            message=f"Scan complete: {total_files} files scanned, {vulnerabilities_found} vulnerabilities found",
            assertion_condition=vulnerabilities_found == 0,
            details={
                "total_files": total_files,
                "vulnerabilities_found": vulnerabilities_found,
                **kwargs
            }
        )


def main():
    """Example usage and testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Vector client")
    parser.add_argument("--endpoint", type=str, help="Vector endpoint URL")
    parser.add_argument("--token", type=str, help="Authentication token")
    parser.add_argument("--test-event", action="store_true", help="Send a test event")
    
    args = parser.parse_args()
    
    # Initialize client
    client = VectorClient(endpoint=args.endpoint, token=args.token)
    
    if not client.is_configured:
        print("❌ Vector client not configured!")
        print("   Set environment variables:")
        print("   - AI_SAST_VECTOR_URL: Your vector/log endpoint URL")
        print("   - AI_SAST_VECTOR_TOKEN: Your authentication token")
        print("\n   Or provide via command line arguments:")
        print("   --endpoint <url> --token <token>")
        return
    
    print(f"✅ Vector client configured")
    print(f"   Endpoint: {client.endpoint}")
    
    if args.test_event:
        print("\n🧪 Sending test event...")
        success = client.log_vulnerability(
            repo_url="https://github.com/test/repo",
            file_path="test/example.py",
            severity="HIGH",
            issue="Test SQL Injection Vulnerability",
            status="Test",
            vuln_id="test-123",
            location="Line 42",
            cvss_score="8.5"
        )
        
        if success:
            print("✅ Test event sent successfully!")
        else:
            print("❌ Failed to send test event")


if __name__ == "__main__":
    main()

