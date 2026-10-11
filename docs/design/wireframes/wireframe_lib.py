"""Shared low-fidelity wireframe helpers — greyscale, boxes + labels only.
No color, no branding, no typography decisions: that's explicitly out of
scope for P0-FE-001 (final visual design is a later pass)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

INK = "#2b2b2b"
LINE = "#8a8a8a"
FILL = "#f2f2f2"
FILL2 = "#e6e6e6"

def new_canvas(w=12.8, h=9.0, title="", subtitle="", device="Desktop"):
    fig, ax = plt.subplots(figsize=(w/1.6, h/1.6))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.invert_yaxis()
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), w, h, fc="white", ec=INK, lw=1.6))
    ax.text(0.25, -0.75, title, fontsize=13, fontweight="bold", color=INK)
    if subtitle:
        ax.text(0.25, -0.28, subtitle, fontsize=9.5, color="#C0392B", fontweight="bold")
        ax.text(w-0.25, -0.28, device, fontsize=9, color=LINE, ha="right")
    else:
        ax.text(w-0.25, -0.75, device, fontsize=9, color=LINE, ha="right")
    return fig, ax, w, h

def box(ax, x, y, w, h, label="", fill=FILL, dashed=False, fs=9, align="center", note=None, safety=False):
    ls = (0,(4,3)) if dashed else "solid"
    ec = "#C0392B" if safety else LINE
    lw = 1.6 if safety else 1.1
    ax.add_patch(Rectangle((x, y), w, h, fc=fill, ec=ec, lw=lw, linestyle=ls))
    if label:
        ha = {"center":"center","left":"left"}[align]
        tx = x + w/2 if align=="center" else x+0.15
        ax.text(tx, y+h/2, label, fontsize=fs, color=INK, ha=ha, va="center", wrap=True)
    if note:
        ax.text(x+w/2, y+h+0.22, note, fontsize=7.6, color="#C0392B" if safety else LINE,
                 ha="center", style="italic", fontweight="bold" if safety else "normal")

def navbar(ax, w, items, active=0):
    box(ax, 0, 0, w, 0.75, fill=FILL2)
    usable = w - 1.3  # leave room for avatar circle
    slot = usable / len(items)
    for i, it in enumerate(items):
        wgt = "bold" if i==active else "normal"
        cx = 0.3 + slot*i + slot/2 - 0.3
        ax.text(cx, 0.375, it, fontsize=9.5, fontweight=wgt, color=INK, va="center", ha="left")
    c = Circle((w-0.55, 0.375), 0.26, fc="white", ec=LINE, lw=1.1)
    ax.add_patch(c)

def input_field(ax, x, y, w, h, label):
    box(ax, x, y, w, h, label=label, fill="white", align="left", fs=8.8)

def button(ax, x, y, w, h, label, filled=True):
    box(ax, x, y, w, h, label=label, fill="#dadada" if filled else "white", fs=9.2)

def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"wireframes/{name}.png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
