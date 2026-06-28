def analyze_plan(plan_json):
    """
    Walks through a Postgres EXPLAIN (ANALYZE, FORMAT JSON) result
    and returns a list of detected issues.
    """
    issues = []
    root_plan = plan_json[0]["Plan"]
    _walk_node(root_plan, issues)
    return issues


def _walk_node(node, issues):
    node_type = node.get("Node Type", "")

    # 1. Sequential scan on a table with many rows
    if node_type == "Seq Scan":
        actual_rows = node.get("Actual Rows", 0)
        rows_removed = node.get("Rows Removed by Filter", 0)
        total_rows_scanned = actual_rows + rows_removed
        has_filter = "Filter" in node

        if has_filter and total_rows_scanned > 1000:
            waste_ratio = rows_removed / total_rows_scanned if total_rows_scanned > 0 else 0

            if waste_ratio > 0.5:
                issues.append({
                    "severity": "high" if total_rows_scanned > 50000 else "medium",
                    "type": "sequential_scan",
                    "table": node.get("Relation Name", "unknown"),
                    "message": (
                        f"Sequential scan on '{node.get('Relation Name', 'unknown')}' "
                        f"scanned {total_rows_scanned} rows but discarded {rows_removed} of them "
                        f"({waste_ratio:.0%} wasted) to find {actual_rows} matches via filter "
                        f"\"{node.get('Filter')}\". Consider adding an index on the filtered column(s)."
                    )
                })
        elif not has_filter and total_rows_scanned > 50000:
            issues.append({
                "severity": "low",
                "type": "unfiltered_sequential_scan",
                "table": node.get("Relation Name", "unknown"),
                "message": (
                    f"Sequential scan on '{node.get('Relation Name', 'unknown')}' read all "
                    f"{total_rows_scanned} rows with no filter applied. This is likely necessary "
                    f"if the query intentionally needs every row, but worth double-checking "
                    f"if that wasn't the intent."
                )
            })

    # 2. Bad row estimates (planner guessed very wrong)
    estimated_rows = node.get("Plan Rows", 0)
    actual_rows = node.get("Actual Rows", 0)
    if estimated_rows > 0 and actual_rows > 0:
        ratio = actual_rows / estimated_rows
        if ratio > 10 or ratio < 0.1:
            issues.append({
                "severity": "medium",
                "type": "bad_row_estimate",
                "table": node.get("Relation Name", "unknown"),
                "message": (
                    f"Planner estimated {estimated_rows} rows but got {actual_rows} actual rows "
                    f"on '{node.get('Node Type')}'. This usually means table statistics are stale — "
                    f"try running ANALYZE on this table."
                )
            })

    # 3. Nested loop joins on large row counts
    if node_type == "Nested Loop":
        actual_rows = node.get("Actual Rows", 0)
        actual_loops = node.get("Actual Loops", 1)
        if actual_rows * actual_loops > 10000:
            issues.append({
                "severity": "high",
                "type": "expensive_nested_loop",
                "message": (
                    f"Nested Loop join processed approximately {actual_rows * actual_loops} "
                    f"row combinations. This join strategy scales poorly — consider whether "
                    f"a hash join or merge join would be more appropriate, often by ensuring "
                    f"join columns are indexed."
                )
            })

    # Recurse into child plan nodes
    for child in node.get("Plans", []):
        _walk_node(child, issues)
