from dataclasses import dataclass

# from pietree.render.spec import RenderSpec


@dataclass(slots=True)
class RenderContext:

    # spec: RenderSpec # Circular import if typed
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

    tip_edge:   float = 0.0   # screen coord of rightmost/bottommost tip node
    label_edge: float = 0.0   # screen coord where tip labels end → panels start

    registry: object = None
    highlights: list | None = None
