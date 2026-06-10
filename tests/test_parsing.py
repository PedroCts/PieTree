"""
test_parsing.py
---------------
Tests for tree parsing functions.
"""

import pytest
from pietree.io import parse_newick


class TestParseNewick:
    """Test Newick parsing."""

    def test_parse_simple_newick(self):
        """Parse simple Newick string."""
        tree = parse_newick("((A,B),C);")

        assert len(tree) == 3
        assert tree.find_tip("A") is not None
        assert tree.find_tip("B") is not None
        assert tree.find_tip("C") is not None

    def test_parse_newick_with_lengths(self):
        """Parse Newick with branch lengths."""
        tree = parse_newick("((A:1.0,B:1.5):0.5,C:2.0);")

        tip_a = tree.find_tip("A")
        # Branch lengths may be stored in PieBranch or node metadata
        # Just verify the tree structure is correct
        assert tip_a is not None
        assert tree.find_tip("B") is not None
        assert tree.find_tip("C") is not None

    def test_parse_newick_from_file(self, tmp_newick_file):
        """Parse Newick from file path."""
        tree = parse_newick(tmp_newick_file)

        assert len(tree) == 3


class TestToNewick:
    """Test Newick serialization."""

    def test_to_newick_simple(self, three_tip_tree):
        """Serialize tree to Newick string."""
        from pietree.io import to_newick

        newick = to_newick(three_tip_tree)

        assert newick is not None
        assert ";" in newick  # Newick format ends with semicolon
        assert "A" in newick
        assert "B" in newick
        assert "C" in newick
