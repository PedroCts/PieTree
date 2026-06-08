"""
label_placement.py
------------------
Smart label placement for internal nodes and branch labels.

Given a set of branch segments (rectilinear lines) and already-placed
label bounding boxes, scores candidate positions for a new label and
returns the best one.

Public API
----------
branch_segments(edges, pos, orientation)
    → list of ((x1,y1),(x2,y2)) for every drawn line segment

find_best_slot(cx, cy, text_w, text_h, gap, candidates, segments, placed)
    → (px, py, text_anchor, box)   [single-label convenience wrapper]

find_best_slot_for_group(cx, cy, items, gap, candidates, segments, placed)
    → (slot_lx, anchor, item_positions, group_box)
       Place a stack of labels as a unit; items is [(w,h), ...]
"""

from __future__ import annotations
import math
from typing import List, Tuple

Segment = Tuple[Tuple[float, float], Tuple[float, float]]
Box = Tuple[float, float, float, float]   # x0, y0, x1, y1


# ---------------------------------------------------------------------------
# Segment helpers
# ---------------------------------------------------------------------------

def branch_segments(edges, pos: dict, orientation: str) -> List[Segment]:
    """
    Expand every RenderEdge into the two rectilinear line segments that are
    actually drawn.  Returns a flat list of ((x1,y1),(x2,y2)) tuples.
    """
    segs: List[Segment] = []
    for edge in edges:
        if edge.source not in pos or edge.target not in pos:
            continue
        px, py = pos[edge.source]
        cx, cy = pos[edge.target]
        if orientation == "horizontal":
            # vertical elbow then horizontal run
            segs.append(((px, py), (px, cy)))   # elbow
            segs.append(((px, cy), (cx, cy)))   # horizontal run
        else:
            # horizontal elbow then vertical run
            segs.append(((px, py), (cx, py)))   # elbow
            segs.append(((cx, py), (cx, cy)))   # vertical run
    return segs


def _dist_point_to_segment(px: float, py: float, seg: Segment) -> float:
    """Euclidean distance from point (px,py) to the nearest point on seg."""
    (ax, ay), (bx, by) = seg
    abx, aby = bx - ax, by - ay
    len2 = abx * abx + aby * aby
    if len2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / len2))
    return math.hypot(px - (ax + t * abx), py - (ay + t * aby))


def _segment_intersects_box(seg: Segment, box: Box, margin: float = 0) -> bool:
    """
    True if any part of *seg* falls within *box* (expanded by *margin*).
    Uses the separating-axis test for a line segment vs an AABB.
    """
    (ax, ay), (bx, by) = seg
    x0, y0, x1, y1 = (
        box[0] - margin, box[1] - margin,
        box[2] + margin, box[3] + margin,
    )
    # Trivial accept: both endpoints inside
    def inside(x, y):
        return x0 <= x <= x1 and y0 <= y <= y1
    if inside(ax, ay) or inside(bx, by):
        return True
    # Clip segment to box (Cohen-Sutherland simplified)
    # Check if segment crosses any of the four edges
    # Use parametric intersection with each box edge
    t_enter, t_exit = 0.0, 1.0
    dx, dy = bx - ax, by - ay
    for (p, q) in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t_enter = max(t_enter, t)
            else:
                t_exit = min(t_exit, t)
    return t_enter <= t_exit


def _boxes_overlap(a: Box, b: Box, margin: float = 2) -> bool:
    return (
        a[0] - margin < b[2] + margin and
        a[2] + margin > b[0] - margin and
        a[1] - margin < b[3] + margin and
        a[3] + margin > b[1] - margin
    )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score(
    box: Box,
    segments: List[Segment],
    placed: List[Box],
    seg_margin: float = 3.0,
    box_margin: float = 2.0,
) -> int:
    """
    Lower is better.
    +1 for every branch segment that intersects the label box.
    +4 for every already-placed label that overlaps.
    """
    score = 0
    for seg in segments:
        if _segment_intersects_box(seg, box, seg_margin):
            score += 1
    for placed_box in placed:
        if _boxes_overlap(box, placed_box, box_margin):
            score += 4
    return score


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

# 8-direction candidates: (offset_x_factor, offset_y_factor, text_anchor)
# The offsets are multiplied by (half_w + gap) or (half_h + gap).
_NODE_CANDIDATES = [
    # right side
    ( 1,  0, "start"),   # right-center    ← default for horizontal trees
    ( 1, -1, "start"),   # upper-right
    ( 1,  1, "start"),   # lower-right
    # left side
    (-1,  0, "end"),     # left-center
    (-1, -1, "end"),     # upper-left
    (-1,  1, "end"),     # lower-left
    # top / bottom (center anchor)
    ( 0, -1, "middle"),  # above
    ( 0,  1, "middle"),  # below
]

# For branch horizontal-segment midpoints: prefer above/below
_BRANCH_H_CANDIDATES = [
    ( 0, -1, "middle"),  # above
    ( 0,  1, "middle"),  # below
    ( 1, -1, "start"),
    (-1, -1, "end"),
    ( 1,  1, "start"),
    (-1,  1, "end"),
]

# For branch vertical-segment midpoints (elbow): prefer left/right
_BRANCH_V_CANDIDATES = [
    (-1,  0, "end"),     # left
    ( 1,  0, "start"),   # right
    (-1, -1, "end"),
    ( 1, -1, "start"),
]


def find_best_slot(
    cx: float,
    cy: float,
    text_w: float,
    text_h: float,
    gap: float,
    candidates: list,          # list of (xf, yf, anchor)
    segments: List[Segment],
    placed: List[Box],
    preferred_index: int = 0,
) -> Tuple[float, float, str, Box]:
    """
    Score every candidate position and return the best one as
    (px, py, text_anchor, bounding_box).

    gap is the distance from the node centre to the nearest edge of the
    label box (not to the label centre).  This keeps labels tighter.
    """
    result = find_best_slot_for_group(
        cx, cy, [(text_w, text_h)], gap, candidates, segments, placed
    )
    # Unpack single-item group result
    group_x0, slot_anchor, item_positions, group_box = result
    (item_cx, item_ly, item_box) = item_positions[0]
    half_h = text_h / 2
    py = item_ly + text_h * 0.35
    if slot_anchor == "start":
        px = group_x0
    elif slot_anchor == "end":
        px = group_x0 + text_w   # group_x0 is right-edge-minus-max_w; for single item right edge = group_x0 + tw
    else:
        px = item_cx   # middle: centred
    return px, py, slot_anchor, item_box


def find_best_slot_for_group(
    cx: float,
    cy: float,
    items: List[Tuple[float, float]],   # [(text_w, text_h), ...]  in priority order
    gap: float,
    candidates: list,
    segments: List[Segment],
    placed: List[Box],
    stack_gap: float = 1.0,
) -> Tuple[float, str, List[Tuple[float, float, Box]], Box]:
    """
    Find the best direction for a *group* of labels that all belong to the
    same node and should be stacked vertically in the chosen slot.

    The stack is centred on cy.  Items are laid out top-to-bottom in the
    order given.

    Returns
    -------
    (slot_lx, anchor, item_positions, group_box)
        slot_lx    : x position for the leftmost edge (start anchor) or
                     rightmost edge (end anchor) or centre (middle anchor)
        anchor     : SVG text-anchor for every item in the group
        item_positions : [(centre_x, centre_y, box), ...] — one per item
        group_box  : combined bounding box of all items
    """
    best_score = None
    best = None

    # advances = item heights as passed in (caller controls line-height via estimate_text_size)
    advances = [h for _, h in items]
    total_h = sum(advances) + stack_gap * (len(items) - 1)
    max_w = max(w for w, _ in items)

    for rank, (xf, yf, anchor) in enumerate(candidates):

        # Compute the group's shared x edge / centre:
        #   "start"  → group_x0 is the left edge  (gap right of node)
        #   "end"    → group_x1 is the right edge  (gap left of node)
        #   "middle" → group centre aligns with cx
        if xf > 0:        # right side — left-justify from group_x0
            group_x0 = cx + gap
        elif xf < 0:      # left side — right-justify to group_x1
            group_x0 = cx - gap - max_w
        else:             # centre column — items centred on cx
            group_x0 = cx - max_w / 2

        # y-centre of the stack
        if yf != 0:
            half_total_h = total_h / 2
            group_cy = cy + (gap + half_total_h) * yf
        else:
            group_cy = cy

        # Lay out items vertically, sharing the group left edge
        top = group_cy - total_h / 2
        item_positions = []
        y_cursor = top
        for (iw, ih), adv in zip(items, advances):
            # All items share the same left edge (group_x0) for start,
            # or right edge (group_x0 + max_w) for end, or centred for middle.
            if xf >= 0:   # start or middle: left edge is group_x0
                item_x0 = group_x0
            else:         # end: right-align each item to group right edge
                item_x0 = group_x0 + (max_w - iw)
            item_cx = item_x0 + iw / 2
            item_cy = y_cursor + adv / 2
            ibox: Box = (item_x0, item_cy - ih / 2,
                         item_x0 + iw, item_cy + ih / 2)
            item_positions.append((item_cx, item_cy, ibox))
            y_cursor += adv + stack_gap

        # Group envelope
        group_box: Box = (
            group_x0,
            min(b[1] for _, _, b in item_positions),
            group_x0 + max_w,
            max(b[3] for _, _, b in item_positions),
        )

        # Score: segment intersections are hard constraints (×1000 each),
        # placed-box overlaps are very soft hints (×1) — rank always wins over them.
        # This ensures center_right (rank 0) is only overridden by actual branch crossings.
        sc = 0
        for seg in segments:
            if _segment_intersects_box(seg, group_box, 3.0):
                sc += 1000
        for pb in placed:
            if _boxes_overlap(group_box, pb, 2.0):
                sc += 1

        sc = sc + rank

        if best_score is None or sc < best_score:
            best_score = sc
            best = (group_x0, anchor, item_positions, group_box)

    return best


# ---------------------------------------------------------------------------
# Estimation helpers (no font measurement available in SVG generation)
# ---------------------------------------------------------------------------

_CHAR_W = 0.60   # px per pt of font size per character
_LINE_H = 0.75   # line height multiplier


def estimate_text_size(text: str, font_size: float) -> Tuple[float, float]:
    """Rough estimate of rendered text dimensions in pixels."""
    w = len(text) * font_size * _CHAR_W
    h = font_size * _LINE_H
    return w, h