from .spec import RenderNode, RenderEdge, RenderSpec
from .layout import build_layout


def build_render_spec(tree):
    coords = build_layout(tree)

    nodes = []
    edges = []

    for node in tree.nodes():  # assuming NX or wrapper API
        x, y = coords[node.id]

        nodes.append(RenderNode(
            id=node.id,
            x=x,
            y=y,
            label=getattr(node, "label", None),
            depth=getattr(node, "depth", None),
            meta=getattr(node, "meta", None),
        ))

        for child in node.children:
            edges.append(RenderEdge(
                source=node.id,
                target=child.id
            ))

    return RenderSpec(
        nodes=nodes,
        edges=edges,
        width=max(n.x for n in nodes) + 1,
        height=max(n.y for n in nodes) + 1,
    )
