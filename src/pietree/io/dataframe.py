"""
dataframe.py
------------
DataFrame export for PieTree.

Converts a phylogenetic tree to a pandas DataFrame with one row per node,
including topology information, metadata, and optional inferred taxonomy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import _require

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    import pandas as pd


def to_dataframe(
    tree: "PieTree",
    include_topology: bool = True,
    infer_taxonomy: bool = True,
    **kwargs
) -> "pd.DataFrame":
    """
    Convert tree to a pandas DataFrame with one row per node.

    Parameters
    ----------
    tree : PieTree
        The tree to export.
    include_topology : bool, default True
        Include topology columns (depth, parent_id, n_children, etc.).
        Currently always included.
    infer_taxonomy : bool, default True
        If True and nodes have 'taxonomy' metadata, infer taxonomy for
        internal nodes and add as 'inferred_taxonomy' column.
    **kwargs
        Reserved for future options.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns:
        - **id**: node UUID
        - **name**: node name (or None)
        - **is_tip**: bool
        - **is_root**: bool
        - **depth**: number of edges from root
        - **parent_id**: UUID of parent node (None for root)
        - **branch_length**: float or None
        - **support**: float or None (from parent branch)
        - **n_children**: int
        - **n_descendants**: int
        - **n_desc_tips**: number of descendant tips
        - **label**: tip/node label text (or None)
        - **meta_<key>**: one column per metadata field (flattened one level)
        - **meta_inferred_taxonomy**: inferred taxonomy (if infer_taxonomy=True)

    Examples
    --------
    >>> df = tree.to_dataframe()
    >>> df.head()
    >>> df[df['is_tip']]['name'].tolist()  # all tip names

    >>> # Export to CSV
    >>> tree.to_dataframe().to_csv("tree_data.csv", index=False)

    Notes
    -----
    Metadata is flattened one level: top-level keys become columns prefixed
    with 'meta_'. Nested structures (lists, dicts) are preserved as-is in
    the cell values.
    """
    pd = _require("pandas")

    rows = []

    # Collect all metadata keys present anywhere in the tree
    all_meta_keys: set = set()
    for node in tree.traverse():
        if hasattr(node, "metadata") and node.metadata:
            all_meta_keys.update(node.metadata.data.keys())

    # Pre-compute inferred taxonomy for all nodes
    inferred_taxonomy: dict = {}
    if infer_taxonomy:
        from pietree.metadata.inference import infer_tree
        inferred_taxonomy = infer_tree(tree, "taxonomy")
        all_meta_keys.add("inferred_taxonomy")

    def _depth(node):
        """Compute depth from root."""
        d = 0
        cur = node
        while cur._parent is not None:
            cur = cur._parent
            d += 1
        return d

    for node in tree.traverse():
        # Find parent branch info
        parent_branch = None
        if node._parent is not None:
            for child, branch in node._parent._children:
                if child is node:
                    parent_branch = branch
                    break

        # Collect metadata
        meta = dict(node.metadata.data) if hasattr(node, "metadata") and node.metadata else {}
        if infer_taxonomy and "taxonomy" not in meta:
            inferred = inferred_taxonomy.get(node.id)
            if inferred is not None:
                meta["inferred_taxonomy"] = inferred

        # Compute descendant counts
        descendants = list(node.descendants) if hasattr(node, "descendants") else []
        desc_tips = [n for n in descendants if n.is_tip]

        # Build row
        row = {
            "id": node.id,
            "name": node.name,
            "is_tip": node.is_tip,
            "is_root": node.is_root,
            "depth": _depth(node),
            "parent_id": node._parent.id if node._parent else None,
            "branch_length": parent_branch.length if parent_branch else None,
            "support": parent_branch.support if parent_branch else None,
            "n_children": len(node._children),
            "n_descendants": len(descendants),
            "n_desc_tips": len(desc_tips),
            "label": node.label.text if hasattr(node, "label") and node.label else None,
        }

        # Flatten one-level metadata into columns
        for k in all_meta_keys:
            row[f"meta_{k}"] = meta.get(k)

        rows.append(row)

    return pd.DataFrame(rows)
