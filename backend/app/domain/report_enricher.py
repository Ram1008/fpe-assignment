import datetime
from typing import Dict, Any, List

def generate_profound_validation_report(
    raw_validator_report: Dict[str, Any],
    tree_dict: Dict[str, Any],
    segments_cache_timestamp: str,
    validator_url: str
) -> Dict[str, Any]:
    """
    Enriches the raw Validator API response with profound structural diagnostics,
    AST metrics, node depth, unique counts, and actionable fix recommendations.
    """
    is_valid = raw_validator_report.get("ok", False)
    raw_errors = raw_validator_report.get("errors", [])
    raw_warnings = raw_validator_report.get("warnings", [])

    # Calculate AST Metrics
    total_nodes = 0
    boolean_groups_count = {"OR": 0, "AND": 0, "total": 0}
    segments_count = 0
    attributes_count = 0
    segments_used = set()
    attributes_used = []
    max_depth = 0

    def traverse(node: Dict[str, Any], depth: int = 1):
        nonlocal total_nodes, segments_count, attributes_count, max_depth
        if not isinstance(node, dict):
            return

        total_nodes += 1
        max_depth = max(max_depth, depth)
        node_type = node.get("type")

        if node_type in ["AND", "OR"]:
            boolean_groups_count[node_type] = boolean_groups_count.get(node_type, 0) + 1
            boolean_groups_count["total"] += 1
            for child in node.get("children", []):
                traverse(child, depth + 1)
        elif node_type == "segment":
            segments_count += 1
            seg_key = node.get("key")
            if seg_key:
                segments_used.add(seg_key)
        elif node_type == "attribute":
            attributes_count += 1
            attributes_used.append({
                "attribute": node.get("attribute"),
                "operator": node.get("operator"),
                "value": node.get("value")
            })

    traverse(tree_dict)

    # Process and enrich errors with actionable fix recommendations
    enriched_errors = []
    for err in raw_errors:
        path = err.get("path", "#")
        code = err.get("code", "VALIDATION_ERROR")
        msg = err.get("message", "")
        recommendation = "Review and edit the specified tree node."

        # Actionable recommendations generator
        if "greater than max of 10000" in msg or "14600" in msg or "max of 10000" in msg:
            recommendation = "The attribute 'account_age_days' exceeds the validator schema limit of 10,000 days (~27.3 years). Set account_age_days <= 10000."
        elif "not in known segments" in msg.lower() or "unknown segment" in msg.lower():
            recommendation = "Segment key is not in the active catalog cache. Use a valid catalog segment key such as 'high_value_customers' or 'recently_active'."
        elif "invalid operator" in msg.lower():
            recommendation = "Check allowed operators for this attribute type (e.g. numeric attributes allow >=, <=, ==, !=, >, <)."

        enriched_errors.append({
            "path": path,
            "code": code,
            "message": msg,
            "actionable_recommendation": recommendation
        })

    # Structural recommendations and optimizations
    optimizations = []

    if is_valid:
        optimizations.append({
            "category": "VALIDATION",
            "level": "SUCCESS",
            "title": "Server Approved AST",
            "details": "The boolean decision tree AST strictly adheres to all external Validator schema rules and catalog constraints."
        })

    if total_nodes == 1 and tree_dict.get("type") in ["AND", "OR"] and len(tree_dict.get("children", [])) == 0:
        optimizations.append({
            "category": "TREE_STRUCTURE",
            "level": "WARNING",
            "title": "Empty Decision Tree Root",
            "details": "The decision tree currently contains no rules or segment filters. Add target segments or attribute criteria."
        })

    if max_depth > 4:
        optimizations.append({
            "category": "PERFORMANCE",
            "level": "INFO",
            "title": "Deep Tree Nesting Detected",
            "details": f"Decision tree has a depth of {max_depth}. Consider flattening nested boolean groups for improved evaluation speed."
        })

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return {
        "ok": is_valid,
        "summary": {
            "status": "PASSED" if is_valid else "FAILED",
            "validated_at": now_iso,
            "validator_service": validator_url,
            "segments_cache_timestamp": segments_cache_timestamp,
            "ast_metrics": {
                "total_nodes": total_nodes,
                "tree_depth": max_depth,
                "node_counts": {
                    "boolean_groups": boolean_groups_count,
                    "segments": segments_count,
                    "attributes": attributes_count
                }
            }
        },
        "structure_analysis": {
            "root_type": tree_dict.get("type"),
            "unique_segments_count": len(segments_used),
            "unique_segments_list": sorted(list(segments_used)),
            "attributes_used": attributes_used
        },
        "diagnostics": {
            "errors_count": len(enriched_errors),
            "errors": enriched_errors,
            "warnings_count": len(raw_warnings),
            "warnings": raw_warnings
        },
        "recommendations_and_insights": optimizations
    }
