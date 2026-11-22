"""normalizer.py - Chuẩn hóa văn phạm tuyến tính (bước 5).

Quy tắc 5 bước ở [Chap4] chỉ xét A -> aB và A -> a (một terminal). Slide chưa dạy luật
A -> w với |w| > 1 (ví dụ S -> abS, S -> Aab), nên đây là phần TỰ BỔ SUNG:
tách bằng biến phụ để mỗi luật chỉ sinh đúng một terminal.
[Chap2] Định nghĩa văn phạm tương đương: L(G1) = L(G2) -> việc tách không đổi ngôn ngữ.
"""
from __future__ import annotations

from core.models import Grammar, Production


def normalize_right_linear(g: Grammar) -> tuple[Grammar, list]:
    """Mọi luật sau chuẩn hóa thuộc một trong: A→aB, A→a, A→ε, A→B (luật đơn vị)."""
    log, used, new_vars, out = [], set(g.variables), set(g.variables), []

    def fresh(base: str) -> str:
        k = 1
        while f"{base}_{k}" in used:
            k += 1
        name = f"{base}_{k}"
        used.add(name)
        new_vars.add(name)
        return name

    for p in g.productions:
        A, rhs = p.lhs[0], p.rhs
        B = rhs[-1] if rhs and rhs[-1] in g.variables else None
        w = rhs[:-1] if B else rhs
        if len(w) <= 1:
            out.append(p)
            continue
        cur, made = A, []
        for idx, a in enumerate(w):
            if idx == len(w) - 1:
                new = Production((cur,), (a,) + ((B,) if B else ()))
            else:
                nxt = fresh(A)
                new = Production((cur,), (a, nxt))
                cur = nxt
            out.append(new)
            made.append(str(new))
        log.append(f"Tách '{p}' thành: " + "; ".join(made))
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return Grammar(new_vars, set(g.terminals), uniq, g.start), log


def reverse_grammar(g: Grammar) -> Grammar:
    """Văn phạm tuyến tính TRÁI -> tuyến tính PHẢI sinh ngôn ngữ đảo L^R.
    A -> B w  thành  A -> w^R B ;  A -> w thành A -> w^R.  [Chap2: phép nghịch đảo ω^R]"""
    prods = []
    for p in g.productions:
        rhs = p.rhs
        if rhs and rhs[0] in g.variables:
            prods.append(Production(p.lhs, tuple(reversed(rhs[1:])) + (rhs[0],)))
        else:
            prods.append(Production(p.lhs, tuple(reversed(rhs))))
    return Grammar(set(g.variables), set(g.terminals), prods, g.start)
