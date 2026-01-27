#!/usr/bin/env python3
"""
Test script for SQLite feedback system

This script tests the new SQLite feedback database functionality.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.scan_database import ScanDatabase
from src.integrations.feedback import get_feedback_client


def test_sqlite_basic():
    """Test basic SQLite operations"""
    print("=" * 60)
    print("TEST 1: Basic SQLite Operations")
    print("=" * 60)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize database
        db = ScanDatabase(db_path=db_path)
        print(f"✅ Database initialized: {db_path}")
        
        # Store feedback
        success = db.store_feedback(
            repo_url="https://github.com/test/repo",
            pr_number=123,
            file_path="src/test.py",
            vulnerability_id="test-001",
            issue="SQL Injection",
            severity="HIGH",
            status="false_positive",
            feedback="Uses parameterized queries",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            location="Line 42",
            user="test_user"
        )
        
        if success:
            print("✅ Stored test feedback")
        else:
            print("❌ Failed to store feedback")
            return False
        
        # Query feedback
        false_positives = db.get_false_positives_for_project(
            "https://github.com/test/repo",
            days_back=7
        )
        
        print(f"✅ Retrieved {len(false_positives)} false positive(s)")
        
        if len(false_positives) == 1:
            fp = false_positives[0]
            print(f"   Issue: {fp['issue']}")
            print(f"   File: {fp['file_path']}")
            print(f"   Severity: {fp['severity']}")
        
        # Get statistics
        stats = db.get_statistics("https://github.com/test/repo")
        print(f"✅ Statistics: {stats}")
        
        db.close()
        return True
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"🧹 Cleaned up test database")


def test_feedback_client_selection():
    """Test automatic feedback client selection"""
    print("\n" + "=" * 60)
    print("TEST 2: Feedback Client Selection")
    print("=" * 60)
    
    # Save original env vars
    original_backend = os.environ.get('AI_SAST_FEEDBACK_BACKEND')
    original_db = os.environ.get('AI_SAST_FEEDBACK_DB')
    
    try:
        # Test SQLite selection (default)
        os.environ.pop('AI_SAST_FEEDBACK_BACKEND', None)
        os.environ.pop('AI_SAST_FEEDBACK_DB', None)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name
        os.environ['AI_SAST_FEEDBACK_DB'] = temp_db
        
        client = get_feedback_client()
        print(f"✅ Default backend: {type(client).__name__}")
        
        if type(client).__name__ == 'ScanDatabase':
            print("✅ Correctly selected SQLite backend")
        else:
            print("❌ Wrong backend selected")
            return False
        
        # Test explicit SQLite selection
        os.environ['AI_SAST_FEEDBACK_BACKEND'] = 'sqlite'
        client = get_feedback_client()
        print(f"✅ Explicit SQLite: {type(client).__name__}")
        
        # Cleanup
        os.unlink(temp_db)
        
        return True
        
    finally:
        # Restore original env vars
        if original_backend:
            os.environ['AI_SAST_FEEDBACK_BACKEND'] = original_backend
        else:
            os.environ.pop('AI_SAST_FEEDBACK_BACKEND', None)
        
        if original_db:
            os.environ['AI_SAST_FEEDBACK_DB'] = original_db
        else:
            os.environ.pop('AI_SAST_FEEDBACK_DB', None)


def test_batch_operations():
    """Test batch feedback operations"""
    print("\n" + "=" * 60)
    print("TEST 3: Batch Operations")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = ScanDatabase(db_path=db_path)
        
        # Create batch feedback
        feedback_list = [
            {
                'vuln_id': 'vuln-001',
                'file_path': 'src/app.py',
                'issue': 'SQL Injection',
                'severity': 'HIGH',
                'status': 'false_positive',
                'feedback': 'Uses parameterized queries',
                'location': 'Line 42'
            },
            {
                'vuln_id': 'vuln-002',
                'file_path': 'src/auth.py',
                'issue': 'Weak Password Hashing',
                'severity': 'CRITICAL',
                'status': 'confirmed_vulnerability',
                'feedback': 'Using MD5 for passwords',
                'location': 'Line 108'
            },
            {
                'vuln_id': 'vuln-003',
                'file_path': 'src/api.py',
                'issue': 'Missing Authentication',
                'severity': 'HIGH',
                'status': 'false_positive',
                'feedback': 'Internal API, not exposed',
                'location': 'Line 25'
            }
        ]
        
        # Store batch
        count = db.store_batch_feedback(
            repo_url="https://github.com/test/batch-repo",
            pr_number=456,
            feedback_list=feedback_list
        )
        
        print(f"✅ Stored {count}/{len(feedback_list)} feedback records")
        
        # Query both types
        fps = db.get_false_positives_for_project("https://github.com/test/batch-repo")
        cvs = db.get_confirmed_vulnerabilities_for_project("https://github.com/test/batch-repo")
        
        print(f"✅ False positives: {len(fps)}")
        print(f"✅ Confirmed vulnerabilities: {len(cvs)}")
        
        # Test context formatting
        context = db.format_feedback_for_context(fps, cvs)
        
        if context and len(context) > 0:
            print(f"✅ Generated context ({len(context)} chars)")
            print("\nSample context:")
            print(context[:300] + "..." if len(context) > 300 else context)
        
        db.close()
        return True
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
            print("🧹 Cleaned up test database")


def main():
    """Run all tests"""
    print("\n🧪 Testing SQLite Feedback System")
    print("=" * 60)
    
    tests = [
        ("Basic Operations", test_sqlite_basic),
        ("Client Selection", test_feedback_client_selection),
        ("Batch Operations", test_batch_operations)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    # Overall result
    all_passed = all(result for _, result in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
