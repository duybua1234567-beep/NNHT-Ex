"""fa_draw.py - Vẽ sơ đồ trạng thái của automaton lên Tkinter Canvas (bước 7: in/vẽ NFA).

[Chap1] FA là đồ thị có hướng G = (V, E): đỉnh = trạng thái, cạnh có nhãn = phép chuyển.
[Chap4] Hình FA trong ví dụ chuyển VPCQ: vòng tròn, trạng thái kết là vòng tròn đôi, mũi tên vào trạng thái đầu.
Phần tính toán bố cục (compute_layout, edge_shapes) là hàm thuần túy, không cần Tkinter nên kiểm thử được.
"""
from __future__ import annotations

import math
from collections import deque

from core.models import Automaton


def node_radius(aut: Automaton) -> int:
    longest = max((len(s) for s in aut.states), default=1)
    return int(min(46, max(24, 4 + longest * 3.4)))


def compute_layout(aut: Automaton, r: int | None = None, min_w: int = 560, min_h: int = 300):
    """Bố cục theo tầng: tầng = khoảng cách BFS từ trạng thái đầu. Trả về (vị trí, (rộng, cao))."""
    r = r or node_radius(aut)
    adj = {s: set() for s in aut.states}
    for (p, _), qs in aut.delta.items():
        adj[p] |= qs
    layer, queue = {aut.start: 0}, deque([aut.start])
    while queue:
        s = queue.popleft()
        for t in sorted(adj[s], key=str):
            if t not in layer:
                layer[t] = layer[s] + 1
                queue.append(t)
    extra = max(layer.values()) + 1
    for s in sorted(aut.states - set(layer), key=str):   # trạng thái không đạt tới được
        layer[s] = extra
    layers = {}
    for s, l in layer.items():
        layers.setdefault(l, []).append(s)
    margin, dx, dy = r + 60, 2 * r + 80, 2 * r + 40
    max_count = max(len(v) for v in layers.values())
    height = max(min_h, 2 * margin + (max_count - 1) * dy)
    width = max(min_w, 2 * margin + (len(layers) - 1) * dx)
    pos = {}
    for l, states in layers.items():
        states.sort(key=str)
        for i, s in enumerate(states):
            pos[s] = (margin + l * dx, height / 2 + (i - (len(states) - 1) / 2) * dy)
    return pos, (width, height)


def _unit(dx: float, dy: float):
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


def edge_shapes(aut: Automaton, pos: dict, r: int) -> list:
    """Mỗi cạnh (đã gộp các nhãn cùng (p,q)) -> dict(points, smooth, label, label_xy)."""
    labels = {}
    for p, a, q in aut.transitions():
        labels.setdefault((p, q), []).append(a)
    shapes = []
    for (p, q), labs in labels.items():
        label = ",".join(sorted(labs))
        x1, y1 = pos[p]
        x2, y2 = pos[q]
        if p == q:                                   # vòng lặp trên đỉnh
            pts = [(x1 - 14, y1 - r + 2), (x1 - 24, y1 - r - 36), (x1 + 24, y1 - r - 36), (x1 + 14, y1 - r + 2)]
            shapes.append(dict(points=pts, smooth=True, label=label, label_xy=(x1, y1 - r - 46)))
            continue
        ux, uy = _unit(x2 - x1, y2 - y1)
        nx, ny = -uy, ux
        if (q, p) in labels:                         # có cạnh ngược lại: vẽ cong để không đè nhau
            cx, cy = (x1 + x2) / 2 + nx * 34, (y1 + y2) / 2 + ny * 34
            sx, sy = _unit(cx - x1, cy - y1)
            ex, ey = _unit(cx - x2, cy - y2)
            pts = [(x1 + sx * r, y1 + sy * r), (cx, cy), (x2 + ex * r, y2 + ey * r)]
            shapes.append(dict(points=pts, smooth=True, label=label, label_xy=(cx + nx * 11, cy + ny * 11)))
        else:
            pts = [(x1 + ux * r, y1 + uy * r), (x2 - ux * r, y2 - uy * r)]
            shapes.append(dict(points=pts, smooth=False, label=label,
                               label_xy=((x1 + x2) / 2 + nx * 12, (y1 + y2) / 2 + ny * 12)))
    return shapes


# --------------------------------------------------------------- widget
def make_view_class():
    """Tạo lớp AutomatonView (chỉ import tkinter khi thật sự cần, để phần logic chạy được không có Tk)."""
    import tkinter as tk
    from tkinter import ttk

    class AutomatonView(ttk.Frame):
        """Canvas có thanh cuộn; show(aut, highlight) vẽ lại sơ đồ."""

        def __init__(self, master, height: int = 300):
            super().__init__(master)
            self.canvas = tk.Canvas(self, bg="white", height=height, highlightthickness=1,
                                    highlightbackground="#b0b0b0")
            hs = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            vs = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.canvas.configure(xscrollcommand=hs.set, yscrollcommand=vs.set)
            self.canvas.grid(row=0, column=0, sticky="nsew")
            vs.grid(row=0, column=1, sticky="ns")
            hs.grid(row=1, column=0, sticky="ew")
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)

        def show(self, aut, highlight=(), caption: str = ""):
            c = self.canvas
            c.delete("all")
            if aut is None:
                c.create_text(20, 20, anchor="nw", text="(chưa có automaton)", fill="#888")
                return
            r = node_radius(aut)
            pos, (w, h) = compute_layout(aut, r)
            c.configure(scrollregion=(0, 0, w, h))
            for sh in edge_shapes(aut, pos, r):
                flat = [v for pt in sh["points"] for v in pt]
                c.create_line(*flat, smooth=sh["smooth"], arrow="last", fill="#444444", width=1.6)
                c.create_text(*sh["label_xy"], text=sh["label"], fill="#0b4fa8", font=("TkDefaultFont", 11, "bold"))
            for s, (x, y) in pos.items():
                fill = "#ffcf70" if s in highlight else "#eef4ff"
                c.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="#222222", width=2)
                if s in aut.accepting:
                    c.create_oval(x - r + 5, y - r + 5, x + r - 5, y + r - 5, outline="#222222", width=2)
                c.create_text(x, y, text=s, font=("TkDefaultFont", 9 if len(s) > 5 else 11))
            sx, sy = pos[aut.start]
            c.create_line(sx - r - 40, sy, sx - r, sy, arrow="last", width=2, fill="#c0392b")
            if caption:
                c.create_text(8, 6, anchor="nw", text=caption, fill="#555555")

    return AutomatonView
