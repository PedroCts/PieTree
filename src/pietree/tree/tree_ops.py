"""
tree_ops.py
-----------
Tree operations mixin for PieTree.

Provides methods for traversing, searching, querying, and analyzing tree topology.
"""

from __future__ import annotations

from typing import Callable, Iterator, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    from pietree.tree.pienode import PieNode
    from pietree.tree.piebranch import PieBranch
    from pietree.tree.pieclade import PieClade

NodeFilter = Callable[["PieNode"], bool]
BranchFilter = Callable[["PieBranch"], bool]


class TreeOpsMixin:
    """Mixin providing tree operation methods for PieTree."""

    def traverse(self, order: str = "preorder") -> Iterator["PieNode"]:
        """
        Iterate over every node in the tree.

        Parameters
        ----------
        order : {'preorder', 'postorder'}
            Traversal order passed through to :meth:`PieNode.walk`.

        Yields
        ------
        PieNode
            Nodes in traversal order.

        Examples
        --------
        >>> for node in tree.traverse():
        ...     print(node.name)
        """
        yield from self.root.walk(order=order)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def find_tip(self, name: str) -> Optional["PieNode"]:
        """
        Return the first tip node whose name matches *name*, or ``None``.

        Parameters
        ----------
        name : str
            The tip name to search for.

        Returns
        -------
        PieNode or None
            The matching tip node, or None if not found.

        Examples
        --------
        >>> tip = tree.find_tip("Human")
        """
        for tip in self.tips:
            if tip.name == name:
                return tip
        return None

    def find_node_by_id(self, node_id: str) -> Optional["PieNode"]:
        """
        Return the node with the given UUID string, or ``None``.

        Parameters
        ----------
        node_id : str
            The node UUID to search for.

        Returns
        -------
        PieNode or None
            The matching node, or None if not found.
        """
        for node in self.traverse():
            if node.id == node_id:
                return node
        return None

    def find_node_by_name(self, name: str) -> Optional["PieNode"]:
        """
        Return the first node (tip or internal) whose name matches *name*.

        Prefer :meth:`find_tip` when you know the target is a leaf.

        Parameters
        ----------
        name : str
            The node name to search for.

        Returns
        -------
        PieNode or None
            The matching node, or None if not found.

        Examples
        --------
        >>> node = tree.find_node_by_name("internal_1")
        """
        for node in self.traverse():
            if node.name == name:
                return node
        return None

    def find_nodes(self, predicate: NodeFilter) -> List["PieNode"]:
        """
        Return all nodes for which *predicate(node)* is ``True``.

        Parameters
        ----------
        predicate : callable
            Function that takes a PieNode and returns bool.

        Returns
        -------
        list of PieNode
            All matching nodes.

        Examples
        --------
        >>> deep_nodes = tree.find_nodes(lambda n: n.depth > 5)
        """
        return [n for n in self.traverse() if predicate(n)]

    def find_branches(self, predicate: BranchFilter) -> List["PieBranch"]:
        """
        Return all branches for which *predicate(branch)* is ``True``.

        Parameters
        ----------
        predicate : callable
            Function that takes a PieBranch and returns bool.

        Returns
        -------
        list of PieBranch
            All matching branches.

        Examples
        --------
        >>> long_branches = tree.find_branches(lambda b: b.length and b.length > 0.5)
        """
        return [b for b in self.iter_branches() if predicate(b)]

    def query(
        self,
        func: Optional[NodeFilter] = None,
        **kwargs,
    ) -> List["PieNode"]:
        """
        Flexible node query.

        Pass a callable *func* to filter by any logic, or keyword arguments
        to match node attributes by equality.

        Parameters
        ----------
        func : callable, optional
            Filter function taking a PieNode and returning bool.
        **kwargs
            Attribute name-value pairs to match (e.g., is_tip=True).

        Returns
        -------
        list of PieNode
            All matching nodes.

        Examples
        --------
        >>> tree.query(is_tip=True)
        >>> tree.query(func=lambda n: "brazil" in (n.get("country") or ""))
        """
        results = []
        for node in self.traverse():
            if func is not None:
                if func(node):
                    results.append(node)
            elif all(getattr(node, k, None) == v for k, v in kwargs.items()):
                results.append(node)
        return results

    # ------------------------------------------------------------------
    # MRCA & distance
    # ------------------------------------------------------------------

    def mrca(self, nodes: List["PieNode"]) -> Optional["PieNode"]:
        """
        Most Recent Common Ancestor of a list of nodes.

        Returns ``None`` for an empty list; returns the node itself for a
        singleton. For two or more nodes, returns the deepest node that is
        an ancestor of all of them.

        Parameters
        ----------
        nodes : list of PieNode
            Nodes to find the MRCA for.

        Returns
        -------
        PieNode or None
            The most recent common ancestor, or None if empty list.

        Examples
        --------
        >>> ancestor = tree.mrca([node1, node2, node3])
        """
        if not nodes:
            return None
        if len(nodes) == 1:
            return nodes[0]

        # Intersection of ancestor sets; start from the first node's path
        common: set = set(nodes[0].path_to_root())
        for node in nodes[1:]:
            common &= set(node.path_to_root())

        if not common:
            return None

        # Deepest = first node in path_to_root that is in common
        for n in nodes[0].path_to_root():
            if n in common:
                return n

        return None  # unreachable, but satisfies type-checker

    def distance(
        self,
        node1: "PieNode",
        node2: "PieNode",
        weighted: bool = False,
    ) -> float:
        """
        Path distance between two nodes.

        Parameters
        ----------
        node1, node2 : PieNode
            The two nodes to measure distance between.
        weighted : bool, default False
            If ``True``, sum branch lengths; if ``False``, count edges.

        Returns
        -------
        float
            The distance between the two nodes.

        Raises
        ------
        ValueError
            If *weighted* is ``True`` but a branch on the path has no length,
            or if nodes share no common ancestor.

        Examples
        --------
        >>> dist = tree.distance(tip1, tip2, weighted=True)
        """
        ancestor = self.mrca([node1, node2])
        if ancestor is None:
            raise ValueError("Nodes share no common ancestor in this tree.")

        def dist_to_ancestor(node: "PieNode", anc: "PieNode") -> float:
            total = 0.0
            current = node
            while current != anc:
                if current.parent is None:
                    break
                if weighted:
                    branch = current.parent_branch
                    if branch is None or branch.length is None:
                        raise ValueError(
                            f"Branch above '{current.name}' has no length; "
                            "set weighted=False or add branch lengths."
                        )
                    total += branch.length
                else:
                    total += 1.0
                current = current.parent  # type: ignore[assignment]
            return total

        return dist_to_ancestor(node1, ancestor) + dist_to_ancestor(node2, ancestor)

    # ------------------------------------------------------------------
    # Clade / subtree
    # ------------------------------------------------------------------

    def clade(
        self,
        nodes: Union["PieNode", List["PieNode"]],
        allow_single_tip: bool = False
    ) -> "PieClade":
        """
        Return the clade (subtree) defined by *nodes*.

        If *nodes* is a list, the clade is rooted at their MRCA.
        If *nodes* is a single :class:`PieNode`, that node is the clade root.

        Parameters
        ----------
        nodes : PieNode or list of PieNode
            Node(s) defining the clade.
        allow_single_tip : bool, default False
            If True, allow single-tip clades.

        Returns
        -------
        PieClade
            The clade object.

        Examples
        --------
        >>> clade = tree.clade([tip1, tip2, tip3])
        >>> clade = tree.clade(internal_node)
        """
        from pietree.tree.pieclade import PieClade

        root = self.mrca(nodes) if isinstance(nodes, list) else nodes
        if allow_single_tip:
            tips = [root] if root.is_tip else root.descendant_tips
        else:
            tips = root.descendant_tips

        return PieClade(
            root=root,
            nodes=[root] + root.descendants,
            tips=tips,
            highlights=self._highlights,
        )

    def find_tips_by_taxon(self, taxon: str) -> List["PieNode"]:
        """
        Return all tip nodes whose taxonomy list contains *taxon*.

        Parameters
        ----------
        taxon : str
            Taxonomic name to search for.

        Returns
        -------
        list of PieNode
            All tips containing this taxon in their taxonomy metadata.

        Examples
        --------
        >>> mammals = tree.find_tips_by_taxon("Mammalia")
        """
        return self.find_nodes(
            lambda n: n.is_tip and taxon in n.get_taxonomy()
        )

    def clade_by_taxon(self, taxon: str) -> "PieClade":
        """
        Return the clade spanning all tips annotated with *taxon*.

        Parameters
        ----------
        taxon : str
            Taxonomic name defining the clade.

        Returns
        -------
        PieClade
            The clade containing all tips with this taxon.

        Examples
        --------
        >>> mammal_clade = tree.clade_by_taxon("Mammalia")
        """
        tips = self.find_tips_by_taxon(taxon)
        return self.clade(tips)

    def induced_subtree(self, tips: List["PieNode"]) -> Optional["PieTree"]:
        """
        Build the minimal subtree that connects *tips* to each other and the
        root, preserving topology and metadata but cloning all nodes.

        Returns ``None`` if *tips* is empty.

        Parameters
        ----------
        tips : list of PieNode
            Tip nodes to include in the subtree.

        Returns
        -------
        PieTree or None
            A new tree containing only the specified tips and their ancestors,
            or None if tips list is empty.

        Examples
        --------
        >>> subtree = tree.induced_subtree([tip1, tip2, tip3])
        """
        from pietree.tree.pienode import PieNode
        from pietree.tree.pietree import PieTree

        if not tips:
            return None

        # Collect every node on any path from a tip to the root
        included: set = set()
        for t in tips:
            included.update(t.path_to_root())

        # The subtree root is the included node closest to the overall root
        root_candidates = [n for n in included if n.parent not in included]
        subtree_root = root_candidates[0]

        def clone(node: "PieNode") -> Optional["PieNode"]:
            if node not in included:
                return None
            new = PieNode(
                name=node.name,
                branch_length=node.branch_length,
                metadata=dict(node._metadata.data),
            )
            for child in node.children:
                child_clone = clone(child)
                if child_clone is not None:
                    new.add_child(child_clone, length=child.branch_length)
            return new

        cloned = clone(subtree_root)
        return PieTree(cloned) if cloned else None

    def subtree_from_tip_names(self, names: List[str]) -> Optional["PieTree"]:
        """
        Convenience wrapper: build an induced subtree from a list of tip names.

        Names that don't match any tip are silently ignored.

        Parameters
        ----------
        names : list of str
            Tip names to include in the subtree.

        Returns
        -------
        PieTree or None
            A new tree containing only the named tips and their ancestors.

        Examples
        --------
        >>> subtree = tree.subtree_from_tip_names(["Human", "Mouse", "Dog"])
        """
        tips = [t for t in (self.find_tip(n) for n in names) if t is not None]
        return self.induced_subtree(tips)

    def iter_branches(self) -> Iterator["PieBranch"]:
        """
        Iterate over all branches in the tree.

        Yields
        ------
        PieBranch
            All branches (edges) in the tree.

        Examples
        --------
        >>> for branch in tree.iter_branches():
        ...     print(branch.length)
        """
        for node in self.traverse():
            if node._parent is not None:
                # Find the branch connecting parent to this node
                for child, branch in node._parent._children:
                    if child is node:
                        yield branch
                        break
