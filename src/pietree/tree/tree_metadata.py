"""
tree_metadata.py
----------------
Metadata operations mixin for PieTree.

Provides methods for annotating trees with metadata from DataFrames or dicts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    from pietree.tree.pienode import PieNode
    import pandas as pd


class TreeMetadataMixin:
    """Mixin providing metadata operations for PieTree."""

    def metadata(self, field: Optional[str] = None):
        """
        Access tree metadata or get a field-scoped view.

        Parameters
        ----------
        field : str, optional
            If provided, returns a MetadataView for this field, enabling
            field-specific operations like highlight(), label_nodes(), panel().
            If None, returns the tree's PieMeta object.

        Returns
        -------
        PieMeta or MetadataView
            Tree metadata object or field-specific view.

        Examples
        --------
        >>> tree.metadata("taxonomy").highlight(depth=1, palette="tab10")
        >>> tree.metadata("group").panel(values=["this_study"])
        """
        if field is None:
            return self._metadata
        from pietree.metadata.piemeta import MetadataView
        return MetadataView(self, field)

    def annotate(
        self,
        metadata_df: "pd.DataFrame",
        on: str = "name",
        overwrite: bool = True,
    ) -> "PieTree":
        """
        Annotate tree nodes from a :class:`pandas.DataFrame`.

        Each row is matched to a node by comparing the *on* column value
        against each node's ``name`` (default), ``id``, or any metadata
        field already stored on the node.

        Parameters
        ----------
        metadata_df : DataFrame
            Must contain a column named *on*. All other columns become
            node metadata keys.
        on : str, default 'name'
            The DataFrame column whose values are matched against node
            names. Pass ``"name"`` (default) to match against
            ``node.name``; pass ``"id"`` to match against the UUID;
            or pass any other column name (e.g. ``"mitogenome_id"``) to
            match against a metadata field of the same name already
            stored on each node **or** against ``node.name`` when the
            column name happens to equal ``"name"``.

            The most common pattern — where the join column is whatever
            the newick tip labels are — works with any column name:

                tree.annotate(samples, on="mitogenome_id")

        overwrite : bool, default True
            Whether incoming values overwrite existing metadata keys.

        Returns
        -------
        PieTree
            ``self``, for optional method chaining.

        Examples
        --------
        >>> import pandas as pd
        >>> samples = pd.read_csv("samples.csv")
        >>> tree.annotate(samples, on="accession")
        >>> tree.annotate(samples, on="name", overwrite=False)

        Raises
        ------
        ValueError
            If the *on* column is not found in the DataFrame.
        """
        if on not in metadata_df.columns:
            raise ValueError(
                f"Column '{on}' not found in DataFrame. "
                f"Available columns: {list(metadata_df.columns)}"
            )

        mapping: Dict[str, dict] = {}
        for _, row in metadata_df.iterrows():
            row_dict = row.to_dict()
            key = row_dict.get(on, None)
            if key is not None:
                mapping[str(key)] = row_dict

        self.annotate_dict(mapping, on=on, overwrite=overwrite)
        return self

    def annotate_dict(
        self,
        metadata: Dict[str, dict],
        on: str = "name",
        overwrite: bool = True,
    ) -> "PieTree":
        """
        Annotate tree nodes from a plain dictionary.

        Parameters
        ----------
        metadata : dict
            Mapping of node identifier → ``{field: value, …}``.

            Example::

                {
                    "sample_1": {"haplogroup": "H1a1", "country": "Brazil"},
                    "sample_2": {"haplogroup": "U5"},
                }

        on : str, default 'name'
            The field used to look up nodes.

            * ``"name"`` (default) — match against ``node.name``.
            * ``"id"`` — match against the node's UUID string.
            * Any other string — match against a metadata field of that
              name already stored on each node (e.g. ``"mitogenome_id"``
              or ``"accession"``).

        overwrite : bool, default True
            Whether incoming values overwrite existing metadata keys.

        Returns
        -------
        PieTree
            ``self``, for optional method chaining.

        Examples
        --------
        >>> metadata = {
        ...     "Human": {"country": "Brazil", "group": "this_study"},
        ...     "Mouse": {"country": "USA", "group": "reference"}
        ... }
        >>> tree.annotate_dict(metadata)
        """
        from pietree.tree.pienode import PieNode

        lookup: Dict[str, "PieNode"] = {}
        named_nodes: List["PieNode"] = []  # candidates for substring fallback

        for node in self.traverse():
            if on == "name":
                if node.name is not None:
                    lookup[node.name] = node
            elif on == "id":
                lookup[node.id] = node
            else:
                # Arbitrary metadata field — e.g. "mitogenome_id"
                val = node.get(on)
                if val is not None:
                    lookup[str(val)] = node
                elif node.name is not None:
                    # Collect for substring fallback: newick labels often
                    # embed the join value as a token, e.g.
                    # "Agelena silvatica NC_033971.1" contains "NC_033971.1"
                    named_nodes.append(node)

        for key, values in metadata.items():
            node = lookup.get(str(key))
            if node is None and named_nodes:
                # Substring fallback
                for candidate in named_nodes:
                    if str(key) in candidate.name:
                        node = candidate
                        lookup[str(key)] = candidate  # cache hit
                        break
            if node is None:
                continue
            for k, v in values.items():
                node.annotate(k, v, overwrite=overwrite)

        return self

    def annotate_all(
        self,
        key: str,
        value: Any,
        node_type: Literal["all", "tip", "internal"] = "all",
    ) -> None:
        """
        Set the same metadata *key*/*value* on every node of the given type.

        Useful for broadcasting a tree-wide flag or resetting a field.

        Parameters
        ----------
        key : str
            Metadata key to set.
        value : any
            Value to assign.
        node_type : {'all', 'tip', 'internal'}, default 'all'
            Which nodes to annotate.

        Examples
        --------
        >>> tree.annotate_all("dataset", "my_experiment")
        >>> tree.annotate_all("selected", True, node_type="tip")
        """
        for node in self.nodes(node_type=node_type):
            node.annotate(key, value)

    def clear_all_metadata(
        self,
        node_type: Literal["all", "tip", "internal"] = "all",
    ) -> None:
        """
        Clear all metadata from every node of the given type.

        Parameters
        ----------
        node_type : {'all', 'tip', 'internal'}, default 'all'
            Which nodes to clear metadata from.

        Examples
        --------
        >>> tree.clear_all_metadata()
        >>> tree.clear_all_metadata(node_type="internal")
        """
        for node in self.nodes(node_type=node_type):
            node.clear_metadata()
