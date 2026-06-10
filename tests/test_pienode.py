"""
test_pienode.py
---------------
Tests for PieNode class - construction, properties, and tree structure.
"""

import pytest
from pietree.tree.pienode import PieNode
from pietree.tree.piebranch import PieBranch


class TestPieNodeConstruction:
    """Test PieNode instantiation and basic properties."""

    def test_create_node_minimal(self):
        """Node can be created with no arguments."""
        node = PieNode()
        assert node.name is None
        assert node.is_tip
        assert node.id is not None  # UUID assigned

    def test_create_node_with_name(self):
        """Node can be created with a name."""
        node = PieNode(name="TestNode")
        assert node.name == "TestNode"

    def test_create_node_with_metadata(self):
        """Node can be created with metadata."""
        node = PieNode(name="Test", metadata={"country": "Brazil"})
        assert node.get("country") == "Brazil"

    def test_node_ids_are_unique(self):
        """Each node gets a unique ID."""
        node1 = PieNode(name="A")
        node2 = PieNode(name="A")  # same name
        assert node1.id != node2.id


class TestPieNodeProperties:
    """Test node type properties (is_tip, is_root, etc.)."""

    def test_is_tip_on_leaf(self):
        """Nodes with no children are tips."""
        node = PieNode(name="Leaf")
        assert node.is_tip
        # Note: a lone tip is also a root (has no parent)

    def test_is_internal_on_parent(self):
        """Nodes with children are not tips."""
        parent = PieNode(name="Parent")
        child = PieNode(name="Child")
        parent.add_child(child)

        assert not parent.is_tip
        assert child.is_tip

    def test_is_root_on_parentless_node(self):
        """Nodes with no parent are roots."""
        root = PieNode(name="Root")
        assert root.is_root

        child = PieNode(name="Child")
        root.add_child(child)

        assert root.is_root
        assert not child.is_root


class TestPieNodeRelationships:
    """Test parent-child relationships."""

    def test_add_child(self):
        """add_child() establishes parent-child relationship."""
        parent = PieNode(name="Parent")
        child = PieNode(name="Child")
        parent.add_child(child, length=1.0)

        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent == parent
        assert child.branch_length == 1.0

    def test_add_multiple_children(self):
        """Parent can have multiple children."""
        parent = PieNode()
        child1 = PieNode(name="A")
        child2 = PieNode(name="B")
        child3 = PieNode(name="C")

        parent.add_child(child1)
        parent.add_child(child2)
        parent.add_child(child3)

        assert len(parent.children) == 3

    def test_detach(self):
        """detach() removes node from parent."""
        parent = PieNode()
        child = PieNode(name="Child")
        parent.add_child(child)

        child.detach()

        assert len(parent.children) == 0
        assert child.parent is None


class TestPieNodeTraversal:
    """Test tree traversal methods."""

    def test_descendants(self, binary_tree):
        """descendants returns all descendant nodes."""
        root = binary_tree.root
        descendants = root.descendants

        assert len(descendants) == 6  # 2 clades + 4 tips

    def test_descendant_tips(self, binary_tree):
        """descendant_tips returns only tip nodes."""
        root = binary_tree.root
        tips = root.descendant_tips

        assert len(tips) == 4
        assert all(t.is_tip for t in tips)


class TestPieNodeDepth:
    """Test depth calculation."""

    def test_root_depth_is_zero(self, three_tip_tree):
        """Root node has depth 0."""
        assert three_tip_tree.root.depth == 0

    def test_tip_depth(self, binary_tree):
        """Tips have correct depth."""
        tips = binary_tree.tips
        assert all(t.depth == 2 for t in tips)


class TestPieNodeMetadata:
    """Test metadata methods (get, set, has from PieObject)."""

    def test_get_existing_metadata(self):
        """get() retrieves existing metadata."""
        node = PieNode(metadata={"country": "Brazil"})
        assert node.get("country") == "Brazil"

    def test_get_missing_metadata_returns_default(self):
        """get() returns default for missing keys."""
        node = PieNode()
        assert node.get("missing", "default") == "default"

    def test_set_metadata(self):
        """set() adds metadata."""
        node = PieNode()
        node.set("country", "Brazil")
        assert node.get("country") == "Brazil"

    def test_has_metadata(self):
        """has() checks if metadata key exists."""
        node = PieNode(metadata={"country": "Brazil"})
        assert node.has("country")
        assert not node.has("missing")
