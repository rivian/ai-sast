#!/usr/bin/env python3
"""
Integration test for the AI-SAST feedback loop

This script demonstrates and tests the complete feedback cycle:
1. Simulates a scan with findings
2. Generates a comment with checkboxes
3. Simulates user feedback (checking boxes)
4. Collects and stores feedback
5. Retrieves feedback for future scans
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.scan_database import ScanDatabase
from src.core.report import HTMLReportGenerator


def test_complete_feedback_loop():
    """Test the complete feedback loop end-to-end"""
    
    print("=" * 70)
    print("🧪 AI-SAST Feedback Loop Integration Test")
    print("=" * 70)
    
    # Step 1: Setup test database
    print("\n📦 Step 1: Setting up test database...")
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = ScanDatabase(db_path=db_path)
    test_repo = "https://github.com/test-org/test-repo"
    test_pr = 42
    
    print(f"✅ Test database created: {db_path}")
    
    try:
        # Step 2: Simulate a scan with findings
        print("\n🔍 Step 2: Simulating security scan...")
        
        mock_results = [
            {
                "file_path": "src/database.py",
                "analysis": """
- **Vulnerability Level**: HIGH
- **Issue**: SQL Injection vulnerability
- **Location**: Line 25
- **Risk**: Attacker could execute arbitrary SQL queries
- **Fix**: Use parameterized queries with prepared statements
                """
            },
            {
                "file_path": "src/auth.py",
                "analysis": """
- **Vulnerability Level**: MEDIUM
- **Issue**: Hardcoded credentials
- **Location**: Line 10
- **Risk**: Credentials exposed in source code
- **Fix**: Move credentials to environment variables
                """
            }
        ]
        
        print(f"✅ Simulated scan with {len(mock_results)} finding(s)")
        
        # Step 3: Generate markdown comment
        print("\n💬 Step 3: Generating PR comment with checkboxes...")
        
        generator = HTMLReportGenerator()
        markdown_comment = generator.generate_markdown_report(
            results=mock_results,
            report_title="🤖 AI-SAST Security Scan",
            repo_url=test_repo,
            ref_name="main",
            report_context_text="PR changes"
        )
        
        print("✅ Generated markdown comment:")
        print("-" * 70)
        print(markdown_comment[:500] + "...\n")
        print("-" * 70)
        
        # Step 4: Simulate user checking boxes
        print("\n✅ Step 4: Simulating developer feedback...")
        
        # Simulate marking first as false positive, second as true positive
        simulated_feedback = [
            {
                'vuln_id': 'test-fp-001',
                'file_path': 'src/database.py',
                'issue': 'SQL Injection vulnerability',
                'severity': 'HIGH',
                'status': 'false_positive',
                'feedback': 'This uses parameterized queries - safe pattern',
                'location': 'Line 25',
                'cvss_vector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'
            },
            {
                'vuln_id': 'test-tp-001',
                'file_path': 'src/auth.py',
                'issue': 'Hardcoded credentials',
                'severity': 'MEDIUM',
                'status': 'confirmed_vulnerability',
                'feedback': 'Valid finding - will fix ASAP',
                'location': 'Line 10',
                'cvss_vector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N'
            }
        ]
        
        print("✅ Simulated feedback:")
        for fb in simulated_feedback:
            status_icon = "✅" if fb['status'] == 'confirmed_vulnerability' else "❌"
            print(f"  {status_icon} {fb['issue']} ({fb['file_path']})")
            print(f"     Status: {fb['status']}")
            print(f"     Comment: {fb['feedback']}")
        
        # Step 5: Store feedback
        print("\n💾 Step 5: Storing feedback in database...")
        
        stored_count = db.store_batch_feedback(
            repo_url=test_repo,
            pr_number=test_pr,
            feedback_list=simulated_feedback
        )
        
        print(f"✅ Stored {stored_count}/{len(simulated_feedback)} feedback records")
        
        # Step 6: Retrieve feedback for future scans
        print("\n🔄 Step 6: Retrieving feedback for future scans...")
        
        false_positives = db.get_false_positives_for_project(
            repo_url=test_repo,
            days_back=90
        )
        
        confirmed_vulns = db.get_confirmed_vulnerabilities_for_project(
            repo_url=test_repo,
            days_back=90
        )
        
        print(f"✅ Retrieved {len(false_positives)} false positive(s)")
        print(f"✅ Retrieved {len(confirmed_vulns)} confirmed vulnerability/ies")
        
        # Step 7: Format feedback for AI context
        print("\n🤖 Step 7: Formatting feedback for AI prompt context...")
        
        context = db.format_feedback_for_context(
            false_positives=false_positives,
            confirmed_vulnerabilities=confirmed_vulns
        )
        
        print("✅ Generated context for AI:")
        print("-" * 70)
        print(context)
        print("-" * 70)
        
        # Step 8: Verify statistics
        print("\n📊 Step 8: Checking database statistics...")
        
        stats = db.get_statistics(test_repo)
        
        print(f"✅ Database statistics:")
        print(f"   Total feedback: {stats['total_feedback']}")
        print(f"   False positives: {stats['false_positives']}")
        print(f"   Confirmed vulnerabilities: {stats['confirmed_vulnerabilities']}")
        
        # Validate results
        assert stats['total_feedback'] == 2, f"Expected 2 feedback records, got {stats['total_feedback']}"
        assert stats['false_positives'] == 1, f"Expected 1 false positive, got {stats['false_positives']}"
        assert stats['confirmed_vulnerabilities'] == 1, f"Expected 1 confirmed vulnerability, got {stats['confirmed_vulnerabilities']}"
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
        print("\n📝 Summary:")
        print("  1. ✅ Scan simulation successful")
        print("  2. ✅ Comment generation successful")
        print("  3. ✅ Feedback collection successful")
        print("  4. ✅ Feedback storage successful")
        print("  5. ✅ Feedback retrieval successful")
        print("  6. ✅ Context formatting successful")
        print("  7. ✅ Statistics verification successful")
        
        print("\n🎯 Next Steps:")
        print("  1. Create a PR in your repository")
        print("  2. Let AI-SAST scan it and post a comment")
        print("  3. Check boxes in the comment")
        print("  4. Watch the feedback-collection workflow run")
        print("  5. Future scans will use your feedback!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
            print(f"\n🧹 Cleaned up test database: {db_path}")


def test_feedback_parsing():
    """Test parsing of actual comment format"""
    
    print("\n" + "=" * 70)
    print("🧪 Testing Feedback Comment Parsing")
    print("=" * 70)
    
    from src.main.collect_feedback import parse_feedback_from_comment
    
    # Simulate an actual PR comment with checked boxes
    test_comment = """
### 🤖 AI-SAST Security Scan
**2** potential issue(s) found.

> 💡 **Help us improve!** Use the checkboxes below to mark each finding...

---

<details><summary>📄 **High Issues (2)**</summary>

---

<!-- vuln-id: abc12345 -->

- [x] ✅ True Positive
- [ ] ❌ False Positive

**ID**: `abc12345`
**Severity**: High
**Issue**: SQL Injection
**Location**: [`user_query.py:42`](https://github.com/org/repo/blob/main/user_query.py#L42)
**CVSS Vector**: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`

---

<!-- vuln-id: def67890 -->

- [ ] ✅ True Positive
- [x] ❌ False Positive

**ID**: `def67890`
**Severity**: High
**Issue**: Missing Authentication
**Location**: [`internal_api.py:25`](https://github.com/org/repo/blob/main/internal_api.py#L25)
**CVSS Vector**: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`

</details>
    """
    
    feedback_list = parse_feedback_from_comment(test_comment)
    
    print(f"\n✅ Parsed {len(feedback_list)} feedback item(s)")
    
    for i, fb in enumerate(feedback_list, 1):
        print(f"\n{i}. Vulnerability ID: {fb.get('vuln_id')}")
        print(f"   Issue: {fb.get('issue')}")
        print(f"   Status: {fb.get('status')}")
        print(f"   File: {fb.get('file_path')}")
        print(f"   Severity: {fb.get('severity')}")
    
    # Validate
    assert len(feedback_list) == 2, f"Expected 2 feedback items, got {len(feedback_list)}"
    assert feedback_list[0]['status'] == 'confirmed_vulnerability', "First should be true positive"
    assert feedback_list[1]['status'] == 'false_positive', "Second should be false positive"
    
    print("\n✅ Comment parsing test PASSED!")
    return True


def main():
    """Run all integration tests"""
    
    print("\n🚀 Starting AI-SAST Feedback Loop Integration Tests\n")
    
    tests = [
        ("Complete Feedback Loop", test_complete_feedback_loop),
        ("Comment Parsing", test_feedback_parsing)
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
    
    # Print final summary
    print("\n" + "=" * 70)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 70)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe feedback loop is working correctly!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
