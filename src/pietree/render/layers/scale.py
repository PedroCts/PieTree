from xml.etree.ElementTree import SubElement
import math


def _nice_round(value: float) -> float:
    """Round to 1 significant figure (1, 2, 5 × 10^n)."""
    if value <= 0:
        return 1.0
    exp = math.floor(math.log10(value))
    frac = value / (10 ** exp)
    if frac < 1.5:
        nice = 1
    elif frac < 3.5:
        nice = 2
    elif frac < 7.5:
        nice = 5
    else:
        nice = 10
    return nice * (10 ** exp)


def _px_per_unit(spec, pos) -> float | None:
    """Compute median px-per-branch-length-unit across all edges that have a length."""
    ratios = []
    for e in spec.edges:
        if not e.length:
            continue
        x1, y1 = pos[e.source]
        x2, y2 = pos[e.target]
        # horizontal tree: only horizontal segment carries length info
        if spec.orientation == "horizontal":
            dist = abs(x2 - x1)
        else:
            dist = abs(y2 - y1)
        if dist > 0:
            ratios.append(dist / e.length)
    if not ratios:
        return None
    ratios.sort()
    return ratios[len(ratios) // 2]  # median


def auto_scale_length(spec, pos, target_fraction: float = 0.15) -> float:
    """
    Compute a nice scale-bar length in data units.

    Targets `target_fraction` of the tree's draw width/height in pixels.
    Falls back to 0.1 if branch lengths are absent.
    """
    ppu = _px_per_unit(spec, pos)
    if ppu is None or ppu == 0:
        return 0.1

    # approximate draw extent from node positions
    if spec.orientation == "horizontal":
        all_x = [pos[n.id][0] for n in spec.nodes]
        draw_extent = max(all_x) - min(all_x)
    else:
        all_y = [pos[n.id][1] for n in spec.nodes]
        draw_extent = max(all_y) - min(all_y)

    raw = (draw_extent * target_fraction) / ppu
    return _nice_round(raw)


def compute_scale_bar(spec, pos, scale_length: float) -> float:
    """Convert a data-unit scale length to pixels."""
    ppu = _px_per_unit(spec, pos)
    if ppu:
        return ppu * scale_length
    return 50  # fallback


def render_scale(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos

    if not spec.scale_bar:
        return

    position = spec.scale_bar.get("position", "bottom_left")
    padding  = spec.scale_bar.get("padding", 20)

    # Auto-compute length if not explicitly set
    length = spec.scale_bar.get("length") or auto_scale_length(spec, pos)
    scale_px = compute_scale_bar(spec, pos, length)

    width  = context.canvas_width
    height = context.canvas_height

    if position == "bottom_left":
        x0 = padding
        y0 = height - padding
    elif position == "bottom_right":
        x0 = width - padding - scale_px
        y0 = height - padding
    else:  # bottom_center
        x0 = (width - scale_px) / 2
        y0 = height - padding

    x1 = x0 + scale_px

    SubElement(svg, "line", {
        "x1": str(x0), "y1": str(y0),
        "x2": str(x1), "y2": str(y0),
        "stroke": "black", "stroke-width": "2"
    })

    SubElement(svg, "text", {
        "x": str((x0 + x1) / 2),
        "y": str(y0 + 15),
        "text-anchor": "middle",
        "font-size": "12",
        "fill": "black"
    }).text = str(length)