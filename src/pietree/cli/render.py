"""
render.py
---------
CLI command for rendering phylogenetic trees to image files.
"""

import sys
import json
from pathlib import Path


def register_parser(subparsers):
    """Register the render subcommand parser."""
    p = subparsers.add_parser(
        "render",
        help="Render a phylogenetic tree to image file",
        description="Render phylogenetic trees with customizable layout, styling, and annotations."
    )

    # Required arguments
    p.add_argument(
        "tree_file",
        help="Path to tree file (Newick, NEXUS, PhyloXML)"
    )

    # Output options
    p.add_argument(
        "-o", "--output",
        default="tree.svg",
        help="Output file path (format inferred from extension) [default: tree.svg]"
    )

    # Input format
    p.add_argument(
        "-f", "--format",
        choices=["newick", "nexus", "phyloxml"],
        help="Input format (auto-detected if not specified)"
    )

    # Layout options
    p.add_argument(
        "-m", "--mode",
        choices=["phylogram", "cladogram", "ultrametric"],
        default="phylogram",
        help="Layout mode [default: phylogram]"
    )

    p.add_argument(
        "--orientation",
        choices=["horizontal", "vertical"],
        default="horizontal",
        help="Tree orientation [default: horizontal]"
    )

    p.add_argument(
        "--size",
        help="Canvas size in pixels (WIDTHxHEIGHT, e.g., 1000x1000) [default: 1000x1000]"
    )

    # Metadata options
    p.add_argument(
        "--metadata",
        help="CSV/JSON file with metadata to annotate"
    )

    p.add_argument(
        "--metadata-on",
        default="name",
        help="Join metadata on this field [default: name]"
    )

    # Styling options
    p.add_argument(
        "--highlight",
        action="append",
        help="Highlight clade by metadata (format: FIELD:VALUE:COLOR)"
    )

    p.add_argument(
        "--style-file",
        help="JSON file with style rules"
    )

    # Display options
    p.add_argument(
        "--no-labels",
        action="store_true",
        help="Hide tip labels"
    )

    p.add_argument(
        "--no-scale",
        action="store_true",
        help="Hide scale bar"
    )


def run(args):
    """Execute the render command."""
    try:
        from pietree.io import parse_newick
        from pietree.tree.pietree import PieTree
        import pandas as pd

        # Load tree
        tree_path = Path(args.tree_file)
        if not tree_path.exists():
            print(f"Error: Tree file not found: {args.tree_file}", file=sys.stderr)
            sys.exit(1)

        # Detect format if not specified
        input_format = args.format
        if not input_format:
            ext = tree_path.suffix.lower()
            format_map = {
                ".newick": "newick",
                ".nwk": "newick",
                ".tree": "newick",
                ".nexus": "nexus",
                ".nex": "nexus",
                ".xml": "phyloxml"
            }
            input_format = format_map.get(ext, "newick")

        # Parse tree
        if input_format == "newick":
            tree = parse_newick(str(tree_path))
        else:
            print(f"Error: Format '{input_format}' not yet supported", file=sys.stderr)
            sys.exit(1)

        # Load and annotate metadata if provided
        if args.metadata:
            metadata_path = Path(args.metadata)
            if not metadata_path.exists():
                print(f"Error: Metadata file not found: {args.metadata}", file=sys.stderr)
                sys.exit(1)

            # Read metadata based on file extension
            ext = metadata_path.suffix.lower()
            if ext == ".csv":
                df = pd.read_csv(metadata_path)
            elif ext == ".json":
                df = pd.read_json(metadata_path)
            else:
                print(f"Error: Unsupported metadata format: {ext}", file=sys.stderr)
                sys.exit(1)

            # Annotate tree
            tree.annotate(df, on=args.metadata_on)

        # Parse size if provided
        width, height = 1000, 1000
        if args.size:
            try:
                w, h = args.size.split("x")
                width, height = int(w), int(h)
            except ValueError:
                print(f"Error: Invalid size format: {args.size} (use WIDTHxHEIGHT)", file=sys.stderr)
                sys.exit(1)

        # Create render options
        render_kwargs = {
            "mode": args.mode,
        }

        # Size is handled separately - tree.to_svg doesn't take width/height directly
        # It would need to be passed to the underlying render pipeline

        # Apply highlights if specified
        # Note: This would need highlighting layer implementation
        # For now, we'll just note them
        if args.highlight:
            # Parse highlight specifications
            # Format: FIELD:VALUE:COLOR
            for spec in args.highlight:
                parts = spec.split(":")
                if len(parts) != 3:
                    print(f"Warning: Invalid highlight spec: {spec} (use FIELD:VALUE:COLOR)", file=sys.stderr)
                    continue
                # TODO: Apply highlighting when rendering

        # Render tree
        output_path = Path(args.output)
        ext = output_path.suffix.lower()

        if ext == ".svg":
            # Render to SVG
            svg_content = tree.to_svg(**render_kwargs)
            output_path.write_text(svg_content)
            print(f"Tree rendered to: {output_path}")

        elif ext in [".png", ".pdf", ".jpg", ".jpeg"]:
            # Render to raster format
            tree.savefig(str(output_path), **render_kwargs)
            print(f"Tree rendered to: {output_path}")

        else:
            print(f"Error: Unsupported output format: {ext}", file=sys.stderr)
            print("Supported formats: .svg, .png, .pdf, .jpg", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
