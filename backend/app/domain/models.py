from enum import Enum
from typing import List, Union, Optional, Any, Literal
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    SEGMENT = "segment"
    ATTRIBUTE = "attribute"
    AND = "AND"
    OR = "OR"

class SegmentNodeModel(BaseModel):
    id: str = Field(..., description="Unique UUID node tracker")
    type: Literal[NodeType.SEGMENT] = NodeType.SEGMENT
    key: str

class AttributeNodeModel(BaseModel):
    id: str = Field(..., description="Unique UUID node tracker")
    type: Literal[NodeType.ATTRIBUTE] = NodeType.ATTRIBUTE
    attribute: str
    operator: str
    value: Union[str, int, float, bool, List[Union[str, int, float]]]

class BooleanNodeModel(BaseModel):
    id: str = Field(..., description="Unique UUID node tracker")
    type: Union[Literal[NodeType.AND], Literal[NodeType.OR]]
    children: List[Union[SegmentNodeModel, AttributeNodeModel, "BooleanNodeModel"]] = Field(default_factory=list)

TreeNodeModel = Union[SegmentNodeModel, AttributeNodeModel, BooleanNodeModel]
BooleanNodeModel.model_rebuild()

class ActionType(str, Enum):
    ADD_SEGMENT = "ADD_SEGMENT"
    ADD_ATTRIBUTE = "ADD_ATTRIBUTE"
    REMOVE_NODE = "REMOVE_NODE"
    REPLACE_NODE = "REPLACE_NODE"
    ADD_BOOLEAN_GROUP = "ADD_BOOLEAN_GROUP"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    VALIDATE_TREE = "VALIDATE_TREE"
    FINISH = "FINISH"

class AgentActionPayload(BaseModel):
    target_parent_id: Optional[str] = Field(None, description="UUID of parent group node to insert under")
    target_node_id: Optional[str] = Field(None, description="UUID of target node to replace or remove")
    segment_key: Optional[str] = Field(None, description="Segment key string")
    attribute: Optional[str] = Field(None, description="Attribute name")
    operator: Optional[str] = Field(None, description="Comparison operator")
    value: Optional[Any] = Field(None, description="Attribute filter value")
    group_type: Optional[Literal["AND", "OR"]] = Field(None, description="Boolean group type")
    question: Optional[str] = Field(None, description="Clarification question when input is ambiguous")
    options: Optional[List[str]] = Field(None, description="Suggested options for user choice")
    reasoning: Optional[str] = Field(None, description="Agent explanation of action taken")

class AgentAction(BaseModel):
    action: ActionType
    payload: AgentActionPayload
