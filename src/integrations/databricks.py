#!/usr/bin/env python3
"""
Databricks Feedback Client

This module provides functionality to fetch feedback data from Databricks
to improve security scanning with historical false positive data.

This is a generic client that can be used with any Databricks instance.
Configure via environment variables to connect to your Databricks workspace.
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatabricksClient:
    """
    Client for fetching feedback data from Databricks SQL warehouses
    """
    
    def __init__(
        self,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        table: Optional[str] = None
    ):
        """
        Initialize Databricks client
        
        Args:
            catalog: Unity Catalog name (from AI_SAST_DATABRICKS_CATALOG env or parameter)
            schema: Schema name (from AI_SAST_DATABRICKS_SCHEMA env or parameter)
            table: Table name (from AI_SAST_DATABRICKS_TABLE env or parameter)
        """
        # AI_SAST_DATABRICKS_HOST: Your Databricks workspace hostname
        # Example: "mycompany.cloud.databricks.com" or "adb-1234567890123456.7.azuredatabricks.net"
        self.server_hostname = os.environ.get('AI_SAST_DATABRICKS_HOST')
        
        # AI_SAST_DATABRICKS_HTTP_PATH: SQL warehouse HTTP path
        # Example: "/sql/1.0/warehouses/abc123def456" (find in SQL Warehouse settings)
        self.http_path = os.environ.get('AI_SAST_DATABRICKS_HTTP_PATH')
        
        # AI_SAST_DATABRICKS_TOKEN: Databricks personal access token
        # Example: "dapi1234567890abcdef..." (generate in User Settings > Access Tokens)
        self.access_token = os.environ.get('AI_SAST_DATABRICKS_TOKEN')
        
        # AI_SAST_DATABRICKS_CATALOG: Unity Catalog name
        # Example: "main", "production", "security_data"
        self.catalog = catalog or os.environ.get('AI_SAST_DATABRICKS_CATALOG')
        
        # AI_SAST_DATABRICKS_SCHEMA: Schema name within the catalog
        # Example: "security", "vulnerability_tracking", "sast_data"
        self.schema = schema or os.environ.get('AI_SAST_DATABRICKS_SCHEMA')
        
        # AI_SAST_DATABRICKS_TABLE: Table name within the schema
        # Example: "scan_feedback", "vulnerability_feedback", "sast_results"
        self.table = table or os.environ.get('AI_SAST_DATABRICKS_TABLE')
        
        self.connection = None
        self.cursor = None
        
        # Check if all required configuration is present
        if not all([self.server_hostname, self.http_path, self.access_token, 
                    self.catalog, self.schema, self.table]):
            logger.info("ℹ️  Databricks not fully configured. Feedback fetching will be skipped.")
            self.is_configured = False
        else:
            self.is_configured = True
            logger.info(f"✅ Databricks client configured for {self.server_hostname}")
    
    def connect(self) -> bool:
        """
        Establish connection to Databricks
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.is_configured:
            logger.debug("Databricks not configured, skipping connection")
            return False
        
        try:
            from databricks import sql
            
            logger.info(f"Connecting to Databricks: {self.server_hostname}")
            
            self.connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token
            )
            self.cursor = self.connection.cursor()
            logger.info("✅ Connected to Databricks successfully")
            return True
        except ImportError:
            logger.warning("databricks-sql-connector not installed. Install: pip install databricks-sql-connector")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Databricks: {e}")
            return False
    
    def store_feedback(
        self,
        repo_url: str,
        pr_number: Optional[int],
        file_path: str,
        vulnerability_id: str,
        issue: str,
        severity: str,
        status: str,
        feedback: Optional[str] = None,
        cvss_vector: Optional[str] = None,
        location: Optional[str] = None
    ) -> bool:
        """
        Store developer feedback about a vulnerability finding
        
        Args:
            repo_url: Repository URL
            pr_number: Pull request number (None for full scans)
            file_path: Path to the file with the vulnerability
            vulnerability_id: Unique ID for the vulnerability
            issue: Description of the issue
            severity: Severity level (Critical, High, Medium, Low)
            status: confirmed_vulnerability or false_positive
            feedback: Optional developer comment
            cvss_vector: Optional CVSS vector string
            location: Optional location (e.g., "Line 42")
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("Databricks not configured - cannot store feedback")
            return False
        
        try:
            # Prepare the feedback record
            timestamp = datetime.now().isoformat()
            
            # SQL INSERT statement
            sql = f"""
            INSERT INTO {self.catalog}.{self.schema}.{self.table}
            (repo_url, pr_number, file_path, vuln_id, issue, severity, status, 
             feedback, cvss_vector, location, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                repo_url,
                pr_number,
                file_path,
                vulnerability_id,
                issue,
                severity,
                status,
                feedback or "",
                cvss_vector or "",
                location or "",
                timestamp,
                timestamp
            )
            
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Stored feedback for {vulnerability_id} in Databricks")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing feedback to Databricks: {str(e)}")
            return False
    
    def store_batch_feedback(
        self,
        repo_url: str,
        pr_number: Optional[int],
        feedback_list: List[Dict]
    ) -> int:
        """
        Store multiple feedback records in batch
        
        Args:
            repo_url: Repository URL
            pr_number: Pull request number
            feedback_list: List of feedback dictionaries
            
        Returns:
            Number of records successfully stored
        """
        if not self.is_configured:
            logger.warning("Databricks not configured - cannot store feedback")
            return 0
        
        success_count = 0
        
        for feedback in feedback_list:
            if self.store_feedback(
                repo_url=repo_url,
                pr_number=pr_number,
                file_path=feedback.get('file_path', ''),
                vulnerability_id=feedback.get('vuln_id', ''),
                issue=feedback.get('issue', ''),
                severity=feedback.get('severity', ''),
                status=feedback.get('status', ''),
                feedback=feedback.get('feedback'),
                cvss_vector=feedback.get('cvss_vector'),
                location=feedback.get('location')
            ):
                success_count += 1
        
        logger.info(f"✅ Stored {success_count}/{len(feedback_list)} feedback records")
        return success_count
    
    def close(self):
        """Close Databricks connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                logger.info("Databricks connection closed")
        except Exception as e:
            logger.warning(f"Error closing Databricks connection: {e}")
    
    def get_false_positives_for_project(
        self,
        repo_url: str,
        days_back: int = 90,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch false positive feedback for a specific project
        
        Args:
            repo_url: Repository URL or project identifier
            days_back: Number of days to look back for feedback
            limit: Maximum number of records to fetch
            
        Returns:
            List of false positive feedback records
        """
        if not self.is_configured:
            logger.info("ℹ️  Databricks not configured. Skipping feedback fetch.")
            return []
        
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            # Extract project identifier from repo URL
            project_identifier = self._extract_project_identifier(repo_url)
            
            # Calculate date filter
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            logger.info(f"Querying false positives for project:")
            logger.info(f"  Repo URL: {repo_url}")
            logger.info(f"  Project identifier: {project_identifier}")
            logger.info(f"  Lookback: last {days_back} days (from {cutoff_date})")
            logger.info(f"  Table: {self.catalog}.{self.schema}.{self.table}")
            
            # Query for false positive feedback records
            # Adjust the query based on your table schema
            feedback_query = f"""
                SELECT 
                    timestamp as ts,
                    vuln_id,
                    comments,
                    user,
                    repository as repo,
                    issue,
                    severity,
                    file_path,
                    location
                FROM {self.catalog}.{self.schema}.{self.table}
                WHERE 
                    status = 'False Positive'
                    AND (
                        repository LIKE '%{project_identifier}%'
                        OR repository LIKE '{repo_url}%'
                    )
                    AND timestamp >= '{cutoff_date}'
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
            
            self.cursor.execute(feedback_query)
            results = self.cursor.fetchall()
            logger.info(f"  Found {len(results)} false positive record(s)")
            
            if not results:
                return []
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in self.cursor.description]
            records = []
            
            for row in results:
                record = dict(zip(columns, row))
                records.append(record)
            
            logger.info(f"Found {len(records)} false positive(s) with details")
            return records
            
        except Exception as e:
            logger.error(f"Error querying false positives: {e}")
            logger.debug(f"  Project URL: {repo_url}")
            logger.debug(f"  Project ID: {project_identifier}")
            return []
    
    def get_confirmed_vulnerabilities_for_project(
        self,
        repo_url: str,
        days_back: int = 90,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch confirmed vulnerability feedback for a specific project
        
        Args:
            repo_url: Repository URL or project identifier
            days_back: Number of days to look back for feedback
            limit: Maximum number of records to fetch
            
        Returns:
            List of confirmed vulnerability feedback records
        """
        if not self.is_configured:
            logger.info("ℹ️  Databricks not configured. Skipping feedback fetch.")
            return []
        
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            project_identifier = self._extract_project_identifier(repo_url)
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            logger.info(f"Querying confirmed vulnerabilities for project:")
            logger.info(f"  Repo URL: {repo_url}")
            logger.info(f"  Project identifier: {project_identifier}")
            logger.info(f"  Lookback: last {days_back} days (from {cutoff_date})")
            
            # Query for confirmed vulnerability records
            query = f"""
                SELECT 
                    timestamp as ts,
                    vuln_id,
                    comments,
                    user,
                    repository as repo,
                    issue,
                    severity,
                    file_path,
                    location
                FROM {self.catalog}.{self.schema}.{self.table}
                WHERE 
                    status = 'Confirmed'
                    AND (
                        repository LIKE '%{project_identifier}%'
                        OR repository LIKE '{repo_url}%'
                    )
                    AND timestamp >= '{cutoff_date}'
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
            
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            logger.info(f"  Found {len(results)} confirmed vulnerability record(s)")
            
            if not results:
                return []
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in self.cursor.description]
            records = []
            
            for row in results:
                record = dict(zip(columns, row))
                records.append(record)
            
            logger.info(f"Found {len(records)} confirmed vulnerabilit(ies) with details")
            return records
            
        except Exception as e:
            logger.error(f"Error querying confirmed vulnerabilities: {e}")
            return []
    
    def _extract_project_identifier(self, repo_url: str) -> str:
        """
        Extract project identifier from repository URL
        
        Args:
            repo_url: Full repository URL (e.g., https://github.com/org/project)
            
        Returns:
            Project identifier (e.g., project name)
        """
        # Remove protocol and trailing slashes
        url = repo_url.replace('https://', '').replace('http://', '').rstrip('/')
        
        # Get the last part of the URL as project identifier
        parts = url.split('/')
        if len(parts) > 0:
            return parts[-1]
        
        return repo_url
    
    def format_feedback_for_context(
        self,
        false_positives: List[Dict],
        confirmed_vulnerabilities: List[Dict]
    ) -> str:
        """
        Format feedback records into context string for AI model
        
        Args:
            false_positives: List of false positive records
            confirmed_vulnerabilities: List of confirmed vulnerability records
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if false_positives:
            fp_count = min(len(false_positives), 10)  # Limit to top 10
            logger.info(f"Adding {fp_count} false positive(s) to AI context")
            
            context_parts.append("## Historical False Positives for This Project\n")
            context_parts.append("The following issues were previously marked as false positives. "
                               "Use this information to avoid reporting similar false positives:\n")
            
            for i, fp in enumerate(false_positives[:10], 1):
                issue = fp.get('issue', 'N/A')
                file_path = fp.get('file_path', 'N/A')
                severity = fp.get('severity', 'N/A')
                comments = fp.get('comments', '')
                
                context_parts.append(f"\n{i}. **Issue**: {issue}")
                context_parts.append(f"   - **File**: {file_path}")
                context_parts.append(f"   - **Severity**: {severity}")
                if comments:
                    context_parts.append(f"   - **Reason**: {comments}")
        
        if confirmed_vulnerabilities:
            cv_count = min(len(confirmed_vulnerabilities), 10)
            logger.info(f"Adding {cv_count} confirmed vulnerabilit(ies) to AI context")
            
            context_parts.append("\n\n## Previously Confirmed Vulnerabilities for This Project\n")
            context_parts.append("The following vulnerabilities were confirmed as legitimate. "
                               "Be vigilant about similar patterns:\n")
            
            for i, vuln in enumerate(confirmed_vulnerabilities[:10], 1):
                issue = vuln.get('issue', 'N/A')
                file_path = vuln.get('file_path', 'N/A')
                severity = vuln.get('severity', 'N/A')
                
                context_parts.append(f"\n{i}. **Issue**: {issue}")
                context_parts.append(f"   - **File**: {file_path}")
                context_parts.append(f"   - **Severity**: {severity}")
        
        formatted_result = '\n'.join(context_parts) if context_parts else ""
        
        # Print formatted feedback for debugging
        if formatted_result:
            print("\n" + "="*80)
            print("FEEDBACK CONTEXT FOR AI MODEL:")
            print("="*80)
            print(formatted_result[:500] + "..." if len(formatted_result) > 500 else formatted_result)
            print("="*80 + "\n")
        
        return formatted_result


def main():
    """
    Main function for testing Databricks client
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Databricks feedback client")
    parser.add_argument("--repo-url", type=str, required=True, help="Repository URL to fetch feedback for")
    parser.add_argument("--days-back", type=int, default=90, help="Days to look back (default: 90)")
    parser.add_argument("--limit", type=int, default=100, help="Maximum records to fetch (default: 100)")
    
    args = parser.parse_args()
    
    # Initialize client
    client = DatabricksClient()
    
    if not client.is_configured:
        print("❌ Databricks is not configured.")
        print("   Set the following required environment variables:")
        print("      - AI_SAST_DATABRICKS_HOST: Your Databricks workspace hostname")
        print("      - AI_SAST_DATABRICKS_HTTP_PATH: SQL warehouse HTTP path")
        print("      - AI_SAST_DATABRICKS_TOKEN: Access token")
        print("      - AI_SAST_DATABRICKS_CATALOG: Your Unity Catalog name")
        print("      - AI_SAST_DATABRICKS_SCHEMA: Your schema name")
        print("      - AI_SAST_DATABRICKS_TABLE: Your table name")
        print("\n   Example:")
        print("      export AI_SAST_DATABRICKS_HOST='your-workspace.cloud.databricks.com'")
        print("      export AI_SAST_DATABRICKS_HTTP_PATH='/sql/1.0/warehouses/abc123'")
        print("      export AI_SAST_DATABRICKS_TOKEN='dapi...'")
        print("      export AI_SAST_DATABRICKS_CATALOG='my_catalog'")
        print("      export AI_SAST_DATABRICKS_SCHEMA='my_schema'")
        print("      export AI_SAST_DATABRICKS_TABLE='my_feedback_table'")
        return
    
    try:
        # Fetch false positives
        print(f"\n🔍 Fetching false positives for: {args.repo_url}")
        false_positives = client.get_false_positives_for_project(
            args.repo_url,
            days_back=args.days_back,
            limit=args.limit
        )
        
        print(f"\n📊 False Positives Found: {len(false_positives)}")
        for fp in false_positives[:5]:  # Show first 5
            print(f"\n  - Vuln ID: {fp.get('vuln_id')}")
            print(f"    Issue: {fp.get('issue')}")
            print(f"    File: {fp.get('file_path')}")
            print(f"    Severity: {fp.get('severity')}")
        
        # Fetch confirmed vulnerabilities
        print(f"\n\n🔍 Fetching confirmed vulnerabilities for: {args.repo_url}")
        confirmed = client.get_confirmed_vulnerabilities_for_project(
            args.repo_url,
            days_back=args.days_back,
            limit=args.limit
        )
        
        print(f"\n📊 Confirmed Vulnerabilities Found: {len(confirmed)}")
        for vuln in confirmed[:5]:  # Show first 5
            print(f"\n  - Vuln ID: {vuln.get('vuln_id')}")
            print(f"    Issue: {vuln.get('issue')}")
            print(f"    File: {vuln.get('file_path')}")
            print(f"    Severity: {vuln.get('severity')}")
        
        # Format as context
        print("\n\n📝 Formatted Context for AI Model:")
        print("=" * 80)
        context = client.format_feedback_for_context(false_positives, confirmed)
        print(context)
        
    finally:
        client.close()


if __name__ == "__main__":
    main()

