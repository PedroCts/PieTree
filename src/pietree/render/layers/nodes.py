from xml.etree.ElementTree import SubElement

from pietree.style.defaults import *


def render_nodes(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos
    resolver = context.resolver
    sources = context.sources

    for node in spec.nodes:

        cx, cy = pos[node.id]

        is_tip = node.id not in sources

        style = resolver.resolve(node.node, context)

        if style.visible is False:
            continue

        # --------------------------------------------------
        # DEFAULTS
        # --------------------------------------------------

        fill = (
            style.fill or DEFAULT_NODE_FILL
            if is_tip
            else style.fill or DEFAULT_INTERNAL_FILL
        )
        radius = (
            style.radius or DEFAULT_NODE_RADIUS
            if is_tip
            else style.radius or DEFAULT_INTERNAL_RADIUS
        )
        stroke = (
            style.stroke
            or DEFAULT_STROKE
        )
        stroke_width = (
            style.stroke_width
            or DEFAULT_STROKE_WIDTH
        )
        opacity = (
            style.opacity
            or DEFAULT_OPACITY
        )

        # --------------------------------------------------
        # DRAW NODE
        # --------------------------------------------------

        SubElement(
            svg,
            "circle",
            {
                "cx": str(cx),
                "cy": str(cy),

                "r": str(radius),

                "fill": fill,

                "stroke": stroke,

                "stroke-width": str(
                    stroke_width
                ),

                "opacity": str(opacity),
            },
        )