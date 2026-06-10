"""
base.py
-------
Abstract base classes for tree I/O operations.

Defines interfaces for parsers and serializers to enable plugin-style
extensibility for supporting new tree file formats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import IO, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree

PathLike = Union[str, Path, IO]


class TreeParser(ABC):
    """
    Base class for tree format parsers.

    Subclass this to implement support for parsing new phylogenetic tree
    file formats. Each parser is responsible for reading a tree from a
    source (file path, file-like object, or string) and returning a
    PieTree instance.

    Examples
    --------
    >>> class MyCustomParser(TreeParser):
    ...     @property
    ...     def format_name(self) -> str:
    ...         return "myformat"
    ...
    ...     def parse(self, source: PathLike) -> PieTree:
    ...         # Custom parsing logic
    ...         return tree
    """

    @abstractmethod
    def parse(self, source: PathLike) -> "PieTree":
        """
        Parse a tree from the given source.

        Parameters
        ----------
        source : str, Path, or file-like
            The tree source to parse. Can be:
            - A file path (str or Path)
            - A file-like object with a `read()` method
            - A string containing the tree data

        Returns
        -------
        PieTree
            The parsed phylogenetic tree.

        Raises
        ------
        ValueError
            If the source format is invalid or cannot be parsed.
        IOError
            If the source file cannot be read.
        """
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """
        Return the format identifier for this parser.

        Returns
        -------
        str
            Format name (e.g., 'newick', 'nexus', 'phyloxml').
        """
        pass


class TreeSerializer(ABC):
    """
    Base class for tree format serializers.

    Subclass this to implement support for serializing trees to new
    phylogenetic file formats. Each serializer is responsible for
    converting a PieTree to its string representation and optionally
    writing it to a destination.

    Examples
    --------
    >>> class MyCustomSerializer(TreeSerializer):
    ...     @property
    ...     def format_name(self) -> str:
    ...         return "myformat"
    ...
    ...     def serialize(self, tree: PieTree, dest=None) -> Optional[str]:
    ...         # Custom serialization logic
    ...         output = "..."
    ...         if dest:
    ...             write_to_dest(output, dest)
    ...             return None
    ...         return output
    """

    @abstractmethod
    def serialize(
        self, tree: "PieTree", dest: Optional[PathLike] = None
    ) -> Optional[str]:
        """
        Serialize a tree to this format.

        Parameters
        ----------
        tree : PieTree
            The tree to serialize.
        dest : str, Path, file-like, or None, optional
            The destination for the serialized output. If None, returns
            the string. If provided, writes to the destination and returns None.

        Returns
        -------
        str or None
            The serialized tree string if dest is None, otherwise None.

        Raises
        ------
        IOError
            If the destination file cannot be written.
        """
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """
        Return the format identifier for this serializer.

        Returns
        -------
        str
            Format name (e.g., 'newick', 'nexus', 'phyloxml').
        """
        pass


class TreeConverter(ABC):
    """
    Base class for tree format converters.

    A converter combines a parser and serializer to convert between
    two specific formats. This is useful for format-specific optimizations
    or when conversion requires format-specific logic beyond simple
    parse-then-serialize.

    Examples
    --------
    >>> class NewickToNexusConverter(TreeConverter):
    ...     @property
    ...     def source_format(self) -> str:
    ...         return "newick"
    ...
    ...     @property
    ...     def target_format(self) -> str:
    ...         return "nexus"
    ...
    ...     def convert(self, source: PathLike, dest: PathLike) -> None:
    ...         # Optimized conversion logic
    ...         pass
    """

    @abstractmethod
    def convert(self, source: PathLike, dest: PathLike) -> None:
        """
        Convert a tree from source format to target format.

        Parameters
        ----------
        source : str, Path, or file-like
            The source tree file.
        dest : str, Path, or file-like
            The destination for the converted tree.

        Raises
        ------
        ValueError
            If the source format is invalid.
        IOError
            If files cannot be read or written.
        """
        pass

    @property
    @abstractmethod
    def source_format(self) -> str:
        """
        Return the source format identifier.

        Returns
        -------
        str
            Source format name (e.g., 'newick').
        """
        pass

    @property
    @abstractmethod
    def target_format(self) -> str:
        """
        Return the target format identifier.

        Returns
        -------
        str
            Target format name (e.g., 'nexus').
        """
        pass
