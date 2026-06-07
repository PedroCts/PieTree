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

        # final positions after collision resolution
        self.final_x = x
        self.final_y = y

        self.metadata = []


def render_labels(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos
    resolver = context.resolver
    sources = context.sources
    options = spec.options

    align = options.align_tip_labels and spec.mode != "ultrametric"

    # --------------------------------------------------
    # ALIGNMENT ANCHOR
    # For horizontal trees: the x of the rightmost tip.
    # For vertical trees:   the y of the bottommost tip.
    # Computed in screen space from pos directly.
    # --------------------------------------------------

    tip_ids = {node.id for node in spec.nodes if node.id not in sources}

    if align and tip_ids:
        align_anchor = context.tip_edge if spec.orientation == "horizontal" else context.tip_edge
    else:
        align_anchor = None

    labels = []

    for node in spec.nodes:

        if not node.label:
            continue
        
        is_tip = node.id not in sources
        
        if is_tip and not options.show_tip_labels:
            continue

        cx, cy = pos[node.id]

        # --------------------------------------------------
        # LABEL POSITIONING
        # When aligning, tip labels all start at align_anchor
        # instead of at their own node x/y.
        # --------------------------------------------------

        if spec.orientation == "horizontal":

            if is_tip and align_anchor is not None:
                px = align_anchor + 10
                py = cy + 4
                anchor = "start"
            elif is_tip:
                px = cx + 10
                py = cy + 4
                anchor = "start"
            else:
                px = cx + 8
                py = cy + 4
                anchor = "start"

        else:

            if is_tip and align_anchor is not None:
                px = cx
                py = align_anchor + 18
                anchor = "middle"
            elif is_tip:
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
                pie_label=node.node.label,
            )
        )
        
    # --------------------------------------------------
    # META NODE LABELS (from metadata().label_nodes())
    # --------------------------------------------------
    meta_label_index = {ml.node_id: ml for ml in getattr(spec, "meta_labels", [])}

    for node in spec.nodes:
        if node.id not in meta_label_index:
            continue
        if node.id not in sources:
            continue  # skip tips

        ml = meta_label_index[node.id]
        cx, cy = pos[node.id]

        if spec.orientation == "horizontal":
            px, py, anchor = cx + 8, cy - 6, "start"
        else:
            px, py, anchor = cx + 5, cy - 8, "start"

        rl = RenderLabel(node=node, text=ml.text, x=px, y=py, is_tip=False)
        rl._meta_font_size = ml.font_size
        rl._meta_font_color = ml.font_color
        labels.append(rl)

    # --------------------------------------------------
    # COLLISION RESOLUTION
    # Only run on non-aligned labels; aligned labels are
    # already on a clean grid and don't need nudging.
    # --------------------------------------------------

    if not align:
        labels = resolve_label_collisions(
            labels=labels,
            nodes=spec.nodes,
            branches=spec.edges,
            pos=pos,
            max_shift=10
        )

    # --------------------------------------------------
    # DRAW GUIDE LINES (before labels so labels sit on top)
    # --------------------------------------------------

    if align and align_anchor is not None:

        guide_color = options.tip_label_guide_color
        guide_width = str(options.tip_label_guide_width)
        guide_style = options.tip_label_guide_style   # "dashed", "dotted", "solid"

        dasharray = (
            "4,4" if guide_style == "dashed"
            else "2,2" if guide_style == "dotted"
            else "none"
        )

        for label in labels:

            if not label.is_tip:
                continue

            node_x, node_y = pos[label.node.id]

            if spec.orientation == "horizontal":
                # horizontal guide: from tip node right edge to align_anchor
                x1 = node_x + (options.tip_label_guide_gap if hasattr(options, "tip_label_guide_gap") else 8)
                y1 = node_y
                x2 = align_anchor
                y2 = node_y
            else:
                # vertical guide: from tip node bottom to align_anchor
                x1 = node_x
                y1 = node_y + (options.tip_label_guide_gap if hasattr(options, "tip_label_guide_gap") else 8)
                x2 = node_x
                y2 = align_anchor

            # skip guide if tip is already at the anchor (rightmost tip)
            if abs(x2 - x1) < 2 and abs(y2 - y1) < 2:
                continue

            attrs = {
                "x1": str(x1),
                "y1": str(y1),
                "x2": str(x2),
                "y2": str(y2),
                "stroke": guide_color,
                "stroke-width": guide_width,
            }
            if dasharray != "none":
                attrs["stroke-dasharray"] = dasharray

            SubElement(svg, "line", attrs)

    # --------------------------------------------------
    # DRAW LABELS
    # --------------------------------------------------

    for label in labels:

        style = resolver.resolve(label, context)
        if label.pie_label is not None:
            label.pie_label.style.apply_to_rule(style)

        if style.visible is False:
            continue

        font_size =  getattr(label, "_meta_font_size", None) or style.font_size or (DEFAULT_TIP_FONT_SIZE if label.is_tip else DEFAULT_INTERNAL_FONT_SIZE)
        font_color = getattr(label, "_meta_font_color", None) or style.font_color or (DEFAULT_TIP_FONT_COLOR if label.is_tip else DEFAULT_INTERNAL_FONT_COLOR)
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