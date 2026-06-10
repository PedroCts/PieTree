"""
tree_edit.py
------------
Tree editing mixin for PieTree.

Provides methods for pruning, rerooting, and cloning trees.
"""

from __future__ import annotations

import copy
from typing import List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    from pietree.tree.pienode import PieNode
    from pietree.tree.piebranch import PieBranch

NodeOrName = Union["PieNode", str]


class TreeEditMixin:
    """Mixin providing tree editing methods for PieTree."""

    def prune(self, tips: List[NodeOrName]) -> None:
        """
        Remove *tips* from the tree in-place.

        Each tip is detached from its parent. If detaching leaves the parent
        with only one remaining child (and the parent is not the root), that
        parent is also collapsed to keep the tree properly resolved.

        Parameters
        ----------
        tips : list of PieNode or str
            Tips to remove. Strings are resolved via :meth:`find_tip`.

        Raises
        ------
        ValueError
            If a name cannot be resolved or a non-tip node is given.

        Examples
        --------
        >>> tree.prune(["Human", "Mouse"])
        >>> tree.prune([tip1, tip2, tip3])

        Notes
        -----
        This operation modifies the tree in-place. After pruning, some
        internal nodes may be collapsed to maintain a bifurcating structure.
        """

        resolved: List["PieNode"] = []
        for item in tips:
            if isinstance(item, str):
                node = self.find_tip(item)
                if node is None:
                    raise ValueError(f"No tip named '{item}'.")
                resolved.append(node)
            elif item.is_tip:
                resolved.append(item)
            else:
                raise ValueError(f"Node '{item.name}' is not a tip; can only prune tips.")

        for tip in resolved:
            parent = tip.parent
            tip.detach()

            # Collapse a now-unary internal node (skip root)
            if parent is not None and parent.parent is not None and len(parent.children) == 1:
                grandparent = parent.parent
                only_child = parent.children[0]
                # Transfer child up, summing branch lengths where possible
                old_bl = parent.branch_length
                child_bl = only_child.branch_length
                new_bl: Optional[float] = None
                if old_bl is not None and child_bl is not None:
                    new_bl = old_bl + child_bl
                grandparent.remove_child(parent)
                grandparent.add_child(only_child, length=new_bl)

    def reroot(self, new_root: Optional["PieNode"], inplace: bool = True) -> "PieTree":
        """
        Reroot the tree at *new_root*.

        Keeps the same :class:`PieNode` and :class:`PieBranch` objects
        (identity-preserving). Reverses parent pointers along the path from
        *new_root* to the old root.

        Parameters
        ----------
        new_root : PieNode or None
            The node that should become the new root. No-op if ``None``.
        inplace : bool, default True
            If ``True``, modifies this tree. If ``False``, returns a deep
            clone rerooted at the equivalent node.

        Returns
        -------
        PieTree
            Self (if inplace=True) or a new rerooted tree (if inplace=False).

        Examples
        --------
        >>> # Reroot at an internal node
        >>> node = tree.find_node_by_name("internal_1")
        >>> tree.reroot(node)

        >>> # Reroot without modifying original
        >>> rerooted = tree.reroot(node, inplace=False)

        Notes
        -----
        Rerooting changes the direction of edges along the path from new_root
        to the old root, but preserves all topology and branch lengths.
        """
        from pietree.tree.piebranch import PieBranch

        if new_root is None:
            return self

        if not inplace:
            cloned = self._deep_clone()
            # Find the equivalent node in the clone by id
            equiv = cloned.find_node_by_id(new_root.id)
            return cloned.reroot(equiv, inplace=True)

        # Walk from new_root up to the old root, reversing pointers
        current: Optional["PieNode"] = new_root
        prev: Optional["PieNode"] = None
        prev_branch: Optional["PieBranch"] = None

        while current is not None:
            parent = current._parent
            original_branch = current._parent_branch

            # Reverse parent pointer
            current._parent = prev
            current._parent_branch = prev_branch

            if prev is not None:
                # Remove 'prev' from current's children (it was already there
                # from an earlier iteration before the pointer flip)
                current._children = [
                    (c, b) for c, b in current._children if c is not prev
                ]
                # Re-add current as a child of prev, reusing the branch
                reused = prev_branch or original_branch or PieBranch(
                    parent_id=prev.id,
                    child_id=current.id,
                    length=None,
                )
                prev._children.append((current, reused))

            prev = current
            prev_branch = original_branch
            current = parent

        self.root = new_root
        self.root._parent = None
        self.root._parent_branch = None

        return self

    def _deep_clone(self) -> "PieTree":
        """
        Return a structurally independent deep copy of this tree.

        Returns
        -------
        PieTree
            A new tree with cloned nodes and branches.

        Notes
        -----
        Node IDs are preserved so that nodes can be looked up by ID after
        cloning. Branch objects are reused (not cloned) for efficiency.
        """
        from pietree.tree.pienode import PieNode
        from pietree.tree.pietree import PieTree

        def clone_node(node: "PieNode") -> "PieNode":
            new = PieNode(
                name=node.name,
                branch_length=node.branch_length,
                metadata=copy.deepcopy(dict(node._metadata.data)),
            )
            new.id = node.id  # preserve identity so callers can look up by id
            for child, branch in node._children:
                child_clone = clone_node(child)
                child_clone._parent = new
                child_clone._parent_branch = branch  # reuse branch reference
                new._children.append((child_clone, branch))
            return new

        cloned_root = clone_node(self.root)
        return PieTree(cloned_root, metadata=copy.deepcopy(dict(self._metadata.data)))
