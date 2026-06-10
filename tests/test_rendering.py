"""
test_rendering.py
-----------------
Tests for tree rendering.
"""

import pytest


class TestRenderSpec:
    """Test to_render_spec()."""

    def test_render_spec_creation(self, three_tip_tree):
        """to_render_spec() creates RenderSpec."""
        spec = three_tip_tree.to_render_spec()

        assert spec is not None
        assert len(spec.nodes) == 4  # 3 tips + 1 root
        assert len(spec.edges) == 3

    def test_render_spec_modes(self, three_tip_tree):
        """Different layout modes work."""
        phylogram = three_tip_tree.to_render_spec(mode="phylogram")
        cladogram = three_tip_tree.to_render_spec(mode="cladogram")

        assert phylogram.mode == "phylogram"
        assert cladogram.mode == "cladogram"


class TestToSVG:
    """Test SVG rendering."""

    def test_to_svg_returns_string(self, three_tip_tree):
        """to_svg() returns SVG string."""
        svg = three_tip_tree.to_svg()

        assert svg is not None
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_to_svg_writes_file(self, three_tip_tree, tmp_output_dir):
        """to_svg(path) writes to file."""
        output_path = tmp_output_dir / "test.svg"

        three_tip_tree.to_svg(path=str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "<svg" in content
