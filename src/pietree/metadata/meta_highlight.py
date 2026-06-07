"""
meta_highlight.py
-----------------
Automatic clade highlighting driven by hierarchical metadata.

Entry point
-----------
    highlight_metadata(tree, field, ...)

Called by MetadataView.highlight().  Mutates tree._highlights in-place,
exactly like a manual clade.highlight() call does.
"""

from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree

from pietree.metadata.inference import infer_tree
from pietree.metadata.palette import assign_colors


def highlight_metadata(
    tree: "PieTree",
    field: str,
    *,
    depth: Optional[int] = None,
    values: Optional[List[str]] = None,
    palette: str = "tab20",
    colors: Optional[Dict[str, str]] = None,
    opacity: float = 0.25,
    label_position: str = "upper_right",
    font_size: float = 11,
    font_color: str = "#444444",
    font_weight: str = "bold",
    padding: float = 10,
    corner_radius: float = 5,
    **highlight_kwargs,
) -> List:
    """
    Automatically create clade highlights from a hierarchical metadata field.

    For each distinct value that appears at the requested *depth* of the
    inferred hierarchy, the function:

    1. Finds all tips whose inferred path contains that value.
    2. Computes their MRCA → builds a :class:`PieClade`.
    3. Appends a :class:`RenderHighlight` to ``tree._highlights``.

    Parameters
    ----------
    tree : PieTree
    field : str
        Metadata field whose values are hierarchical lists.
    depth : int, optional
        Which level of the hierarchy to highlight (0 = root taxon, 1 = next,
        …).  When omitted, the **deepest level at which all member tips still
        agree** is used for each group independently — i.e. the full inferred
        value for each internal node is used as-is.
    values : list of str, optional
        Restrict highlighting to these specific taxon names.  When omitted,
        every distinct value at the target depth is highlighted.
    palette : str
        Named color palette for automatic color assignment (default
        ``'tab20'``).  Ignored for labels that appear in *colors*.
    colors : dict, optional
        ``{taxon_name: hex_color}`` overrides.  Any taxon not listed here
        falls back to the palette.
    opacity : float
        Fill opacity for every generated highlight rect.
    label_position : str
        Position keyword passed to :class:`RenderHighlight`.
    font_size, font_color, font_weight, padding, corner_radius
        Visual parameters forwarded to :class:`RenderHighlight`.
    **highlight_kwargs
        Any additional keyword arguments are forwarded verbatim to
        :class:`RenderHighlight`, letting callers tweak shape etc.

    Returns
    -------
    list of RenderHighlight
        The highlights that were appended to ``tree._highlights``.
    """
    from pietree.render.layers.highlights import RenderHighlight

    # ------------------------------------------------------------------
    # 1. Run inference once for the whole tree
    # ------------------------------------------------------------------
    inferred: Dict[str, Optional[List]] = infer_tree(tree, field)

    # ------------------------------------------------------------------
    # 2. Collect all tips and their inferred paths
    # ------------------------------------------------------------------
    tip_paths: Dict[str, List] = {}   # node_id → inferred path

    for node in tree.tips:
        path = inferred.get(node.id)
        if path:
            tip_paths[node.id] = path

    if not tip_paths:
        return []

    # ------------------------------------------------------------------
    # 3. Determine the depth slice we are highlighting
    #
    #    depth=None  → group by the *full inferred path* of each MRCA
    #                  (i.e. whatever the MRCA's inferred value is).
    #    depth=N     → group by path[N] (the element at position N).
    # ------------------------------------------------------------------

    # Build {taxon_name → [tip_node, ...]}
    groups: Dict[str, List] = {}

    all_tip_nodes = {n.id: n for n in tree.tips}

    for tip_id, path in tip_paths.items():
        tip_node = all_tip_nodes[tip_id]

        if depth is not None:
            if depth >= len(path):
                # This tip's path doesn't reach the requested depth — skip.
                continue
            key = path[depth]
        else:
            # Use the most specific (last) element of the inferred path.
            key = path[-1]

        groups.setdefault(key, []).append(tip_node)

    if not groups:
        return []

    # ------------------------------------------------------------------
    # 4. Apply the `values` filter
    # ------------------------------------------------------------------
    if values is not None:
        values_set = set(values)
        groups = {k: v for k, v in groups.items() if k in values_set}

    if not groups:
        return []

    # ------------------------------------------------------------------
    # 5. Assign colors
    # ------------------------------------------------------------------
    color_map = assign_colors(
        labels=list(groups.keys()),
        palette=palette,
        overrides=colors or {},
    )

    # ------------------------------------------------------------------
    # 6. Build one PieClade + RenderHighlight per group
    # ------------------------------------------------------------------
    created = []

    for taxon, tip_nodes in groups.items():

        if not tip_nodes:
            continue

        # MRCA of the tips in this group
        clade = tree.clade(tip_nodes)   # returns PieClade, shares tree._highlights

        h = RenderHighlight(
            clade=clade,
            fill=color_map[taxon],
            opacity=opacity,
            label=taxon,
            label_position=label_position,
            font_size=font_size,
            font_color=font_color,
            font_weight=font_weight,
            padding=padding,
            corner_radius=corner_radius,
            **highlight_kwargs,
        )

        tree._highlights.append(h)
        created.append(h)

    return created