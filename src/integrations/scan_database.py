#!/usr/bin/env python3
"""
SQLite Scan Database

This module provides local storage for scan results and feedback using SQLite.
Stores both initial vulnerability findings and developer feedback for continuous improvement.

Default location: ~/.ai-sast/scans.db
"""

import os
import sqlite3
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class ScanDatabase:
    """
    Local SQLite database for storing scan results and feedback.
    
    Stores:
    - Scan results (vulnerabilities found during scans)
    - Developer feedback (true positives / false positives)
    - Historical data for improving AI accuracy
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the scan database
        
        Args:
            db_path: Path to SQLite database file. If None, uses AI_SAST_DB_PATH
                    environment variable or default (~/.ai-sast/scans.db)
        """
        if db_path is None:
            db_path = os.environ.get('AI_SAST_DB_PATH')
            
            if not db_path:
                home_dir = Path.home()
                ai_sast_dir = home_dir / '.ai-sast'
                ai_sast_dir.mkdir(exist_ok=True)
                db_path = str(ai_sast_dir / 'scans.db')
        
        self.db_path = db_path
        self.is_configured = True
        self._init_database()
        logger.info(f"✅ Scan database initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Scan results table - stores initial findings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                repository TEXT NOT NULL,
                pr_number INTEGER,
                file_path TEXT NOT NULL,
                vuln_id TEXT NOT NULL,
                issue TEXT NOT NULL,
                severity TEXT NOT NULL,
                cvss_vector TEXT,
                location TEXT,
                description TEXT,
                risk TEXT,
                fix TEXT,
                scan_type TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(repository, vuln_id, scan_id)
            )
        ''')
        
        # Feedback table - stores developer feedback
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                repository TEXT NOT NULL,
                pr_number INTEGER,
                file_path TEXT NOT NULL,
                vuln_id TEXT NOT NULL,
                issue TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                feedback_text TEXT,
                cvss_vector TEXT,
                location TEXT,
                user TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(repository, vuln_id, status)
            )
        ''')
        
        # Create indices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_repository ON scan_results(repository)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON scan_results(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_repository ON feedback(repository)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)')
        
        conn.commit()
        conn.close()
    
    def store_scan_result(
        self,
        scan_id: str,
        repo_url: str,
        pr_number: Optional[int],
        file_path: str,
        vulnerability_id: str,
        issue: str,
        severity: str,
        cvss_vector: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        risk: Optional[str] = None,
        fix: Optional[str] = None,
        scan_type: str = "full"
    ) -> bool:
        """Store a scan result (vulnerability finding)"""
        try:
            timestamp = datetime.now().isoformat()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO scan_results
                (scan_id, timestamp, repository, pr_number, file_path, vuln_id, 
                 issue, severity, cvss_vector, location, description, risk, fix,
                 scan_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_id, timestamp, repo_url, pr_number, file_path, vulnerability_id,
                issue, severity, cvss_vector or "", location or "", description or "",
                risk or "", fix or "", scan_type, timestamp
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error storing scan result: {e}")
            return False
    
    def store_batch_scan_results(
        self,
        scan_id: str,
        repo_url: str,
        pr_number: Optional[int],
        results: List[Dict],
        scan_type: str = "full"
    ) -> int:
        """Store multiple scan results"""
        count = 0
        for result in results:
            if self.store_scan_result(
                scan_id=scan_id,
                repo_url=repo_url,
                pr_number=pr_number,
                file_path=result.get('file_path', ''),
                vulnerability_id=result.get('vuln_id', ''),
                issue=result.get('issue', ''),
                severity=result.get('severity', ''),
                cvss_vector=result.get('cvss_vector'),
                location=result.get('location'),
                description=result.get('description'),
                risk=result.get('risk'),
                fix=result.get('fix'),
                scan_type=scan_type
            ):
                count += 1
        return count
    
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
        location: Optional[str] = None,
        user: Optional[str] = None
    ) -> bool:
        """Store developer feedback"""
        try:
            timestamp = datetime.now().isoformat()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO feedback
                (timestamp, repository, pr_number, file_path, vuln_id, issue, severity, 
                 status, feedback_text, cvss_vector, location, user, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, repo_url, pr_number, file_path, vulnerability_id,
                issue, severity, status, feedback or "", cvss_vector or "",
                location or "", user or "", timestamp
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Stored feedback for {vulnerability_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            return False
    
    def store_batch_feedback(
        self,
        repo_url: str,
        pr_number: Optional[int],
        feedback_list: List[Dict]
    ) -> int:
        """Store multiple feedback records"""
        count = 0
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
                location=feedback.get('location'),
                user=feedback.get('user')
            ):
                count += 1
        logger.info(f"✅ Stored {count}/{len(feedback_list)} feedback records")
        return count
    
    def get_false_positives_for_project(
        self,
        repo_url: str,
        days_back: int = 90,
        limit: int = 100
    ) -> List[Dict]:
        """Get false positive feedback for a project"""
        try:
            project_id = self._extract_project_identifier(repo_url)
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    timestamp as ts,
                    vuln_id,
                    feedback_text as comments,
                    user,
                    repository as repo,
                    issue,
                    severity,
                    file_path,
                    location
                FROM feedback
                WHERE 
                    status = 'false_positive'
                    AND (repository LIKE ? OR repository LIKE ?)
                    AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{project_id}%', f'{repo_url}%', cutoff_date, limit))
            
            results = cursor.fetchall()
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error querying false positives: {e}")
            return []
    
    def get_confirmed_vulnerabilities_for_project(
        self,
        repo_url: str,
        days_back: int = 90,
        limit: int = 100
    ) -> List[Dict]:
        """Get confirmed vulnerabilities for a project"""
        try:
            project_id = self._extract_project_identifier(repo_url)
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    timestamp as ts,
                    vuln_id,
                    feedback_text as comments,
                    user,
                    repository as repo,
                    issue,
                    severity,
                    file_path,
                    location
                FROM feedback
                WHERE 
                    status = 'confirmed_vulnerability'
                    AND (repository LIKE ? OR repository LIKE ?)
                    AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{project_id}%', f'{repo_url}%', cutoff_date, limit))
            
            results = cursor.fetchall()
            conn.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error querying confirmed vulnerabilities: {e}")
            return []
    
    def _extract_project_identifier(self, repo_url: str) -> str:
        """Extract project name from URL"""
        url = repo_url.replace('https://', '').replace('http://', '').rstrip('/')
        parts = url.split('/')
        return parts[-1] if parts else repo_url
    
    def format_feedback_for_context(
        self,
        false_positives: List[Dict],
        confirmed_vulnerabilities: List[Dict]
    ) -> str:
        """Format feedback for AI context"""
        context_parts = []
        
        if false_positives:
            fp_count = min(len(false_positives), 10)
            context_parts.append("## Historical False Positives\n")
            context_parts.append("Avoid reporting similar issues:\n")
            
            for i, fp in enumerate(false_positives[:10], 1):
                context_parts.append(f"\n{i}. **Issue**: {fp.get('issue', 'N/A')}")
                context_parts.append(f"   - **File**: {fp.get('file_path', 'N/A')}")
                context_parts.append(f"   - **Severity**: {fp.get('severity', 'N/A')}")
                if fp.get('comments'):
                    context_parts.append(f"   - **Reason**: {fp.get('comments')}")
        
        if confirmed_vulnerabilities:
            cv_count = min(len(confirmed_vulnerabilities), 10)
            context_parts.append("\n\n## Previously Confirmed Vulnerabilities\n")
            context_parts.append("Be vigilant about similar patterns:\n")
            
            for i, vuln in enumerate(confirmed_vulnerabilities[:10], 1):
                context_parts.append(f"\n{i}. **Issue**: {vuln.get('issue', 'N/A')}")
                context_parts.append(f"   - **File**: {vuln.get('file_path', 'N/A')}")
                context_parts.append(f"   - **Severity**: {vuln.get('severity', 'N/A')}")
        
        return '\n'.join(context_parts) if context_parts else ""
    
    def get_statistics(self, repo_url: Optional[str] = None) -> Dict:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if repo_url:
                project_id = self._extract_project_identifier(repo_url)
                # Use DISTINCT to avoid double-counting when both LIKE patterns match
                where = "WHERE (repository LIKE ? OR repository LIKE ?)"
                params = (f'%{project_id}%', f'{repo_url}%')
            else:
                where = ""
                params = ()
            
            # Feedback stats - using DISTINCT to avoid double counting
            cursor.execute(f'SELECT COUNT(DISTINCT id) FROM feedback {where}', params)
            total_feedback = cursor.fetchone()[0]
            
            cursor.execute(f'''
                SELECT COUNT(DISTINCT id) FROM feedback 
                {where} {"AND" if where else "WHERE"} status = 'false_positive'
            ''', params)
            false_positives = cursor.fetchone()[0]
            
            cursor.execute(f'''
                SELECT COUNT(DISTINCT id) FROM feedback 
                {where} {"AND" if where else "WHERE"} status = 'confirmed_vulnerability'
            ''', params)
            confirmed = cursor.fetchone()[0]
            
            # Scan results stats
            cursor.execute(f'SELECT COUNT(DISTINCT id) FROM scan_results {where}', params)
            total_scans = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_feedback': total_feedback,
                'false_positives': false_positives,
                'confirmed_vulnerabilities': confirmed,
                'total_scan_results': total_scans,
                'repository': repo_url
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'total_feedback': 0, 'false_positives': 0, 'confirmed_vulnerabilities': 0, 'total_scan_results': 0}
    
    def close(self):
        """Close database connection (no-op for SQLite)"""
        pass


def main():
    """CLI for testing database"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-SAST Scan Database")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--repo-url", type=str, help="Repository URL")
    
    args = parser.parse_args()
    
    db = ScanDatabase()
    print(f"✅ Database: {db.db_path}")
    
    if args.stats:
        stats = db.get_statistics(args.repo_url)
        print(f"\n📊 Statistics:")
        print(f"  Scan results: {stats['total_scan_results']}")
        print(f"  Total feedback: {stats['total_feedback']}")
        print(f"  False positives: {stats['false_positives']}")
        print(f"  Confirmed vulnerabilities: {stats['confirmed_vulnerabilities']}")


if __name__ == "__main__":
    main()
