"""
convert.py
----------
CLI command for converting between tree file formats.
"""

import sys
from pathlib import Path


def register_parser(subparsers):
    """Register the convert subcommand parser."""
    p = subparsers.add_parser(
        "convert",
        help="Convert between tree file formats",
        description="Convert phylogenetic trees between different file formats (Newick, NEXUS, PhyloXML)."
    )

    # Required arguments
    p.add_argument(
        "input_file",
        help="Path to input tree file"
    )

    p.add_argument(
        "output_file",
        help="Path to output tree file (format inferred from extension)"
    )

    # Format options
    p.add_argument(
        "--from",
        dest="input_format",
        choices=["newick", "nexus", "phyloxml"],
        help="Input format (auto-detected if not specified)"
    )

    p.add_argument(
        "--to",
        dest="output_format",
        choices=["newick", "nexus", "phyloxml"],
        help="Output format (inferred from output file extension if not specified)"
    )

    # Options
    p.add_argument(
        "--preserve-metadata",
        action="store_true",
        help="Preserve node metadata in output (if format supports it)"
    )


def run(args):
    """Execute the convert command."""
    try:
        from pietree.io import parse_newick, to_newick

        # Load input tree
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
            sys.exit(1)

        # Detect input format
        input_format = args.input_format
        if not input_format:
            ext = input_path.suffix.lower()
            format_map = {
                ".newick": "newick",
                ".nwk": "newick",
                ".tree": "newick",
                ".nexus": "nexus",
                ".nex": "nexus",
                ".xml": "phyloxml"
            }
            input_format = format_map.get(ext, "newick")
            print(f"Auto-detected input format: {input_format}")

        # Parse tree
        if input_format == "newick":
            tree = parse_newick(str(input_path))
        else:
            print(f"Error: Input format '{input_format}' not yet supported", file=sys.stderr)
            print("Currently supported: newick", file=sys.stderr)
            sys.exit(1)

        # Detect output format
        output_path = Path(args.output_file)
        output_format = args.output_format
        if not output_format:
            ext = output_path.suffix.lower()
            format_map = {
                ".newick": "newick",
                ".nwk": "newick",
                ".tree": "newick",
                ".nexus": "nexus",
                ".nex": "nexus",
                ".xml": "phyloxml"
            }
            output_format = format_map.get(ext, "newick")
            print(f"Auto-detected output format: {output_format}")

        # Convert
        if output_format == "newick":
            output_content = to_newick(tree)
        else:
            print(f"Error: Output format '{output_format}' not yet supported", file=sys.stderr)
            print("Currently supported: newick", file=sys.stderr)
            sys.exit(1)

        # Write output
        output_path.write_text(output_content)

        print(f"Converted {input_path.name} ({input_format}) -> {output_path.name} ({output_format})")
        print(f"Output written to: {output_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
