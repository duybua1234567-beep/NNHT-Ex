"""simulator.py - Mô phỏng chuỗi đầu vào trên automaton (bước 8, 9).

[Chap2]   Chuỗi thuộc Σ*, kiểm tra ký hiệu hợp lệ.
[Chap2_1] Cấu hình (trạng thái, vị trí đọc), move, accepter yes/no, automata không đơn định.
[Chap6]   Cách in từng bước mượn ý tưởng hình thái (ID) và quan hệ ⊢; NPDA "đoán đúng":
          chuỗi được chấp nhận nếu TỒN TẠI một đường đi dẫn tới trạng thái chấp nhận.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from core.models import EPS, Automaton


@dataclass
class SimResult:
    accepted: bool
    steps: list          # (số ký tự đã đọc, đã đọc, còn lại, tập trạng thái)
    path: list | None    # một đường đi chấp nhận: [(p, nhãn, q), ...]


def validate_input(aut: Automaton, w: str) -> None:
    bad = sorted({c for c in w if c not in aut.alphabet})
    if bad:
        raise ValueError(f"Chuỗi chứa ký hiệu không thuộc Σ={sorted(aut.alphabet)}: {bad}")


def accepts(aut: Automaton, w: str) -> bool:
    """Nhanh, không in bước. Ký hiệu lạ => bị từ chối."""
    cur = aut.eps_closure({aut.start})
    for c in w:
        cur = aut.eps_closure(aut.move(cur, c))
        if not cur:
            return False
    return bool(cur & aut.accepting)


def find_accepting_path(aut: Automaton, w: str):
    """Một đường đi chấp nhận (BFS trên cặp (trạng thái, vị trí)) hoặc None."""
    start = (aut.start, 0)
    parent, queue = {start: None}, deque([start])
    while queue:
        q, i = queue.popleft()
        if i == len(w) and q in aut.accepting:
            path, cur = [], (q, i)
            while parent[cur] is not None:
                prev, label = parent[cur]
                path.append((prev[0], label, cur[0]))
                cur = prev
            return list(reversed(path))
        for r in aut.delta.get((q, EPS), ()):
            if (r, i) not in parent:
                parent[(r, i)] = ((q, i), EPS)
                queue.append((r, i))
        if i < len(w):
            for r in aut.delta.get((q, w[i]), ()):
                if (r, i + 1) not in parent:
                    parent[(r, i + 1)] = ((q, i), w[i])
                    queue.append((r, i + 1))
    return None


def simulate(aut: Automaton, w: str) -> SimResult:
    validate_input(aut, w)
    cur = aut.eps_closure({aut.start})
    steps = [(0, "", w, sorted(cur, key=str))]
    for i, c in enumerate(w, 1):
        cur = aut.eps_closure(aut.move(cur, c))
        steps.append((i, w[:i], w[i:], sorted(cur, key=str)))
    accepted = bool(cur & aut.accepting)
    return SimResult(accepted, steps, find_accepting_path(aut, w) if accepted else None)


def format_trace(res: SimResult, w: str) -> str:
    lines = [f"Chuỗi nhập: {w if w else EPS}  (độ dài {len(w)})"]
    for n, read, rest, states in res.steps:
        lines.append(f"  đã đọc {read or EPS!s:<8} còn lại {rest or EPS!s:<8} "
                     f"tập trạng thái = {{{', '.join(states) if states else ''}}}")
    if res.path is not None:
        lines.append("  Một đường đi chấp nhận: "
                     + (" ".join(f"{p} -{a}-> {q}" for p, a, q in res.path) if res.path else "(không cần chuyển)"))
    lines.append("  => " + ("CHẤP NHẬN (yes)" if res.accepted else "TỪ CHỐI (no)"))
    return "\n".join(lines)
