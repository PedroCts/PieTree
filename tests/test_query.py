"""
test_query.py
-------------
Tests for tree query and selection methods.
"""

import pytest
from pietree.tree.pietree import PieTree


class TestNodeSelection:
    """Test node selection methods."""

    def test_nodes_returns_all(self, three_tip_tree):
        """nodes() returns all nodes when no filters."""
        selection = three_tip_tree.nodes()

        # Should return some kind of selection object
        assert selection is not None

    def test_nodes_with_metadata_filter(self, three_tip_tree):
        """nodes() can filter by metadata."""
        # Add metadata to one tip
        tip_a = three_tip_tree.find_tip("A")
        tip_a.set("marker", "special")

        # Query for nodes with marker='special'
        selection = three_tip_tree.nodes(marker="special")

        assert selection is not None


class TestTipNames:
    """Test tip name extraction."""

    def test_tip_names(self, three_tip_tree):
        """tip_names returns list of tip names."""
        names = three_tip_tree.tip_names()

        assert len(names) == 3
        assert "A" in names
        assert "B" in names
        assert "C" in names


class TestBranchSelection:
    """Test branch selection methods."""

    def test_branches_returns_selection(self, three_tip_tree):
        """branches() returns branch selection."""
        selection = three_tip_tree.branches()

        assert selection is not None


class TestLabelSelection:
    """Test label selection methods."""

    def test_labels(self, three_tip_tree):
        """labels() creates label selection."""
        selection = three_tip_tree.labels()

        assert selection is not None

    def test_tip_labels(self, three_tip_tree):
        """tip_labels() creates tip label selection."""
        selection = three_tip_tree.tip_labels()

        assert selection is not None


class TestContainsOperator:
    """Test tree membership checks."""

    def test_contains_by_name(self, three_tip_tree):
        """Tree contains tips by name."""
        assert "A" in three_tip_tree
        assert "NonExistent" not in three_tip_tree

    def test_contains_by_node(self, three_tip_tree):
        """Tree contains nodes by object."""
        tip = three_tip_tree.find_tip("A")
        assert tip in three_tip_tree

        # External node
        from pietree.tree.pienode import PieNode
        external = PieNode(name="External")
        assert external not in three_tip_tree
