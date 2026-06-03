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
        width=None,
        opacity: Optional[float] = 1.0,
        visible: Optional[bool] = True
    ):
        self.target = target
        
        self.fill = fill
        
        self.stroke = stroke
        self.stroke_width = stroke_width

        self.font_size = font_size
        self.font_color = font_color

        self.radius = radius
        
        self.width = width

        self.opacity = opacity
        
        self.visible = visible

    @property
    def items(self):
        return [
            "target",
            "fill",
            "stroke",
            "stroke_width",
            "radius",
            "font_size",
            "font_color",
            "width",
            "opacity",
            "visible"
        ]