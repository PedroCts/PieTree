"""
pieobject.py
------------
Base class for all PieTree objects with metadata and styling support.
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Optional

from pietree.metadata.piemeta import PieMeta


class PieObject(ABC):
    """
    Base class for all PieTree objects with metadata and styling.

    Provides a common interface for metadata access and storage.
    Subclasses (PieNode, PieBranch) can override _default_style()
    to provide type-specific styling.
    """

    def __init__(self, metadata: Optional[dict] = None):
        self._metadata = PieMeta(metadata or {})

    @property
    def metadata(self) -> PieMeta:
        """Access the metadata mapping for this object."""
        return self._metadata

    def get(self, key: str, default: Any = None) -> Any:
        """
        Convenience accessor for metadata values.

        Parameters
        ----------
        key : str
            Metadata key to retrieve.
        default : any, optional
            Default value if key is not present.

        Returns
        -------
        any
            The metadata value or default.

        Examples
        --------
        >>> node.get("taxonomy")
        ['Animalia', 'Chordata', 'Mammalia']
        >>> node.get("missing_key", default="N/A")
        'N/A'
        """
        return self._metadata.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Convenience setter for metadata values.

        Parameters
        ----------
        key : str
            Metadata key to set.
        value : any
            Value to assign.

        Examples
        --------
        >>> node.set("country", "Brazil")
        >>> node.get("country")
        'Brazil'
        """
        self._metadata[key] = value

    def has(self, key: str) -> bool:
        """
        Check if a metadata key exists.

        Parameters
        ----------
        key : str
            Metadata key to check.

        Returns
        -------
        bool
            True if the key exists, False otherwise.

        Examples
        --------
        >>> node.has("taxonomy")
        True
        >>> node.has("missing_key")
        False
        """
        return key in self._metadata.data