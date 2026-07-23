from typing import Dict, Any
from app.domain.models import TreeNodeModel, BooleanNodeModel, SegmentNodeModel, AttributeNodeModel, NodeType

def serialize_tree_for_validator(node: TreeNodeModel) -> Dict[str, Any]:
    """
    Recursively converts an internal TreeNodeModel (with node IDs) into the exact JSON
    structure expected by the Validator API (/v1/validate).
    """
    if isinstance(node, dict):
        # Handle dictionary input if pre-parsed
        node_type = node.get("type")
        if node_type in ["AND", "OR"]:
            children = [_strip_node_ids(c) for c in node.get("children", [])]
            return {"type": node_type, "children": children}
        elif node_type == "segment":
            return {"type": "segment", "key": node.get("key")}
        elif node_type == "attribute":
            return {
                "type": "attribute",
                "attribute": node.get("attribute"),
                "operator": node.get("operator"),
                "value": node.get("value")
            }

    if node.type in [NodeType.AND, NodeType.OR]:
        assert isinstance(node, BooleanNodeModel)
        return {
            "type": node.type.value,
            "children": [serialize_tree_for_validator(c) for c in node.children]
        }
    elif node.type == NodeType.SEGMENT:
        assert isinstance(node, SegmentNodeModel)
        return {
            "type": "segment",
            "key": node.key
        }
    elif node.type == NodeType.ATTRIBUTE:
        assert isinstance(node, AttributeNodeModel)
        return {
            "type": "attribute",
            "attribute": node.attribute,
            "operator": node.operator,
            "value": node.value
        }
    
    raise ValueError(f"Unknown node type: {node.type}")

def _strip_node_ids(data: Dict[str, Any]) -> Dict[str, Any]:
    node_type = data.get("type")
    if node_type in ["AND", "OR"]:
        return {
            "type": node_type,
            "children": [_strip_node_ids(c) for c in data.get("children", [])]
        }
    elif node_type == "segment":
        return {"type": "segment", "key": data.get("key")}
    elif node_type == "attribute":
        return {
            "type": "attribute",
            "attribute": data.get("attribute"),
            "operator": data.get("operator"),
            "value": data.get("value")
        }
    return data
