from xml.etree.ElementTree import SubElement

from pietree.style.defaults import *


def render_branches(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos
    resolver = context.resolver

    for edge in spec.edges:

        style = resolver.resolve(edge.branch, context)

        if style.visible is False:
            continue

        parent_x, parent_y = pos[edge.source]
        child_x, child_y = pos[edge.target]
        
        stroke = (style.stroke or DEFAULT_STROKE)
        stroke_width = (style.stroke_width or DEFAULT_STROKE_WIDTH)
        opacity = (style.opacity or DEFAULT_OPACITY)

        if spec.orientation == "horizontal":

            SubElement(
                svg,
                "line",
                {
                    "x1": str(parent_x),
                    "y1": str(parent_y),
                    "x2": str(parent_x),
                    "y2": str(child_y),

                    "stroke": stroke,
                    "stroke-width": str(
                        stroke_width
                    ),

                    "opacity": str(opacity),
                },
            )

            SubElement(
                svg,
                "line",
                {
                    "x1": str(parent_x),
                    "y1": str(child_y),
                    "x2": str(child_x),
                    "y2": str(child_y),

                    "stroke": stroke,
                    "stroke-width": str(
                        stroke_width
                    ),

                    "opacity": str(opacity),
                },
            )

        else:

            SubElement(
                svg,
                "line",
                {
                    "x1": str(parent_x),
                    "y1": str(parent_y),
                    "x2": str(child_x),
                    "y2": str(parent_y),

                    "stroke": stroke,
                    "stroke-width": str(
                        stroke_width
                    ),

                    "opacity": str(opacity),
                },
            )

            SubElement(
                svg,
                "line",
                {
                    "x1": str(child_x),
                    "y1": str(parent_y),
                    "x2": str(child_x),
                    "y2": str(child_y),

                    "stroke": stroke,
                    "stroke-width": str(
                        stroke_width
                    ),

                    "opacity": str(opacity),
                },
            )