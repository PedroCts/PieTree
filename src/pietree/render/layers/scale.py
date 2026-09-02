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


# ---------------------------------------------------------------------------
# Circular scale bar
# ---------------------------------------------------------------------------

def _auto_scale_length_circular(context) -> float:
    """
    Auto-compute a nice scale-bar length (in data units) for circular mode.

    Uses context.circular_scale (px per data-radius-unit) and targets
    ~15 % of the tip radius.
    """
    scale = context.circular_scale  # px / data-unit
    if not scale:
        return 0.1
    tip_r_px = context.tip_edge     # pixel radius to tip circle
    raw = (tip_r_px * 0.15) / scale
    return _nice_round(raw)


def _render_circular_scale(context):
    """
    Draw a curved (arc) scale bar for circular trees.

    The bar is an arc at a radius just inside the tip circle, centred at
    the bottom of the canvas (270° = 6 o'clock).  Two short radial tick
    lines cap each end, and the length label sits below the arc midpoint.

    Visual anatomy
    --------------

              |   arc   |       ← arc at r = bar_r, spanning ±half_angle
              ↑         ↑       ← radial tick lines (length = tick_h)
           (t1)       (t2)
                label             ← text below arc midpoint
    """
    spec  = context.spec
    svg   = context.svg
    scale = context.circular_scale   # px per data-radius-unit
    cx    = context.circular_cx
    cy    = context.circular_cy

    if not spec.scale_bar or cx is None or scale is None:
        return

    length = spec.scale_bar.get("length") or _auto_scale_length_circular(context)

    # Arc radius: sit just inside the tip circle with a small gap
    tip_r = context.tip_edge
    gap   = 14.0          # px gap between tip circle and scale arc
    bar_r = tip_r - gap
    bar_r = max(bar_r, 10.0)

    # How many degrees does `length` data-units subtend at radius bar_r?
    arc_px     = length * scale          # chord equivalent in radial px
    half_angle = math.degrees(math.asin(min(arc_px / (2 * bar_r), 1.0)))
    # → full sweep = 2 * half_angle degrees

    # Centre the arc at 270° (bottom, 6 o'clock)
    mid_angle  = 270.0
    t1_deg     = mid_angle - half_angle
    t2_deg     = mid_angle + half_angle
    t1         = math.radians(t1_deg)
    t2         = math.radians(t2_deg)

    tick_h    = 7.0   # radial tick line half-length (px) on each side of arc
    font_size = 11
    stroke    = "black"
    sw        = "2"

    # Arc start / end points
    ax1 = cx + bar_r * math.cos(t1)
    ay1 = cy + bar_r * math.sin(t1)
    ax2 = cx + bar_r * math.cos(t2)
    ay2 = cy + bar_r * math.sin(t2)

    # Arc path (always small arc, sweep clockwise)
    arc_d = (
        f"M {ax1:.2f} {ay1:.2f} "
        f"A {bar_r:.2f} {bar_r:.2f} 0 0 1 {ax2:.2f} {ay2:.2f}"
    )
    SubElement(svg, "path", {
        "d": arc_d,
        "stroke": stroke,
        "stroke-width": sw,
        "fill": "none",
    })

    # Radial tick lines at each end
    for t in (t1, t2):
        cos_t = math.cos(t)
        sin_t = math.sin(t)
        SubElement(svg, "line", {
            "x1": f"{cx + (bar_r - tick_h) * cos_t:.2f}",
            "y1": f"{cy + (bar_r - tick_h) * sin_t:.2f}",
            "x2": f"{cx + (bar_r + tick_h) * cos_t:.2f}",
            "y2": f"{cy + (bar_r + tick_h) * sin_t:.2f}",
            "stroke": stroke,
            "stroke-width": sw,
        })

    # Label below arc midpoint
    mid_rad = math.radians(mid_angle)
    lx = cx + (bar_r + tick_h + font_size) * math.cos(mid_rad)
    ly = cy + (bar_r + tick_h + font_size) * math.sin(mid_rad)

    SubElement(svg, "text", {
        "x": f"{lx:.2f}",
        "y": f"{ly:.2f}",
        "text-anchor": "middle",
        "font-size": str(font_size),
        "fill": stroke,
    }).text = str(length)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_scale(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos

    if not spec.scale_bar:
        return

    if spec.mode == "circular":
        _render_circular_scale(context)
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
