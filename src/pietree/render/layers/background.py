from xml.etree.ElementTree import SubElement

def render_background(context):

    SubElement(
        context.svg,
        "rect",
        {
            "x": "0",
            "y": "0",

            "width": str(context.canvas_width),
            "height": str(context.canvas_height),
            "fill": "white",
        },
    )
