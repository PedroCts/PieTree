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
    show_duplicates=True,
    depth: Optional[int] = None,
    values: Optional[List[str]] = None,
    palette: str = "tab20",
    colors: Optional[Dict[str, str]] = None,
    opacity: float = 0.25,
    label: str | bool = True,
    scattered_label: bool = True,
    label_position: str = "upper_right",
    font_size: float = 11,
    font_color: str = "#444444",
    font_weight: str = "bold",
    padding: float = 10,
    corner_radius: float = 5,
    allow_single_tip: bool = False,
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
    # 1. Collect tips, handling both flat and hierarchical field values
    # ------------------------------------------------------------------
    tip_paths: Dict[str, List] = {}
    tip_flat: Dict[str, str] = {}

    for node in tree.tips:
        value = node.get(field)
        if isinstance(value, list) and value:
            tip_paths[node.id] = value
        elif isinstance(value, str) and value:
            tip_flat[node.id] = value

    is_flat = not tip_paths and bool(tip_flat)

    if not tip_paths and not tip_flat:
        return []

    # ------------------------------------------------------------------
    # 2. Build groups {taxon_name → [tip_node, ...]}
    # ------------------------------------------------------------------
    groups: Dict[str, List] = {}
    all_tip_nodes = {n.id: n for n in tree.tips}
    _values_set = set(values) if values is not None else None

    if is_flat:
        for tip_id, value in tip_flat.items():
            if _values_set is not None and value not in _values_set:
                continue
            groups.setdefault(value, []).append(all_tip_nodes[tip_id])
    else:
        for tip_id, path in tip_paths.items():
            tip_node = all_tip_nodes[tip_id]
            if depth is not None:
                if depth >= len(path):
                    continue
                key = path[depth]
            else:
                if _values_set is not None:
                    key = next((p for p in path if p in _values_set), path[-1])
                else:
                    key = path[-1]
            groups.setdefault(key, []).append(tip_node)

        if values is not None:
            groups = {k: v for k, v in groups.items() if k in _values_set}

    if not groups:
        return []

    # ------------------------------------------------------------------
    # 3. Assign colors
    # ------------------------------------------------------------------
    color_map = assign_colors(
        labels=list(groups.keys()),
        palette=palette,
        overrides=colors or {},
    )

    # ------------------------------------------------------------------
    # 4. Build RenderHighlights
    # ------------------------------------------------------------------
    created = []

    def _make_highlight(clade, taxon, label=label):
        
        if label and isinstance(label, str):
            label_text = label
        elif label and isinstance(label, bool):
            label_text = taxon
        else:
            label_text = None

        h = RenderHighlight(
            clade=clade,
            fill=color_map[taxon],
            opacity=opacity,
            label=label_text,
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

    for taxon, tip_nodes in groups.items():
        if not tip_nodes:
            continue

        if not show_duplicates:
            if not tree._meta_registry.claim(field, taxon, "highlight"):
                continue

        if is_flat:
            # Check if MRCA clade is pure (all its tips share this taxon value)
            clade = tree.clade(tip_nodes, allow_single_tip=allow_single_tip)
            all_tips_match = all(n.get(field) == taxon for n in clade.tips)

            if all_tips_match:
                _make_highlight(clade, taxon, label=label)
            else:
                # Scattered tips — highlight each individually, label only the first
                for i, tip_node in enumerate(tip_nodes):
                    tip_clade = tree.clade(tip_node, allow_single_tip=True)
                    _make_highlight(tip_clade, taxon, label=(label if scattered_label else (label and i == 0)))
        else:
            clade = tree.clade(tip_nodes, allow_single_tip=allow_single_tip)
            _make_highlight(clade, taxon, label=label)

    return created