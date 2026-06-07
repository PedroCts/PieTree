"""
palette.py
----------
Color palette utilities for automatic highlight color assignment.

Provides a small set of named palettes and a function to assign colors
from them given an ordered list of labels.
"""

from __future__ import annotations

from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Built-in palettes (hex strings)
# ---------------------------------------------------------------------------

_PALETTES: Dict[str, List[str]] = {

    # Matplotlib tab10
    "tab10": [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ],

    # Matplotlib tab20 (20 colors, good for many groups)
    "tab20": [
        "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c",
        "#98df8a", "#d62728", "#ff9896", "#9467bd", "#c5b0d5",
        "#8c564b", "#c49c94", "#e377c2", "#f7b6d2", "#7f7f7f",
        "#c7c7c7", "#bcbd22", "#dbdb8d", "#17becf", "#9edae5",
    ],

    # Colorbrewer Set1 (9 bold, good for small N)
    "set1": [
        "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
        "#a65628", "#f781bf", "#999999", "#ffff33",
    ],

    # Colorbrewer Pastel1 (soft fills, good for overlapping highlights)
    "pastel1": [
        "#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6",
        "#ffffcc", "#e5d8bd", "#fddaec", "#f2f2f2",
    ],

    # Colorbrewer Set2 (8 medium-saturation)
    "set2": [
        "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
        "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3",
    ],
    
    "set3": [
        "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
        "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
        "#ccebc5", "#ffed6f",
    ],

    # Single grey — useful as a no-color fallback
    "grey": ["#cccccc"],
}


def get_palette(name: str) -> List[str]:
    """
    Return the color list for the named palette.

    Raises
    ------
    ValueError
        If the palette name is not recognised.
    """
    key = name.lower()
    if key not in _PALETTES:
        available = ", ".join(sorted(_PALETTES))
        raise ValueError(
            f"Unknown palette {name!r}. Available: {available}"
        )
    return list(_PALETTES[key])


def assign_colors(
    labels: List[str],
    palette: str = "tab20",
    overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Assign one color per label from a named palette, cycling if needed.

    Parameters
    ----------
    labels : list of str
        Ordered list of unique labels to color.
    palette : str
        Name of the palette to use (default ``'tab20'``).
    overrides : dict, optional
        ``{label: color}`` mapping that takes precedence over the palette.

    Returns
    -------
    dict
        ``{label: hex_color}``
    """
    colors = get_palette(palette)
    overrides = overrides or {}
    result: Dict[str, str] = {}

    color_idx = 0
    for label in labels:
        if label in overrides:
            result[label] = overrides[label]
        else:
            result[label] = colors[color_idx % len(colors)]
            color_idx += 1

    return result