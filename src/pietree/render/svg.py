from xml.etree.ElementTree import tostring
from xml.dom import minidom

from pietree.style import (
    StyleResolver,
    StyleSheet,
)

from .canvas import build_canvas
from .context import RenderContext

from .layers.background import render_background
from .layers.branches import render_branches
from .layers.nodes import render_nodes
from .layers.labels import render_labels
from .layers.highlights import render_highlights
from .layers.scale import render_scale

def _prettify(svg_element):

    rough = tostring(
        svg_element,
        encoding="unicode",
    )

    return minidom.parseString(rough).toprettyxml(indent="  ")

def render_svg(spec, resolver=None, style=None):

    if resolver is None:
        resolver = StyleResolver(StyleSheet([]))

    canvas = build_canvas(spec)
    sources = {e.source for e in spec.edges}

    context = RenderContext(
        spec=spec,
        svg=canvas["svg"],
        resolver=resolver,
        pos=canvas["pos"],

        canvas_width=canvas["canvas_width"],
        canvas_height=canvas["canvas_height"],

        padding_left=canvas["padding_left"],
        padding_right=canvas["padding_right"],
        padding_top=canvas["padding_top"],
        padding_bottom=canvas["padding_bottom"],

        sources=sources,
        
        highlights=style.highlights if style is not None else []
    )

    render_background(context)
    render_highlights(context)
    render_branches(context)
    render_nodes(context)
    render_labels(context)
    render_scale(context)

    return _prettify(context.svg)