from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .style import RenderStyle

from pietree.metadata.piemeta import PieMeta

from pietree.render.layers.nodes import RenderNode
from pietree.render.layers.labels import RenderLabel
from pietree.render.layers.branches import RenderEdge


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

        