"""
test_metadata.py
----------------
Tests for metadata annotation and querying.
"""

import pytest
import pandas as pd
from pietree.tree.pietree import PieTree


class TestAnnotateFromDataFrame:
    """Test tree.annotate() with DataFrame."""

    def test_annotate_by_name(self, three_tip_tree, metadata_df):
        """Annotate nodes by matching node names."""
        tree = three_tip_tree

        # Note: metadata_df has Human/Mouse/Dog, tree has A/B/C
        # So we need a matching DataFrame
        df = pd.DataFrame({
            "name": ["A", "B", "C"],
            "value": [1, 2, 3]
        })

        tree.annotate(df, on="name")

        assert tree.find_tip("A").get("value") == 1
        assert tree.find_tip("B").get("value") == 2
        assert tree.find_tip("C").get("value") == 3

    def test_annotate_missing_column_raises(self, three_tip_tree):
        """annotate() raises if 'on' column missing."""
        df = pd.DataFrame({"wrong_column": [1, 2, 3]})

        with pytest.raises(ValueError, match="not found"):
            three_tip_tree.annotate(df, on="name")


class TestAnnotateFromDict:
    """Test tree.annotate_dict()."""

    def test_annotate_dict_by_name(self, three_tip_tree):
        """Annotate from dict mapping names to metadata."""
        metadata = {
            "A": {"country": "Brazil"},
            "B": {"country": "USA"},
            "C": {"country": "UK"}
        }

        three_tip_tree.annotate_dict(metadata, on="name")

        assert three_tip_tree.find_tip("A").get("country") == "Brazil"
        assert three_tip_tree.find_tip("B").get("country") == "USA"


class TestMetadataView:
    """Test tree.metadata(field) → MetadataView."""

    def test_metadata_view_creation(self, simple_tree_with_taxonomy):
        """tree.metadata(field) returns MetadataView."""
        view = simple_tree_with_taxonomy.metadata("taxonomy")

        assert view.field == "taxonomy"
        assert view._tree == simple_tree_with_taxonomy
