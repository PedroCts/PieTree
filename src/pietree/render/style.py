from dataclasses import dataclass, field

from pietree.tree.pieclade import PieClade
from pietree.render.layers.highlights import (
    Highlight
)

@dataclass
class RenderStyle:
    show_node_labels: bool = True
    show_tip_labels: bool = True
    show_branch_labels: bool = False
    show_support: bool = False

    support_threshold: float = 0.0
    branch_color: str = "#888"
    font_size: int = 12
    color: str = "#222"

    highlights: list = field(default_factory=list)
    
    def highlight(self, clade, **kwargs):

        if not isinstance(clade, PieClade):
            raise TypeError("Expected a PieClade instance")

        h = Highlight(
            clade,
            **kwargs,
        )

        self.highlights.append(h)

        return h