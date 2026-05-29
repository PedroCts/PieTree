from typing import Callable, List

from pietree.tree.pienode import PieNode
from pietree.tree.piebranch import PieBranch


def iter_nodes(node: PieNode):

    yield node

    for child, _ in node._children:
        yield from iter_nodes(child)


def iter_branches(node: PieNode):

    for child, branch in node._children:

        yield branch

        yield from iter_branches(child)


def find_nodes(
    root: PieNode,
    predicate: Callable[[PieNode], bool]
) -> List[PieNode]:

    return [
        node
        for node in iter_nodes(root)
        if predicate(node)
    ]


def find_branches(
    root: PieNode,
    predicate: Callable[[PieBranch], bool]
) -> List[PieBranch]:

    return [
        branch
        for branch in iter_branches(root)
        if predicate(branch)
    ]