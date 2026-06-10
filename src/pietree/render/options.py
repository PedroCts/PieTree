from dataclasses import dataclass

@dataclass
class RenderOptions:
    # Root
    show_root_branch: bool = True           # draw a stub branch at root
    root_branch_length: float = 50.0        # pixel length of root stub

    # Nodes
    show_node_labels: bool = True
    show_tip_markers: bool = True           # show tip circles

    # Tips
    show_tip_labels: bool = True
    align_tip_labels: bool = True
    tip_label_guide_style: str = "dashed"
    tip_label_guide_color: str = "#888888"
    tip_label_guide_width: float = 2.0
    tip_label_guide_gap: float = 10.0       # gap between tip and guide start

    # Internal Nodes
    show_internal_node_labels: bool = True
    show_internal_markers: bool = True      # show internal node circles

    # Branches
    show_branch_labels: bool = False
    show_branch_lengths: bool = False       # show branch length values
    branch_length_precision: int = 3        # decimal places for branch lengths
    branch_length_placement: str = "branch" # "branch" | "node" (same options as support)

    # Support
    show_support: bool = True
    support_threshold: float = 0.0
    support_keys: list[str] | None = None
    support_placement: str = "node"         # "node" | "branch"

    # General Style
    branch_color: str = "#888"
    font_size: int = 12
    color: str = "#222"

    # Panels
    panel_spacing: float = 14.0
    panel_font_size: float = 11.0
    panel_color: str = "#555555"
    panel_font_color: str = "#333333"
    panel_line_cap: str = "round"           # already in panels
    meta_label_offset_x: float = 6.0        # breathing room for node labels
    meta_label_offset_y: float = -8.0

    # Highlights
    highlight_opacity: float = 0.18         # softer default for print
    highlight_corner_radius: float = 4.0
