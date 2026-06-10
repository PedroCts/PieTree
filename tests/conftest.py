"""
conftest.py
-----------
Shared test fixtures for PieTree test suite.

Provides sample trees, metadata, and helper functions for building test cases.
"""

import pytest
import pandas as pd
from pietree.tree.pienode import PieNode
from pietree.tree.piebranch import PieBranch
from pietree.tree.pietree import PieTree


# ---------------------------------------------------------------------------
# Tree Building Helpers
# ---------------------------------------------------------------------------

def tip(name: str, taxonomy: list = None, **metadata):
    """
    Create a tip node with optional taxonomy and metadata.

    Examples
    --------
    >>> tip("Human", ["Animalia", "Chordata", "Mammalia"])
    >>> tip("Sample1", country="Brazil", group="this_study")
    """
    meta = metadata.copy()
    if taxonomy is not None:
        meta["taxonomy"] = taxonomy
    return PieNode(name=name, metadata=meta)


def internal(name: str = None, **metadata):
    """Create an internal node with optional name and metadata."""
    return PieNode(name=name, metadata=metadata)


def attach(parent: PieNode, *children: PieNode):
    """
    Attach children to parent node.

    Examples
    --------
    >>> root = internal()
    >>> attach(root, tip("A"), tip("B"), tip("C"))
    """
    for child in children:
        parent.add_child(child)
    return parent


# ---------------------------------------------------------------------------
# Simple Trees (Basic Tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def three_tip_tree():
    """
    Simple three-tip tree:
           root
          / | \
         A  B  C
    """
    root = internal("root")
    attach(root,
           tip("A", branch_length=1.0),
           tip("B", branch_length=1.0),
           tip("C", branch_length=2.0))
    return PieTree(root)


@pytest.fixture
def simple_tree_with_taxonomy():
    """
    Three-tip tree with taxonomy metadata:
           root
          /    \
       Human  Mouse
    """
    root = internal()
    attach(root,
           tip("Human", ["Animalia", "Chordata", "Mammalia"]),
           tip("Mouse", ["Animalia", "Chordata", "Mammalia"]),
           tip("Yeast", ["Fungi", "Ascomycota"]))
    return PieTree(root)


@pytest.fixture
def binary_tree():
    """
    Fully bifurcating tree with 4 tips:
           root
          /    \
       clade1  clade2
       /  \     /  \
      A    B   C    D
    """
    clade1 = internal("clade1")
    attach(clade1,
           tip("A", branch_length=1.0),
           tip("B", branch_length=1.0))

    clade2 = internal("clade2")
    attach(clade2,
           tip("C", branch_length=1.0),
           tip("D", branch_length=1.0))

    root = internal("root")
    attach(root, clade1, clade2)

    return PieTree(root)


# ---------------------------------------------------------------------------
# Complex Trees (Advanced Tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def taxonomy_tree():
    """
    Tree with hierarchical taxonomy at different depths:
           root
          /    \
       clade1  clade2
       /  \     /   \
      A    B   C     D
    """
    clade1 = internal("clade1")
    attach(clade1,
           tip("A", ["Eukaryota", "Animalia", "Chordata", "Mammalia"]),
           tip("B", ["Eukaryota", "Animalia", "Chordata", "Reptilia"]))

    clade2 = internal("clade2")
    attach(clade2,
           tip("C", ["Eukaryota", "Animalia", "Arthropoda", "Insecta"]),
           tip("D", ["Eukaryota", "Animalia", "Arthropoda", "Arachnida"]))

    root = internal("root")
    attach(root, clade1, clade2)

    return PieTree(root)


@pytest.fixture
def ultrametric_tree():
    """
    Ultrametric tree (all tips equidistant from root):
           root
          /    \
       clade1  C (bl=2.0)
       /  \
      A    B
    (bl=1.0 each)
    """
    clade1 = internal("clade1")
    clade1._branch_length = 1.0
    attach(clade1,
           tip("A", branch_length=1.0),
           tip("B", branch_length=1.0))

    root = internal("root")
    root.add_child(clade1, length=1.0)
    root.add_child(tip("C", branch_length=2.0), length=2.0)

    return PieTree(root)


# ---------------------------------------------------------------------------
# Metadata DataFrames
# ---------------------------------------------------------------------------

@pytest.fixture
def metadata_df():
    """
    Sample metadata DataFrame for annotation tests.
    """
    return pd.DataFrame({
        "name": ["Human", "Mouse", "Dog"],
        "country": ["Brazil", "USA", "UK"],
        "group": ["this_study", "reference", "reference"],
        "haplogroup": ["H1a", "U5", "K1"]
    })


@pytest.fixture
def metadata_dict():
    """
    Sample metadata dictionary for annotation tests.
    """
    return {
        "Human": {"country": "Brazil", "group": "this_study"},
        "Mouse": {"country": "USA", "group": "reference"},
        "Dog": {"country": "UK", "group": "reference"}
    }


# ---------------------------------------------------------------------------
# Newick Strings (Parsing Tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def newick_strings():
    """Sample Newick strings for parsing tests."""
    return {
        "simple": "((A,B),C);",
        "with_lengths": "((A:1.0,B:1.0):0.5,C:2.0);",
        "with_support": "((A,B)100,C);",
        "with_names": "((A,B)clade1,C)root;",
        "complex": "((A:1.0,B:1.5)95:0.5,(C:0.8,D:0.9)85:0.3)100:0.1;",
    }


# ---------------------------------------------------------------------------
# Temporary Files (I/O Tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_newick_file(tmp_path):
    """Create a temporary Newick file."""
    newick_file = tmp_path / "test_tree.newick"
    newick_file.write_text("((A:1.0,B:1.0):0.5,C:2.0);")
    return newick_file


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# ---------------------------------------------------------------------------
# Fake Tree for Edge Cases
# ---------------------------------------------------------------------------

class _FakeTree:
    """Minimal tree-like object for edge case testing."""
    def __init__(self, root):
        self.root = root

    def traverse(self):
        yield from self.root.walk()


@pytest.fixture
def minimal_tree():
    """Single-node tree (edge case)."""
    root = tip("OnlyTip")
    return PieTree(root)


@pytest.fixture
def empty_metadata_tree():
    """Tree with no metadata on any nodes."""
    root = internal()
    attach(root, tip("A"), tip("B"), tip("C"))
    return PieTree(root)
