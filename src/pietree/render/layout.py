from pietree.render.geometry import (
        label_branch_repulsion
    )

def compute_root_to_tip_distances(tree):

    root = tree.root
    distances = {}

    def dfs(node, acc):

        is_leaf = node.is_tip

        if is_leaf:
            distances[node.id] = acc

        for child, branch in node._children:

            length = branch.length if branch and branch.length is not None else 1.0

            dfs(child, acc + length)

    dfs(root, 0.0)

    return distances

def axis_map(orientation):

    if orientation == "horizontal":
        return "x", "y"

    if orientation == "vertical":
        return "y", "x"

    raise ValueError("Unknown orientation")

def assign_leaf_order(root):

    order = {}
    counter = 0

    def dfs(n):
        nonlocal counter

        if n.is_tip:
            order[n.id] = counter
            counter += 1
            return

        for c, _ in n._children:
            dfs(c)

    dfs(root)
    return order

def compute_positions(
    tree,
    use_branch_lengths=False,
    ultrametric=False,
    orientation="horizontal",
):

    leaf_order = assign_leaf_order(tree.root)

    coords = {}

    max_distance = 0.0

    if ultrametric:

        distances = compute_root_to_tip_distances(tree)

        if distances:
            max_distance = max(distances.values())

    def dfs(node, acc):

        # -----------------------------------------
        # TIP
        # -----------------------------------------

        if node.is_tip:

            leaf_pos = leaf_order[node.id]

            if ultrametric:
                depth = max_distance
            else:
                depth = acc

            # IMPORTANT:
            # horizontal trees:
            #   x = depth
            #   y = leaf order
            #
            # vertical trees:
            #   x = leaf order
            #   y = depth

            if orientation == "horizontal":
                coords[node.id] = (depth, leaf_pos)
            else:
                coords[node.id] = (leaf_pos, depth)

            return leaf_pos

        # -----------------------------------------
        # INTERNAL NODE
        # -----------------------------------------

        child_positions = []

        for child, branch in node._children:

            if use_branch_lengths:

                length = (
                    branch.length
                    if branch and branch.length is not None
                    else 1.0
                )

            else:
                length = 1.0

            child_positions.append(
                dfs(child, acc + length)
            )

        # internal node centered on descendants
        leaf_center = sum(child_positions) / len(child_positions)

        depth = acc

        if orientation == "horizontal":
            coords[node.id] = (depth, leaf_center)
        else:
            coords[node.id] = (leaf_center, depth)

        return leaf_center

    dfs(tree.root, 0.0)

    return coords

def resolve_label_collisions(labels, nodes, branches, pos, max_shift=10):

    def overlaps(a, b):
        return abs(a.x - b.x) < 10 and abs(a.y - b.y) < 10

    for _ in range(5):

        moved = False

        for i, l1 in enumerate(labels):

            dx, dy = 0, 0

            # --------------------------------------------------
            # label-label collisions
            # --------------------------------------------------
            for j, l2 in enumerate(labels):

                if i == j:
                    continue

                if overlaps(l1, l2):
                    dx += l1.x - l2.x
                    dy += l1.y - l2.y
                    moved = True

            # --------------------------------------------------
            # node collision
            # --------------------------------------------------
            for node in nodes:
                cx, cy = pos[node.node.id]

                if abs(l1.x - cx) < 8 and abs(l1.y - cy) < 8:
                    dx += l1.x - cx
                    dy += l1.y - cy
                    moved = True

            # --------------------------------------------------
            # branch collision (NEW)
            # --------------------------------------------------
            for branch in branches:

                a = branch.source
                b = branch.target

                ax, ay = pos[a]
                bx, by = pos[b]

                # --------------------------------------------------
                # SPATIAL FILTER (correct version)
                # only consider branches near the label
                # --------------------------------------------------

                lx, ly = l1.x, l1.y

                if (
                    abs(lx - ax) > 80 and abs(lx - bx) > 80 and
                    abs(ly - ay) > 80 and abs(ly - by) > 80
                ):
                    continue

                bx, by = label_branch_repulsion(
                    l1,
                    pos,
                    a,
                    b,
                    strength=1.5,
                    min_dist=14
                )

                dx += bx * (1.0 / (1 + len(branches)))
                dy += by * (1.0 / (1 + len(branches)))

                if bx != 0 or by != 0:
                    moved = True

            # --------------------------------------------------
            # apply clamp
            # --------------------------------------------------
            l1.final_x += max(-max_shift, min(max_shift, dx))
            l1.final_y += max(-max_shift, min(max_shift, dy))

        if not moved:
            break

    return labels

def compute_repulsion_vector(collisions):

    dx, dy = 0, 0

    for c in collisions:

        if c.ype == "node":
            dx += label.x - c.x
            dy += label.y - c.y

        elif c.ype == "branch":
            dx += c.normal_x
            dy += c.normal_y

        elif c.ype == "label":
            dx += label.x - c.x
            dy += label.y - c.y

    return dx, dy

def compute_circular_positions(
    tree,
    use_branch_lengths=False,
    ultrametric=False,
    arc=360.0,
    start_angle=-90.0,
):
    """
    Compute polar-then-Cartesian positions for a circular tree layout.

    Tips are evenly distributed around `arc` degrees starting from
    `start_angle`.  Branch depth becomes the radius.  Internal nodes
    are centred angularly on their descendants.

    Returns {node_id: (x, y)} where (x, y) are Cartesian coordinates
    centred at (0, 0); canvas.py re-centres them onto the SVG canvas.
    Also stores per-node angles and radii on the returned dict as a
    side-channel via the ``_circular_meta`` key:
        _circular_meta[node_id] = {"angle": float_deg, "r": float}
    This is used by the branch / label renderers.
    """
    import math

    leaf_order = assign_leaf_order(tree.root)
    n_tips = len(leaf_order)

    # Angular spacing between tips (degrees)
    if n_tips > 1:
        step = arc / n_tips
    else:
        step = 0.0

    # Angle for each tip (in degrees, measured from start_angle)
    tip_angles = {}
    for node_id, order in leaf_order.items():
        tip_angles[node_id] = start_angle + (order + 0.5) * step

    # Max depth for ultrametric
    max_distance = 0.0
    if ultrametric:
        distances = compute_root_to_tip_distances(tree)
        if distances:
            max_distance = max(distances.values())

    coords = {}
    _circular_meta = {}  # node_id → {"angle": deg, "r": float, "r_true": float}

    def dfs(node, acc):
        if node.is_tip:
            r_true = acc  # actual accumulated depth (before any alignment)
            if ultrametric:
                r = max_distance
            else:
                r = acc
            angle_deg = tip_angles[node.id]
            angle_rad = math.radians(angle_deg)
            coords[node.id] = (r * math.cos(angle_rad), r * math.sin(angle_rad))
            _circular_meta[node.id] = {"angle": angle_deg, "r": r, "r_true": r_true}
            return angle_deg

        child_angles = []
        for child, branch in node._children:
            if use_branch_lengths:
                length = (branch.length if branch and branch.length is not None else 1.0)
            else:
                length = 1.0
            child_angles.append(dfs(child, acc + length))

        angle_deg = sum(child_angles) / len(child_angles)
        angle_rad = math.radians(angle_deg)
        r = acc
        coords[node.id] = (r * math.cos(angle_rad), r * math.sin(angle_rad))
        _circular_meta[node.id] = {"angle": angle_deg, "r": r, "r_true": acc}
        return angle_deg

    dfs(tree.root, 0.0)

    # Attach meta as a special key so canvas.py can read it
    coords["_circular_meta"] = _circular_meta  # type: ignore[assignment]
    return coords


def build_layout(tree, mode="phylogram", orientation="horizontal", options=None):

    if mode == "cladogram":

        return compute_positions(
            tree,
            use_branch_lengths=False,
            ultrametric=False,
            orientation=orientation,
        )

    elif mode == "phylogram":

        return compute_positions(
            tree,
            use_branch_lengths=True,
            ultrametric=False,
            orientation=orientation,
        )

    elif mode == "ultrametric":

        return compute_positions(
            tree,
            use_branch_lengths=True,
            ultrametric=True,
            orientation=orientation,
        )

    elif mode == "circular":
        arc   = getattr(options, "circular_arc",         360.0) if options else 360.0
        start = getattr(options, "circular_start_angle", -90.0) if options else -90.0
        return compute_circular_positions(
            tree,
            use_branch_lengths=True,
            ultrametric=False,
            arc=arc,
            start_angle=start,
        )

    else:
        raise ValueError(f"Unknown layout mode: {mode}")
