from dataclasses import dataclass, field

@dataclass
class RenderOptions:
    # Nodes
    show_node_labels: bool = True
    
    # Tips
    show_tip_labels: bool = True
    align_tip_labels: bool = True
    tip_label_guide_style: str = "dashed"
    tip_label_guide_color: str = "#888888"
    tip_label_guide_width: float = 2.0
    tip_label_guide_gap: float = 10.0 # gap between tip and guide start
    
    # Internal Nodes
    show_internal_node_labels: bool = True
    
    # Branches
    show_branch_labels: bool = False

    # Support
    show_support: bool = False
    support_threshold: float = 0.0
    
    # General Style
    branch_color: str = "#888"
    font_size: int = 12
    color: str = "#222"

    # Panels
    panel_spacing: float = 14.0
    panel_font_size: float = 11.0
    panel_color: str = "#555555"
    panel_font_color: str = "#333333"