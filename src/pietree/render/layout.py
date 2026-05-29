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

def build_layout(tree, mode="phylogram", orientation="horizontal"):

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

    else:
        raise ValueError(f"Unknown layout mode: {mode}")