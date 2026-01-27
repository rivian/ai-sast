#!/usr/bin/env python3
"""
Jira Client for fetching vulnerability information.

This is a generic Jira client that can be used with any Jira instance.
Configure via environment variables to connect to your Jira server.
"""

import os
from typing import Optional, List, Dict, Any, cast
from jira import JIRA, JIRAError
from jira.resources import Issue


class JiraClient:
    """A client to interact with the Jira API."""

    def __init__(self, server_url: str, username: str, api_token: str):
        """
        Initialize the Jira client.
        
        Args:
            server_url: The URL of the Jira instance (e.g., https://your-domain.atlassian.net).
            username: The username (email) for authentication.
            api_token: The Jira API token for authentication.
        """
        self.client: Optional[JIRA] = None
        try:
            print("Attempting to connect to Jira...")
            self.client = JIRA(
                server=server_url,
                basic_auth=(username, api_token)
            )
            # Test connection by ensuring client was created before using it
            if self.client:
                self.client.server_info()
                print("✅ Successfully connected to Jira.")
        except JIRAError as e:
            print(f"❌ ERROR: Failed to connect to Jira. Status: {e.status_code}, Text: {e.text}")
            # The client will be None, and subsequent calls will fail gracefully.

    def is_connected(self) -> bool:
        """Check if the client is successfully connected to Jira."""
        return self.client is not None

    def get_vulnerability_tickets(self, jql_query: str) -> List[Dict[str, Any]]:
        """
        Fetch vulnerability tickets from Jira using a JQL query.
        
        Args:
            jql_query: The JQL query to execute.
        
        Returns:
            A list of dictionaries, each containing details of a vulnerability ticket.
        """
        if not self.is_connected() or not jql_query:
            return []

        # This assertion helps the linter understand that self.client is not None here.
        assert self.client is not None
        
        print(f"Searching Jira with JQL: \"{jql_query}\"")
        
        all_issues = []
        start_at = 0
        max_results = 50  # Standard page size
        total_issues = None

        while True:
            try:
                issues_page = self.client.search_issues(
                    jql_query,
                    startAt=start_at,
                    maxResults=max_results,
                    fields="summary,description,status,key"
                )
                
                # We cast here to inform the linter of the expected type.
                issues = cast(List[Issue], issues_page)

                if not issues:
                    break  # No more issues to fetch

                # Get total count from the first page if not already set
                if total_issues is None:
                    try:
                        total_issues = issues_page.total
                        print(f"📊 Total issues found: {total_issues}")
                    except AttributeError:
                        # Fallback: if total attribute is not available, we'll continue until no more issues
                        print("⚠️  Warning: Could not determine total issue count. Fetching all pages...")

                all_issues.extend(issues)
                start_at += len(issues)
                
                print(f"📄 Fetched {len(issues)} issues (total so far: {len(all_issues)})")

                # Check if we've fetched all issues
                if total_issues is not None and start_at >= total_issues:
                    print(f"✅ All {total_issues} issues fetched successfully")
                    break
                elif len(issues) < max_results:
                    # If we got fewer issues than requested, we've reached the end
                    print(f"✅ Reached end of results (got {len(issues)} < {max_results})")
                    break

            except JIRAError as e:
                print(f"❌ ERROR: Failed to fetch issues from Jira. Status: {e.status_code}, Text: {e.text}")
                # Return what we have so far, or an empty list if this was the first request
                break 

        tickets = []
        for issue in all_issues:
            tickets.append({
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": getattr(issue.fields, 'description', 'No description.'),
                "status": issue.fields.status.name,
            })
        
        print(f"Found {len(tickets)} relevant vulnerability tickets in Jira.")
        return tickets


def main():
    """Example usage and testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Jira client connection and query")
    parser.add_argument("--url", type=str, help="Jira server URL (or set JIRA_URL env var)")
    parser.add_argument("--username", type=str, help="Jira username (or set JIRA_USERNAME env var)")
    parser.add_argument("--token", type=str, help="Jira API token (or set JIRA_API_TOKEN env var)")
    parser.add_argument("--jql", type=str, default="project = SECURITY", help="JQL query to test")
    
    args = parser.parse_args()
    
    # Get configuration from args or environment
    jira_url = args.url or os.environ.get('JIRA_URL')
    jira_username = args.username or os.environ.get('JIRA_USERNAME')
    jira_token = args.token or os.environ.get('JIRA_API_TOKEN')
    
    if not all([jira_url, jira_username, jira_token]):
        print("❌ Missing required configuration!")
        print("   Provide via arguments or environment variables:")
        print("   - JIRA_URL: Your Jira server URL")
        print("   - JIRA_USERNAME: Your Jira username/email")
        print("   - JIRA_API_TOKEN: Your Jira API token")
        return
    
    # Initialize and test client
    client = JiraClient(jira_url, jira_username, jira_token)
    
    if client.is_connected():
        print(f"\n🔍 Testing JQL query: {args.jql}")
        tickets = client.get_vulnerability_tickets(args.jql)
        
        print(f"\n📊 Results: {len(tickets)} tickets found")
        for ticket in tickets[:5]:  # Show first 5
            print(f"\n  {ticket['key']}: {ticket['summary']}")
            print(f"  Status: {ticket['status']}")
    else:
        print("❌ Could not connect to Jira.")


if __name__ == "__main__":
    main()

