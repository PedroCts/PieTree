from xml.etree.ElementTree import SubElement

from pietree.style.defaults import *
from pietree.render.layout import resolve_label_collisions


class RenderLabel:
    def __init__(self, node, text, x, y, is_tip=False, label_type="node", pie_label=None):
        self.node = node
        self.text = text
        self.x = x
        self.y = y
        self.label_type = label_type
        self.is_tip = is_tip
        self.pie_label = pie_label 

        # computed later
        self.final_x = x
        self.final_y = y
        
        self.metadata = []


def render_labels(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos
    resolver = context.resolver
    sources = context.sources
    
    labels = []

    for node in spec.nodes:

        if not node.label:
            continue

        cx, cy = pos[node.id]

        is_tip = node.id not in sources

        # --------------------------------------------------
        # LABEL POSITIONING
        # --------------------------------------------------

        if spec.orientation == "horizontal":

            if is_tip:
                px = cx + 10
                py = cy + 4
                anchor = "start"
            else:
                px = cx + 8
                py = cy + 4
                anchor = "start"

        else:

            if is_tip:
                px = cx
                py = cy + 18
                anchor = "middle"
            else:
                px = cx + 5
                py = cy - 5
                anchor = "start"
                
        labels.append(
            RenderLabel(
                node=node,
                x=px,
                y=py,
                text=node.node.label.text,
                is_tip=is_tip,
                pie_label=node.node.label
            )
        )

    # --------------------------------------------------
    # DRAW LABEL
    # --------------------------------------------------
    
    labels = resolve_label_collisions(
        labels=labels,
        nodes=spec.nodes,
        branches=spec.edges,
        pos=pos,
        max_shift=10
    )
    
    for label in labels:

        style = resolver.resolve(label, context)
        if label.pie_label is not None:
            label.pie_label.style.apply_to_rule(style)
        
        if style.visible is False:
            continue

        # ----------------------------
        # base styling (unchanged)
        # ----------------------------
        font_size = style.font_size or (DEFAULT_TIP_FONT_SIZE if label.is_tip else DEFAULT_INTERNAL_FONT_SIZE)
        font_color = style.font_color or (DEFAULT_TIP_FONT_COLOR if label.is_tip else DEFAULT_INTERNAL_FONT_COLOR)
        font_weight = style.font_weight or "normal"
        font_style_attr = style.font_style or "normal"
        text_decoration = style.text_decoration or "none"
        opacity = style.opacity or DEFAULT_OPACITY

        SubElement(
            svg,
            "text",
            {
                "x": str(label.final_x),
                "y": str(label.final_y),
                "font-size": str(font_size),
                "fill": str(font_color),
                "font-weight": font_weight,
                "font-style": font_style_attr,
                "text-decoration": text_decoration,
                "text-anchor": anchor,
                "opacity": str(opacity),
            },
        ).text = label.text