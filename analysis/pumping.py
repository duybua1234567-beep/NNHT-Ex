"""pumping.py - Thử bơm trên automaton cụ thể (bước 20).

[Chap4] Bổ đề Bơm, dạng CHUẨN: L chính quy => ∃n: mọi z ∈ L, |z| >= n, viết được z = xyw
        với |xy| <= n, |y| >= 1 và ∀i >= 0: x y^i w ∈ L.   (Slide ghi |z| <= n, |xy| < n: nhầm so với chuẩn.)
Ý tưởng: DFA có n trạng thái, đọc chuỗi dài >= n thì trong n+1 vị trí đầu phải có trạng thái lặp.
Đây là PHÉP THỬ XÁC NHẬN trên một DFA cụ thể, không phải chứng minh.
"""
from __future__ import annotations

from analysis.language_analysis import coreachable
from core.models import Automaton
from conversion.nfa_to_dfa import to_dfa
from simulation.simulator import accepts


def accepted_strings(d: Automaton, length: int, limit: int = 3) -> list:
    """Vài chuỗi được chấp nhận có độ dài đúng `length` (DFS, cắt tỉa trạng thái chết)."""
    co, out = coreachable(d), []

    def dfs(q, prefix):
        if len(out) >= limit:
            return
        if len(prefix) == length:
            if q in d.accepting:
                out.append("".join(prefix))
            return
        for a in sorted(d.alphabet):
            r = d.step(q, a)
            if r is not None and r in co:
                dfs(r, prefix + [a])

    dfs(d.start, [])
    return out


def decompose(d: Automaton, z: str):
    """Tìm cặp vị trí đầu tiên có trạng thái lặp => (x, y, w)."""
    n = len(d.states)
    q, states = d.start, [d.start]
    for c in z:
        q = d.step(q, c)
        states.append(q)
    seen = {}
    for j in range(min(len(z), n) + 1):
        if states[j] in seen:
            i = seen[states[j]]
            return z[:i], z[i:j], z[j:], states[j]
        seen[states[j]] = j
    return None


def pump_test(aut: Automaton, z: str, max_i: int = 3) -> dict:
    d = to_dfa(aut)
    n = len(d.states)
    parts = decompose(d, z)
    if parts is None:
        return {"n": n, "z": z, "ok": False, "reason": "chuỗi ngắn hơn n hoặc không chấp nhận"}
    x, y, w, loop_state = parts
    results = {i: accepts(d, x + y * i + w) for i in range(max_i + 1)}
    ok = all(results.values()) and len(x + y) <= n and len(y) >= 1
    return {"n": n, "z": z, "x": x, "y": y, "w": w, "loop_state": loop_state,
            "results": results, "ok": ok, "reason": ""}


def pump_report(aut: Automaton, max_i: int = 3, per_length: int = 2) -> tuple[list, str]:
    """Thử bơm trên vài chuỗi độ dài n, n+1, n+2. Trả về (danh sách kết quả, ghi chú)."""
    d = to_dfa(aut)
    n = len(d.states)
    reports = []
    for length in (n, n + 1, n + 2):
        for z in accepted_strings(d, length, per_length):
            reports.append(pump_test(d, z, max_i))
    note = "" if reports else (f"Không có chuỗi chấp nhận độ dài >= n={n} "
                               f"(ngôn ngữ hữu hạn hoặc chuỗi dài nhất ngắn hơn n) - không có gì để bơm")
    return reports, note


def format_pump(r: dict) -> str:
    if "x" not in r:
        return f"  z={r['z']!r}: {r['reason']}"
    show = lambda s: s if s else "ε"
    lines = [f"  n={r['n']}, z={r['z']}  =>  x={show(r['x'])}, y={show(r['y'])}, w={show(r['w'])}  "
             f"(|xy|={len(r['x'] + r['y'])} <= n, |y|={len(r['y'])} >= 1, lặp ở trạng thái {r['loop_state']})"]
    for i, acc in r["results"].items():
        lines.append(f"     i={i}: {show(r['x'] + r['y'] * i + r['w'])}  -> {'∈ L' if acc else '∉ L'}")
    return "\n".join(lines)
