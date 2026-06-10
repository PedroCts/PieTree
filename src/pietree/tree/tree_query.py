"""
tree_query.py
-------------
Query and selection interface mixin for PieTree.

Provides methods for creating selections of nodes, branches, and labels
based on type and metadata filters.
"""

from __future__ import annotations

from typing import List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    from pietree.query.selection import NodeSelection, BranchSelection, LabelSelection
    from pietree.render.layers.panels import PanelLayer


class TreeQueryMixin:
    """Mixin providing query/selection methods for PieTree."""

    def nodes(
        self,
        node_type: Literal["all", "tip", "internal"] = "all",
        **metadata_filters
    ) -> "NodeSelection":
        """
        Return nodes filtered by type and metadata.

        Parameters
        ----------
        node_type : {'all', 'tip', 'internal'}, default 'all'
            Which subset of nodes to return.
        **metadata_filters
            Key-value pairs to filter by metadata (e.g., country="Brazil").

        Returns
        -------
        NodeSelection
            A selection of matching nodes with styling methods.

        Examples
        --------
        >>> tips = tree.nodes(node_type="tip")
        >>> brazilian_tips = tree.nodes(node_type="tip", country="Brazil")
        >>> tree.nodes(group="this_study").style(fill="red")
        """
        from pietree.query.selection import NodeSelection

        if node_type == "tip":
            candidates = self.tips
        elif node_type == "internal":
            candidates = self.internal_nodes
        else:
            candidates = self.all_nodes

        if metadata_filters:
            def matches(node):
                for key, value in metadata_filters.items():
                    if node.get(key) != value:
                        return False
                return True
            candidates = [n for n in candidates if matches(n)]

        return NodeSelection(candidates, highlights=self._highlights)

    def tip_names(self) -> List[Optional[str]]:
        """
        Return list of all tip names.

        Returns
        -------
        list of str or None
            Names of all tip nodes (None for unnamed tips).

        Examples
        --------
        >>> names = tree.tip_names()
        >>> print(names)
        ['Human', 'Mouse', 'Dog']
        """
        return [t.name for t in self.tips]

    # ------------------------------------------------------------------
    # Branch access
    # ------------------------------------------------------------------

    def branches(self, **metadata_filters) -> "BranchSelection":
        """
        Return a selection of branches matching metadata filters.

        Parameters
        ----------
        **metadata_filters
            Key-value pairs to filter branches by metadata.

        Returns
        -------
        BranchSelection
            A selection of matching branches with styling methods.

        Examples
        --------
        >>> all_branches = tree.branches()
        >>> long_branches = tree.branches()  # then filter programmatically
        """
        from pietree.query.selection import BranchSelection

        candidates = list(self.iter_branches())

        if metadata_filters:
            def matches(branch):
                for key, value in metadata_filters.items():
                    meta = branch._metadata
                    if meta.get(key) != value:
                        return False
                return True
            candidates = [b for b in candidates if matches(b)]

        return BranchSelection(candidates)

    # ------------------------------------------------------------------
    # Label access
    # ------------------------------------------------------------------

    def labels(
        self,
        target: str = "all",   # "all" | "tip" | "internal"
        **metadata_filters,
    ) -> "LabelSelection":
        """
        Return a selection of node labels.

        Parameters
        ----------
        target : {'all', 'tip', 'internal'}, default 'all'
            Which nodes to get labels from.
        **metadata_filters
            Key-value pairs to filter by metadata.

        Returns
        -------
        LabelSelection
            A selection of labels with styling methods.

        Examples
        --------
        >>> tree.labels(target="tip")
        >>> tree.labels(country="Brazil").suffix(" *")
        """
        from pietree.query.selection import LabelSelection

        if target == "tip":
            candidates = self.tips
        elif target == "internal":
            candidates = self.internal_nodes
        else:
            candidates = self.all_nodes

        if metadata_filters:
            def matches(node):
                return all(node.get(k) == v for k, v in metadata_filters.items())
            candidates = [n for n in candidates if matches(n)]

        return LabelSelection(n.label for n in candidates)

    def tip_labels(self, **metadata_filters) -> "LabelSelection":
        """
        Return a selection of tip labels only.

        Parameters
        ----------
        **metadata_filters
            Key-value pairs to filter by metadata.

        Returns
        -------
        LabelSelection
            A selection of tip labels with styling methods.

        Examples
        --------
        >>> tree.tip_labels().style(font_weight="bold")
        >>> tree.tip_labels(group="this_study").suffix(" *")
        """
        return self.labels(target="tip", **metadata_filters)

    def panel(self, field: str, values=None, **kwargs) -> "PanelLayer":
        """
        Register a metadata panel for rendering.

        Metadata panels display categorical data as colored bars alongside
        the tree, automatically positioned after tip labels.

        Parameters
        ----------
        field : str
            The metadata field to display.
        values : list of str, optional
            Specific values to show. If None, shows all unique values.
        **kwargs
            Additional styling options passed to PanelLayer.

        Returns
        -------
        PanelLayer
            The created panel layer (also added to tree._panels).

        Examples
        --------
        >>> tree.panel("group", values=["this_study", "reference"])
        >>> tree.panel("country")
        """
        from pietree.render.layers.panels import PanelLayer

        panel_layer = PanelLayer(
            field=field,
            index=len(self._panels),
            values=values,
            **kwargs
        )
        self._panels.append(panel_layer)
        return panel_layer
