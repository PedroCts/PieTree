from dataclasses import dataclass
from typing import Optional, Literal

class StyleRule:

    def __init__(
        self,
        target: Literal['node', 'node_label', 'branch', 'branch_label', 'tip', 'tip_label', 'all'] = "node",
        fill=None,
        stroke=None,
        stroke_width=None,
        radius=None,
        font_size=None,
        font_color=None,
        font_weight: str | None = None,
        font_style: str | None = None,
        text_decoration: str | None = None,
        width=None,
        opacity: Optional[float] = 1.0,
        visible: Optional[bool] = True
    ):
        self.target = target
        
        self.fill = fill
        
        self.radius = radius
        self.width = width
        
        self.stroke = stroke
        self.stroke_width = stroke_width

        self.font_size = font_size
        self.font_color = font_color
        self.font_weight = font_weight
        self.font_style = font_style
        self.text_decoration = text_decoration

        self.opacity = opacity
        self.visible = visible

    @property
    def items(self):
        return [
            "target",
            "fill",
            "radius",
            "width",
            "stroke",
            "stroke_width",
            "font_size", "font_color", "font_weight", "font_style", "text_decoration",
            "opacity",
            "visible"
        ]