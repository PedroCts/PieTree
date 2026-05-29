from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .style import RenderStyle
from pietree.tree.pienode import PieNode
from pietree.tree.piebranch import PieBranch
from pietree.metadata.piemeta import PieMeta

@dataclass
class RenderNode:
    id: str
    x: float
    y: float
    node: PieNode
    label: Optional[str] = None
    depth: Optional[int] = None
    metadata: Optional[PieMeta] = None


@dataclass
class RenderEdge:
    source: str
    target: str
    length: float
    label: str
    branch: PieBranch
    metadata: Optional[PieMeta] = None


@dataclass
class RenderSpec:
    nodes: List[RenderNode]
    edges: List[RenderEdge]
    width: float
    height: float

    mode: str = "phylogram"
    orientation: str = "horizontal"
    style: RenderStyle = RenderStyle()
    
    metadata: Optional[PieMeta] = None
    
    scale_bar: dict | None = None
    
class RenderLabel:
    def __init__(self, node, text, x, y, is_tip=False, label_type="node"):
        self.node = node
        self.text = text
        self.x = x
        self.y = y
        self.label_type = label_type
        self.is_tip = is_tip

        # computed later
        self.final_x = x
        self.final_y = y
        
        self.metadata = []
        