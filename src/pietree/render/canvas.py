from xml.etree.ElementTree import Element


# Approximate px-per-character for the default font at 1px font-size.
# Multiply by font_size to get px per char.
_CHAR_WIDTH_RATIO = 0.6


def _estimate_label_budget(spec) -> float:
    """
    Estimate the pixel width needed for tip labels.
    Uses the longest tip label text × font_size × char_width_ratio.
    Returns 0 if tip labels are disabled.
    """
    options = spec.options

    if not options.show_tip_labels:
        return 0.0

    sources = {e.source for e in spec.edges}
    tip_labels = [
        n.node.label.text
        for n in spec.nodes
        if n.id not in sources and n.node.label and n.node.label.text
    ]

    if not tip_labels:
        return 0.0

    max_chars = max(len(t) for t in tip_labels)
    font_size = options.font_size  # default tip font size
    gap = 10  # px gap between tip node and label start

    return gap + max_chars * font_size * _CHAR_WIDTH_RATIO


def _estimate_panel_budget(spec) -> float:
    """
    Estimate the total pixel width consumed by all registered panels.
    Returns 0 if no panels.
    """
    if not spec.panels:
        return 0.0

    options = spec.options
    n = len(spec.panels)
    spacing = options.panel_spacing

    # Each panel: line_width + spacing. Plus one leading spacing gap.
    total = spacing  # gap between label edge and first panel
    for panel in spec.panels:
        total += panel.line_width + spacing

    return total


def build_canvas(spec):

    canvas_width, canvas_height = spec.canvas_size

    padding_left   = 50.0
    padding_top    = 50.0
    padding_bottom = 50.0
    padding_margin = 20.0  # minimum right margin after all content

    # --------------------------------------------------
    # Compute content budgets
    # --------------------------------------------------

    label_budget = _estimate_label_budget(spec)
    panel_budget = _estimate_panel_budget(spec)

    right_content = label_budget + panel_budget + padding_margin

    # --------------------------------------------------
    # Draw area: the region the tree occupies
    # --------------------------------------------------

    draw_w = canvas_width  - padding_left  - right_content
    draw_h = canvas_height - padding_top   - padding_bottom

    # Guard: never let the tree be squeezed to nothing
    draw_w = max(draw_w, 100.0)
    draw_h = max(draw_h, 100.0)

    svg = Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width":  str(canvas_width),
            "height": str(canvas_height),
            "viewBox": f"0 0 {canvas_width} {canvas_height}",
        },
    )

    all_x = [n.x for n in spec.nodes]
    all_y = [n.y for n in spec.nodes]

    x_min = min(all_x);  x_max = max(all_x)
    y_min = min(all_y);  y_max = max(all_y)

    x_range = (x_max - x_min) or 1.0
    y_range = (y_max - y_min) or 1.0

    def to_px(nx, ny):
        px = padding_left + ((nx - x_min) / x_range) * draw_w
        py = padding_top  + ((ny - y_min) / y_range) * draw_h
        return px, py

    pos = {n.id: to_px(n.x, n.y) for n in spec.nodes}

    # --------------------------------------------------
    # Derived anchors — shared by labels, panels, highlights
    # --------------------------------------------------

    sources = {e.source for e in spec.edges}
    tip_ids = [n.id for n in spec.nodes if n.id not in sources]

    if tip_ids:
        if spec.orientation == "horizontal":
            tip_edge = max(pos[nid][0] for nid in tip_ids)  # rightmost tip x
        else:
            tip_edge = max(pos[nid][1] for nid in tip_ids)  # bottommost tip y
    else:
        tip_edge = (
            padding_left + draw_w if spec.orientation == "horizontal"
            else padding_top + draw_h
        )

    # label_edge: where tip label text ends (start of panels / highlight right edge)
    label_edge = tip_edge + label_budget

    return {
        "svg": svg,
        "pos": pos,

        "canvas_width":  canvas_width,
        "canvas_height": canvas_height,

        "padding_left":   padding_left,
        "padding_right":  right_content,   # actual right content width
        "padding_top":    padding_top,
        "padding_bottom": padding_bottom,

        # NEW — used by panels, highlights, and labels
        "tip_edge":   tip_edge,
        "label_edge": label_edge,
    }
