from xml.etree.ElementTree import SubElement
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PanelLayer:
    """
    A metadata side panel: one column of grouped bars rendered to the
    right of the tip labels, one bar per distinct metadata value.
    """
    field: str                          # metadata key to group by
    values: None | list[str] = None     # if given, only render these values
    index: int = 0                      # column index (0 = leftmost panel)

    line_width: float = 4.0
    color: Optional[str] = None         # falls back to options.panel_color
    font_size: Optional[float] = None   # falls back to options.panel_font_size
    font_color: Optional[str] = None    # falls back to options.panel_font_color


def render_panels(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos
    options = spec.options

    if not spec.panels:
        return

    # --------------------------------------------------
    # Coordinate helpers
    # --------------------------------------------------

    sources = context.sources
    tip_nodes = [n for n in spec.nodes if n.id not in sources]

    # Build lookup: node_id → PieNode (to read metadata)
    node_lookup = {n.id: n for n in spec.nodes}

    # Right edge where tip labels end (same anchor used by highlights)
    label_right = context.label_edge
    
    panel_label_padding = 4

    for panel in spec.panels:

        # --------------------------------------------------
        # Group tips by metadata value
        # --------------------------------------------------

        groups: dict[str, list] = {}

        for rnode in tip_nodes:
            pie_node = rnode.node
            value = pie_node.get(panel.field)
            if value is None:
                continue
            value = str(value)
            groups.setdefault(value, []).append(rnode.id)

        if not groups:
            continue

        # --------------------------------------------------
        # Panel x position — stack panels left to right
        # starting just past the label column
        # --------------------------------------------------

        spacing = options.panel_spacing
        col_x = (
            label_right
            + spacing                           # gap from label edge
            + panel.index * (panel.line_width + spacing + panel_label_padding)
        )

        color    = panel.color     or options.panel_color
        font_sz  = panel.font_size or options.panel_font_size
        font_col = panel.font_color or options.panel_font_color

        # --------------------------------------------------
        # Draw one bar per group value
        # --------------------------------------------------

        for value, node_ids in groups.items():

            if panel.values and value not in panel.values:
                continue

            if spec.orientation == "horizontal":

                ys = [pos[nid][1] for nid in node_ids if nid in pos]
                if not ys:
                    continue

                y_min = min(ys)
                y_max = max(ys)
                y_mid = (y_min + y_max) / 2

                # vertical bar
                SubElement(svg, "line", {
                    "x1": str(col_x),
                    "y1": str(y_min),
                    "x2": str(col_x),
                    "y2": str(y_max),
                    "stroke": color,
                    "stroke-width": str(panel.line_width),
                    "stroke-linecap": "round",
                })

                # label — rotated 90° centered on the bar
                SubElement(svg, "text", {
                    "x": str(col_x + font_sz + panel_label_padding),
                    "y": str(y_mid),
                    "font-size": str(font_sz),
                    "fill": font_col,
                    "text-anchor": "middle",
                    "dominant-baseline": "auto",
                    "transform": f"rotate(-90, {col_x + font_sz + panel_label_padding}, {y_mid})",
                }).text = value

            else:  # vertical tree

                xs = [pos[nid][0] for nid in node_ids if nid in pos]
                if not xs:
                    continue

                x_min = min(xs)
                x_max = max(xs)
                x_mid = (x_min + x_max) / 2

                # horizontal bar below the labels
                bar_y = (
                    context.canvas_height
                    - context.padding_bottom
                    + spacing
                    + panel.index * (panel.line_width + spacing)
                )

                SubElement(svg, "line", {
                    "x1": str(x_min),
                    "y1": str(bar_y),
                    "x2": str(x_max),
                    "y2": str(bar_y),
                    "stroke": color,
                    "stroke-width": str(panel.line_width),
                    "stroke-linecap": "round",
                })

                SubElement(svg, "text", {
                    "x": str(x_mid),
                    "y": str(bar_y + font_sz + panel_label_padding),
                    "font-size": str(font_sz),
                    "fill": font_col,
                    "text-anchor": "middle",
                }).text = value