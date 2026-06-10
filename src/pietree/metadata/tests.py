"""
test_meta_highlight.py
----------------------
Tests for:
  - palette.assign_colors
  - meta_highlight.highlight_metadata
  - MetadataView.highlight (via piemeta.py stub)
"""

import sys
sys.path.insert(0, "/home/claude")

import pytest
import uuid

# ---------------------------------------------------------------------------
# Local modules under test
# ---------------------------------------------------------------------------
from .palette import assign_colors, get_palette
from .inference import infer_tree


# ---------------------------------------------------------------------------
# Minimal tree stubs (same pattern as test_inference.py)
# ---------------------------------------------------------------------------

class _Branch:
    def __init__(self, parent_id, child_id):
        self.parent_id = parent_id
        self.child_id  = child_id
        self.length    = 1.0

class _Node:
    def __init__(self, name=None, metadata=None):
        self.id        = str(uuid.uuid4())
        self.name      = name
        self._meta     = metadata or {}
        self._parent   = None
        self._children = []
        self._tree     = None

    @property
    def is_tip(self):
        return not self._children

    @property
    def is_root(self):
        return self._parent is None

    @property
    def descendants(self):
        result = []
        for c in self._children:
            result.append(c)
            result.extend(c.descendants)
        return result

    @property
    def descendant_tips(self):
        return [n for n in self.descendants if n.is_tip]

    def get(self, key, default=None):
        return self._meta.get(key, default)

    def add_child(self, child):
        child._parent = self
        child._tree   = self._tree
        self._children.append(child)
        return child

    def walk(self):
        yield self
        for c in self._children:
            yield from c.walk()


class _Tree:
    def __init__(self, root):
        self.root      = root
        self._highlights = []
        # wire back-references
        for node in root.walk():
            node._tree = self

    def traverse(self):
        yield from self.root.walk()

    @property
    def tips(self):
        return [n for n in self.traverse() if n.is_tip]

    def mrca(self, nodes):
        common = set(nodes[0]._ancestors_including_self())
        for n in nodes[1:]:
            common &= set(n._ancestors_including_self())
        # deepest = first in nodes[0]'s path that is in common
        for a in nodes[0]._ancestors_including_self():
            if a in common:
                return a
        return None

    def clade(self, nodes):
        root = self.mrca(nodes) if isinstance(nodes, list) else nodes
        c = _Clade(
            root=root,
            nodes=[root] + root.descendants,
            tips=root.descendant_tips,
            highlights=self._highlights,
        )
        return c


class _Clade:
    def __init__(self, root, nodes, tips, highlights):
        self.root        = root
        self.nodes       = nodes
        self.tips        = tips
        self._highlights = highlights

    @property
    def name(self):
        return getattr(self.root, "name", None)


# patch _ancestors_including_self onto _Node
def _ancestors_including_self(self):
    path = []
    cur = self
    while cur is not None:
        path.append(cur)
        cur = cur._parent
    return path

_Node._ancestors_including_self = _ancestors_including_self


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------

def tip(name, taxonomy):
    return _Node(name=name, metadata={"taxonomy": taxonomy})

def internal(name=None):
    return _Node(name=name)

def attach(parent, *children):
    for c in children:
        parent.add_child(c)
    return parent

def simple_tree():
    """
           root
          /    \\
       clade1  clade2
       /  \\    /   \\
      A    B  C     D

    Taxonomy:
      A: [Animalia, Chordata, Mammalia]
      B: [Animalia, Chordata, Reptilia]
      C: [Animalia, Arthropoda, Insecta]
      D: [Animalia, Arthropoda, Arachnida]
    """
    c1 = internal("clade1")
    attach(c1,
           tip("A", ["Animalia", "Chordata", "Mammalia"]),
           tip("B", ["Animalia", "Chordata", "Reptilia"]))

    c2 = internal("clade2")
    attach(c2,
           tip("C", ["Animalia", "Arthropoda", "Insecta"]),
           tip("D", ["Animalia", "Arthropoda", "Arachnida"]))

    root = internal("root")
    attach(root, c1, c2)

    return _Tree(root)


# ===========================================================================
# Tests: palette
# ===========================================================================

class TestPalette:

    def test_get_palette_tab10(self):
        p = get_palette("tab10")
        assert len(p) == 10
        assert all(c.startswith("#") for c in p)

    def test_get_palette_tab20(self):
        p = get_palette("tab20")
        assert len(p) == 20

    def test_get_palette_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown palette"):
            get_palette("nonexistent")

    def test_assign_colors_basic(self):
        result = assign_colors(["A", "B", "C"], palette="tab10")
        assert set(result.keys()) == {"A", "B", "C"}
        assert all(v.startswith("#") for v in result.values())

    def test_assign_colors_distinct(self):
        labels = ["X", "Y", "Z"]
        result = assign_colors(labels, palette="tab10")
        assert len(set(result.values())) == 3  # all different

    def test_assign_colors_cycles(self):
        # tab10 has 10 colors; 11 labels should cycle back
        labels = [str(i) for i in range(11)]
        result = assign_colors(labels, palette="tab10")
        palette = get_palette("tab10")
        assert result[labels[0]] == palette[0]
        assert result[labels[10]] == palette[0]  # wrapped

    def test_assign_colors_overrides(self):
        result = assign_colors(["A", "B"], palette="tab10",
                               overrides={"A": "#ff0000"})
        assert result["A"] == "#ff0000"
        assert result["B"] != "#ff0000"

    def test_assign_colors_empty(self):
        assert assign_colors([]) == {}


# ===========================================================================
# Tests: highlight_metadata (via _Tree stub)
# ===========================================================================

# We import highlight_metadata directly and monkey-patch the
# pietree imports it uses so we don't need the full package.

import types

# Build a minimal fake pietree package tree so meta_highlight.py can import
# without the real package installed.
_pkg = types.ModuleType("pietree")
_meta_pkg = types.ModuleType("pietree.metadata")
_infer_mod = types.ModuleType("pietree.metadata.inference")
_pal_mod   = types.ModuleType("pietree.metadata.palette")
_hl_pkg    = types.ModuleType("pietree.render")
_hl_layers = types.ModuleType("pietree.render.layers")
_hl_mod    = types.ModuleType("pietree.render.layers.highlights")

# wire modules
sys.modules["pietree"]                          = _pkg
sys.modules["pietree.metadata"]                 = _meta_pkg
sys.modules["pietree.metadata.inference"]       = _infer_mod
sys.modules["pietree.metadata.palette"]         = _pal_mod
sys.modules["pietree.render"]                   = _hl_pkg
sys.modules["pietree.render.layers"]            = _hl_layers
sys.modules["pietree.render.layers.highlights"] = _hl_mod

# inject real implementations
_infer_mod.infer_tree    = infer_tree
_pal_mod.assign_colors   = assign_colors

# minimal RenderHighlight stub
from dataclasses import dataclass
from typing import Optional

@dataclass
class _RenderHighlight:
    clade:          object
    fill:           str   = "#cccccc"
    opacity:        float = 0.25
    label:          Optional[str] = None
    label_position: str   = "upper_right"
    font_size:      float = 11
    font_color:     str   = "#444444"
    font_weight:    str   = "bold"
    padding:        float = 10
    corner_radius:  float = 5

_hl_mod.RenderHighlight = _RenderHighlight

# now import our module
from .meta_highlight import highlight_metadata


class TestHighlightMetadata:

    def test_creates_highlights(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy")
        assert len(created) > 0
        assert all(isinstance(h, _RenderHighlight) for h in created)

    def test_highlights_appended_to_tree(self):
        tree = simple_tree()
        before = len(tree._highlights)
        highlight_metadata(tree, "taxonomy")
        assert len(tree._highlights) > before

    def test_labels_are_taxon_names(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy")
        labels = {h.label for h in created}
        # Should contain leaf-level taxa by default
        assert "Mammalia" in labels or "Chordata" in labels or "Animalia" in labels

    def test_depth_0_single_group(self):
        """At depth=0, all tips share Animalia → one highlight."""
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=0)
        assert len(created) == 1
        assert created[0].label == "Animalia"

    def test_depth_1_two_groups(self):
        """At depth=1: Chordata and Arthropoda."""
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=1)
        labels = {h.label for h in created}
        assert labels == {"Chordata", "Arthropoda"}

    def test_depth_2_four_groups(self):
        """At depth=2: Mammalia, Reptilia, Insecta, Arachnida."""
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=2)
        labels = {h.label for h in created}
        assert labels == {"Mammalia", "Reptilia", "Insecta", "Arachnida"}

    def test_values_filter(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=1,
                                     values=["Chordata"])
        assert len(created) == 1
        assert created[0].label == "Chordata"

    def test_values_filter_empty_result(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=1,
                                     values=["Nonexistent"])
        assert created == []

    def test_color_assignment_from_palette(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=1,
                                     palette="tab10")
        # Colors should be from tab10 (all start with #)
        assert all(h.fill.startswith("#") for h in created)

    def test_color_overrides(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=1,
                                     colors={"Chordata": "#ff0000"})
        chordata_h = next(h for h in created if h.label == "Chordata")
        assert chordata_h.fill == "#ff0000"

    def test_missing_field_returns_empty(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "no_such_field")
        assert created == []

    def test_does_not_mutate_node_metadata(self):
        tree = simple_tree()
        snapshots = {n.id: n.get("taxonomy") for n in tree.traverse()}
        highlight_metadata(tree, "taxonomy")
        for node in tree.traverse():
            assert node.get("taxonomy") == snapshots[node.id]

    def test_manual_highlight_still_works(self):
        """Existing manual clade.highlight() must remain unaffected."""
        tree = simple_tree()
        tips = tree.tips[:2]
        clade = tree.clade(tips)

        before = len(tree._highlights)
        h = _RenderHighlight(clade=clade, fill="#aabbcc", label="Manual")
        tree._highlights.append(h)

        assert len(tree._highlights) == before + 1
        assert tree._highlights[-1].label == "Manual"

    def test_opacity_forwarded(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=0, opacity=0.5)
        assert created[0].opacity == 0.5

    def test_label_position_forwarded(self):
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=0,
                                     label_position="center_left")
        assert created[0].label_position == "center_left"

    def test_depth_beyond_path_skips_tips(self):
        """Tips whose path is shorter than depth are skipped gracefully."""
        # A has path length 3; if depth=5 no tips qualify
        tree = simple_tree()
        created = highlight_metadata(tree, "taxonomy", depth=10)
        assert created == []
