"""
render/layers/labels.py
-----------------------
Unified label rendering for pietree.

Label types
-----------
tip            : species/sequence names — always right of tip, aligned
node           : internal node names — smart placement around node
support        : branch support values — near node (placement="node") or
                 mid-branch (placement="branch")
branch         : arbitrary branch annotations (PieBranch.label.text)
branch_length  : numeric branch length values
meta           : metadata-derived labels (from metadata().label_nodes())

Multiple labels per object
--------------------------
Each type can contribute independently.  They are collected into a flat
list of RenderLabel objects, each carrying its own (px, py, text_anchor)
already resolved by the time drawing starts.

Node-group stacking order (top → bottom)
-----------------------------------------
  1. node name
  2. support  (when support_placement="node")
  3. branch length  (when branch_length_placement="node")
  4. meta label

Smart placement
---------------
For node / support / branch labels the renderer probes candidate positions
(8 directions for nodes, 2–4 for branch segments) and picks the one with
the least overlap with drawn branch segments and already-placed labels.
Tip labels are exempt: they live in clear whitespace to the right.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from xml.etree.ElementTree import SubElement

from pietree.style.defaults import (
    DEFAULT_TIP_FONT_SIZE,
    DEFAULT_INTERNAL_FONT_SIZE,
    DEFAULT_TIP_FONT_COLOR,
    DEFAULT_INTERNAL_FONT_COLOR,
    DEFAULT_OPACITY,
)
from pietree.render.label_placement import (
    branch_segments,
    estimate_text_size,
    find_best_slot,
    find_best_slot_for_group,
    _NODE_CANDIDATES,
    _BRANCH_H_CANDIDATES,
    _BRANCH_V_CANDIDATES,
)


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class RenderLabel:
    """A single text label ready to be drawn."""

    # source object (RenderNode or RenderEdge)
    node: object

    text: str

    # pre-resolved SVG insertion point and anchor
    x: float
    y: float
    text_anchor: str = "start"

    # classification
    label_type: str = "node"   # "tip" | "node" | "support" | "branch" | "branch_length" | "meta"
    is_tip: bool = False
    slot_index: int = 0        # stacking index when multiple labels share an object

    # style overrides (populated from PieLabel.style or meta_label)
    font_size: Optional[float] = None
    font_color: Optional[str] = None
    font_weight: str = "normal"
    font_style: str = "normal"
    text_decoration: str = "none"
    opacity: float = 1.0

    # back-reference to PieLabel for stylesheet resolution
    pie_label: object = None

    # bounding box for collision tracking (set after placement)
    _box: Optional[Tuple[float, float, float, float]] = field(
        default=None, repr=False
    )

    # --- legacy compat ---
    @property
    def final_x(self) -> float:
        return self.x

    @property
    def final_y(self) -> float:
        return self.y


# ---------------------------------------------------------------------------
# Internal builder helpers
# ---------------------------------------------------------------------------

_LABEL_GAP = 6.0   # px from node centre to nearest edge of label box


def _default_font(label_type: str, is_tip: bool) -> Tuple[float, str]:
    if is_tip or label_type == "tip":
        return DEFAULT_TIP_FONT_SIZE, DEFAULT_TIP_FONT_COLOR
    return DEFAULT_INTERNAL_FONT_SIZE, DEFAULT_INTERNAL_FONT_COLOR


def _extract_style(pie_label, resolver, context, label_type, is_tip):
    """
    Resolve stylesheet + PieLabel.style into flat style attributes.
    Returns a dict with font_size, font_color, font_weight, font_style,
    text_decoration, opacity, visible.
    """
    style_rule = resolver.resolve(pie_label, context) if pie_label else None
    if pie_label is not None:
        pie_label.style.apply_to_rule(style_rule)

    default_size, default_color = _default_font(label_type, is_tip)

    return dict(
        font_size=(style_rule.font_size if style_rule else None) or default_size,
        font_color=(style_rule.font_color if style_rule else None) or default_color,
        font_weight=(style_rule.font_weight if style_rule else None) or "normal",
        font_style=(style_rule.font_style if style_rule else None) or "normal",
        text_decoration=(style_rule.text_decoration if style_rule else None) or "none",
        opacity=(style_rule.opacity if style_rule else None) or DEFAULT_OPACITY,
        visible=getattr(style_rule, "visible", True) if style_rule else True,
    )


def _format_branch_length(value: float, precision: int) -> str:
    """Format a branch length for display, trimming unnecessary trailing zeros."""
    formatted = f"{value:.{precision}f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


# ---------------------------------------------------------------------------
# Tip labels  (no smart placement — always right-aligned)
# ---------------------------------------------------------------------------

def _collect_tip_labels(spec, pos, sources, resolver, context, align_anchor) -> List[RenderLabel]:
    labels = []
    for node in spec.nodes:
        if node.id in sources:
            continue
        if not spec.options.show_tip_labels:
            break
        if not node.label:
            continue

        cx, cy = pos[node.id]

        if spec.orientation == "horizontal":
            px = (align_anchor + 10) if align_anchor is not None else (cx + 10)
            py = cy + 4
            anchor = "start"
        else:
            px = cx
            py = (align_anchor + 18) if align_anchor is not None else (cy + 18)
            anchor = "middle"

        pie_label = node.node.label
        style = _extract_style(pie_label, resolver, context, "tip", True)
        if not style["visible"]:
            continue

        labels.append(RenderLabel(
            node=node, text=node.node.label.text,
            x=px, y=py, text_anchor=anchor,
            label_type="tip", is_tip=True,
            pie_label=pie_label,
            **{k: v for k, v in style.items() if k != "visible"},
        ))
    return labels


# ---------------------------------------------------------------------------
# Unified per-node label group placement
# ---------------------------------------------------------------------------
#
# Labels that share the same node (node-name, support, branch-length, meta)
# are placed as a vertical stack in the single best direction rather than
# placed independently (which can cause one label to fall into a branch
# while another sits cleanly on the other side).
#
# Priority within each stack (top → bottom):
#   1. node-name label
#   2. support value  (when support_placement="node")
#   3. branch length  (when branch_length_placement="node")
#   4. meta label(s)

_STACK_GAP = 0.0   # px between stacked labels (advance-based, so visually tight)


def _collect_node_group_labels(
    spec, pos, sources, resolver, context, segments, placed_boxes
) -> List[RenderLabel]:
    """
    Collect node-name, support, branch-length, and meta labels together and
    place each node's group as a unit (vertical stack in the best direction).
    """
    options = spec.options
    meta_labels_src = getattr(spec, "meta_labels", [])
    meta_index = {ml.node_id: ml for ml in meta_labels_src}

    # Build edge lookup: child_node_id → edge  (for support + branch length)
    edge_by_child = {e.target: e for e in spec.edges}

    output: List[RenderLabel] = []

    for node in spec.nodes:
        if node.id not in sources:
            continue  # skip tips

        cx, cy = pos[node.id]

        # --------------------------------------------------
        # 1. Gather candidate label specs for this node
        # --------------------------------------------------
        # Each entry: (text, font_size, font_color, font_weight, font_style,
        #              text_decoration, opacity, label_type, pie_label)
        group_specs = []

        # Node-name label
        if options.show_node_labels and node.label:
            pie_label = node.node.label
            style = _extract_style(pie_label, resolver, context, "node", False)
            if style["visible"]:
                text = node.node.label.text
                group_specs.append((
                    text,
                    style["font_size"], style["font_color"], style["font_weight"],
                    style["font_style"], style["text_decoration"], style["opacity"],
                    "node", pie_label,
                ))

        # Support label — only when placement is "node"
        if options.show_support and options.support_placement == "node":
            edge = edge_by_child.get(node.id)
            if edge is not None:
                branch = edge.branch
                support_val = getattr(branch, "support", None)
                if support_val:
                    keys = options.support_keys
                    vals = [support_val[k] for k in keys if k in support_val] if keys else list(support_val.values())
                    if vals and vals[0] >= options.support_threshold:
                        text = "/".join(
                            f"{v:.0f}" if v > 1 else f"{v:.2f}".rstrip("0").rstrip(".")
                            for v in vals
                        )
                        font_size = options.font_size * 0.85
                        pie_label = getattr(branch, "label", None)
                        group_specs.append((
                            text, font_size, options.color, "normal",
                            "normal", "none", DEFAULT_OPACITY, "support", pie_label,
                        ))

        # Branch length label — only when placement is "node"
        if options.show_branch_lengths and options.branch_length_placement == "node":
            edge = edge_by_child.get(node.id)
            if edge is not None and edge.length is not None:
                text = _format_branch_length(edge.length, options.branch_length_precision)
                font_size = options.font_size * 0.80
                group_specs.append((
                    text, font_size, options.branch_length_color, "normal",
                    "italic", "none", DEFAULT_OPACITY, "branch_length", None,
                ))

        # Meta label
        if node.id in meta_index:
            ml = meta_index[node.id]
            group_specs.append((
                ml.text,
                ml.font_size, ml.font_color, "normal",
                "normal", "none", DEFAULT_OPACITY,
                "meta", None,
            ))

        if not group_specs:
            continue

        # --------------------------------------------------
        # 2. Estimate sizes
        # --------------------------------------------------
        sizes = [estimate_text_size(gs[0], gs[1]) for gs in group_specs]

        # --------------------------------------------------
        # 3. Place as group
        # --------------------------------------------------
        _, anchor, item_positions, group_box = find_best_slot_for_group(
            cx, cy, sizes, _LABEL_GAP,
            _NODE_CANDIDATES, segments, placed_boxes,
            stack_gap=_STACK_GAP,
        )
        placed_boxes.append(group_box)

        # group_box[0] is the shared left edge (for "start"),
        # group_box[2] is the shared right edge (for "end").
        group_x0 = group_box[0]
        group_x1 = group_box[2]

        # --------------------------------------------------
        # 4. Emit RenderLabels with final positions
        # --------------------------------------------------
        for i, (gs, (tw, th), (item_cx, item_cy, item_box)) in enumerate(
            zip(group_specs, sizes, item_positions)
        ):
            text, font_size, font_color, font_weight, font_style, text_dec, opacity, ltype, pie_label = gs

            if anchor == "start":
                px = group_x0
            elif anchor == "end":
                px = group_x1
            else:   # middle — centre each item on cx
                px = item_cx

            py = item_cy + font_size * 0.35   # SVG baseline: ~35% of cap-height below centre

            output.append(RenderLabel(
                node=node,
                text=text,
                x=px, y=py,
                text_anchor=anchor,
                label_type=ltype,
                is_tip=False,
                slot_index=i,
                font_size=font_size,
                font_color=font_color,
                font_weight=font_weight,
                font_style=font_style,
                text_decoration=text_dec,
                opacity=opacity,
                pie_label=pie_label,
            ))

    return output


# ---------------------------------------------------------------------------
# Branch-segment labels  (support, branch annotations, branch lengths)
# ---------------------------------------------------------------------------
#
# All three types share the same midpoint-anchor logic.  They are placed
# independently (not stacked) because they live on the branch line itself
# rather than next to a node — crowding is rare in practice.
#
# Bug fix: the original code gated the entire function on show_branch_labels,
# which silently suppressed support-on-branch and branch-length-on-branch
# when only those options were enabled.  The early-return now checks all
# three independently.

def _collect_branch_labels(
    spec, pos, resolver, context, segments, placed_boxes
) -> List[RenderLabel]:
    labels = []
    options = spec.options

    want_annotations   = options.show_branch_labels
    want_support       = options.show_support and options.support_placement == "branch"
    want_branch_length = options.show_branch_lengths and options.branch_length_placement == "branch"

    if not (want_annotations or want_support or want_branch_length):
        return labels

    for edge in spec.edges:
        branch = edge.branch

        px_parent, py_parent = pos[edge.source]
        px_child,  py_child  = pos[edge.target]

        if spec.orientation == "horizontal":
            # Midpoint of the horizontal child-run segment
            mid_cx = (px_parent + px_child) / 2
            mid_cy = py_child
            cands  = _BRANCH_H_CANDIDATES
        else:
            # Midpoint of the vertical child-run segment
            mid_cx = px_child
            mid_cy = (py_parent + py_child) / 2
            cands  = _BRANCH_V_CANDIDATES

        # --------------------------------------------------
        # Arbitrary branch annotation  (PieBranch.label.text)
        # --------------------------------------------------
        if want_annotations:
            pie_label = getattr(branch, "label", None)
            if pie_label and pie_label.text:
                text  = pie_label.text
                style = _extract_style(pie_label, resolver, context, "branch", False)
                if style["visible"]:
                    tw, th = estimate_text_size(text, style["font_size"])
                    px, py, anchor, box = find_best_slot(
                        mid_cx, mid_cy, tw, th, _LABEL_GAP * 0.5,
                        cands, segments, placed_boxes,
                    )
                    placed_boxes.append(box)
                    labels.append(RenderLabel(
                        node=None, text=text,
                        x=px, y=py, text_anchor=anchor,
                        label_type="branch", is_tip=False,
                        pie_label=pie_label,
                        **{k: v for k, v in style.items() if k != "visible"},
                    ))

        # --------------------------------------------------
        # Support value on branch
        # --------------------------------------------------
        if want_support:
            support_val = getattr(branch, "support", None)
            if support_val:
                keys = options.support_keys
                vals = (
                    [support_val[k] for k in keys if k in support_val]
                    if keys
                    else list(support_val.values())
                )
                if vals and vals[0] >= options.support_threshold:
                    text = "/".join(
                        f"{v:.0f}" if v > 1 else f"{v:.2f}".rstrip("0").rstrip(".")
                        for v in vals
                    )
                    font_size = options.font_size * 0.85
                    tw, th = estimate_text_size(text, font_size)
                    px, py, anchor, box = find_best_slot(
                        mid_cx, mid_cy, tw, th, _LABEL_GAP * 0.5,
                        cands, segments, placed_boxes,
                    )
                    placed_boxes.append(box)
                    labels.append(RenderLabel(
                        node=None, text=text,
                        x=px, y=py, text_anchor=anchor,
                        label_type="support", is_tip=False,
                        font_size=font_size,
                        font_color=options.color,
                        font_weight="normal",
                        font_style="normal",
                        text_decoration="none",
                        opacity=DEFAULT_OPACITY,
                    ))

        # --------------------------------------------------
        # Branch length value on branch
        # --------------------------------------------------
        if want_branch_length and edge.length is not None:
            text = _format_branch_length(edge.length, options.branch_length_precision)
            font_size = options.font_size * 0.80
            tw, th = estimate_text_size(text, font_size)
            px, py, anchor, box = find_best_slot(
                mid_cx, mid_cy, tw, th, _LABEL_GAP * 0.5,
                cands, segments, placed_boxes,
            )
            placed_boxes.append(box)
            labels.append(RenderLabel(
                node=None, text=text,
                x=px, y=py, text_anchor=anchor,
                label_type="branch_length", is_tip=False,
                font_size=font_size,
                font_color=options.branch_length_color,
                font_weight="normal",
                font_style="italic",
                text_decoration="none",
                opacity=DEFAULT_OPACITY,
            ))

    return labels


# (meta labels are handled inside _collect_node_group_labels)


# ---------------------------------------------------------------------------
# Guide lines for aligned tip labels
# ---------------------------------------------------------------------------

def _draw_guides(svg, spec, pos, labels, context):
    options = spec.options
    guide_color = options.tip_label_guide_color
    guide_width = str(options.tip_label_guide_width)
    guide_style = options.tip_label_guide_style

    dasharray = (
        "4,4" if guide_style == "dashed"
        else "2,2" if guide_style == "dotted"
        else "none"
    )

    for label in labels:
        if label.label_type != "tip":
            continue

        node_x, node_y = pos[label.node.id]
        tip_edge = context.tip_edge

        if spec.orientation == "horizontal":
            x1 = node_x + options.tip_label_guide_gap
            y1 = node_y
            x2 = tip_edge
            y2 = node_y
        else:
            x1 = node_x
            y1 = node_y + options.tip_label_guide_gap
            x2 = node_x
            y2 = tip_edge

        if abs(x2 - x1) < 2 and abs(y2 - y1) < 2:
            continue

        attrs = {
            "x1": str(x1), "y1": str(y1),
            "x2": str(x2), "y2": str(y2),
            "stroke": guide_color,
            "stroke-width": guide_width,
        }
        if dasharray != "none":
            attrs["stroke-dasharray"] = dasharray

        SubElement(svg, "line", attrs)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_labels(context):

    spec = context.spec
    svg = context.svg
    pos = context.pos
    resolver = context.resolver
    sources = context.sources
    options = spec.options

    align = options.align_tip_labels and spec.mode != "ultrametric"
    align_anchor = context.tip_edge if align else None

    # --------------------------------------------------
    # Pre-compute all branch segments (used for collision)
    # --------------------------------------------------
    segs = branch_segments(spec.edges, pos, spec.orientation)

    # Shared list of placed bounding boxes; grows as we add labels
    placed: List[Tuple[float, float, float, float]] = []

    # --------------------------------------------------
    # Collect labels in priority order
    # (tip first so their boxes don't block themselves,
    #  but we don't add tip boxes to `placed` because
    #  they're in separate whitespace)
    # --------------------------------------------------
    tip_labels = _collect_tip_labels(
        spec, pos, sources, resolver, context, align_anchor
    )
    node_group_labels = _collect_node_group_labels(
        spec, pos, sources, resolver, context, segs, placed
    )
    branch_ann_labels = _collect_branch_labels(
        spec, pos, resolver, context, segs, placed
    )

    all_labels = tip_labels + node_group_labels + branch_ann_labels

    # --------------------------------------------------
    # Guide lines (before labels so they render underneath)
    # --------------------------------------------------
    if align and align_anchor is not None:
        _draw_guides(svg, spec, pos, tip_labels, context)

    # --------------------------------------------------
    # Draw labels
    # --------------------------------------------------
    for label in all_labels:
        SubElement(
            svg, "text",
            {
                "x": str(label.x),
                "y": str(label.y),
                "font-size": str(label.font_size or DEFAULT_INTERNAL_FONT_SIZE),
                "fill": str(label.font_color or DEFAULT_INTERNAL_FONT_COLOR),
                "font-weight": label.font_weight,
                "font-style": label.font_style,
                "text-decoration": label.text_decoration,
                "text-anchor": label.text_anchor,
                "opacity": str(label.opacity),
            },
        ).text = label.text
