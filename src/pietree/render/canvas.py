from xml.etree.ElementTree import Element


def build_canvas(spec):

    padding_left = 50.0
    padding_right = 250.0
    padding_top = 50.0
    padding_bottom = 50.0

    canvas_width = 800
    canvas_height = 1200

    draw_w = (
        canvas_width
        - padding_left
        - padding_right
    )

    draw_h = (
        canvas_height
        - padding_top
        - padding_bottom
    )

    svg = Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(canvas_width),
            "height": str(canvas_height),
            "viewBox": (
                f"0 0 "
                f"{canvas_width} "
                f"{canvas_height}"
            ),
        },
    )

    all_x = [n.x for n in spec.nodes]
    all_y = [n.y for n in spec.nodes]

    x_min = min(all_x)
    x_max = max(all_x)

    y_min = min(all_y)
    y_max = max(all_y)

    x_range = (x_max - x_min) or 1.0
    y_range = (y_max - y_min) or 1.0

    def to_px(nx, ny):

        px = (
            padding_left
            + ((nx - x_min) / x_range)
            * draw_w
        )

        py = (
            padding_top
            + ((ny - y_min) / y_range)
            * draw_h
        )

        return px, py

    pos = {
        n.id: to_px(n.x, n.y)
        for n in spec.nodes
    }

    return {
        "svg": svg,
        "pos": pos,

        "canvas_width": canvas_width,
        "canvas_height": canvas_height,

        "padding_left": padding_left,
        "padding_right": padding_right,
        "padding_top": padding_top,
        "padding_bottom": padding_bottom,
    }