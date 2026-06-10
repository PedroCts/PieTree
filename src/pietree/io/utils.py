"""
utils.py
--------
Shared I/O utility functions for PieTree.

Provides helpers for handling file paths, file-like objects, and optional
dependency imports used across parsing and serialization modules.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import IO, Optional, Union

PathLike = Union[str, Path, IO]


def _require(pkg: str, install: Optional[str] = None):
    """
    Lazily import an optional dependency or raise a helpful error.

    Parameters
    ----------
    pkg : str
        The package/module name to import.
    install : str, optional
        The pip install name if different from pkg.

    Returns
    -------
    module
        The imported module.

    Raises
    ------
    ImportError
        If the package is not installed, with installation instructions.

    Examples
    --------
    >>> cairosvg = _require("cairosvg")
    >>> psd_tools = _require("psd_tools", "psd-tools")
    """
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        hint = f"pip install {install or pkg}"
        raise ImportError(
            f"'{pkg}' is required for this operation. Install with: {hint}"
        ) from None


def _open_source(source: PathLike, mode: str = "r") -> tuple[IO, bool]:
    """
    Open a source as a file handle, accepting paths or file-like objects.

    Accepts a string-that-is-a-path, a Path object, or a file-like object.
    Returns (file_handle, should_close).

    A string is treated as raw content (not a path) when it:
    - Contains a newline character, or
    - Starts with '(' (typical Newick), or
    - Starts with '#NEXUS' (NEXUS format)

    Otherwise, the string is treated as a file path.

    Parameters
    ----------
    source : str, Path, or file-like
        The source to open.
    mode : str, default 'r'
        File mode for opening (e.g., 'r', 'w', 'rb').

    Returns
    -------
    tuple[IO, bool]
        (file_handle, should_close) — if should_close is True, the caller
        must close the handle when done.

    Examples
    --------
    >>> fh, close = _open_source("tree.newick")
    >>> try:
    ...     content = fh.read()
    ... finally:
    ...     if close:
    ...         fh.close()
    """
    if hasattr(source, "read"):
        return source, False

    s = str(source)
    # Heuristic: paths don't contain newlines; tree content often does
    if "\n" in s or s.strip().startswith("(") or s.strip().upper().startswith("#NEXUS"):
        return io.StringIO(s), True

    return open(s, mode), True


def _write_dest(content: str, dest: Optional[PathLike] = None) -> Optional[str]:
    """
    Write content to a destination or return it as a string.

    Parameters
    ----------
    content : str
        The content to write.
    dest : str, Path, file-like, or None
        If None, returns the content as a string.
        If a path or file-like object, writes the content and returns None.

    Returns
    -------
    str or None
        The content if dest is None, otherwise None.

    Examples
    --------
    >>> result = _write_dest("content", None)
    >>> result
    'content'
    >>> _write_dest("content", "output.txt")  # writes to file, returns None
    """
    if dest is None:
        return content

    if hasattr(dest, "write"):
        dest.write(content)
        return None

    Path(dest).write_text(content, encoding="utf-8")
    return None
