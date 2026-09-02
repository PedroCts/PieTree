import math
from xml.etree.ElementTree import SubElement

from typing import Optional
from dataclasses import dataclass

from pietree.render.context import RenderContext
from pietree.style.defaults import *
from pietree.tree.piebranch import PieBranch
from pietree.metadata.piemeta import PieMeta

@dataclass
class RenderEdge:
    source: str
    target: str
    length: float
    label: str
    branch: PieBranch
    metadata: Optional[PieMeta] = None


def _circular_branch(svg, context, edge, stroke, stroke_width, opacity):
    """
    Draw one edge in circular (polar) mode.

    Each edge consists of two segments:
      1. An arc at the parent's radius, sweeping from the parent's angle
         to the child's angle.
      2. A radial line from the arc end-point to the child's pixel position.
    """
    meta = context.spec.circular_meta or {}
    cx = context.circular_cx
    cy = context.circular_cy
    scale = context.circular_scale

    if cx is None or scale is None or edge.source not in meta or edge.target not in meta:
        return  # fall back to nothing if meta is missing

    parent_meta = meta[edge.source]
    child_meta  = meta[edge.target]

    parent_r_px  = parent_meta["r"] * scale
    child_angle  = math.radians(child_meta["angle"])
    parent_angle = math.radians(parent_meta["angle"])

    # Arc end-point: parent radius, at child's angle
    arc_x = cx + parent_r_px * math.cos(child_angle)
    arc_y = cy + parent_r_px * math.sin(child_angle)

    # Arc start-point: parent radius, at parent's angle
    arc_sx = cx + parent_r_px * math.cos(parent_angle)
    arc_sy = cy + parent_r_px * math.sin(parent_angle)

    # Child pixel position (already in pos dict)
    child_x, child_y = context.pos[edge.target]

    # Determine sweep direction and large-arc flag.
    # We always sweep in the direction of increasing angle (sweep-flag=1 in SVG).
    d_angle = child_meta["angle"] - parent_meta["angle"]
    # Normalise to (-180, 180]
    d_angle = (d_angle + 180) % 360 - 180
    large_arc = 1 if abs(d_angle) > 180 else 0
    sweep = 1 if d_angle >= 0 else 0

    attrs = {
        "stroke": stroke,
        "stroke-width": str(stroke_width),
        "opacity": str(opacity),
        "fill": "none",
    }

    # Only draw arc if parent radius > 0 (root has r=0)
    if parent_r_px > 0.5:
        arc_d = (
            f"M {arc_sx:.3f} {arc_sy:.3f} "
            f"A {parent_r_px:.3f} {parent_r_px:.3f} 0 {large_arc} {sweep} "
            f"{arc_x:.3f} {arc_y:.3f}"
        )
        SubElement(svg, "path", {**attrs, "d": arc_d})

    # Radial line from arc end-point to child position
    SubElement(svg, "line", {
        "x1": f"{arc_x:.3f}",
        "y1": f"{arc_y:.3f}",
        "x2": f"{child_x:.3f}",
        "y2": f"{child_y:.3f}",
        "stroke": stroke,
        "stroke-width": str(stroke_width),
        "opacity": str(opacity),
    })


def render_branches(context: RenderContext):

    spec = context.spec
    svg = context.svg
    pos = context.pos
    resolver = context.resolver

    for edge in spec.edges:

        style = resolver.resolve(edge.branch, context)
        edge.branch.style.apply_to_rule(style)

        if style.visible is False:
            continue

        parent_x, parent_y = pos[edge.source]
        child_x, child_y = pos[edge.target]

        stroke = (style.stroke or DEFAULT_STROKE)
        stroke_width = (style.stroke_width or DEFAULT_STROKE_WIDTH)
        opacity = (style.opacity or DEFAULT_OPACITY)

        if spec.mode == "circular":
            _circular_branch(svg, context, edge, stroke, stroke_width, opacity)
            continue

        if spec.orientation == "horizontal":

            SubElement(
                svg, "line",
                {
                    "x1": str(parent_x),
                    "y1": str(parent_y),
                    "x2": str(parent_x),
                    "y2": str(child_y),

                    "stroke": stroke,
                    "stroke-width": str(stroke_width),
                    "opacity": str(opacity),
                },
            )

            SubElement(
                svg, "line",
                {
                    "x1": str(parent_x),
                    "y1": str(child_y),
                    "x2": str(child_x),
                    "y2": str(child_y),

                    "stroke": stroke,
                    "stroke-width": str(stroke_width),
                    "opacity": str(opacity),
                },
            )

        else:

            SubElement(
                svg, "line",
                {
                    "x1": str(parent_x),
                    "y1": str(parent_y),
                    "x2": str(child_x),
                    "y2": str(parent_y),

                    "stroke": stroke,
                    "stroke-width": str(stroke_width),
                    "opacity": str(opacity),
                },
            )

            SubElement(
                svg, "line",
                {
                    "x1": str(child_x),
                    "y1": str(parent_y),
                    "x2": str(child_x),
                    "y2": str(child_y),

                    "stroke": stroke,
                    "stroke-width": str(stroke_width),
                    "opacity": str(opacity),
                },
            )
