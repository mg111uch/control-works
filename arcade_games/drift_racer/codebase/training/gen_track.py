"""Procedural closed-loop track generator (same JSON schema as tracks/*.json).

Usage (from codebase/):
    conda run -n myenv python training/gen_track.py --seed 7 --lobes 2
    conda run -n myenv python training/gen_track.py --seed 7 --lobes 1 --out /tmp/oval7.json

Rejects layouts with: spawn off asphalt, crossover lens < car width,
checkpoint boxes off asphalt. Prints the acceptance report.
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.track import Track  # noqa: E402

SCREEN_W, SCREEN_H = 600, 400
MIN_LENS = 40  # min crossover asphalt width (px)
BOX = 44  # checkpoint box size (fits narrow rings)
MIN_LAP_BOXES = 4

PALETTE = {'track_color': [80, 80, 80], 'border_color': [255, 255, 255],
           'grass_color': [0, 128, 0], 'background_color': [128, 128, 128],
           'border_width': 2}


def _lobe(rng):
    rx = rng.uniform(80, 140)
    ry = rng.uniform(100, 160)
    s = rng.uniform(0.40, 0.65)
    hrx, hry = rx * s, ry * s
    # eccentric hole: jitter center, clamped so ≥25px ring remains
    hjx = rng.uniform(-1, 1) * max(0, rx - hrx - 25)
    hjy = rng.uniform(-1, 1) * max(0, ry - hry - 25)
    return {'rx': rx, 'ry': ry, 'hrx': hrx, 'hry': hry, 'hjx': hjx, 'hjy': hjy}


def _asphalt_runs(track, y, x0=0, x1=SCREEN_W, step=4):
    """Contiguous on-track x-runs at height y."""
    runs, cur = [], None
    x = x0
    while x <= x1:
        on = track.is_on_track(x, y)
        if on and cur is None:
            cur = [x, x]
        elif on:
            cur[1] = x
        elif cur is not None:
            runs.append(tuple(cur))
            cur = None
        x += step
    if cur is not None:
        runs.append(tuple(cur))
    return runs


def _box_ok(track, cx, cy, size=BOX):
    """Box valid if center + inset corners are all asphalt."""
    m = size / 2 - 6
    return all(track.is_on_track(px, py) for px, py in
               [(cx, cy), (cx - m, cy - m), (cx + m, cy - m),
                (cx - m, cy + m), (cx + m, cy + m)])


def _ring_pt(L, ang_deg):
    """Point on the mid-ring ellipse at angle (deg, screen coords y down)."""
    import math
    a = math.radians(ang_deg)
    mx, my = (L['rx'] + L['hrx']) / 2, (L['ry'] + L['hry']) / 2
    return (L['cx'] + mx * math.cos(a), L['cy'] + my * math.sin(a))


def _rot(dx, dy, ang_deg):
    """Local-frame offset to world (inverse of Track._to_local)."""
    import math
    a = math.radians(ang_deg)
    return (dx * math.cos(a) - dy * math.sin(a),
            dx * math.sin(a) + dy * math.cos(a))


def _find_box(track, cx, cy, ang_deg, size, rmax=300):
    """Search outward along a ray for a box fully on asphalt.

    Shape-agnostic (works for ellipse/rect/stadium/spline rings):
    scans distance until a whole box fits.
    """
    import math
    a = math.radians(ang_deg)
    d = 12
    while d <= rmax:
        px, py = cx + d * math.cos(a), cy + d * math.sin(a)
        if _box_ok(track, px, py, size=size):
            return (px, py)
        d += 8
    return None


def _find_ring_box(track, cx, cy, rx, ry, ang_deg, size):
    """Legacy ellipse-ring placement (kept for compatibility)."""
    import math
    a = math.radians(ang_deg)
    for k in [0.55, 0.45, 0.65, 0.35, 0.75, 0.3, 0.8, 0.25, 0.85]:
        px, py = cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)
        if _box_ok(track, px, py, size=size):
            return (px, py)
    return None


def _box(cx, cy, i, size=BOX):
    h = size / 2
    return {'id': i, 'type': 'position', 'x_min': cx - h, 'x_max': cx + h,
            'y_min': cy - h, 'y_max': cy + h}


def _inside(x, y, m=15):
    return m <= x <= SCREEN_W - m and m <= y <= SCREEN_H - m


def _seg_cross(p1, p2, p3, p4):
    """Proper segment intersection (excludes touching endpoints)."""
    def _o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = _o(p3, p4, p1), _o(p3, p4, p2), _o(p1, p2, p3), _o(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _simple(poly):
    """Closed polygon has no self-intersections."""
    n = len(poly)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if _seg_cross(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n]):
                return False
    return True


def _spline_elements(rng):
    """Closed spline ring: Fourier centerline offset along normals.

    Returns (elements, (pcx, pcy)) or (None, reason). Single loop only.
    """
    import math
    cx = rng.uniform(240, 360)
    cy = rng.uniform(160, 240)
    R0 = rng.uniform(115, 150)
    a1, p1 = rng.uniform(0, 0.22), rng.uniform(0, 2 * math.pi)
    a2, p2 = rng.uniform(0, 0.15), rng.uniform(0, 2 * math.pi)
    W0 = rng.uniform(48, 68)
    b, p3 = rng.uniform(0, 0.3), rng.uniform(0, 2 * math.pi)
    N = 64
    cl = []
    for i in range(N):
        th = 2 * math.pi * i / N
        r = R0 * (1 + a1 * math.sin(th + p1) + a2 * math.sin(2 * th + p2))
        cl.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    outer, inner, widths = [], [], []

    def _rebuild():
        outer.clear()
        inner.clear()
        for i in range(N):
            x0, y0 = cl[i]
            tx = cl[(i + 1) % N][0] - cl[(i - 1) % N][0]
            ty = cl[(i + 1) % N][1] - cl[(i - 1) % N][1]
            L = math.hypot(tx, ty) or 1.0
            # outward normal: centerline winds clockwise (y-down)
            nx, ny = ty / L, -tx / L
            w = widths[i]
            outer.append([round(x0 + nx * w / 2, 1), round(y0 + ny * w / 2, 1)])
            inner.append([round(x0 - nx * w / 2, 1), round(y0 - ny * w / 2, 1)])

    for i in range(N):
        th = 2 * math.pi * i / N
        w = W0 * (1 + b * math.sin(3 * th + p3))
        if w < 30:
            return None, 'spline too pinched'
        widths.append(w)
    # auto-fit: scale about centroid, then centre mid-screen
    maxhw = max(widths) / 2
    xs = [p[0] for p in cl]
    ys = [p[1] for p in cl]
    s = min(1.0, (SCREEN_W - 30) / ((max(xs) - min(xs)) + 2 * maxhw),
            (SCREEN_H - 30) / ((max(ys) - min(ys)) + 2 * maxhw))
    if s < 1:
        gx, gy = sum(xs) / N, sum(ys) / N
        for i in range(N):
            cl[i] = (gx + (cl[i][0] - gx) * s, gy + (cl[i][1] - gy) * s)
        widths = [w * s for w in widths]
        if min(widths) < 30:
            return None, 'spline fit too pinched'
    xs = [p[0] for p in cl]
    ys = [p[1] for p in cl]
    shx, shy = (SCREEN_W / 2 - (min(xs) + max(xs)) / 2,
                SCREEN_H / 2 - (min(ys) + max(ys)) / 2)
    for i in range(N):
        cl[i] = (cl[i][0] + shx, cl[i][1] + shy)
    _rebuild()
    pcx = sum(p[0] for p in cl) / N
    pcy = sum(p[1] for p in cl) / N
    if not all(_inside(x, y, 10) for ring in (outer, inner) for x, y in ring):
        return None, 'spline out of bounds'
    if not _simple(outer) or not _simple(inner):
        return None, 'spline self-intersects'
    els = [{'type': 'polygon', 'center_x': pcx, 'center_y': pcy,
            'vertices': outer, 'is_hole': False},
           {'type': 'polygon', 'center_x': pcx, 'center_y': pcy,
            'vertices': inner, 'is_hole': True}]
    return els, (pcx, pcy)


def _try_layout(rng, lobes, reverse=False, shape=None):
    els, boxes, runs_report = [], [], {}
    fam = shape or rng.choice(['ellipse', 'rect', 'stadium', 'spline'])
    if lobes == 2:
        fam = 'ellipse'  # legacy figure-8 stays ellipse-pair
    runs_report['shape'] = fam
    ang = rng.uniform(-25, 25) if fam != 'ellipse' else rng.uniform(-15, 15)
    if lobes == 1 and fam == 'spline':
        res, center = _spline_elements(rng)
        if res is None:
            return None, center
        els.extend(res)
        pcx, pcy = center
    elif lobes == 1 and fam == 'ellipse':
        cx = rng.uniform(240, 360)
        cy = rng.uniform(160, 240)
        L = _lobe(rng)
        L.update(cx=cx, cy=cy)
        lobespec = [L]
        els.append({'type': 'ellipse', 'center_x': cx, 'center_y': cy,
                    'radius_x': L['rx'], 'radius_y': L['ry'],
                    'angle': ang, 'is_hole': False})
        els.append({'type': 'ellipse', 'center_x': cx + L['hjx'],
                    'center_y': cy + L['hjy'], 'radius_x': L['hrx'],
                    'radius_y': L['hry'], 'angle': 0, 'is_hole': True})
        pcx, pcy = cx, cy
    elif lobes == 1 and fam in ('rect', 'stadium'):
        cx = rng.uniform(230, 370)
        cy = rng.uniform(150, 250)
        w = rng.uniform(220, 330)
        h = rng.uniform(170, 260)
        if fam == 'rect':
            s = rng.uniform(0.45, 0.65)
            hw, hh = w * s, h * s
            ox = rng.uniform(-1, 1) * max(0, (w - hw) / 2 - 25)
            oy = rng.uniform(-1, 1) * max(0, (h - hh) / 2 - 25)
            corners = [((dx, dy)) for dx in (-w / 2, w / 2) for dy in (-h / 2, h / 2)]
            if not all(_inside(cx + qx, cy + qy)
                       for dx, dy in corners
                       for qx, qy in [_rot(dx, dy, ang)]):
                return None, 'rect out of bounds'
            els.append({'type': 'rectangle', 'center_x': cx, 'center_y': cy,
                        'width': w, 'height': h, 'angle': ang, 'is_hole': False})
            els.append({'type': 'rectangle', 'center_x': cx + ox,
                        'center_y': cy + oy, 'width': hw, 'height': hh,
                        'angle': ang, 'is_hole': True})
        else:  # stadium: rect spine + 2 circle caps, uniform ring t
            t = rng.uniform(35, 60)
            if h - 2 * t < 40:
                return None, 'stadium ring too thin'
            ex = w / 2 + h / 2 + 15  # conservative extent
            if not all(_inside(cx + qx, cy + qy)
                       for dx, dy in ((-ex, 0), (ex, 0), (0, -h / 2), (0, h / 2))
                       for qx, qy in [_rot(dx, dy, ang)]):
                return None, 'stadium out of bounds'
            els.append({'type': 'rectangle', 'center_x': cx, 'center_y': cy,
                        'width': w, 'height': h, 'angle': ang, 'is_hole': False})
            for sxn in (-1, 1):
                qx, qy = _rot(sxn * w / 2, 0, ang)
                els.append({'type': 'ellipse', 'center_x': cx + qx,
                            'center_y': cy + qy, 'radius_x': h / 2,
                            'radius_y': h / 2, 'angle': 0, 'is_hole': False})
            els.append({'type': 'rectangle', 'center_x': cx, 'center_y': cy,
                        'width': w, 'height': h - 2 * t,
                        'angle': ang, 'is_hole': True})
            for sxn in (-1, 1):
                qx, qy = _rot(sxn * w / 2, 0, ang)
                els.append({'type': 'ellipse', 'center_x': cx + qx,
                            'center_y': cy + qy, 'radius_x': h / 2 - t,
                            'radius_y': h / 2 - t, 'angle': 0, 'is_hole': True})
        pcx, pcy = cx, cy
    else:
        cx0 = rng.uniform(140, 210)
        L0 = _lobe(rng)
        L1 = _lobe(rng)
        gap = rng.uniform(140, 180)
        cy0 = rng.uniform(160, 240)
        cy1 = min(280, max(120, cy0 + rng.uniform(-40, 40)))
        L0.update(cx=cx0, cy=cy0)
        L1.update(cx=cx0 + gap, cy=cy1)
        # lobes must overlap horizontally
        if gap >= L0['rx'] + L1['rx'] - 20:
            return None, 'lobes do not overlap'
        lobespec = [L0, L1]
        for L in lobespec:
            els.append({'type': 'ellipse', 'center_x': L['cx'], 'center_y': L['cy'],
                        'radius_x': L['rx'], 'radius_y': L['ry'],
                        'angle': 0, 'is_hole': False})
        for L in lobespec:
            els.append({'type': 'ellipse', 'center_x': L['cx'] + L['hjx'],
                        'center_y': L['cy'] + L['hjy'],
                        'radius_x': L['hrx'], 'radius_y': L['hry'],
                        'angle': 0, 'is_hole': True})
        pcx, pcy = L0['cx'], L0['cy']

    data = {'name': 'proc', 'version': '1.0', 'difficulty': 'medium',
            'screen_size': {'width': SCREEN_W, 'height': SCREEN_H},
            'start_position': {'x': 0, 'y': 0, 'angle': 0},
            'track_elements': els, 'checkpoints': [],
            'lap_completion': {'required_checkpoints': [], 'sequence_required': True},
            'visual': PALETTE}
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmp = f.name
    track = Track(tmp, rasterize=False)  # analytic is plenty for validation
    os.unlink(tmp)

    if lobes == 2 or fam == 'ellipse':
        L0 = lobespec[0]
        sy = L0['cy']
    else:
        sy = pcy
    runs = [r for r in _asphalt_runs(track, sy) if r[1] - r[0] >= 30]
    if not runs:
        return None, 'no spawn run'
    sx = (runs[0][0] + runs[0][1]) / 2  # mid leftmost asphalt (hole-aware)
    if not track.is_on_track(sx, sy):
        return None, 'spawn off asphalt'

    pts = []  # (x, y) box centers in travel order
    box_size = rng.uniform(40, 56)

    def _rp2(cx, cy, ang):
        p = _find_box(track, cx, cy, ang, box_size)
        if p is None:
            return None
        pts.append(p)
        return p

    pts.append((sx, sy))
    if _rp2(pcx, pcy, 225) is None:  # top-left of lobe0
        return None, 'box 1 no placement'
    if lobes == 2:
        L0 = lobespec[0]
        L1 = lobespec[1]
        ycross = (L0['cy'] + L1['cy']) / 2
        runs = [r for r in _asphalt_runs(track, ycross)
                if r[0] <= (L0['cx'] + L1['cx']) / 2 <= r[1]]
        if not runs or runs[0][1] - runs[0][0] < MIN_LENS:
            return None, 'crossover lens too narrow'
        runs_report['lens'] = round(runs[0][1] - runs[0][0])
        pts.append(((L0['cx'] + L1['cx']) / 2, ycross - L0['ry'] * 0.35))
        if _rp2(L1['cx'], L1['cy'], 225) is None or \
                _rp2(L1['cx'], L1['cy'], 0) is None or \
                _rp2(L1['cx'], L1['cy'], 45) is None:
            return None, 'lobe1 box no placement'
        pts.append(((L0['cx'] + L1['cx']) / 2, ycross + L0['ry'] * 0.35))
        if _rp2(pcx, pcy, 45) is None:  # bottom-left of lobe0
            return None, 'box 7 no placement'
    else:
        if _rp2(pcx, pcy, 315) is None or _rp2(pcx, pcy, 0) is None or \
                _rp2(pcx, pcy, 45) is None or _rp2(pcx, pcy, 135) is None:
            return None, 'ring box no placement'

    if len(pts) < MIN_LAP_BOXES:
        return None, 'too few boxes'
    if reverse:
        pts = [pts[0]] + pts[:0:-1]  # same loop, opposite direction
    elif lobes == 1 and rng.random() < 0.3:
        pts = [pts[0], pts[1], pts[3], pts[4]]  # 4-box variant
    for i, (px, py) in enumerate(pts):
        if not _box_ok(track, px, py, size=box_size):
            return None, f'box {i} off asphalt'
        boxes.append(_box(px, py, i, size=box_size))

    data['checkpoints'] = boxes
    data['lap_completion']['required_checkpoints'] = list(range(len(boxes)))
    data['start_position'] = {'x': round(sx, 1), 'y': round(sy, 1),
                              'angle': 180 if reverse else 0}
    return data, runs_report


def generate(seed, lobes=2, tries=80, reverse=None, shape=None):
    """Generate a valid track dict (raises RuntimeError if all tries rejected)."""
    for t in range(tries):
        rng = random.Random(f'{seed}:{t}')
        rev = reverse if reverse is not None else rng.random() < 0.3
        data, report = _try_layout(rng, lobes, reverse=rev, shape=shape)
        if data is not None:
            data['name'] = f'proc_{seed}' + ('_rev' if rev else '')
            report['tries'] = t + 1
            report['reverse'] = rev
            return data, report
    raise RuntimeError(f'no valid layout in {tries} tries (seed={seed})')


def main():
    ap = argparse.ArgumentParser(description='Generate a random closed-loop track')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--lobes', type=int, choices=[1, 2], default=1)
    ap.add_argument('--shape', type=str, choices=['ellipse', 'rect', 'stadium', 'spline'],
                    default=None, help='Force shape family (default: random)')
    ap.add_argument('--reverse', action='store_true',
                    help='Force clockwise (angle 180) layout; default is 30% random')
    ap.add_argument('--out', type=str, default=None)
    ap.add_argument('--tries', type=int, default=80)
    args = ap.parse_args()
    data, report = generate(args.seed, args.lobes, args.tries,
                            reverse=args.reverse or None, shape=args.shape)
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '..', 'tracks', f"proc_{args.seed}.json")
    data['name'] = os.path.splitext(os.path.basename(out))[0]
    with open(out, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'wrote {out}: {len(data["checkpoints"])} boxes, report={report}')


if __name__ == '__main__':
    main()
