"""
base.py
-------
Abstract base classes for rendering operations.

Defines interfaces for layout engines and layer renderers to enable
plugin-style extensibility for new layout algorithms and rendering layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    from pietree.render.options import RenderOptions
    from pietree.render.spec import RenderSpec
    from pietree.render.context import RenderContext


class LayoutEngine(ABC):
    """
    Base class for tree layout algorithms.

    A layout engine computes the 2D positions of all nodes and edges in
    a tree for rendering. Different layout engines implement different
    visualization strategies (phylogram, cladogram, circular, etc.).

    Examples
    --------
    >>> class CircularLayout(LayoutEngine):
    ...     @property
    ...     def layout_name(self) -> str:
    ...         return "circular"
    ...
    ...     def compute_layout(self, tree: PieTree, options: RenderOptions) -> RenderSpec:
    ...         # Compute circular layout positions
    ...         return spec
    """

    @abstractmethod
    def compute_layout(
        self, tree: "PieTree", options: "RenderOptions"
    ) -> "RenderSpec":
        """
        Compute node and edge positions for rendering.

        Parameters
        ----------
        tree : PieTree
            The phylogenetic tree to layout.
        options : RenderOptions
            Rendering options (orientation, spacing, etc.).

        Returns
        -------
        RenderSpec
            A specification containing node positions, edge paths, and
            rendering metadata.
        """
        pass

    @property
    @abstractmethod
    def layout_name(self) -> str:
        """
        Return the layout identifier.

        Returns
        -------
        str
            Layout name (e.g., 'phylogram', 'cladogram', 'circular').
        """
        pass


class LayerRenderer(ABC):
    """
    Base class for render layer implementations.

    A layer renderer is responsible for rendering one aspect of a tree
    visualization (branches, nodes, labels, highlights, etc.) as SVG.
    Layers are composited in a specific order to build the final image.

    The rendering pipeline calls each layer's `render()` method with a
    RenderContext containing all necessary data (positions, styles, options).

    Examples
    --------
    >>> class CustomAnnotationLayer(LayerRenderer):
    ...     @property
    ...     def layer_name(self) -> str:
    ...         return "annotations"
    ...
    ...     def render(self, context: RenderContext) -> str:
    ...         # Generate SVG for custom annotations
    ...         return svg_string
    """

    @abstractmethod
    def render(self, context: "RenderContext") -> str:
        """
        Render this layer as SVG.

        Parameters
        ----------
        context : RenderContext
            The rendering context containing positions, styles, options,
            and registered visual elements.

        Returns
        -------
        str
            SVG string for this layer's content.
        """
        pass

    @property
    @abstractmethod
    def layer_name(self) -> str:
        """
        Return the layer identifier.

        Returns
        -------
        str
            Layer name (e.g., 'branches', 'nodes', 'labels', 'highlights').
        """
        pass

    @property
    def z_order(self) -> int:
        """
        Return the rendering order (lower values render first, behind later layers).

        Override this to control layer stacking. Default order:
        - 0: background
        - 10: highlights
        - 20: branches
        - 30: nodes
        - 40: labels
        - 50: panels
        - 60: scale bar

        Returns
        -------
        int
            Z-order value for layer stacking.
        """
        return 50  # Default to middle priority


class ExportEngine(ABC):
    """
    Base class for tree export engines.

    An export engine handles conversion from SVG to other image formats
    (PNG, PDF, JPEG, etc.) or specialized formats (PSD with layers).

    Examples
    --------
    >>> class TIFFExporter(ExportEngine):
    ...     @property
    ...     def format_name(self) -> str:
    ...         return "tiff"
    ...
    ...     def export(self, svg_string: str, output_path: str, **options) -> None:
    ...         # Convert SVG to TIFF
    ...         pass
    """

    @abstractmethod
    def export(self, svg_string: str, output_path: str, **options) -> None:
        """
        Export SVG to this format.

        Parameters
        ----------
        svg_string : str
            The SVG content to export.
        output_path : str
            The destination file path.
        **options
            Format-specific export options (dpi, quality, etc.).

        Raises
        ------
        IOError
            If the file cannot be written.
        """
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """
        Return the export format identifier.

        Returns
        -------
        str
            Format name (e.g., 'png', 'pdf', 'jpeg', 'tiff', 'psd').
        """
        pass

    @property
    def file_extension(self) -> str:
        """
        Return the default file extension for this format.

        Returns
        -------
        str
            File extension including the dot (e.g., '.png', '.pdf').
        """
        return f".{self.format_name}"
