"""
test_cli.py
-----------
Tests for CLI commands.
"""

import pytest
import subprocess
import sys
from pathlib import Path
import tempfile


# Helper to run CLI commands
def run_cli(*args):
    """Run pietree CLI with given arguments."""
    cmd = [sys.executable, "-m", "pietree.cli.main"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    return result


class TestRenderCommand:
    """Test pietree render command."""

    def test_render_basic(self, tmp_path):
        """Render simple tree to SVG."""
        output = tmp_path / "test.svg"
        result = run_cli(
            "render",
            "examples/data/example.newick",
            "-o", str(output)
        )

        assert result.returncode == 0
        assert output.exists()
        assert output.stat().st_size > 0
        assert "<svg" in output.read_text()

    def test_render_missing_file(self):
        """Render fails with missing file."""
        result = run_cli(
            "render",
            "nonexistent.newick",
            "-o", "/tmp/test.svg"
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()

    def test_render_with_mode(self, tmp_path):
        """Render with cladogram mode."""
        output = tmp_path / "cladogram.svg"
        result = run_cli(
            "render",
            "examples/data/example.newick",
            "-m", "cladogram",
            "-o", str(output)
        )

        assert result.returncode == 0
        assert output.exists()


class TestQueryCommand:
    """Test pietree query command."""

    def test_query_tips(self):
        """Query all tips."""
        result = run_cli(
            "query",
            "examples/data/example.newick",
            "tips"
        )

        assert result.returncode == 0
        assert "name=A" in result.stdout or "A" in result.stdout

    def test_query_count(self):
        """Query node counts."""
        result = run_cli(
            "query",
            "examples/data/example.newick",
            "count"
        )

        assert result.returncode == 0
        assert "tips:" in result.stdout

    def test_query_json_output(self):
        """Query with JSON output."""
        result = run_cli(
            "query",
            "examples/data/example.newick",
            "tips",
            "-o", "json"
        )

        assert result.returncode == 0
        # Should be valid JSON
        import json
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_query_missing_file(self):
        """Query fails with missing file."""
        result = run_cli(
            "query",
            "nonexistent.newick",
            "tips"
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestAnnotateCommand:
    """Test pietree annotate command."""

    def test_annotate_basic(self, tmp_path):
        """Annotate tree with metadata."""
        output = tmp_path / "annotated.newick"
        result = run_cli(
            "annotate",
            "examples/data/example.newick",
            "examples/data/example_metadata.csv",
            "-o", str(output)
        )

        assert result.returncode == 0
        assert output.exists()
        assert "Annotated" in result.stdout

    def test_annotate_missing_tree(self, tmp_path):
        """Annotate fails with missing tree file."""
        output = tmp_path / "annotated.newick"
        result = run_cli(
            "annotate",
            "nonexistent.newick",
            "examples/data/example_metadata.csv",
            "-o", str(output)
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()

    def test_annotate_missing_metadata(self, tmp_path):
        """Annotate fails with missing metadata file."""
        output = tmp_path / "annotated.newick"
        result = run_cli(
            "annotate",
            "examples/data/example.newick",
            "nonexistent.csv",
            "-o", str(output)
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestConvertCommand:
    """Test pietree convert command."""

    def test_convert_newick_to_newick(self, tmp_path):
        """Convert Newick to Newick."""
        output = tmp_path / "converted.newick"
        result = run_cli(
            "convert",
            "examples/data/example.newick",
            str(output)
        )

        assert result.returncode == 0
        assert output.exists()
        assert "Converted" in result.stdout

    def test_convert_missing_file(self, tmp_path):
        """Convert fails with missing file."""
        output = tmp_path / "converted.newick"
        result = run_cli(
            "convert",
            "nonexistent.newick",
            str(output)
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestValidateCommand:
    """Test pietree validate command."""

    def test_validate_valid_tree(self):
        """Validate a valid tree."""
        result = run_cli(
            "validate",
            "examples/data/example.newick"
        )

        assert result.returncode == 0
        assert "✅" in result.stdout or "passed" in result.stdout.lower()

    def test_validate_missing_file(self):
        """Validate fails with missing file."""
        result = run_cli(
            "validate",
            "nonexistent.newick"
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestInfoCommand:
    """Test pietree info command."""

    def test_info_basic(self):
        """Get info about tree."""
        result = run_cli(
            "info",
            "examples/data/example.newick"
        )

        assert result.returncode == 0
        # Should show tree statistics
        assert "tips" in result.stdout.lower() or "nodes" in result.stdout.lower()

    def test_info_missing_file(self):
        """Info fails with missing file."""
        result = run_cli(
            "info",
            "nonexistent.newick"
        )

        assert result.returncode != 0


class TestCLIHelp:
    """Test CLI help messages."""

    def test_main_help(self):
        """Main CLI shows help."""
        result = run_cli("--help")

        assert result.returncode == 0
        assert "pietree" in result.stdout.lower()
        assert "render" in result.stdout
        assert "query" in result.stdout

    def test_render_help(self):
        """Render command shows help."""
        result = run_cli("render", "--help")

        assert result.returncode == 0
        assert "render" in result.stdout.lower()
        assert "--output" in result.stdout

    def test_query_help(self):
        """Query command shows help."""
        result = run_cli("query", "--help")

        assert result.returncode == 0
        assert "query" in result.stdout.lower()
