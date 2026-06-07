from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .options import RenderOptions

from pietree.metadata.piemeta import PieMeta

from pietree.render.layers.nodes import RenderNode
from pietree.render.layers.labels import RenderLabel
from pietree.render.layers.branches import RenderEdge
from pietree.render.layers.panels import PanelLayer


@dataclass
class RenderSpec:
    
    width: float
    height: float
    
    nodes: List[RenderNode]
    edges: List[RenderEdge]
    
    registry: object = None
    
    highlights: list = field(default_factory=list)
    panels: list[PanelLayer] = field(default_factory=list)
    meta_labels: list = field(default_factory=list)

    mode: str = "phylogram"
    orientation: str = "horizontal"
    
    options: RenderOptions = field(default_factory=RenderOptions)

    metadata: Optional[PieMeta] = None
    
    scale_bar: dict | None = None
    
    canvas_size: tuple[int, int] = (1000, 1000)

        