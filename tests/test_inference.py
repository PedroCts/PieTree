"""
test_inference.py
-----------------
Unit tests for pietree.metadata.inference.

Tests cover:
  - longest_common_prefix (pure algorithm)
  - infer_node (single node, tip and internal)
  - infer_tree (whole-tree mapping)

All trees are built manually from PieNode / PieBranch so the tests
have zero I/O dependencies.
"""

import pytest

from pietree.metadata.inference import longest_common_prefix, infer_node, infer_tree
from pietree.tree.pienode import PieNode
from pietree.tree.piebranch import PieBranch
from pietree.tree.pietree import PieTree
import sys, types, importlib

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def tip(name, taxonomy):
    return PieNode(name=name, metadata={"taxonomy": taxonomy})

def internal(name=None):
    return PieNode(name=name)

def attach(parent, *children):
    for c in children:
        parent.add_child(c)
    return parent


# ===========================================================================
# Tests: longest_common_prefix
# ===========================================================================

class TestLongestCommonPrefix:

    def test_identical_paths(self):
        paths = [
            ["Animalia", "Chordata", "Mammalia"],
            ["Animalia", "Chordata", "Mammalia"],
        ]
        assert longest_common_prefix(paths) == ["Animalia", "Chordata", "Mammalia"]

    def test_partial_overlap(self):
        paths = [
            ["Animalia", "Chordata", "Mammalia"],
            ["Animalia", "Chordata", "Amphibia"],
        ]
        assert longest_common_prefix(paths) == ["Animalia", "Chordata"]

    def test_only_root_in_common(self):
        paths = [
            ["Animalia", "Chordata"],
            ["Animalia", "Arthropoda"],
        ]
        assert longest_common_prefix(paths) == ["Animalia"]

    def test_no_common_prefix(self):
        paths = [
            ["Animalia", "Chordata"],
            ["Fungi", "Basidiomycota"],
        ]
        assert longest_common_prefix(paths) == []

    def test_single_path(self):
        paths = [["Animalia", "Chordata", "Mammalia"]]
        assert longest_common_prefix(paths) == ["Animalia", "Chordata", "Mammalia"]

    def test_empty_input(self):
        assert longest_common_prefix([]) == []

    def test_one_empty_path(self):
        paths = [[], ["Animalia"]]
        assert longest_common_prefix(paths) == []

    def test_three_paths_partial(self):
        paths = [
            ["A", "B", "C", "D"],
            ["A", "B", "C", "E"],
            ["A", "B", "F"],
        ]
        assert longest_common_prefix(paths) == ["A", "B"]

    def test_prefix_longer_than_shortest(self):
        # zip stops at the shortest — prefix can't exceed shortest path length
        paths = [
            ["A", "B"],
            ["A", "B", "C"],
        ]
        assert longest_common_prefix(paths) == ["A", "B"]

    def test_non_string_elements(self):
        paths = [[1, 2, 3], [1, 2, 4]]
        assert longest_common_prefix(paths) == [1, 2]


# ===========================================================================
# Tests: infer_node
# ===========================================================================

class TestInferNode:

    def test_tip_returns_own_value(self):
        n = tip("Human", ["Animalia", "Chordata", "Mammalia"])
        assert infer_node(n, "taxonomy") == ["Animalia", "Chordata", "Mammalia"]

    def test_tip_missing_field_returns_none(self):
        n = tip("Human", ["Animalia"])
        assert infer_node(n, "missing_field") is None

    def test_tip_non_list_value_returns_none(self):
        n = PieNode(name="X", metadata={"taxonomy": "Mammalia"})
        assert infer_node(n, "taxonomy") is None

    def test_internal_two_tips_common_prefix(self):
        root = internal("root")
        attach(root,
               tip("Human", ["Animalia", "Chordata", "Mammalia"]),
               tip("Toad",  ["Animalia", "Chordata", "Amphibia"]))
        assert infer_node(root, "taxonomy") == ["Animalia", "Chordata"]

    def test_internal_identical_tips(self):
        root = internal()
        attach(root,
               tip("Cat", ["Animalia", "Chordata", "Mammalia"]),
               tip("Dog", ["Animalia", "Chordata", "Mammalia"]))
        assert infer_node(root, "taxonomy") == ["Animalia", "Chordata", "Mammalia"]

    def test_internal_no_common_prefix_returns_none(self):
        root = internal()
        attach(root,
               tip("Human", ["Animalia", "Chordata"]),
               tip("Yeast",  ["Fungi",   "Ascomycota"]))
        # prefix is [] which collapses to None
        assert infer_node(root, "taxonomy") is None

    def test_internal_tips_missing_field_returns_none(self):
        root = internal()
        attach(root,
               PieNode(name="A"),   # no taxonomy
               PieNode(name="B"))
        assert infer_node(root, "taxonomy") is None

    def test_internal_some_tips_missing_field(self):
        # Tips without the field are skipped; inference from those that have it
        root = internal()
        attach(root,
               tip("Human", ["Animalia", "Chordata", "Mammalia"]),
               PieNode(name="Unknown"))   # no taxonomy
        # Only one path → prefix is that path itself
        assert infer_node(root, "taxonomy") == ["Animalia", "Chordata", "Mammalia"]

    def test_deep_tree(self):
        #        root
        #       /    \
        #    clade1  clade2
        #    /  \      |
        #  A     B     C
        clade1 = internal("clade1")
        attach(clade1,
               tip("A", ["Animalia", "Chordata", "Mammalia"]),
               tip("B", ["Animalia", "Chordata", "Reptilia"]))

        clade2 = internal("clade2")
        attach(clade2,
               tip("C", ["Animalia", "Arthropoda", "Insecta"]))

        root = internal("root")
        attach(root, clade1, clade2)

        assert infer_node(clade1, "taxonomy") == ["Animalia", "Chordata"]
        assert infer_node(clade2, "taxonomy") == ["Animalia", "Arthropoda", "Insecta"]
        assert infer_node(root,   "taxonomy") == ["Animalia"]


# ===========================================================================
# Tests: infer_tree
# ===========================================================================

class TestInferTree:

    def _build_simple_tree(self):
        #   root
        #   /  \
        #  A    B
        root = internal("root")
        a = tip("A", ["Animalia", "Chordata", "Mammalia"])
        b = tip("B", ["Animalia", "Chordata", "Amphibia"])
        attach(root, a, b)
        return _Tree(root), root, a, b

    def test_returns_all_node_ids(self):
        tree, root, a, b = self._build_simple_tree()
        result = infer_tree(tree, "taxonomy")
        assert set(result.keys()) == {root.id, a.id, b.id}

    def test_tip_values_preserved(self):
        tree, root, a, b = self._build_simple_tree()
        result = infer_tree(tree, "taxonomy")
        assert result[a.id] == ["Animalia", "Chordata", "Mammalia"]
        assert result[b.id] == ["Animalia", "Chordata", "Amphibia"]

    def test_internal_value_inferred(self):
        tree, root, a, b = self._build_simple_tree()
        result = infer_tree(tree, "taxonomy")
        assert result[root.id] == ["Animalia", "Chordata"]

    def test_does_not_mutate_node_metadata(self):
        tree, root, a, b = self._build_simple_tree()
        before_a    = a.get("taxonomy")[:]
        before_root = root.get("taxonomy")      # None before inference

        infer_tree(tree, "taxonomy")

        assert a.get("taxonomy") == before_a
        assert root.get("taxonomy") == before_root   # still None

    def test_four_tip_tree(self):
        #       root
        #      /    \
        #   clade1  clade2
        #   /  \    /   \
        #  A    B  C     D
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

        result = infer_tree(_Tree(root), "taxonomy")

        assert result[clade1.id] == ["Eukaryota", "Animalia", "Chordata"]
        assert result[clade2.id] == ["Eukaryota", "Animalia", "Arthropoda"]
        assert result[root.id]   == ["Eukaryota", "Animalia"]

    def test_missing_field_throughout(self):
        root = internal("root")
        attach(root, PieNode(name="X"), PieNode(name="Y"))
        result = infer_tree(_Tree(root), "taxonomy")
        assert all(v is None for v in result.values())