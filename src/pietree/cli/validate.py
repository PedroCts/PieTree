"""
validate.py
-----------
CLI command for validating tree files.
"""

import sys
from pathlib import Path


def register_parser(subparsers):
    """Register the validate subcommand parser."""
    p = subparsers.add_parser(
        "validate",
        help="Validate tree file structure",
        description="Check phylogenetic tree files for structural validity and common issues."
    )

    # Required arguments
    p.add_argument(
        "tree_file",
        help="Path to tree file to validate"
    )

    # Format options
    p.add_argument(
        "-f", "--format",
        choices=["newick", "nexus", "phyloxml"],
        help="Input format (auto-detected if not specified)"
    )

    # Validation options
    p.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation (fail on warnings)"
    )

    p.add_argument(
        "--check-ultrametric",
        action="store_true",
        help="Check if tree is ultrametric"
    )

    p.add_argument(
        "--check-bifurcating",
        action="store_true",
        help="Check if tree is strictly bifurcating"
    )


def run(args):
    """Execute the validate command."""
    try:
        from pietree.io import parse_newick

        # Load tree
        tree_path = Path(args.tree_file)
        if not tree_path.exists():
            print(f"❌ Error: Tree file not found: {args.tree_file}", file=sys.stderr)
            sys.exit(1)

        # Detect format
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
        print(f"Validating {tree_path.name} ({input_format})...")
        print()

        try:
            if input_format == "newick":
                tree = parse_newick(str(tree_path))
            else:
                print(f"❌ Error: Format '{input_format}' not yet supported", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"❌ Parse Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Basic validation
        issues = []
        warnings = []

        # Check basic structure
        print("✅ File successfully parsed")
        print(f"✅ Tree has {tree.n_tips} tips and {len(tree.internal_nodes)} internal nodes")

        # Check for root
        if tree.root is None:
            issues.append("Tree has no root node")
        else:
            print("✅ Tree has a valid root")

        # Check for unnamed tips
        unnamed_tips = [tip for tip in tree.tips if tip.name is None]
        if unnamed_tips:
            warnings.append(f"{len(unnamed_tips)} tips have no name")
        else:
            print("✅ All tips have names")

        # Check for duplicate tip names
        tip_names = [tip.name for tip in tree.tips if tip.name is not None]
        duplicates = set([name for name in tip_names if tip_names.count(name) > 1])
        if duplicates:
            issues.append(f"Duplicate tip names found: {', '.join(sorted(duplicates))}")
        else:
            print("✅ No duplicate tip names")

        # Check bifurcation
        if args.check_bifurcating:
            non_bifurcating = [
                node for node in tree.internal_nodes
                if len(node.children) != 2
            ]
            if non_bifurcating:
                warnings.append(f"Tree is not strictly bifurcating ({len(non_bifurcating)} nodes have ≠2 children)")
            else:
                print("✅ Tree is strictly bifurcating")

        # Check ultrametricity
        if args.check_ultrametric:
            # Simple check: all tips should be at same distance from root
            # This is a simplified check; full ultrametric check would need branch lengths
            warnings.append("Ultrametric check not yet implemented")

        # Report results
        print()
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
            print()

        if issues:
            print("❌ Issues:")
            for issue in issues:
                print(f"  - {issue}")
            print()
            sys.exit(1)
        else:
            if warnings and args.strict:
                print("❌ Validation failed (strict mode enabled, warnings treated as errors)")
                sys.exit(1)
            else:
                print("✅ Validation passed!")
                sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
