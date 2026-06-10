"""
tree_io.py
----------
I/O factory methods for PieTree.

Provides convenience methods on the PieTree class for parsing and serializing
trees in various formats.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    import pandas as pd


class TreeIOMixin:
    """Mixin providing I/O methods for PieTree."""

    # ------------------------------------------------------------------
    # Parsing (class methods)
    # ------------------------------------------------------------------

    @classmethod
    def from_newick(cls, newick_str=None, path=None, support_format=None) -> "PieTree":
        """
        Parse a Newick tree from a string or file path.

        Parameters
        ----------
        newick_str : str, optional
            Newick string to parse. Either this or `path` must be provided.
        path : str, optional
            Path to Newick file. Either this or `newick_str` must be provided.
        support_format : str, optional
            Support value format string (e.g., '{bootstrap}/{alrt}').

        Returns
        -------
        PieTree
            The parsed tree.

        Examples
        --------
        >>> tree = PieTree.from_newick("((A,B),C);")
        >>> tree = PieTree.from_newick(path="tree.newick")
        >>> tree = PieTree.from_newick(path="tree.nwk", support_format="{bootstrap}/{alrt}")
        """
        from pietree.io import parse_newick
        source = path or newick_str
        return parse_newick(source, support_format=support_format)

    @classmethod
    def from_nexus(cls, source) -> "PieTree":
        """
        Parse a NEXUS tree from a string or file path.

        Parameters
        ----------
        source : str or Path
            NEXUS string or file path.

        Returns
        -------
        PieTree
            The parsed tree.

        Examples
        --------
        >>> tree = PieTree.from_nexus("tree.nex")
        """
        from pietree.io import parse_nexus
        return parse_nexus(source)

    @classmethod
    def from_phyloxml(cls, source) -> "PieTree":
        """
        Parse a PhyloXML tree from a string or file path.

        Parameters
        ----------
        source : str or Path
            PhyloXML string or file path.

        Returns
        -------
        PieTree
            The parsed tree.

        Examples
        --------
        >>> tree = PieTree.from_phyloxml("tree.xml")
        """
        from pietree.io import parse_phyloxml
        return parse_phyloxml(source)

    # ------------------------------------------------------------------
    # Serialization (instance methods)
    # ------------------------------------------------------------------

    def to_newick(self, path=None) -> Optional[str]:
        """
        Serialize tree to Newick format.

        Parameters
        ----------
        path : str, optional
            If provided, writes to this file path. Otherwise returns the string.

        Returns
        -------
        str or None
            Newick string if path is None, otherwise None.

        Examples
        --------
        >>> newick = tree.to_newick()
        >>> tree.to_newick("output.newick")
        """
        from pietree.io import to_newick
        return to_newick(self, dest=path)

    def to_nexus(self, path=None) -> Optional[str]:
        """
        Serialize tree to NEXUS format.

        Parameters
        ----------
        path : str, optional
            If provided, writes to this file path. Otherwise returns the string.

        Returns
        -------
        str or None
            NEXUS string if path is None, otherwise None.

        Examples
        --------
        >>> nexus = tree.to_nexus()
        >>> tree.to_nexus("output.nex")
        """
        from pietree.io import to_nexus
        return to_nexus(self, dest=path)

    def to_phyloxml(self, path=None) -> Optional[str]:
        """
        Serialize tree to PhyloXML format.

        Parameters
        ----------
        path : str, optional
            If provided, writes to this file path. Otherwise returns the string.

        Returns
        -------
        str or None
            PhyloXML string if path is None, otherwise None.

        Examples
        --------
        >>> xml = tree.to_phyloxml()
        >>> tree.to_phyloxml("output.xml")
        """
        from pietree.io import to_phyloxml
        return to_phyloxml(self, dest=path)

    def savefig(self, path: str, **kwargs) -> None:
        """
        Save tree visualization to an image file.

        Format is inferred from file extension (.svg, .png, .pdf, .jpg, .tiff, .psd).

        Parameters
        ----------
        path : str
            Output file path.
        **kwargs
            Additional arguments passed to savefig (dpi, quality, size, mode, etc.).
            See pietree.io.savefig for full documentation.

        Examples
        --------
        >>> tree.savefig("tree.svg")
        >>> tree.savefig("tree.png", dpi=300)
        >>> tree.savefig("tree.pdf", mode="cladogram")
        """
        from pietree.io import savefig
        savefig(self, path, **kwargs)

    def to_dataframe(
        self,
        node_type="tip",
        include_topology=True,
        infer_taxonomy=True
    ) -> "pd.DataFrame":
        """
        Export tree to a pandas DataFrame.

        Parameters
        ----------
        node_type : str, default 'tip'
            Reserved for future use (currently all nodes are exported).
        include_topology : bool, default True
            Include topology columns (depth, parent_id, etc.).
        infer_taxonomy : bool, default True
            Infer taxonomy for internal nodes if 'taxonomy' metadata exists.

        Returns
        -------
        pandas.DataFrame
            One row per node with topology and metadata columns.

        Examples
        --------
        >>> df = tree.to_dataframe()
        >>> df.to_csv("tree_data.csv", index=False)
        """
        from pietree.io import to_dataframe
        return to_dataframe(
            self,
            include_topology=include_topology,
            infer_taxonomy=infer_taxonomy
        )
