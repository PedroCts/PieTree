import math


def project_point_to_segment(px, py, ax, ay, bx, by):
    """
    Returns closest point on segment AB to point P,
    plus parameter t in [0,1]
    """

    abx = bx - ax
    aby = by - ay

    apx = px - ax
    apy = py - ay

    ab_len2 = abx * abx + aby * aby

    if ab_len2 == 0:
        return ax, ay, 0

    t = (apx * abx + apy * aby) / ab_len2
    t = max(0, min(1, t))

    cx = ax + t * abx
    cy = ay + t * aby

    return cx, cy, t

def label_branch_repulsion(label, pos, branch_a, branch_b, strength=1.0, min_dist=12):
    """
    Push label away from a branch segment if too close.
    """

    lx, ly = label.x, label.y

    ax, ay = pos[branch_a]
    bx, by = pos[branch_b]

    cx, cy, _ = project_point_to_segment(lx, ly, ax, ay, bx, by)

    # skip if far away in bounding box sense first
    if abs(lx - cx) > min_dist * 2 and abs(ly - cy) > min_dist * 2:
        return 0, 0

    dx = lx - cx
    dy = ly - cy

    dist2 = dx * dx + dy * dy

    if dist2 > min_dist * min_dist:
        return 0, 0

    dist = math.sqrt(dist2) or 1e-6

    # normalized repulsion direction
    nx = dx / dist
    ny = dy / dist

    # stronger when closer
    force = (min_dist - dist) / min_dist
    force = max(force, 0)

    # stronger decay (critical fix)
    force = force * force

    return nx * force * strength, ny * force * strength

def node_to_screen(node, scale_x, scale_y, offset_x, offset_y):

    x = offset_x + node.x * scale_x
    y = offset_y + node.y * scale_y

    return x, y

def branch_midpoint(parent, child, orientation="horizontal"):

    """
    Compute midpoint of the visible branch segment
    used for labels/support rendering.
    """

    px, py = parent
    cx, cy = child

    # -----------------------------------------
    # HORIZONTAL TREE
    # -----------------------------------------

    if orientation == "horizontal":

        # midpoint of horizontal child connector
        mx = (px + cx) / 2
        my = cy

    # -----------------------------------------
    # VERTICAL TREE
    # -----------------------------------------

    else:

        mx = cx
        my = (py + cy) / 2

    return mx, my

def backbone_midpoint(coords, orientation="horizontal"):

    if orientation == "horizontal":

        xs = [x for x, _ in coords]
        ys = [y for _, y in coords]

        return xs[0], (min(ys) + max(ys)) / 2

    else:

        xs = [x for x, _ in coords]
        ys = [y for _, y in coords]

        return (min(xs) + max(xs)) / 2, ys[0]
