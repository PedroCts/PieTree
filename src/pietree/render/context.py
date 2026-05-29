from dataclasses import dataclass


@dataclass(slots=True)
class RenderContext:

    spec: object

    svg: object

    resolver: object

    pos: dict

    canvas_width: int
    canvas_height: int

    padding_left: float
    padding_right: float
    padding_top: float
    padding_bottom: float

    sources: set
    
    highlights: list | None = None