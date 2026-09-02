import math
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


def _circular_sector_path(cx, cy, r_inner, r_outer, theta1_deg, theta2_deg, padding_deg=0.0):
    """
    Build an SVG path string for an annular sector (donut slice).

    Parameters
    ----------
    cx, cy      : canvas centre
    r_inner     : inner radius (px) — set to 0 for a pie slice
    r_outer     : outer radius (px)
    theta1_deg  : start angle (degrees, SVG convention: 0=right, clockwise)
    theta2_deg  : end angle (degrees)
    padding_deg : angular padding added on each side
    """
    t1 = math.radians(theta1_deg - padding_deg)
    t2 = math.radians(theta2_deg + padding_deg)

    # Clamp so t2 > t1
    if t2 <= t1:
        t2 += 2 * math.pi

    large_arc = 1 if (t2 - t1) > math.pi else 0

    # Outer arc corners
    ox1 = cx + r_outer * math.cos(t1)
    oy1 = cy + r_outer * math.sin(t1)
    ox2 = cx + r_outer * math.cos(t2)
    oy2 = cy + r_outer * math.sin(t2)

    if r_inner <= 0:
        # Pie slice
        d = (
            f"M {cx:.2f} {cy:.2f} "
            f"L {ox1:.2f} {oy1:.2f} "
            f"A {r_outer:.2f} {r_outer:.2f} 0 {large_arc} 1 {ox2:.2f} {oy2:.2f} "
            f"Z"
        )
    else:
        # Annular sector
        ix1 = cx + r_inner * math.cos(t1)
        iy1 = cy + r_inner * math.sin(t1)
        ix2 = cx + r_inner * math.cos(t2)
        iy2 = cy + r_inner * math.sin(t2)
        d = (
            f"M {ox1:.2f} {oy1:.2f} "
            f"A {r_outer:.2f} {r_outer:.2f} 0 {large_arc} 1 {ox2:.2f} {oy2:.2f} "
            f"L {ix2:.2f} {iy2:.2f} "
            f"A {r_inner:.2f} {r_inner:.2f} 0 {large_arc} 0 {ix1:.2f} {iy1:.2f} "
            f"Z"
        )
    return d


def _render_circular_highlight(svg, context, highlight):
    """Draw a clade highlight as an annular sector for circular trees."""
    spec    = context.spec
    pos     = context.pos
    meta    = spec.circular_meta or {}
    cx      = context.circular_cx
    cy      = context.circular_cy

    if cx is None:
        return

    clade = highlight.clade
    tips  = clade.tips
    if not tips:
        return

    # Collect tip angles
    tip_angles = [meta[n.id]["angle"] for n in tips if n.id in meta]
    if not tip_angles:
        return

    theta_min = min(tip_angles)
    theta_max = max(tip_angles)

    # Radii
    clade_root_meta = meta.get(clade.root.id, {})
    r_inner_data = clade_root_meta.get("r", 0.0)
    scale = context.circular_scale or 1.0
    r_inner_px = r_inner_data * scale - highlight.padding

    if highlight.include_labels and spec.options.show_tip_labels:
        r_outer_px = context.label_edge + highlight.padding
    else:
        r_outer_px = context.tip_edge + highlight.padding

    r_inner_px = max(r_inner_px, 0.0)

    d = _circular_sector_path(
        cx, cy,
        r_inner_px, r_outer_px,
        theta_min, theta_max,
        padding_deg=0.5,
    )

    SubElement(svg, "path", {
        "d": d,
        "fill": highlight.fill,
        "opacity": str(highlight.opacity),
    })

    # Label at midpoint of the outer arc
    if highlight.label:
        mid_angle = math.radians((theta_min + theta_max) / 2)
        lx = cx + (r_outer_px + highlight.font_size) * math.cos(mid_angle)
        ly = cy + (r_outer_px + highlight.font_size) * math.sin(mid_angle)
        SubElement(svg, "text", {
            "x": f"{lx:.2f}",
            "y": f"{ly:.2f}",
            "font-size": str(highlight.font_size),
            "fill": highlight.font_color,
            "font-weight": highlight.font_weight,
            "text-anchor": "middle",
            "opacity": "1",
        }).text = highlight.label


def render_highlights(context):

    if not context.highlights:
        return

    spec = context.spec
    svg = context.svg
    pos = context.pos
    options = spec.options

    for highlight in context.highlights:

        if spec.mode == "circular":
            _render_circular_highlight(svg, context, highlight)
            continue

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
