"""fa_to_grammar.py - Automaton -> văn phạm chính quy (bước 14).

[Chap4] Định lý 2: tập chính quy được sinh bởi văn phạm tuyến tính trái hoặc phải.
Slide chỉ khẳng định tồn tại; cách dựng dưới đây là thuật toán chuẩn:
  p --a--> q  =>  p → a q ;  p --ε--> q  =>  p → q ;  q chấp nhận  =>  q → ε.
Tuyến tính trái: dựng cho automaton đảo (L^R) rồi đảo vế phải. [Chap2: ω^R, (αβ)^R = β^R α^R]
"""
from __future__ import annotations

import string

from operations.fa_ops import reverse_automaton
from core.models import EPS, Automaton, Grammar, Production


def _names(aut: Automaton) -> dict:
    """Đặt tên biến: trạng thái đầu -> S, còn lại A, B, C... (hoặc Q1, Q2... nếu nhiều)."""
    others = sorted(aut.states - {aut.start}, key=str)
    mp = {aut.start: "S"}
    pool = [c for c in string.ascii_uppercase if c != "S"]
    if len(others) <= len(pool):
        mp.update(dict(zip(others, pool)))
    else:
        mp.update({s: f"Q{i}" for i, s in enumerate(others, 1)})
    return mp


def fa_to_right_linear(aut: Automaton) -> Grammar:
    mp = _names(aut)
    prods = []
    for (p, a), qs in aut.delta.items():
        for q in qs:
            prods.append(Production((mp[p],), (mp[q],) if a == EPS else (a, mp[q])))
    for f in aut.accepting:
        prods.append(Production((mp[f],), ()))
    prods.sort(key=lambda r: (r.lhs[0] != "S", r.lhs[0], r.rhs))
    return Grammar(set(mp.values()), set(aut.alphabet), prods, "S")


def fa_to_left_linear(aut: Automaton) -> Grammar:
    g = fa_to_right_linear(reverse_automaton(aut))      # sinh L^R, tuyến tính phải
    prods = []
    for p in g.productions:
        rhs = p.rhs
        if rhs and rhs[-1] in g.variables:
            prods.append(Production(p.lhs, (rhs[-1],) + tuple(reversed(rhs[:-1]))))
        else:
            prods.append(Production(p.lhs, tuple(reversed(rhs))))
    return Grammar(set(g.variables), set(g.terminals), prods, g.start)
