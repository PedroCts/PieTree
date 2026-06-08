def register_parser(subparsers):
    p = subparsers.add_parser("query", help="Query nodes and clades in a tree.")
    p.add_argument("tree_file", help="Path to Newick tree file.")


def run(args):
    print("Query subsystem not implemented yet.")