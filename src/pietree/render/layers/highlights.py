from xml.etree.ElementTree import SubElement
from dataclasses import dataclass

from pietree.tree.pieclade import PieClade

@dataclass(slots=True)
class Highlight:

    clade: PieClade

    shape: str = "rect"
    
    fill: str = "#cccccc"
    opacity: float = 0.25
    padding: float = 10
    
    include_labels: bool = True
    
def render_highlights(context):

    if not context.highlights:
        return

    spec = context.spec
    svg = context.svg
    pos = context.pos

    for highlight in context.highlights:

        clade = highlight.clade

        tips = clade.tips

        if not tips:
            continue

        # --------------------------------------------------
        # ROOT POSITION
        # --------------------------------------------------

        root_x, root_y = pos[
            clade.root.id
        ]

        # --------------------------------------------------
        # TIP POSITIONS
        # --------------------------------------------------

        tip_xs = []
        tip_ys = []

        for node in tips:

            if node.id not in pos:
                continue

            x, y = pos[node.id]

            tip_xs.append(x)
            tip_ys.append(y)

        if not tip_xs:
            continue

        # --------------------------------------------------
        # BOUNDS
        # --------------------------------------------------

        if spec.orientation == "horizontal":

            min_x = (
                root_x
                - highlight.padding
            )

            max_x = (
                max(tip_xs)
                + highlight.padding
            )

            min_y = (
                min(tip_ys)
                - highlight.padding
            )

            max_y = (
                max(tip_ys)
                + highlight.padding
            )

            # label extension

            if highlight.include_labels:

                max_x += 140

        else:

            min_x = (
                min(tip_xs)
                - highlight.padding
            )

            max_x = (
                max(tip_xs)
                + highlight.padding
            )

            min_y = (
                root_y
                - highlight.padding
            )

            max_y = (
                max(tip_ys)
                + highlight.padding
            )

        # --------------------------------------------------
        # DRAW
        # --------------------------------------------------

        SubElement(
            svg,
            "rect",
            {
                "x": str(min_x),
                "y": str(min_y),

                "width": str(
                    max_x - min_x
                ),

                "height": str(
                    max_y - min_y
                ),

                "fill": highlight.fill,

                "opacity": str(
                    highlight.opacity
                ),
            },
        )