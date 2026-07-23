import pytest
from app.domain.tree_engine import TreeEngine
from app.domain.models import NodeType

def test_default_tree_engine_has_or_root():
    engine = TreeEngine()
    assert engine.root.type == NodeType.OR
    assert len(engine.root.children) == 0

def test_add_segment():
    engine = TreeEngine()
    seg = engine.add_segment("high_value_customers")
    assert seg.key == "high_value_customers"
    assert len(engine.root.children) == 1
    assert engine.root.children[0].id == seg.id

def test_add_attribute():
    engine = TreeEngine()
    attr = engine.add_attribute("age", ">=", 25)
    assert attr.attribute == "age"
    assert attr.operator == ">="
    assert attr.value == 25
    assert len(engine.root.children) == 1

def test_remove_node():
    engine = TreeEngine()
    seg1 = engine.add_segment("seg_1")
    seg2 = engine.add_segment("seg_2")
    assert len(engine.root.children) == 2

    success = engine.remove_node(seg1.id)
    assert success is True
    assert len(engine.root.children) == 1
    assert engine.root.children[0].id == seg2.id

def test_add_boolean_group():
    engine = TreeEngine()
    seg1 = engine.add_segment("seg_1")
    seg2 = engine.add_segment("seg_2")

    group = engine.add_boolean_group("AND", children_ids=[seg1.id, seg2.id])
    assert group.type == NodeType.AND
    assert len(group.children) == 2
    assert len(engine.root.children) == 1
