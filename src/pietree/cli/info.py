def register_parser(subparsers):
    p = subparsers.add_parser("info", help="Display summary information about a tree.")
    p.add_argument("tree_file", help="Path to Newick tree file.")


def run(args):
    from pietree.tree.pietree import PieTree

    tree = PieTree.from_newick(args.tree_file)

    nodes = list(tree.traverse())
    tips = [n for n in nodes if n.is_tip]
    branches = [n for n in nodes if not n.is_tip]

    print(f"Nodes    : {len(nodes)}")
    print(f"Tips     : {len(tips)}")
    print(f"Branches : {len(branches)}")
