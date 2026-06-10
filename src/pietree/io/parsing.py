"""
parsing.py
----------
Tree parsing functions for PieTree.

Supports parsing phylogenetic trees from Newick, NEXUS, and PhyloXML formats
via BioPython, with custom support string parsing for bootstrap/aLRT values.
"""

from __future__ import annotations

import re as _re
from typing import Optional, TYPE_CHECKING

from .utils import PathLike, _open_source

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree


def _biopython_to_pietree(bio_tree, support_format: Optional[str] = None) -> "PieTree":
    """
    Convert a Bio.Phylo.BaseTree.Tree to a PieTree instance.

    Performs a single DFS pass, creating PieNode + PieBranch objects and
    wiring them up as expected by the PieTree engine.

    Parameters
    ----------
    bio_tree : Bio.Phylo.BaseTree.Tree
        The BioPython tree object.
    support_format : str, optional
        Format string for parsing support values (e.g., '{bootstrap}/{alrt}').
        If None, confidence values are stored as {"support": float}.

    Returns
    -------
    PieTree
        The converted PieTree instance.
    """
    from pietree.tree.pienode import PieNode
    from pietree.tree.piebranch import PieBranch
    from pietree.tree.pietree import PieTree

    node_map: dict = {}  # id(bio_clade) → PieNode

    field_names = _parse_support_format(support_format) if support_format else None

    def _convert(bio_clade, parent_pie: Optional[PieNode], parent_id: Optional[str]):
        name = bio_clade.name or None
        confidence = getattr(bio_clade, "confidence", None)
        branch_length = getattr(bio_clade, "branch_length", None)

        support = None
        if confidence is not None:
            raw = str(confidence)
            if field_names:
                support = _parse_support_string(raw, field_names)
            else:
                try:
                    support = {"support": float(raw)}
                except ValueError:
                    pass
        elif name is not None and bio_clade.clades:
            # internal node — name may be a support string
            if field_names:
                parsed = _parse_support_string(name, field_names)
            else:
                m = _re.match(r'^(\d+(?:\.\d+)?)$', name.strip())
                parsed = {"support": float(m.group(1))} if m else None
            if parsed:
                support = parsed
                name = None

        pie = PieNode(name=name)
        node_map[id(bio_clade)] = pie

        if parent_pie is not None:
            branch = PieBranch(
                parent_id=parent_id,
                child_id=pie.id,
                length=branch_length,
                support=support
            )
            parent_pie._children.append((pie, branch))
            pie._parent = parent_pie

        for child_clade in bio_clade.clades:
            _convert(child_clade, pie, pie.id)

        return pie

    root = _convert(bio_tree.root, None, None)
    tree = PieTree(root=root)

    # wire back-references
    for node in tree.traverse():
        node._tree = tree

    return tree


def _parse_bio(source: PathLike, fmt: str, support_format=None) -> "PieTree":
    """
    Parse source with BioPython Phylo and return the first tree.

    Parameters
    ----------
    source : str, Path, or file-like
        The tree source to parse.
    fmt : str
        BioPython format name ('newick', 'nexus', 'phyloxml').
    support_format : str, optional
        Support value format string (e.g., '{bootstrap}/{alrt}').

    Returns
    -------
    PieTree
        The parsed tree.

    Raises
    ------
    ValueError
        If no trees are found in the source.

    Warnings
    --------
    UserWarning
        If multiple trees are found (only the first is returned).
    """
    from Bio import Phylo

    fh, should_close = _open_source(source)
    try:
        trees = list(Phylo.parse(fh, fmt))
    finally:
        if should_close:
            fh.close()

    if not trees:
        raise ValueError(f"No trees found in {fmt} source.")

    if len(trees) > 1:
        import warnings
        warnings.warn(
            f"{len(trees)} trees found; loading the first one. "
            "Use parse_multi() to load all.",
            stacklevel=3,
        )

    return _biopython_to_pietree(trees[0], support_format=support_format)


def _parse_bio_multi(source: PathLike, fmt: str, support_format=None) -> list["PieTree"]:
    """
    Parse all trees from source.

    Parameters
    ----------
    source : str, Path, or file-like
        The tree source to parse.
    fmt : str
        BioPython format name ('newick', 'nexus', 'phyloxml').
    support_format : str, optional
        Support value format string (e.g., '{bootstrap}/{alrt}').

    Returns
    -------
    list[PieTree]
        All parsed trees from the source.
    """
    from Bio import Phylo

    fh, should_close = _open_source(source)
    try:
        trees = list(Phylo.parse(fh, fmt))
    finally:
        if should_close:
            fh.close()

    return [_biopython_to_pietree(t, support_format=support_format) for t in trees]


def _parse_support_format(fmt: str) -> list[str]:
    """
    Extract field names from a format string like '{bootstrap}/{alrt}'.

    Parameters
    ----------
    fmt : str
        Format string with field names in curly braces.

    Returns
    -------
    list[str]
        Extracted field names.

    Examples
    --------
    >>> _parse_support_format('{bootstrap}/{alrt}')
    ['bootstrap', 'alrt']
    """
    return _re.findall(r'\{(\w+)\}', fmt)


def _parse_support_string(raw: str, field_names: list[str]) -> Optional[dict]:
    """
    Split raw support string by non-numeric separators and map to field_names.

    Parameters
    ----------
    raw : str
        Raw support string (e.g., '100/95').
    field_names : list[str]
        Field names to map values to.

    Returns
    -------
    dict or None
        Mapping of field names to float values, or None if parsing fails
        or token count doesn't match.

    Examples
    --------
    >>> _parse_support_string('100/95', ['bootstrap', 'alrt'])
    {'bootstrap': 100.0, 'alrt': 95.0}
    """
    tokens = _re.split(r'[^0-9.]+', raw.strip())
    tokens = [t for t in tokens if t]

    if len(tokens) != len(field_names):
        return None

    try:
        return {k: float(v) for k, v in zip(field_names, tokens)}
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Public parsing API
# ---------------------------------------------------------------------------

def parse_newick(source: PathLike, support_format=None) -> "PieTree":
    """
    Parse a Newick string, path, or file-like object to PieTree.

    Parameters
    ----------
    source : str, Path, or file-like
        Newick tree source. Can be a file path, file-like object with
        read(), or a raw Newick string.
    support_format : str, optional
        Support value format string (e.g., '{bootstrap}/{alrt}').
        If provided, internal node labels are parsed according to this
        format. If None, single numeric labels are stored as
        {"support": float}.

    Returns
    -------
    PieTree
        The parsed phylogenetic tree.

    Examples
    --------
    >>> tree = parse_newick("((A,B),C);")
    >>> tree = parse_newick("tree.newick")
    >>> tree = parse_newick("tree.newick", support_format="{bootstrap}/{alrt}")
    """
    return _parse_bio(source, "newick", support_format=support_format)


def parse_nexus(source: PathLike) -> "PieTree":
    """
    Parse a NEXUS string, path, or file-like object to PieTree.

    Parameters
    ----------
    source : str, Path, or file-like
        NEXUS tree source.

    Returns
    -------
    PieTree
        The parsed phylogenetic tree.

    Examples
    --------
    >>> tree = parse_nexus("tree.nex")
    """
    return _parse_bio(source, "nexus")


def parse_phyloxml(source: PathLike) -> "PieTree":
    """
    Parse a PhyloXML string, path, or file-like object to PieTree.

    Parameters
    ----------
    source : str, Path, or file-like
        PhyloXML tree source.

    Returns
    -------
    PieTree
        The parsed phylogenetic tree.

    Examples
    --------
    >>> tree = parse_phyloxml("tree.xml")
    """
    return _parse_bio(source, "phyloxml")


def parse_newick_multi(source: PathLike, support_format=None) -> list["PieTree"]:
    """
    Parse all Newick trees from source.

    Parameters
    ----------
    source : str, Path, or file-like
        Source containing one or more Newick trees.
    support_format : str, optional
        Support value format string (e.g., '{bootstrap}/{alrt}').

    Returns
    -------
    list[PieTree]
        All parsed trees.

    Examples
    --------
    >>> trees = parse_newick_multi("forest.newick")
    """
    return _parse_bio_multi(source, "newick", support_format=support_format)


def parse_nexus_multi(source: PathLike) -> list["PieTree"]:
    """
    Parse all NEXUS trees from source.

    Parameters
    ----------
    source : str, Path, or file-like
        NEXUS source containing one or more trees.

    Returns
    -------
    list[PieTree]
        All parsed trees.

    Examples
    --------
    >>> trees = parse_nexus_multi("forest.nex")
    """
    return _parse_bio_multi(source, "nexus")
