"""pda_demo.py - Mô phỏng ôtômát đẩy xuống (PDA): giải thích vì sao CFG vượt ngoài FA (bước 22).

[Chap6] Định nghĩa PDA M(Q, Σ, Γ, δ, q0, Z0, F); hình thái (ID) và ⊢; chấp nhận bằng Stack rỗng;
        Thí dụ 6.1 (w c w^R, đơn định), Thí dụ 6.3 (w w^R, KHÔNG đơn định), điều kiện DPDA.
[Chap2] Phân cấp Chomsky: L3 ⊂ L2 (a^n b^n là phi ngữ cảnh nhưng không chính quy).
Quy ước như slide: ký hiệu bên TRÁI nhất của chuỗi Stack là ĐỈNH Stack.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from core.models import EPS


@dataclass
class PDA:
    states: set
    input_alphabet: set
    stack_alphabet: set
    delta: dict          # (q, a hoặc EPS, Z) -> set các (p, γ: tuple)
    start: str
    z0: str
    accepting: set       # rỗng nếu chấp nhận bằng Stack rỗng


def make_pda(rules, start, z0) -> PDA:
    """rules: [(q, a, Z, p, γ)]; a == '' nghĩa là ε; γ == '' nghĩa là ε (pop)."""
    delta, states, ins, stk = {}, {start}, set(), {z0}
    for q, a, Z, p, gamma in rules:
        a = a or EPS
        delta.setdefault((q, a, Z), set()).add((p, tuple(gamma)))
        states |= {q, p}
        stk |= {Z} | set(gamma)
        if a != EPS:
            ins.add(a)
    return PDA(states, ins, stk, delta, start, z0, set())


def is_deterministic(pda: PDA) -> bool:
    """[Chap6 - DPDA] (1) δ(q,ε,Z) ≠ ∅ => δ(q,a,Z) = ∅ ∀a;  (2) mỗi δ(q,a,Z) có <= 1 phần tử."""
    for (q, a, Z), targets in pda.delta.items():
        if len(targets) > 1:
            return False
        if a == EPS and any(pda.delta.get((q, b, Z)) for b in pda.input_alphabet):
            return False
    return True


def pda_accepts(pda: PDA, w: str, max_extra_stack: int = 3):
    """Chấp nhận bằng Stack rỗng: (q0,w,Z0) ⊢* (p,ε,ε). Không đơn định: tồn tại một dãy chọn đúng.
    Trả về (bool, danh sách ID của một dãy chấp nhận)."""
    start = (pda.start, 0, (pda.z0,))
    parent, queue = {start: None}, deque([start])
    while queue:
        cfg = queue.popleft()
        q, i, stack = cfg
        if i == len(w) and not stack:
            ids, cur = [], cfg
            while cur is not None:
                ids.append(cur)
                cur = parent[cur]
            return True, [(s, w[k:], "".join(st) or EPS) for s, k, st in reversed(ids)]
        if not stack:
            continue
        top = stack[0]
        for a in ([EPS] + ([w[i]] if i < len(w) else [])):
            for p, gamma in pda.delta.get((q, a, top), ()):
                nxt = (p, i + (a != EPS), gamma + stack[1:])
                if len(nxt[2]) <= len(w) + max_extra_stack and nxt not in parent:
                    parent[nxt] = cfg
                    queue.append(nxt)
    return False, None


def format_ids(ids: list) -> str:
    return "\n".join(("   " if k == 0 else " ⊢ ") + f"({q}, {rest or EPS}, {st})" for k, (q, rest, st) in enumerate(ids))


# ---- Các PDA mẫu (Chap6)
def pda_wcwr() -> PDA:
    """[Chap6 - Thí dụ 6.1] {w c w^R | w ∈ (0+1)*}, Stack rỗng, ĐƠN ĐỊNH (12 luật)."""
    r = []
    for q_sym, g in (("R", "R"), ("B", "B"), ("Y", "Y")):
        r.append(("q1", "0", q_sym, "q1", "B" + g))
        r.append(("q1", "1", q_sym, "q1", "Y" + g))
        r.append(("q1", "c", q_sym, "q2", g))
    r += [("q2", "0", "B", "q2", ""), ("q2", "1", "Y", "q2", ""), ("q2", "", "R", "q2", "")]
    return make_pda(r, "q1", "R")


def pda_wwr() -> PDA:
    """[Chap6 - Thí dụ 6.3] {w w^R | w ∈ (0+1)*}, Stack rỗng, KHÔNG đơn định (10 luật)."""
    r = [("q1", "0", "R", "q1", "BR"), ("q1", "1", "R", "q1", "YR"),
         ("q1", "0", "B", "q1", "BB"), ("q1", "0", "B", "q2", ""),
         ("q1", "0", "Y", "q1", "BY"), ("q1", "1", "B", "q1", "YB"),
         ("q1", "1", "Y", "q1", "YY"), ("q1", "1", "Y", "q2", ""),
         ("q2", "0", "B", "q2", ""), ("q2", "1", "Y", "q2", ""),
         ("q1", "", "R", "q2", ""), ("q2", "", "R", "q2", "")]
    return make_pda(r, "q1", "R")


def pda_anbn() -> PDA:
    """{a^n b^n | n >= 1}: tự thiết kế theo mẫu Thí dụ 6.1 (đẩy A khi đọc a, bỏ A khi đọc b)."""
    r = [("q1", "a", "R", "q1", "AR"), ("q1", "a", "A", "q1", "AA"),
         ("q1", "b", "A", "q2", ""), ("q2", "b", "A", "q2", ""), ("q2", "", "R", "q2", "")]
    return make_pda(r, "q1", "R")


PDA_SAMPLES = {
    "wcwR": (pda_wcwr, lambda s: bool(s.count("c") == 1) and s.split("c")[0] == s.split("c")[1][::-1]
             and set(s) <= set("01c")),
    "wwR": (pda_wwr, lambda s: set(s) <= set("01") and len(s) % 2 == 0 and s == s[::-1]),
    "anbn": (pda_anbn, lambda s: len(s) >= 2 and len(s) % 2 == 0 and s == "a" * (len(s) // 2) + "b" * (len(s) // 2)),
}
