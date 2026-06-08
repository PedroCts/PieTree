def register_parser(subparsers):
    p = subparsers.add_parser("render", help="Render a phylogenetic tree to SVG.")
    p.add_argument("tree_file", help="Path to Newick tree file.")


def run(args):
    print(f"Rendering tree: {args.tree_file}")