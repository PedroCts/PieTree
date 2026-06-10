"""
query.py
--------
CLI command for querying nodes and clades in phylogenetic trees.
"""

import sys
import json
from pathlib import Path


def register_parser(subparsers):
    """Register the query subcommand parser."""
    p = subparsers.add_parser(
        "query",
        help="Query nodes and clades in a tree",
        description="Query phylogenetic trees using expressions to find tips, clades, and metadata."
    )

    # Required arguments
    p.add_argument(
        "tree_file",
        help="Path to tree file (Newick, NEXUS, PhyloXML)"
    )

    p.add_argument(
        "expression",
        help="Query expression (e.g., 'tips', 'clade:Mammalia', 'metadata:country=Brazil')"
    )

    # Input format
    p.add_argument(
        "-f", "--format",
        choices=["newick", "nexus", "phyloxml"],
        help="Input format (auto-detected if not specified)"
    )

    # Output format
    p.add_argument(
        "-o", "--output",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format [default: text]"
    )

    # Metadata for annotation
    p.add_argument(
        "--metadata",
        help="CSV/JSON file with metadata to annotate before querying"
    )

    p.add_argument(
        "--metadata-on",
        default="name",
        help="Join metadata on this field [default: name]"
    )


def run(args):
    """Execute the query command."""
    try:
        from pietree.io import parse_newick
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

            ext = metadata_path.suffix.lower()
            if ext == ".csv":
                df = pd.read_csv(metadata_path)
            elif ext == ".json":
                df = pd.read_json(metadata_path)
            else:
                print(f"Error: Unsupported metadata format: {ext}", file=sys.stderr)
                sys.exit(1)

            tree.annotate(df, on=args.metadata_on)

        # Parse and execute query
        results = execute_query(tree, args.expression)

        # Output results
        if args.output == "text":
            print_text_results(results, args.expression)
        elif args.output == "json":
            print_json_results(results)
        elif args.output == "csv":
            print_csv_results(results)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def execute_query(tree, expression):
    """
    Execute a query expression on the tree.

    Supported expressions:
    - "tips" - list all tip names
    - "internal" - list all internal node names
    - "clade:TAXON" - find tips in a taxonomic clade
    - "metadata:FIELD=VALUE" - find nodes with matching metadata
    - "count" - count nodes
    """
    expr = expression.lower().strip()

    # Tips query
    if expr == "tips":
        return [{"name": tip.name or tip.id[:8]} for tip in tree.tips]

    # Internal nodes query
    elif expr == "internal":
        return [{"name": node.name or node.id[:8]} for node in tree.internal_nodes]

    # Count query
    elif expr == "count":
        return {
            "tips": tree.n_tips,
            "internal": len(tree.internal_nodes),
            "total": tree.n_nodes
        }

    # Clade query: clade:TAXON
    elif expr.startswith("clade:"):
        taxon = expression.split(":", 1)[1].strip()
        tips = tree.find_tips_by_taxon(taxon)
        return [{"name": tip.name or tip.id[:8], "taxon": taxon} for tip in tips]

    # Metadata query: metadata:FIELD=VALUE
    elif expr.startswith("metadata:"):
        _, query = expression.split(":", 1)
        if "=" not in query:
            raise ValueError("Metadata query must be in format 'metadata:FIELD=VALUE'")

        field, value = query.split("=", 1)
        field = field.strip()
        value = value.strip()

        # Find nodes with matching metadata
        matching = tree.find_nodes(lambda n: n.get(field) == value)
        return [
            {
                "name": node.name or node.id[:8],
                field: node.get(field),
                "is_tip": node.is_tip
            }
            for node in matching
        ]

    else:
        raise ValueError(f"Unknown query expression: {expression}")


def print_text_results(results, expression):
    """Print results in human-readable text format."""
    if isinstance(results, dict):
        # Count or summary results
        for key, value in results.items():
            print(f"{key}: {value}")
    elif isinstance(results, list):
        # List of nodes
        print(f"Query: {expression}")
        print(f"Results: {len(results)} nodes")
        print()
        for item in results:
            if isinstance(item, dict):
                parts = [f"{k}={v}" for k, v in item.items()]
                print(f"  {', '.join(parts)}")
            else:
                print(f"  {item}")
    else:
        print(results)


def print_json_results(results):
    """Print results as JSON."""
    print(json.dumps(results, indent=2))


def print_csv_results(results):
    """Print results as CSV."""
    if isinstance(results, list) and results and isinstance(results[0], dict):
        # Extract headers
        headers = list(results[0].keys())
        print(",".join(headers))

        # Print rows
        for item in results:
            values = [str(item.get(h, "")) for h in headers]
            print(",".join(values))
    else:
        print("Error: CSV output only supported for list results", file=sys.stderr)
