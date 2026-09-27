import uuid
from typing import Optional, List, Dict, Any, Union, Literal
from app.domain.models import (
    TreeNodeModel, BooleanNodeModel, SegmentNodeModel, AttributeNodeModel, NodeType
)
from app.domain.validator_serializer import serialize_tree_for_validator

def generate_node_id() -> str:
    return f"node_{uuid.uuid4().hex[:8]}"

class TreeEngine:
    def __init__(self, root: Optional[TreeNodeModel] = None):
        if root is None:
            self.root = BooleanNodeModel(
                id=generate_node_id(),
                type=NodeType.OR,
                children=[]
            )
        else:
            self.root = root

    def find_node(self, node_id: str, current: Optional[TreeNodeModel] = None) -> Optional[TreeNodeModel]:
        if current is None:
            current = self.root
        if current.id == node_id:
            return current
        if isinstance(current, BooleanNodeModel):
            for child in current.children:
                found = self.find_node(node_id, child)
                if found:
                    return found
        return None

    def find_parent(self, node_id: str, current: Optional[TreeNodeModel] = None) -> Optional[BooleanNodeModel]:
        if current is None:
            current = self.root
        if isinstance(current, BooleanNodeModel):
            for child in current.children:
                if child.id == node_id:
                    return current
                found = self.find_parent(node_id, child)
                if found:
                    return found
        return None

    def add_segment(self, segment_key: str, parent_id: Optional[str] = None) -> SegmentNodeModel:
        new_node = SegmentNodeModel(id=generate_node_id(), key=segment_key)
        target = self.find_node(parent_id) if parent_id else self.root
        if target and isinstance(target, BooleanNodeModel):
            target.children.append(new_node)
        else:
            # Fallback to root if target is not a Boolean group
            if isinstance(self.root, BooleanNodeModel):
                self.root.children.append(new_node)
        return new_node

    def add_attribute(self, attribute: str, operator: str, value: Any, parent_id: Optional[str] = None) -> AttributeNodeModel:
        new_node = AttributeNodeModel(
            id=generate_node_id(),
            attribute=attribute,
            operator=operator,
            value=value
        )
        target = self.find_node(parent_id) if parent_id else self.root
        if target and isinstance(target, BooleanNodeModel):
            target.children.append(new_node)
        else:
            if isinstance(self.root, BooleanNodeModel):
                self.root.children.append(new_node)
        return new_node

    def remove_node(self, node_id: str) -> bool:
        if self.root.id == node_id:
            self.root = BooleanNodeModel(id=generate_node_id(), type=NodeType.OR, children=[])
            return True
        parent = self.find_parent(node_id)
        if parent and isinstance(parent, BooleanNodeModel):
            parent.children = [c for c in parent.children if c.id != node_id]
            self.prune_empty_groups()
            return True
        return False

    def replace_node(self, target_node_id: str, replacement: TreeNodeModel) -> bool:
        if self.root.id == target_node_id:
            self.root = replacement
            return True
        parent = self.find_parent(target_node_id)
        if parent and isinstance(parent, BooleanNodeModel):
            new_children = []
            for child in parent.children:
                if child.id == target_node_id:
                    new_children.append(replacement)
                else:
                    new_children.append(child)
            parent.children = new_children
            return True
        return False

    def add_boolean_group(self, group_type: Literal["AND", "OR"], children_ids: Optional[List[str]] = None, parent_id: Optional[str] = None) -> BooleanNodeModel:
        new_group = BooleanNodeModel(
            id=generate_node_id(),
            type=NodeType[group_type],
            children=[]
        )
        if children_ids:
            moved_nodes = []
            for cid in children_ids:
                node = self.find_node(cid)
                if node:
                    moved_nodes.append(node)
                    self.remove_node(cid)
            new_group.children = moved_nodes

        target = self.find_node(parent_id) if parent_id else self.root
        if target and isinstance(target, BooleanNodeModel):
            target.children.append(new_group)
        else:
            if isinstance(self.root, BooleanNodeModel):
                self.root.children.append(new_group)
        return new_group

    def prune_empty_groups(self, current: Optional[TreeNodeModel] = None) -> None:
        if current is None:
            current = self.root
        if isinstance(current, BooleanNodeModel):
            pruned_children = []
            for child in current.children:
                if isinstance(child, BooleanNodeModel):
                    self.prune_empty_groups(child)
                    # Retain child boolean group if it has 1+ children
                    if len(child.children) > 0:
                        pruned_children.append(child)
                else:
                    pruned_children.append(child)
            current.children = pruned_children

    def serialize_for_validator(self) -> Dict[str, Any]:
        return serialize_tree_for_validator(self.root)

    def to_dict(self) -> Dict[str, Any]:
        return self.root.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TreeEngine":
        if "type" in data:
            node_type = data["type"]
            if node_type == "segment":
                node = SegmentNodeModel(**data)
            elif node_type == "attribute":
                node = AttributeNodeModel(**data)
            elif node_type in ["AND", "OR"]:
                node = BooleanNodeModel(**data)
            else:
                raise ValueError(f"Unknown node type in dict: {node_type}")
            return cls(root=node)
        return cls()
