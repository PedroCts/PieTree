"""
pietree/io/io.py
----------------
IO engine for PieTree: parsing, serialisation, rasterisation, and
dataframe export.

Parsing  (format → PieTree)
----------------------------
_biopython_to_pietree(bio_tree)   internal converter from Bio.Phylo.BaseTree
parse_newick(source)              Newick string / path / file-like
parse_nexus(source)               NEXUS file / string
parse_phyloxml(source)            PhyloXML file / string

Serialisation  (PieTree → format)
----------------------------------
to_newick(tree, dest)             returns str or writes to file/path
to_nexus(tree, dest)              returns str or writes to file/path
to_phyloxml(tree, dest)           returns str or writes to file/path

Rasterisation  (RenderSpec → file)
------------------------------------
savefig(tree, path, **kwargs)     SVG / PNG / JPEG / PDF / TIFF / PSD
                                  format inferred from extension
_render_layer(spec, layer_name)   render a single named layer to SVG string
_svg_to_pil(svg_str, dpi)         cairosvg → Pillow Image
_save_layered_psd(spec, path, dpi) full layered PSD via psd-tools

Dataframe
---------
to_dataframe(tree)                one row per node
"""

from __future__ import annotations

import io
import os
import re as _re
import textwrap
from pathlib import Path
from typing import IO, Optional, Union

# ---------------------------------------------------------------------------
# Optional heavy deps — imported lazily so the module loads even when absent
# ---------------------------------------------------------------------------

def _require(pkg: str, install: str | None = None):
    import importlib
    try:
        return importlib.import_module(pkg)
    except ImportError:
        hint = f"pip install {install or pkg}"
        raise ImportError(
            f"'{pkg}' is required for this operation. Install with: {hint}"
        ) from None


PathLike = Union[str, Path, IO]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_source(source: PathLike, mode: str = "r") -> tuple[IO, bool]:
    """
    Accept a string-that-is-a-path, a Path object, or a file-like object.
    Returns (file_handle, should_close).

    A string is treated as a path only when it looks like one (has a newline →
    raw content; starts with a tree char → raw content; otherwise → path).
    """
    if hasattr(source, "read"):
        return source, False
    s = str(source)
    # Heuristic: paths don't contain newlines; Newick/NEXUS content often does
    if "\n" in s or s.strip().startswith("(") or s.strip().upper().startswith("#NEXUS"):
        return io.StringIO(s), True
    return open(s, mode), True


def _write_dest(content: str, dest: PathLike | None) -> str | None:
    """Write *content* to dest (path, file-like) or return it as a string."""
    if dest is None:
        return content
    if hasattr(dest, "write"):
        dest.write(content)
        return None
    Path(dest).write_text(content, encoding="utf-8")
    return None


# ---------------------------------------------------------------------------
# BioPython ↔ PieTree conversion
# ---------------------------------------------------------------------------

def _biopython_to_pietree(bio_tree, support_format: str | None = None):
    """
    Convert a Bio.Phylo.BaseTree.Tree to a PieTree instance.

    We do a single DFS pass, creating PieNode + PieBranch objects and
    wiring them up exactly as the rest of the engine expects.
    """
    # These imports live inside the function so this module can be imported
    # before the full pietree package is assembled.
    from pietree.tree.pienode import PieNode
    from pietree.tree.piebranch import PieBranch
    from pietree.tree.pietree import PieTree

    node_map: dict = {}   # id(bio_clade) → PieNode
    
    field_names = _parse_support_format(support_format) if support_format else None

    def _convert(bio_clade, parent_pie: PieNode | None, parent_id: str | None):
        name = bio_clade.name or None
        confidence = getattr(bio_clade, "confidence", None)
        branch_length = getattr(bio_clade, "branch_length", None)
        
        support = None
        if confidence is not None:
            raw = str(confidence)
            if field_names:
                support = _parse_support_string(raw, field_names)
            else:
                try:
                    support = {"support": float(raw)}
                except ValueError:
                    pass
        elif name is not None and bio_clade.clades:
            # internal node — name may be a support string
            if field_names:
                parsed = _parse_support_string(name, field_names)
            else:
                m = _re.match(r'^(\d+(?:\.\d+)?)$', name.strip())
                parsed = {"support": float(m.group(1))} if m else None
            if parsed:
                support = parsed
                name = None
        
        pie = PieNode(name=name)
        node_map[id(bio_clade)] = pie
        
        if parent_pie is not None:
            branch = PieBranch(parent_id=parent_id, child_id=pie.id,
                               length=branch_length, support=support)
            parent_pie._children.append((pie, branch))
            pie._parent = parent_pie

        for child_clade in bio_clade.clades:
            _convert(child_clade, pie, pie.id)

        return pie

    root = _convert(bio_tree.root, None, None)
    tree = PieTree(root=root)

    # wire back-references
    for node in tree.traverse():
        node._tree = tree

    return tree


def _pietree_to_biopython(tree):
    """
    Convert a PieTree to a Bio.Phylo.BaseTree.Tree (for serialisation).
    """
    from Bio.Phylo import BaseTree

    def _convert(pie_node):
        clades = []
        for child, branch in pie_node._children:
            child_clade = _convert(child)
            child_clade.branch_length = branch.length if branch else None
            child_clade.confidence    = branch.support if branch else None
            clades.append(child_clade)
        return BaseTree.Clade(
            name=pie_node.name,
            clades=clades,
        )

    bio_root = _convert(tree.root)
    return BaseTree.Tree(root=bio_root)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_bio(source: PathLike, fmt: str, support_format=None):
    """Parse source with BioPython Phylo and return the first tree."""
    from Bio import Phylo
    fh, should_close = _open_source(source)
    try:
        trees = list(Phylo.parse(fh, fmt))
    finally:
        if should_close:
            fh.close()
    if not trees:
        raise ValueError(f"No trees found in {fmt} source.")
    if len(trees) > 1:
        import warnings
        warnings.warn(
            f"{len(trees)} trees found; loading the first one. "
            "Use parse_multi() to load all.",
            stacklevel=3,
        )
    return _biopython_to_pietree(trees[0], support_format=support_format)


def _parse_bio_multi(source: PathLike, fmt: str, support_format=None) -> list:
    """Parse all trees from source."""
    from Bio import Phylo
    fh, should_close = _open_source(source)
    try:
        trees = list(Phylo.parse(fh, fmt))
    finally:
        if should_close:
            fh.close()
    return [_biopython_to_pietree(t, support_format=support_format) for t in trees]

def _parse_support_format(fmt: str) -> list[str]:
    """Extract field names from a format like '{bootstrap}/{alrt}'."""
    return _re.findall(r'\{(\w+)\}', fmt)

def _parse_support_string(raw: str, field_names: list[str]) -> dict | None:
    """
    Split raw support string by non-numeric separators and map to field_names.
    Returns None if parsing fails or token count doesn't match.
    """
    tokens = _re.split(r'[^0-9.]+', raw.strip())
    tokens = [t for t in tokens if t]
    if len(tokens) != len(field_names):
        return None
    try:
        return {k: float(v) for k, v in zip(field_names, tokens)}
    except ValueError:
        return None

def parse_newick(source: PathLike, support_format=None):
    """Parse a Newick string, path, or file-like object → PieTree."""
    return _parse_bio(source, "newick", support_format=support_format)

def parse_nexus(source: PathLike):
    """Parse a NEXUS string, path, or file-like object → PieTree."""
    return _parse_bio(source, "nexus")

def parse_phyloxml(source: PathLike):
    """Parse a PhyloXML string, path, or file-like object → PieTree."""
    return _parse_bio(source, "phyloxml")

def parse_newick_multi(source: PathLike) -> list:
    return _parse_bio_multi(source, "newick")

def parse_nexus_multi(source: PathLike) -> list:
    return _parse_bio_multi(source, "nexus")


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _write_bio(tree, dest: PathLike | None, fmt: str) -> str | None:
    bio_tree = _pietree_to_biopython(tree)
    from Bio import Phylo
    buf = io.StringIO()
    Phylo.write(bio_tree, buf, fmt)
    return _write_dest(buf.getvalue(), dest)


def to_newick(tree, dest: PathLike | None = None) -> str | None:
    """
    Serialise *tree* to Newick format.

    Parameters
    ----------
    dest : path, file-like, or None
        If None, returns the Newick string.  Otherwise writes to the target.
    """
    return _write_bio(tree, dest, "newick")


def to_nexus(tree, dest: PathLike | None = None) -> str | None:
    """Serialise *tree* to NEXUS format."""
    return _write_bio(tree, dest, "nexus")


def to_phyloxml(tree, dest: PathLike | None = None) -> str | None:
    """Serialise *tree* to PhyloXML format."""
    return _write_bio(tree, dest, "phyloxml")


# ---------------------------------------------------------------------------
# Rasterisation helpers
# ---------------------------------------------------------------------------

def _svg_to_pil(svg_str: str, dpi: int = 150):
    """Convert an SVG string to a Pillow Image via cairosvg."""
    cairosvg = _require("cairosvg")
    from PIL import Image
    png_bytes = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), dpi=dpi)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


# Layer names and how to activate each one.
# Each entry is (layer_name, flag_attr_on_options_or_None, render_fn)
_LAYER_DEFS = [
    "background",
    "highlights",
    "branches",
    "nodes",
    "labels",
    "panels",
    "scale",
]


def _render_single_layer(spec, layer_name: str) -> str:
    """
    Render one named layer in isolation and return the SVG string.

    We clone the spec, disable all other layers, run the full render
    pipeline (so canvas / context are built correctly) but only the
    target render_* function contributes elements.
    """
    import copy
    from xml.etree.ElementTree import Element, tostring
    from xml.dom import minidom

    from pietree.style import StyleResolver, StyleSheet
    from pietree.render.canvas import build_canvas
    from pietree.render.context import RenderContext
    from pietree.render.layers.background  import render_background
    from pietree.render.layers.highlights  import render_highlights
    from pietree.render.layers.branches    import render_branches
    from pietree.render.layers.nodes       import render_nodes
    from pietree.render.layers.labels      import render_labels
    from pietree.render.layers.panels      import render_panels
    from pietree.render.layers.scale       import render_scale

    _renderers = {
        "background": render_background,
        "highlights": render_highlights,
        "branches":   render_branches,
        "nodes":      render_nodes,
        "labels":     render_labels,
        "panels":     render_panels,
        "scale":      render_scale,
    }

    resolver = StyleResolver(StyleSheet([]))
    canvas   = build_canvas(spec)
    sources  = {e.source for e in spec.edges}

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
    )

    _renderers[layer_name](ctx)

    rough = tostring(ctx.svg, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")


def _save_layered_psd(spec, path: str, dpi: int = 150):
    """
    Render each layer independently and combine into a layered PSD file.
    Requires psd-tools and cairosvg.
    """
    _require("psd_tools", "psd-tools")
    from psd_tools import PSDImage
    from psd_tools.constants import ColorMode
    from PIL import Image

    layer_images: list[tuple[str, Image.Image]] = []

    for layer_name in _LAYER_DEFS:
        try:
            svg_str = _render_single_layer(spec, layer_name)
            img = _svg_to_pil(svg_str, dpi=dpi)
            layer_images.append((layer_name, img))
        except Exception:
            # A layer may be empty (no highlights, no scale bar etc.) — skip
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


# ---------------------------------------------------------------------------
# savefig — the public rasterisation entry point
# ---------------------------------------------------------------------------

_FORMAT_MAP = {
    ".svg":  "svg",
    ".png":  "png",
    ".jpg":  "jpeg",
    ".jpeg": "jpeg",
    ".pdf":  "pdf",
    ".tiff": "tiff",
    ".tif":  "tiff",
    ".psd":  "psd",
}


def savefig(
    tree,
    path: str,
    *,
    size: tuple[int, int] | None = None,  # canvas size in pixels (for raster formats)
    dpi: int = 150,
    quality: int = 92,          # JPEG quality
    tiff_compression: str = "lzw",
    layered_psd: bool = True,   # if False, flat PSD (faster)
    spec=None,                  # pre-built RenderSpec; if None, tree.render_spec() is called
    **render_kwargs,
):
    """
    Save the tree figure to *path*.

    Format is inferred from the file extension.  Supported:
      .svg .png .jpg/.jpeg .pdf .tiff/.tif .psd

    Parameters
    ----------
    dpi         : int   — rasterisation resolution (PNG / JPEG / TIFF / PSD).
    quality     : int   — JPEG quality (1-95).
    tiff_compression : str — LZW, JPEG, raw, etc.
    layered_psd : bool  — if True, each rendering layer becomes a PSD layer.
    spec        : RenderSpec — pass a pre-built spec to skip tree.render_spec().
    **render_kwargs
        Forwarded to tree.render_spec() when spec is None.
    """
    ext = Path(path).suffix.lower()
    fmt = _FORMAT_MAP.get(ext)
    if fmt is None:
        raise ValueError(
            f"Unknown extension '{ext}'. Supported: {sorted(_FORMAT_MAP)}"
        )

    # Build or reuse the render spec
    if spec is None:
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
    svg_str  = render_svg(spec)
    pil_img  = _svg_to_pil(svg_str, dpi=dpi)

    if fmt == "png":
        pil_img.save(path, format="PNG")

    elif fmt == "jpeg":
        pil_img.convert("RGB").save(path, format="JPEG", quality=quality)

    elif fmt == "tiff":
        pil_img.save(path, format="TIFF", compression=tiff_compression)

    elif fmt == "psd":   # flat PSD fallback
        _require("psd_tools", "psd-tools")
        from psd_tools import PSDImage
        psd = PSDImage.frompil(pil_img)
        psd.save(path)


# ---------------------------------------------------------------------------
# to_svg  (convenience — returns SVG string or writes to dest)
# ---------------------------------------------------------------------------

def to_svg(tree, dest: PathLike | None = None, *, spec=None, **render_kwargs) -> str | None:
    """
    Render the tree to SVG.

    Returns the SVG string when dest is None, otherwise writes to path/file.
    """
    from pietree.render.svg import render_svg
    if spec is None:
        spec = tree.render_spec(**render_kwargs)
    svg_str = render_svg(spec)
    return _write_dest(svg_str, dest)


# ---------------------------------------------------------------------------
# to_dataframe
# ---------------------------------------------------------------------------

def to_dataframe(tree, include_topology: bool = True, infer_taxonomy: bool = True, **kwargs):
    """
    Return a pandas DataFrame with one row per node.

    Columns
    -------
    id          node UUID
    name        node name (or None)
    is_tip      bool
    is_root     bool
    depth       number of edges from root
    parent_id   UUID of parent node (None for root)
    branch_length   float or None
    support         float or None (from parent branch)
    n_children  int
    n_descendants int
    n_desc_tips   int
    label       tip/node label text (or None)
    + all top-level metadata keys (flattened one level)
    """
    pd = _require("pandas")

    rows = []
    # Collect all metadata keys present anywhere
    all_meta_keys: set = set()
    for node in tree.traverse():
        if hasattr(node, "metadata") and node.metadata:
            all_meta_keys.update(node.metadata.data.keys())
            
    # Pre-compute inferred taxonomy for all nodes
    inferred_taxonomy: dict = {}
    if infer_taxonomy:
        from pietree.metadata.inference import infer_tree
        inferred_taxonomy = infer_tree(tree, "taxonomy")
        all_meta_keys.add("inferred_taxonomy")

    def _depth(node):
        d = 0
        cur = node
        while cur._parent is not None:
            cur = cur._parent
            d += 1
        return d

    for node in tree.traverse():
        # parent branch info
        parent_branch = None
        if node._parent is not None:
            for child, branch in node._parent._children:
                if child is node:
                    parent_branch = branch
                    break

        meta = dict(node.metadata.data) if hasattr(node, "metadata") and node.metadata else {}
        if infer_taxonomy and "taxonomy" not in meta:
            inferred = inferred_taxonomy.get(node.id)
            if inferred is not None:
                meta["inferred_taxonomy"] = inferred
                
        descendants = list(node.descendants) if hasattr(node, "descendants") else []
        desc_tips   = [n for n in descendants if n.is_tip]

        row = {
            "id":            node.id,
            "name":          node.name,
            "is_tip":        node.is_tip,
            "is_root":       node.is_root,
            "depth":         _depth(node),
            "parent_id":     node._parent.id if node._parent else None,
            "branch_length": parent_branch.length  if parent_branch else None,
            "support":       parent_branch.support if parent_branch else None,
            "n_children":    len(node._children),
            "n_descendants": len(descendants),
            "n_desc_tips":   len(desc_tips),
            "label":         node.label.text if hasattr(node, "label") and node.label else None,
        }
        # flatten one-level metadata
        for k in all_meta_keys:
            row[f"meta_{k}"] = meta.get(k)

        rows.append(row)

    return pd.DataFrame(rows)