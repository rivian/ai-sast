#!/usr/bin/env python3
"""
Unified Feedback Client

This module provides a unified interface for storing and retrieving vulnerability feedback.
It automatically selects the appropriate backend (SQLite or Databricks) based on configuration.

Usage:
    from src.integrations.feedback import get_feedback_client
    
    client = get_feedback_client()
    client.store_feedback(...)
    feedback = client.get_false_positives_for_project(repo_url)
"""

import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def get_feedback_client():
    """
    Get the appropriate feedback client based on configuration.
    
    Selection priority:
    1. If AI_SAST_FEEDBACK_BACKEND is set to 'databricks', use Databricks
    2. If Databricks environment variables are set, use Databricks
    3. Otherwise, use SQLite (default)
    
    Returns:
        Feedback client instance (FeedbackDatabase or DatabricksClient)
    """
    
    # Check explicit backend selection
    backend = os.environ.get('AI_SAST_FEEDBACK_BACKEND', '').lower()
    
    if backend == 'databricks':
        logger.info("📊 Feedback backend explicitly set to Databricks")
        return _get_databricks_client()
    
    # Check if Databricks is configured
    databricks_host = os.environ.get('AI_SAST_DATABRICKS_HOST')
    databricks_configured = all([
        databricks_host,
        os.environ.get('AI_SAST_DATABRICKS_HTTP_PATH'),
        os.environ.get('AI_SAST_DATABRICKS_TOKEN'),
        os.environ.get('AI_SAST_DATABRICKS_CATALOG'),
        os.environ.get('AI_SAST_DATABRICKS_SCHEMA'),
        os.environ.get('AI_SAST_DATABRICKS_TABLE')
    ])
    
    if databricks_configured:
        logger.info("📊 Databricks configuration detected, using Databricks backend")
        return _get_databricks_client()
    
    # Default to SQLite
    logger.info("💾 Using local SQLite feedback database (default)")
    return _get_sqlite_client()


def _get_sqlite_client():
    """Get SQLite scan database client"""
    try:
        from .scan_database import ScanDatabase
        return ScanDatabase()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite client: {e}")
        raise


def _get_databricks_client():
    """Get Databricks feedback client"""
    try:
        from .databricks import DatabricksClient
        client = DatabricksClient()
        
        if not client.is_configured:
            logger.warning("⚠️  Databricks not fully configured, falling back to SQLite")
            return _get_sqlite_client()
        
        return client
    except ImportError:
        logger.warning("⚠️  Databricks connector not installed, falling back to SQLite")
        logger.info("   Install with: pip install databricks-sql-connector")
        return _get_sqlite_client()
    except Exception as e:
        logger.error(f"Failed to initialize Databricks client: {e}")
        logger.info("Falling back to SQLite")
        return _get_sqlite_client()


class FeedbackClientInterface:
    """
    Interface class defining the feedback client API.
    Both SQLite and Databricks clients should implement these methods.
    """
    
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
        """Store a single feedback record"""
        raise NotImplementedError
    
    def store_batch_feedback(
        self,
        repo_url: str,
        pr_number: Optional[int],
        feedback_list: List[Dict]
    ) -> int:
        """Store multiple feedback records"""
        raise NotImplementedError
    
    def get_false_positives_for_project(
        self,
        repo_url: str,
        days_back: int = 90,
        limit: int = 100
    ) -> List[Dict]:
        """Get false positive feedback for a project"""
        raise NotImplementedError
    
    def get_confirmed_vulnerabilities_for_project(
        self,
        repo_url: str,
        days_back: int = 90,
        limit: int = 100
    ) -> List[Dict]:
        """Get confirmed vulnerability feedback for a project"""
        raise NotImplementedError
    
    def format_feedback_for_context(
        self,
        false_positives: List[Dict],
        confirmed_vulnerabilities: List[Dict]
    ) -> str:
        """Format feedback for AI model context"""
        raise NotImplementedError
    
    def close(self):
        """Close database connection"""
        raise NotImplementedError


def main():
    """Test feedback client selection"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test feedback client")
    parser.add_argument("--backend", type=str, choices=['sqlite', 'databricks', 'auto'],
                       default='auto', help="Backend to test (default: auto)")
    parser.add_argument("--test-store", action="store_true", help="Test storing feedback")
    parser.add_argument("--repo-url", type=str, help="Repository URL for testing")
    
    args = parser.parse_args()
    
    # Set backend if specified
    if args.backend != 'auto':
        os.environ['AI_SAST_FEEDBACK_BACKEND'] = args.backend
    
    print("🔍 Testing feedback client selection...")
    print("=" * 60)
    
    # Get client
    client = get_feedback_client()
    
    print(f"\n✅ Selected backend: {type(client).__name__}")
    print(f"   Configured: {client.is_configured}")
    
    if hasattr(client, 'db_path'):
        print(f"   Database: {client.db_path}")
    elif hasattr(client, 'server_hostname'):
        print(f"   Server: {client.server_hostname}")
    
    if args.test_store:
        print("\n🧪 Testing feedback storage...")
        success = client.store_feedback(
            repo_url=args.repo_url or "https://github.com/test/repo",
            pr_number=123,
            file_path="test/example.py",
            vulnerability_id="test-123",
            issue="Test vulnerability",
            severity="HIGH",
            status="false_positive",
            feedback="Test feedback",
            location="Line 42"
        )
        
        if success:
            print("✅ Feedback stored successfully!")
        else:
            print("❌ Failed to store feedback")
    
    client.close()
    print("\n✨ Test complete!")


if __name__ == "__main__":
    main()
