"""Plot a policy trajectory CSV over its track layout.

Usage (from codebase/ — one lap per episode):
    conda run -n myenv python training/train_nn.py --eval-only --eval-laps 1 --track infinity_loop \\
        --traj-out /tmp/opencode/inf.csv
    conda run -n myenv python training/plot_traj.py /tmp/opencode/inf.csv \\
        tracks/infinity_loop.json /tmp/opencode/traj_inf.png
"""
import sys
import csv
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon, Rectangle


def main():
    traj_csv, track_json, out_png = sys.argv[1], sys.argv[2], sys.argv[3]
    track = json.load(open(track_json))
    w, h = track['screen_size']['width'], track['screen_size']['height']

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect('equal')
    ax.invert_yaxis()  # screen coords: y down
    ax.set_facecolor('#008000')

    for e in track['track_elements']:
        color = '#808080' if not e['is_hole'] else '#008000'
        if e.get('vertices'):
            ax.add_patch(Polygon(e['vertices'], closed=True,
                                 facecolor=color, edgecolor='white', lw=1))
        elif e.get('type') == 'rectangle':
            ax.add_patch(Rectangle((e['center_x'] - e['width'] / 2,
                                    e['center_y'] - e['height'] / 2),
                                   e['width'], e['height'],
                                   facecolor=color,
                                   edgecolor='white', lw=1))
        else:
            ax.add_patch(Ellipse((e['center_x'], e['center_y']),
                                 2 * e['radius_x'], 2 * e['radius_y'],
                                 facecolor=color,
                                 edgecolor='white', lw=1))

    rows = list(csv.DictReader(open(traj_csv)))
    for ep in sorted(set(r['episode'] for r in rows)):
        e = [r for r in rows if r['episode'] == ep]
        xs = [float(r['x']) for r in e]
        ys = [float(r['y']) for r in e]
        ax.plot(xs, ys, lw=1.2, label=f"ep{ep} laps={e[-1]['laps']}")
        ax.plot(xs[0], ys[0], 'go', ms=7)
        ax.plot(xs[-1], ys[-1], 'rx', ms=8, mew=2)
    ax.legend(loc='upper right', fontsize=8)
    ax.set_title(f"{track['name']} — policy trajectory (o=start, x=end)")
    fig.savefig(out_png, dpi=100, bbox_inches='tight')
    print(f'saved {out_png}: {len(rows)} steps')


if __name__ == '__main__':
    main()
