import argparse
from pietree.cli import render, info, query, annotate, convert, validate


def main():
    parser = argparse.ArgumentParser(
        prog="pietree",
        description="PieTree — metadata-aware phylogenetic analysis and visualization.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # Register all commands
    render.register_parser(subparsers)
    info.register_parser(subparsers)
    query.register_parser(subparsers)
    annotate.register_parser(subparsers)
    convert.register_parser(subparsers)
    validate.register_parser(subparsers)

    args = parser.parse_args()

    dispatch = {
        "render": render.run,
        "info": info.run,
        "query": query.run,
        "annotate": annotate.run,
        "convert": convert.run,
        "validate": validate.run,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()