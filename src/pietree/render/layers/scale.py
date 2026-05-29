from xml.etree.ElementTree import SubElement

def compute_scale_bar(spec, pos, scale_length):

    # estimate pixel-per-unit from layout
    # using first edge as approximation

    for e in spec.edges:
        x1, y1 = pos[e.source]
        x2, y2 = pos[e.target]

        dx = x2 - x1
        dy = y2 - y1

        dist = (dx**2 + dy**2) ** 0.5

        if e.length:
            return dist / e.length * scale_length

    return 50  # fallback

def render_scale(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos

    if not spec.scale_bar:
        return

    length = spec.scale_bar.get("length", 0.1)
    position = spec.scale_bar.get("position", "bottom_left")
    padding = spec.scale_bar.get("padding", 20)

    scale_px = compute_scale_bar(spec, pos, length)

    width = context.canvas_width
    height = context.canvas_height

    # --------------------------------------------------
    # POSITIONING
    # --------------------------------------------------

    if position == "bottom_left":
        x0 = padding
        y0 = height - padding

    elif position == "bottom_right":
        x0 = width - padding - scale_px
        y0 = height - padding

    else:  # bottom_center
        x0 = (width - scale_px) / 2
        y0 = height - padding

    x1 = x0 + scale_px
    y1 = y0

    # --------------------------------------------------
    # DRAW LINE
    # --------------------------------------------------

    SubElement(svg, "line", {
        "x1": str(x0),
        "y1": str(y0),
        "x2": str(x1),
        "y2": str(y1),
        "stroke": "black",
        "stroke-width": "2"
    })

    # --------------------------------------------------
    # LABEL
    # --------------------------------------------------

    SubElement(svg, "text", {
        "x": str((x0 + x1) / 2),
        "y": str(y0 + 15),
        "text-anchor": "middle",
        "font-size": "12",
        "fill": "black"
    }).text = str(length)