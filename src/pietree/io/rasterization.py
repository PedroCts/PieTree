"""
rasterization.py
----------------
Image export functions for PieTree.

Handles conversion from SVG to raster formats (PNG, JPEG, PDF, TIFF) and
layered PSD files via cairosvg, Pillow, and psd-tools.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .utils import _require

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree
    from pietree.render.spec import RenderSpec


# Layer names for layered PSD export (in rendering order)
_LAYER_DEFS = [
    "background",
    "highlights",
    "branches",
    "nodes",
    "labels",
    "panels",
    "scale",
]


def _svg_to_pil(svg_str: str, dpi: int = 150):
    """
    Convert an SVG string to a Pillow Image via cairosvg.

    Parameters
    ----------
    svg_str : str
        SVG content as a string.
    dpi : int, default 150
        Rasterization resolution (dots per inch).

    Returns
    -------
    PIL.Image.Image
        Rasterized image in RGBA mode.

    Raises
    ------
    ImportError
        If cairosvg or Pillow is not installed.
    """
    cairosvg = _require("cairosvg")
    from PIL import Image

    png_bytes = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), dpi=dpi)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def _render_single_layer(spec: "RenderSpec", layer_name: str) -> str:
    """
    Render one named layer in isolation and return the SVG string.

    Clones the spec, disables all other layers, runs the full render
    pipeline so canvas/context are built correctly, but only the
    target render function contributes elements.

    Parameters
    ----------
    spec : RenderSpec
        The render specification.
    layer_name : str
        Layer to render ('background', 'highlights', 'branches', etc.).

    Returns
    -------
    str
        SVG string for this layer only.
    """
    from xml.etree.ElementTree import tostring
    from xml.dom import minidom

    from pietree.style import StyleResolver, StyleSheet
    from pietree.render.canvas import build_canvas
    from pietree.render.context import RenderContext
    from pietree.render.layers.background import render_background
    from pietree.render.layers.highlights import render_highlights
    from pietree.render.layers.branches import render_branches
    from pietree.render.layers.nodes import render_nodes
    from pietree.render.layers.labels import render_labels
    from pietree.render.layers.panels import render_panels
    from pietree.render.layers.scale import render_scale

    _renderers = {
        "background": render_background,
        "highlights": render_highlights,
        "branches": render_branches,
        "nodes": render_nodes,
        "labels": render_labels,
        "panels": render_panels,
        "scale": render_scale,
    }

    resolver = StyleResolver(StyleSheet([]))
    canvas = build_canvas(spec)
    sources = {e.source for e in spec.edges}

    ctx = RenderContext(
        spec=spec,
        svg=canvas["svg"],
        resolver=resolver,
        pos=canvas["pos"],
        canvas_width=canvas["canvas_width"],
        canvas_height=canvas["canvas_height"],
        padding_left=canvas["padding_left"],
        padding_right=canvas["padding_right"],
        padding_top=canvas["padding_top"],
        padding_bottom=canvas["padding_bottom"],
        sources=sources,
        registry=spec.registry,
        highlights=spec.highlights,
        tip_edge=canvas["tip_edge"],
        label_edge=canvas["label_edge"],
        circular_cx=canvas.get("_circular_cx"),
        circular_cy=canvas.get("_circular_cy"),
        circular_scale=canvas.get("_circular_scale"),
    )

    _renderers[layer_name](ctx)

    rough = tostring(ctx.svg, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")


def _save_layered_psd(spec: "RenderSpec", path: str, dpi: int = 150):
    """
    Render each layer independently and combine into a layered PSD file.

    Requires psd-tools and cairosvg.

    Parameters
    ----------
    spec : RenderSpec
        The render specification.
    path : str
        Output PSD file path.
    dpi : int, default 150
        Rasterization resolution.

    Raises
    ------
    ImportError
        If psd-tools, cairosvg, or Pillow is not installed.
    RuntimeError
        If no layers could be rendered.
    """
    _require("psd_tools", "psd-tools")
    from psd_tools import PSDImage
    from PIL import Image

    layer_images: list[tuple[str, Image.Image]] = []

    for layer_name in _LAYER_DEFS:
        try:
            svg_str = _render_single_layer(spec, layer_name)
            img = _svg_to_pil(svg_str, dpi=dpi)
            layer_images.append((layer_name, img))
        except Exception:
            # A layer may be empty (no highlights, no scale bar, etc.) — skip
            continue

    if not layer_images:
        raise RuntimeError("No layers could be rendered.")

    # Use the first layer to get dimensions
    w, h = layer_images[0][1].size
    psd = PSDImage.new("RGBA", (w, h))

    for name, img in layer_images:
        # Ensure same size (floating-point diffs can cause 1px difference)
        if img.size != (w, h):
            img = img.resize((w, h), Image.LANCZOS)
        layer = PSDImage.frompil(img)
        layer.name = name
        psd.append(layer)

    psd.save(path)


# File extension to format mapping
_FORMAT_MAP = {
    ".svg": "svg",
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".pdf": "pdf",
    ".tiff": "tiff",
    ".tif": "tiff",
    ".psd": "psd",
}


def savefig(
    tree: "PieTree",
    path: str,
    *,
    size: Optional[tuple[int, int]] = None,  # canvas size in pixels (for raster)
    dpi: int = 150,
    quality: int = 92,  # JPEG quality
    tiff_compression: str = "lzw",
    layered_psd: bool = True,  # if False, flat PSD (faster)
    spec: Optional["RenderSpec"] = None,  # pre-built RenderSpec
    **render_kwargs,
):
    """
    Save the tree figure to a file.

    Format is inferred from the file extension. Supported formats:
    .svg, .png, .jpg/.jpeg, .pdf, .tiff/.tif, .psd

    Parameters
    ----------
    tree : PieTree
        The tree to render and save.
    path : str
        Output file path. Format is inferred from extension.
    size : tuple[int, int], optional
        Canvas size in pixels (width, height) for raster formats.
        If None, uses default from tree.render_options.
    dpi : int, default 150
        Rasterization resolution (PNG, JPEG, TIFF, PSD).
    quality : int, default 92
        JPEG quality (1-95).
    tiff_compression : str, default 'lzw'
        TIFF compression method ('lzw', 'jpeg', 'raw', etc.).
    layered_psd : bool, default True
        If True, each rendering layer becomes a PSD layer.
        If False, creates a flat PSD (faster).
    spec : RenderSpec, optional
        Pre-built render specification. If None, tree.to_render_spec() is called.
    **render_kwargs
        Additional arguments forwarded to tree.to_render_spec() when spec is None
        (e.g., mode, orientation, canvas_size).

    Raises
    ------
    ValueError
        If the file extension is not supported.
    ImportError
        If required dependencies for the format are not installed.

    Examples
    --------
    >>> tree.savefig("tree.svg")
    >>> tree.savefig("tree.png", dpi=300)
    >>> tree.savefig("tree.jpg", quality=95)
    >>> tree.savefig("tree.pdf")
    >>> tree.savefig("tree.psd", layered_psd=True)
    >>> tree.savefig("tree.png", mode="cladogram", size=(1200, 800))

    Notes
    -----
    - SVG: No additional dependencies
    - PNG, JPEG, TIFF, PDF: Requires cairosvg and Pillow
    - Layered PSD: Requires psd-tools, cairosvg, and Pillow
    """
    ext = Path(path).suffix.lower()
    fmt = _FORMAT_MAP.get(ext)
    if fmt is None:
        raise ValueError(
            f"Unknown extension '{ext}'. Supported: {sorted(_FORMAT_MAP)}"
        )

    # Build or reuse the render spec
    if spec is None:
        # canvas_size comes from `size`; remove it from render_kwargs to avoid duplicate
        render_kwargs.pop("canvas_size", None)
        spec = tree.to_render_spec(canvas_size=size, **render_kwargs)

    # --- SVG -----------------------------------------------------------------
    if fmt == "svg":
        from pietree.render.svg import render_svg
        svg_str = render_svg(spec)
        Path(path).write_text(svg_str, encoding="utf-8")
        return

    # --- PDF -----------------------------------------------------------------
    if fmt == "pdf":
        cairosvg = _require("cairosvg")
        from pietree.render.svg import render_svg
        svg_str = render_svg(spec)
        cairosvg.svg2pdf(bytestring=svg_str.encode(), write_to=path)
        return

    # --- PSD (layered) -------------------------------------------------------
    if fmt == "psd" and layered_psd:
        _save_layered_psd(spec, path, dpi=dpi)
        return

    # --- PNG / JPEG / TIFF / flat PSD ----------------------------------------
    from pietree.render.svg import render_svg
    svg_str = render_svg(spec)
    pil_img = _svg_to_pil(svg_str, dpi=dpi)

    if fmt == "png":
        pil_img.save(path, format="PNG")

    elif fmt == "jpeg":
        pil_img.convert("RGB").save(path, format="JPEG", quality=quality)

    elif fmt == "tiff":
        pil_img.save(path, format="TIFF", compression=tiff_compression)

    elif fmt == "psd":  # flat PSD fallback
        _require("psd_tools", "psd-tools")
        from psd_tools import PSDImage
        psd = PSDImage.frompil(pil_img)
        psd.save(path)
