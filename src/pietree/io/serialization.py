"""
serialization.py
----------------
Tree serialization functions for PieTree.

Supports exporting PieTree instances to Newick, NEXUS, and PhyloXML formats
via BioPython.
"""

from __future__ import annotations

import io
from typing import Optional, TYPE_CHECKING

from .utils import PathLike, _write_dest

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree


def _pietree_to_biopython(tree: "PieTree"):
    """
    Convert a PieTree to a Bio.Phylo.BaseTree.Tree for serialization.

    Parameters
    ----------
    tree : PieTree
        The PieTree instance to convert.

    Returns
    -------
    Bio.Phylo.BaseTree.Tree
        The BioPython tree object.
    """
    from Bio.Phylo import BaseTree

    def _convert(pie_node):
        clades = []
        for child, branch in pie_node._children:
            child_clade = _convert(child)
            child_clade.branch_length = branch.length if branch else None
            child_clade.confidence = branch.support if branch else None
            clades.append(child_clade)

        return BaseTree.Clade(
            name=pie_node.name,
            clades=clades,
        )

    bio_root = _convert(tree.root)
    return BaseTree.Tree(root=bio_root)


def _write_bio(tree: "PieTree", dest: Optional[PathLike], fmt: str) -> Optional[str]:
    """
    Serialize tree to BioPython format.

    Parameters
    ----------
    tree : PieTree
        The tree to serialize.
    dest : str, Path, file-like, or None
        Destination for output. If None, returns the string.
    fmt : str
        BioPython format name ('newick', 'nexus', 'phyloxml').

    Returns
    -------
    str or None
        Serialized string if dest is None, otherwise None.
    """
    bio_tree = _pietree_to_biopython(tree)
    from Bio import Phylo

    buf = io.StringIO()
    Phylo.write(bio_tree, buf, fmt)
    return _write_dest(buf.getvalue(), dest)


# ---------------------------------------------------------------------------
# Public serialization API
# ---------------------------------------------------------------------------

def to_newick(tree: "PieTree", dest: Optional[PathLike] = None) -> Optional[str]:
    """
    Serialize tree to Newick format.

    Parameters
    ----------
    tree : PieTree
        The tree to serialize.
    dest : str, Path, file-like, or None
        If None, returns the Newick string. Otherwise writes to the
        destination (file path or file-like object).

    Returns
    -------
    str or None
        Newick string if dest is None, otherwise None.

    Examples
    --------
    >>> newick_str = to_newick(tree)
    >>> to_newick(tree, "output.newick")  # writes to file
    """
    return _write_bio(tree, dest, "newick")


def to_nexus(tree: "PieTree", dest: Optional[PathLike] = None) -> Optional[str]:
    """
    Serialize tree to NEXUS format.

    Parameters
    ----------
    tree : PieTree
        The tree to serialize.
    dest : str, Path, file-like, or None
        If None, returns the NEXUS string. Otherwise writes to the
        destination.

    Returns
    -------
    str or None
        NEXUS string if dest is None, otherwise None.

    Examples
    --------
    >>> nexus_str = to_nexus(tree)
    >>> to_nexus(tree, "output.nex")
    """
    return _write_bio(tree, dest, "nexus")


def to_phyloxml(tree: "PieTree", dest: Optional[PathLike] = None) -> Optional[str]:
    """
    Serialize tree to PhyloXML format.

    Parameters
    ----------
    tree : PieTree
        The tree to serialize.
    dest : str, Path, file-like, or None
        If None, returns the PhyloXML string. Otherwise writes to the
        destination.

    Returns
    -------
    str or None
        PhyloXML string if dest is None, otherwise None.

    Examples
    --------
    >>> xml_str = to_phyloxml(tree)
    >>> to_phyloxml(tree, "output.xml")
    """
    return _write_bio(tree, dest, "phyloxml")


def to_svg(tree: "PieTree", dest: Optional[PathLike] = None, *, spec=None, **render_kwargs) -> Optional[str]:
    """
    Render the tree to SVG.

    Parameters
    ----------
    tree : PieTree
        The tree to render.
    dest : str, Path, file-like, or None
        If None, returns the SVG string. Otherwise writes to the destination.
    spec : RenderSpec, optional
        Pre-built render specification. If None, tree.to_render_spec() is called.
    **render_kwargs
        Additional arguments forwarded to tree.to_render_spec() when spec is None.

    Returns
    -------
    str or None
        SVG string if dest is None, otherwise None.

    Examples
    --------
    >>> svg_str = to_svg(tree)
    >>> to_svg(tree, "tree.svg")
    >>> to_svg(tree, mode="cladogram", orientation="vertical")
    """
    from pietree.render.svg import render_svg
    from .utils import _write_dest

    if spec is None:
        spec = tree.to_render_spec(**render_kwargs)

    svg_str = render_svg(spec)
    return _write_dest(svg_str, dest)
