"""
test_tree_ops.py
----------------
Tests for tree operations - MRCA, distance, clade extraction.
"""

import pytest
from pietree.tree.pietree import PieTree


class TestTraversal:
    """Test tree traversal methods."""

    def test_traverse_preorder(self, binary_tree):
        """traverse() visits nodes in preorder."""
        nodes = list(binary_tree.traverse(order="preorder"))

        # Root should be first
        assert nodes[0] == binary_tree.root
        # All nodes visited
        assert len(nodes) == 7

    def test_traverse_postorder(self, binary_tree):
        """traverse() visits nodes in postorder."""
        nodes = list(binary_tree.traverse(order="postorder"))

        # Root should be last in postorder
        assert nodes[-1] == binary_tree.root
        assert len(nodes) == 7


class TestFindMethods:
    """Test node lookup methods."""

    def test_find_tip(self, three_tip_tree):
        """find_tip() returns tip node by name."""
        tip = three_tip_tree.find_tip("A")

        assert tip is not None
        assert tip.name == "A"
        assert tip.is_tip

    def test_find_tip_returns_none_for_missing(self, three_tip_tree):
        """find_tip() returns None for non-existent tip."""
        tip = three_tip_tree.find_tip("NonExistent")
        assert tip is None

    def test_find_node_by_name(self, binary_tree):
        """find_node_by_name() finds any node by name."""
        clade = binary_tree.find_node_by_name("clade1")

        assert clade is not None
        assert clade.name == "clade1"
        assert not clade.is_tip

    def test_find_nodes_by_predicate(self, binary_tree):
        """find_nodes() returns nodes matching predicate."""
        tips = binary_tree.find_nodes(lambda n: n.is_tip)

        assert len(tips) == 4
        assert all(n.is_tip for n in tips)


class TestMRCA:
    """Test Most Recent Common Ancestor."""

    def test_mrca_of_two_tips(self, binary_tree):
        """mrca() finds common ancestor of two tips."""
        tip_a = binary_tree.find_tip("A")
        tip_b = binary_tree.find_tip("B")

        ancestor = binary_tree.mrca([tip_a, tip_b])

        assert ancestor is not None
        assert ancestor.name == "clade1"

    def test_mrca_of_all_tips_is_root(self, binary_tree):
        """mrca() of all tips is root."""
        tips = list(binary_tree.tips)

        ancestor = binary_tree.mrca(tips)

        assert ancestor == binary_tree.root

    def test_mrca_of_single_node(self, binary_tree):
        """mrca() of single node is the node itself."""
        tip_a = binary_tree.find_tip("A")

        ancestor = binary_tree.mrca([tip_a])

        assert ancestor == tip_a


class TestDistance:
    """Test distance calculations."""

    def test_distance_between_tips(self, binary_tree):
        """distance() calculates path length between two tips."""
        tip_a = binary_tree.find_tip("A")
        tip_b = binary_tree.find_tip("B")

        # Distance might be 0 if no branch lengths set
        # Just verify it returns a number
        dist = binary_tree.distance(tip_a, tip_b)
        assert dist is not None
        assert dist >= 0

    def test_distance_from_node_to_itself(self, binary_tree):
        """distance() from node to itself is 0."""
        tip_a = binary_tree.find_tip("A")

        dist = binary_tree.distance(tip_a, tip_a)
        assert dist == 0


class TestClade:
    """Test clade extraction."""

    def test_clade_from_node(self, binary_tree):
        """clade() extracts clade rooted at node."""
        clade1 = binary_tree.find_node_by_name("clade1")

        clade = binary_tree.clade(clade1)

        assert clade is not None
        # Clade should have 2 tips (A and B)
        assert len(clade.tips) == 2

    def test_clade_from_tip_list(self, binary_tree):
        """clade() can extract clade from tip list."""
        tip_a = binary_tree.find_tip("A")
        tip_b = binary_tree.find_tip("B")

        clade = binary_tree.clade([tip_a, tip_b])

        assert clade is not None
        assert len(clade.tips) == 2


class TestTaxonomyQueries:
    """Test taxonomy-based queries."""

    def test_find_tips_by_taxon(self, taxonomy_tree):
        """find_tips_by_taxon() finds tips with matching taxon."""
        # Find all Chordata
        tips = taxonomy_tree.find_tips_by_taxon("Chordata")

        assert len(tips) == 2  # A and B are Chordata

    def test_clade_by_taxon(self, taxonomy_tree):
        """clade_by_taxon() extracts clade for taxon."""
        # Get Arthropoda clade
        arthropods = taxonomy_tree.clade_by_taxon("Arthropoda")

        assert arthropods is not None
        assert len(arthropods.tips) == 2  # C and D


class TestInducedSubtree:
    """Test induced subtree extraction."""

    def test_induced_subtree(self, binary_tree):
        """induced_subtree() creates tree from selected tips."""
        tip_a = binary_tree.find_tip("A")
        tip_c = binary_tree.find_tip("C")

        subtree = binary_tree.induced_subtree([tip_a, tip_c])

        assert subtree is not None
        assert len(subtree.tips) == 2

    def test_subtree_from_tip_names(self, binary_tree):
        """subtree_from_tip_names() creates subtree from names."""
        subtree = binary_tree.subtree_from_tip_names(["A", "B"])

        assert subtree is not None
        assert len(subtree.tips) == 2
