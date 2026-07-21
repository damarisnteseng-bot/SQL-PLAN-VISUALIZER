import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.analyzer.rules import analyze_plan

def make_plan(node):
    """Helper to wrap a plan node in the format EXPLAIN returns."""
    return [{"Plan": node, "Planning Time": 1.0, "Execution Time": 10.0, "Triggers": []}]

def test_sequential_scan_with_filter_flags_issue():
    plan = make_plan({
        "Node Type": "Seq Scan",
        "Relation Name": "orders",
        "Actual Rows": 10,
        "Actual Loops": 1,
        "Plan Rows": 10,
        "Filter": "(order_status = 'pending')",
        "Rows Removed by Filter": 99990,
        "Plans": []
    })
    issues = analyze_plan(plan)
    assert len(issues) == 1
    assert issues[0]["type"] == "sequential_scan"
    assert issues[0]["severity"] == "high"
    assert "suggested_index" in issues[0]
    print("PASS: sequential scan with filter correctly flagged")

def test_sequential_scan_without_filter_is_low_severity():
    plan = make_plan({
        "Node Type": "Seq Scan",
        "Relation Name": "order_items",
        "Actual Rows": 500000,
        "Actual Loops": 1,
        "Plan Rows": 500000,
        "Plans": []
    })
    issues = analyze_plan(plan)
    assert len(issues) == 1
    assert issues[0]["type"] == "unfiltered_sequential_scan"
    assert issues[0]["severity"] == "low"
    print("PASS: unfiltered sequential scan correctly flagged as low severity")

def test_small_sequential_scan_not_flagged():
    plan = make_plan({
        "Node Type": "Seq Scan",
        "Relation Name": "products",
        "Actual Rows": 50,
        "Actual Loops": 1,
        "Plan Rows": 50,
        "Filter": "(category = 'Books')",
        "Rows Removed by Filter": 100,
        "Plans": []
    })
    issues = analyze_plan(plan)
    assert len(issues) == 0
    print("PASS: small sequential scan correctly not flagged")

def test_bad_row_estimate_flagged():
    plan = make_plan({
        "Node Type": "Seq Scan",
        "Relation Name": "orders",
        "Actual Rows": 50000,
        "Actual Loops": 1,
        "Plan Rows": 1,
        "Plans": []
    })
    issues = analyze_plan(plan)
    assert any(i["type"] == "bad_row_estimate" for i in issues)
    print("PASS: bad row estimate correctly flagged")

def test_bad_row_estimate_not_flagged_under_limit():
    plan = make_plan({
        "Node Type": "Limit",
        "Actual Rows": 50000,
        "Actual Loops": 1,
        "Plan Rows": 50000,
        "Plans": [{
            "Node Type": "Nested Loop",
            "Actual Rows": 50000,
            "Actual Loops": 1,
            "Plan Rows": 1,
            "Plans": []
        }]
    })
    issues = analyze_plan(plan)
    assert not any(i["type"] == "bad_row_estimate" for i in issues)
    print("PASS: bad row estimate correctly suppressed under LIMIT node")

def test_expensive_nested_loop_flagged():
    plan = make_plan({
        "Node Type": "Nested Loop",
        "Actual Rows": 50000,
        "Actual Loops": 1,
        "Plan Rows": 50000,
        "Plans": []
    })
    issues = analyze_plan(plan)
    assert any(i["type"] == "expensive_nested_loop" for i in issues)
    print("PASS: expensive nested loop correctly flagged")

def test_clean_index_scan_no_issues():
    plan = make_plan({
        "Node Type": "Index Scan",
        "Relation Name": "orders",
        "Index Name": "idx_orders_customer_id",
        "Actual Rows": 37,
        "Actual Loops": 1,
        "Plan Rows": 40,
        "Plans": []
    })
    issues = analyze_plan(plan)
    assert len(issues) == 0
    print("PASS: clean index scan correctly produces no issues")

if __name__ == "__main__":
    test_sequential_scan_with_filter_flags_issue()
    test_sequential_scan_without_filter_is_low_severity()
    test_small_sequential_scan_not_flagged()
    test_bad_row_estimate_flagged()
    test_bad_row_estimate_not_flagged_under_limit()
    test_expensive_nested_loop_flagged()
    test_clean_index_scan_no_issues()
    print("\nAll 7 tests passed!")
