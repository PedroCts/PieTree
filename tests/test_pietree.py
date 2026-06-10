"""
test_pietree.py
---------------
Tests for PieTree class - construction and basic properties.
"""

import pytest
from pietree.tree.pietree import PieTree
from pietree.tree.pienode import PieNode


class TestPieTreeConstruction:
    """Test PieTree instantiation."""

    def test_create_tree_from_root(self):
        """Tree can be created from a root node."""
        root = PieNode(name="Root")
        tree = PieTree(root)

        assert tree.root == root
        assert len(tree) == 1  # 1 tip

    def test_tree_registers_nodes(self, three_tip_tree):
        """All nodes have _tree back-reference."""
        for node in three_tip_tree.traverse():
            assert node._tree == three_tip_tree


class TestPieTreeProperties:
    """Test tree-level properties."""

    def test_len_returns_tip_count(self, binary_tree):
        """len(tree) returns number of tips."""
        assert len(binary_tree) == 4

    def test_n_tips(self, binary_tree):
        """n_tips property."""
        assert binary_tree.n_tips == 4

    def test_n_nodes(self, binary_tree):
        """n_nodes includes tips and internals."""
        assert binary_tree.n_nodes == 7  # 4 tips + 3 internal

    def test_n_branches(self, binary_tree):
        """n_branches counts edges."""
        assert binary_tree.n_branches == 6

    def test_max_depth(self, binary_tree):
        """max_depth returns deepest tip."""
        assert binary_tree.max_depth == 2


class TestPieTreeCollections:
    """Test node collection properties."""

    def test_all_nodes(self, three_tip_tree):
        """all_nodes returns all nodes."""
        assert len(three_tip_tree.all_nodes) == 4  # 3 tips + 1 root

    def test_tips(self, three_tip_tree):
        """tips returns only tips."""
        tips = three_tip_tree.tips
        assert len(tips) == 3
        assert all(t.is_tip for t in tips)

    def test_internal_nodes(self, three_tip_tree):
        """internal_nodes returns only internal nodes."""
        internals = three_tip_tree.internal_nodes
        assert len(internals) == 1
        assert not any(n.is_tip for n in internals)


class TestPieTreeContains:
    """Test __contains__ operator."""

    def test_contains_tip_by_name(self, three_tip_tree):
        """Tree contains tips by name."""
        assert "A" in three_tip_tree
        assert "Z" not in three_tip_tree

    def test_contains_node_by_object(self, three_tip_tree):
        """Tree contains nodes by object identity."""
        tip = list(three_tip_tree.tips)[0]
        assert tip in three_tip_tree

        external_node = PieNode(name="External")
        assert external_node not in three_tip_tree
