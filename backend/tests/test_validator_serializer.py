from app.domain.tree_engine import TreeEngine
from app.domain.validator_serializer import serialize_tree_for_validator

def test_serialize_tree_strips_ids():
    engine = TreeEngine()
    engine.add_segment("high_value_customers")
    engine.add_attribute("age", ">=", 25)

    serialized = serialize_tree_for_validator(engine.root)
    
    assert "id" not in serialized
    assert serialized["type"] == "OR"
    assert len(serialized["children"]) == 2
    assert serialized["children"][0] == {"type": "segment", "key": "high_value_customers"}
    assert serialized["children"][1] == {"type": "attribute", "attribute": "age", "operator": ">=", "value": 25}
