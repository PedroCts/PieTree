"""
inference.py
------------
Hierarchical metadata inference for PieTree.

Given a metadata field whose values are lists representing a hierarchical
path (e.g. ["Animalia", "Chordata", "Mammalia"]), this module infers the
value for any internal node by computing the longest common prefix of the
paths stored on its descendant tips.

Nothing is written back to the tree — all results are computed on the fly
and returned as plain dicts.
"""

from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pienode import PieNode


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def longest_common_prefix(paths: List[List]) -> List:
    """
    Return the longest common prefix shared by all *paths*.

    Parameters
    ----------
    paths : list of list
        Each element is an ordered sequence representing one hierarchical path.

    Returns
    -------
    list
        The longest prefix common to every path.  Empty list if *paths* is
        empty or the very first elements differ.

    Examples
    --------
    >>> longest_common_prefix([
    ...     ["Animalia", "Chordata", "Mammalia"],
    ...     ["Animalia", "Chordata", "Amphibia"],
    ... ])
    ['Animalia', 'Chordata']

    >>> longest_common_prefix([
    ...     ["Animalia", "Chordata"],
    ...     ["Fungi", "Basidiomycota"],
    ... ])
    []

    >>> longest_common_prefix([])
    []
    """
    if not paths:
        return []

    prefix: List = []

    for elements in zip(*paths):
        # zip stops at the shortest path — no out-of-bounds risk
        unique = set(elements)
        if len(unique) == 1:
            prefix.append(elements[0])
        else:
            break

    return prefix


def infer_node(node: "PieNode", field: str) -> Optional[List]:
    """
    Infer the hierarchical metadata value for a single *node*.

    - **Tips**: return the stored value directly (or ``None`` if absent /
      not a list).
    - **Internal nodes**: collect all descendant-tip values, then return
      their longest common prefix.  Returns ``None`` when no tips carry
      the field or the prefix is empty.

    Parameters
    ----------
    node : PieNode
    field : str
        The metadata field name whose value is a hierarchical list.

    Returns
    -------
    list or None
    """
    if node.is_tip:
        value = node.get(field)
        return value if isinstance(value, list) else None

    tip_paths: List[List] = []

    for tip in node.descendant_tips:
        value = tip.get(field)
        if isinstance(value, list) and value:
            tip_paths.append(value)

    if not tip_paths:
        return None

    prefix = longest_common_prefix(tip_paths)
    return prefix if prefix else None


def infer_tree(tree, field: str) -> Dict[str, Optional[List]]:
    """
    Infer *field* for every node in *tree* and return a mapping of
    ``node.id → inferred_value``.

    Tips with no value for *field* map to ``None``.
    Internal nodes map to their longest-common-prefix result, or ``None``
    when inference yields an empty prefix.

    Parameters
    ----------
    tree : PieTree
    field : str

    Returns
    -------
    dict
        ``{node_id: list_or_None}``
    """
    return {node.id: infer_node(node, field) for node in tree.traverse()}
