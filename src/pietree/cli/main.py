import argparse
from pietree.cli import render, info, query


def main():
    parser = argparse.ArgumentParser(
        prog="pietree",
        description="PieTree — metadata-aware phylogenetic analysis and visualization.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    render.register_parser(subparsers)
    info.register_parser(subparsers)
    query.register_parser(subparsers)

    args = parser.parse_args()

    dispatch = {
        "render": render.run,
        "info":   info.run,
        "query":  query.run,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()