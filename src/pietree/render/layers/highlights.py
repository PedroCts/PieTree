from xml.etree.ElementTree import SubElement
from dataclasses import dataclass
from typing import Optional, Literal

# Type alias
LabelPosition = Literal[
    "upper_left",   "upper_center",   "upper_right",
    "center_left",  "center",         "center_right",
    "lower_left",   "lower_center",   "lower_right",
]

@dataclass(slots=False)
class RenderHighlight:

    clade: object

    shape: str = "rect"

    fill: str = "#cccccc"
    opacity: float = 0.25
    padding: float = 10

    corner_radius: float = 5

    include_labels: bool = True

    # --------------------------------------------------
    # Label
    # --------------------------------------------------
    label: Optional[str] = None
    label_position: LabelPosition | None = "upper_right"
    font_size: float = 11
    font_color: str = "#444444"
    font_weight: str = "bold"


def _resolve_label_position(
    label_position: str,
    min_x: float, max_x: float,
    min_y: float, max_y: float,
    padding: float,
    font_size: float,
) -> tuple[float, float, str]:
    """
    Resolve a named label_position into (lx, ly, text_anchor).

    The 3×3 grid maps like this inside the rect:

        upper_left    upper_center    upper_right
        center_left   center          center_right
        lower_left    lower_center    lower_right

    lx/ly are in SVG screen coordinates.
    ly accounts for the SVG text baseline (font_size * 0.35 offset).
    """

    mid_x = (min_x + max_x) / 2
    mid_y = (min_y + max_y) / 2

    # SVG text y is the baseline, not the top of the glyph.
    # Shift down by ~35% of font_size so the visual center aligns.
    baseline = font_size * 0.35

    # --------------------------------------------------
    # HORIZONTAL component → lx, text_anchor
    # --------------------------------------------------
    h = label_position.split("_")[-1]           # left / center / right
    v = label_position.split("_")[0]             # upper / center / lower

    # edge case: bare "center"
    if label_position == "center":
        h, v = "center", "center"

    if h == "left":
        lx = min_x + padding
        anchor = "start"
    elif h == "right":
        lx = max_x - padding
        anchor = "end"
    else:                                        # center
        lx = mid_x
        anchor = "middle"

    # --------------------------------------------------
    # VERTICAL component → ly
    # --------------------------------------------------
    if v == "upper":
        ly = min_y + padding + font_size        # one line below top edge
    elif v == "lower":
        ly = max_y - padding                    # one line above bottom edge
    else:                                       # center
        ly = mid_y + baseline

    return lx, ly, anchor


def render_highlights(context):

    if not context.highlights:
        return

    spec = context.spec
    svg = context.svg
    pos = context.pos
    options = spec.options

    for highlight in context.highlights:

        clade = highlight.clade
        tips = clade.tips

        if not tips:
            continue

        # --------------------------------------------------
        # ROOT POSITION
        # --------------------------------------------------

        root_x, root_y = pos[clade.root.id]

        # --------------------------------------------------
        # TIP POSITIONS
        # --------------------------------------------------

        tip_xs = []
        tip_ys = []

        for node in tips:
            if node.id not in pos:
                continue
            x, y = pos[node.id]
            tip_xs.append(x)
            tip_ys.append(y)

        if not tip_xs:
            continue

        # --------------------------------------------------
        # BOUNDS
        # --------------------------------------------------

        if spec.orientation == "horizontal":

            min_x = root_x - highlight.padding

            if highlight.include_labels and options.show_tip_labels:
                max_x = context.label_edge - highlight.padding
            else:
                max_x = max(tip_xs) + highlight.padding

            min_y = min(tip_ys) - highlight.padding
            max_y = max(tip_ys) + highlight.padding

        else:

            min_x = min(tip_xs) - highlight.padding
            max_x = max(tip_xs) + highlight.padding

            min_y = root_y - highlight.padding

            if highlight.include_labels:
                max_y = context.label_edge - highlight.padding
            else:
                max_y = max(tip_ys) + highlight.padding

        # --------------------------------------------------
        # DRAW RECT
        # --------------------------------------------------

        SubElement(
            svg,
            "rect",
            {
                "x": str(min_x),
                "y": str(min_y),
                "width": str(max_x - min_x),
                "height": str(max_y - min_y),
                "fill": highlight.fill,
                "rx": str(highlight.corner_radius),
                "ry": str(highlight.corner_radius),
                "opacity": str(highlight.opacity),
            },
        )

        # --------------------------------------------------
        # DRAW LABEL
        # --------------------------------------------------

        label_text = highlight.label
        if not label_text:
            continue

        lx, ly, anchor = _resolve_label_position(
            label_position=highlight.label_position,
            min_x=min_x, max_x=max_x,
            min_y=min_y, max_y=max_y,
            padding=highlight.padding,
            font_size=highlight.font_size,
        )

        SubElement(
            svg,
            "text",
            {
                "x": str(lx),
                "y": str(ly),
                "font-size": str(highlight.font_size),
                "fill": highlight.font_color,
                "font-weight": highlight.font_weight,
                "text-anchor": anchor,
                "opacity": "1",
            },
        ).text = label_text
