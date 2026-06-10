"""
pietree.io
----------
I/O operations for PieTree: parsing, serialization, rasterization, and export.

This module provides functions for reading and writing phylogenetic trees
in various formats, as well as exporting visualizations to image formats
and data to DataFrames.

Parsing (format → PieTree)
---------------------------
- parse_newick(source, support_format=None)
- parse_nexus(source)
- parse_phyloxml(source)
- parse_newick_multi(source, support_format=None)
- parse_nexus_multi(source)

Serialization (PieTree → format)
---------------------------------
- to_newick(tree, dest=None)
- to_nexus(tree, dest=None)
- to_phyloxml(tree, dest=None)
- to_svg(tree, dest=None, **kwargs)

Rasterization (PieTree → image)
--------------------------------
- savefig(tree, path, **kwargs)

Data Export
-----------
- to_dataframe(tree, infer_taxonomy=True)

Examples
--------
>>> from pietree.io import parse_newick, to_svg, savefig
>>> tree = parse_newick("tree.newick")
>>> to_svg(tree, "tree.svg")
>>> savefig(tree, "tree.png", dpi=300)
"""

# Parsing
from .parsing import (
    parse_newick,
    parse_nexus,
    parse_phyloxml,
    parse_newick_multi,
    parse_nexus_multi,
)

# Serialization
from .serialization import (
    to_newick,
    to_nexus,
    to_phyloxml,
    to_svg,
)

# Rasterization
from .rasterization import savefig

# Data export
from .dataframe import to_dataframe

__all__ = [
    # Parsing
    "parse_newick",
    "parse_nexus",
    "parse_phyloxml",
    "parse_newick_multi",
    "parse_nexus_multi",
    # Serialization
    "to_newick",
    "to_nexus",
    "to_phyloxml",
    "to_svg",
    # Rasterization
    "savefig",
    # Data export
    "to_dataframe",
]
