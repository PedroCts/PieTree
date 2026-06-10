"""
annotate.py
-----------
CLI command for annotating trees with metadata.
"""

import sys
from pathlib import Path


def register_parser(subparsers):
    """Register the annotate subcommand parser."""
    p = subparsers.add_parser(
        "annotate",
        help="Annotate tree with metadata",
        description="Add metadata to tree nodes from CSV or JSON files."
    )

    # Required arguments
    p.add_argument(
        "tree_file",
        help="Path to input tree file (Newick, NEXUS, PhyloXML)"
    )

    p.add_argument(
        "metadata_file",
        help="Path to metadata file (CSV or JSON)"
    )

    # Output options
    p.add_argument(
        "-o", "--output",
        required=True,
        help="Output tree file (Newick format)"
    )

    # Input format
    p.add_argument(
        "-f", "--format",
        choices=["newick", "nexus", "phyloxml"],
        help="Input tree format (auto-detected if not specified)"
    )

    # Annotation options
    p.add_argument(
        "--on",
        default="name",
        help="Join metadata on this field [default: name]"
    )

    # Metadata embedding
    p.add_argument(
        "--embed",
        action="store_true",
        help="Embed metadata in Newick comments (e.g., [&country=Brazil])"
    )


def run(args):
    """Execute the annotate command."""
    try:
        from pietree.io import parse_newick, to_newick
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

        # Load metadata
        metadata_path = Path(args.metadata_file)
        if not metadata_path.exists():
            print(f"Error: Metadata file not found: {args.metadata_file}", file=sys.stderr)
            sys.exit(1)

        ext = metadata_path.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(metadata_path)
        elif ext == ".json":
            df = pd.read_json(metadata_path)
        else:
            print(f"Error: Unsupported metadata format: {ext}", file=sys.stderr)
            print("Supported formats: .csv, .json", file=sys.stderr)
            sys.exit(1)

        # Annotate tree
        print(f"Annotating tree with metadata from {metadata_path.name}...")
        tree.annotate(df, on=args.on)

        # Count annotated nodes
        annotated = sum(1 for node in tree.traverse() if node.metadata.data)
        print(f"Annotated {annotated} nodes")

        # Write output
        output_path = Path(args.output)
        newick_str = to_newick(tree)

        output_path.write_text(newick_str)
        print(f"Annotated tree written to: {output_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
