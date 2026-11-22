"""fa_ops.py - Các phép toán trên automaton (bước 15, 16, 17).

[Chap4] Định lý 3: hợp, nối, bao đóng Kleene.   Định lý 4: phần bù.   Định lý 5: giao.
[Chap6] Định lý 6.5: "chạy song song" hai máy -> tích trạng thái (ở đây cho hai FA).
Lưu ý: slide chỉ PHÁT BIỂU định lý; các phép dựng dưới đây là thuật toán chuẩn của môn.
"""
from __future__ import annotations

from collections import deque

from core.models import EPS, Automaton
from conversion.nfa_to_dfa import complete_dfa, to_dfa


def rename_states(a: Automaton, prefix: str):
    """Đổi tên trạng thái (start -> prefix0, ...) để ghép hai automaton không trùng tên."""
    order = [a.start] + sorted(a.states - {a.start}, key=str)
    mp = {s: f"{prefix}{i}" for i, s in enumerate(order)}
    res = Automaton({mp[s] for s in a.states}, set(a.alphabet), {}, mp[a.start],
                    {mp[s] for s in a.accepting})
    for (p, x), qs in a.delta.items():
        for q in qs:
            res.add_transition(mp[p], x, mp[q])
    return res, mp


def _merge(a: Automaton, b: Automaton, start: str, accepting: set) -> Automaton:
    res = Automaton(a.states | b.states | {start}, a.alphabet | b.alphabet, {}, start, set(accepting))
    for src in (a, b):
        for (p, x), qs in src.delta.items():
            for q in qs:
                res.add_transition(p, x, q)
    return res


def union(a: Automaton, b: Automaton) -> Automaton:
    """[Chap4 - Định lý 3] Trạng thái đầu mới, ε-chuyển tới đầu của cả hai."""
    a2, _ = rename_states(a, "a")
    b2, _ = rename_states(b, "b")
    res = _merge(a2, b2, "s0", a2.accepting | b2.accepting)
    res.add_transition("s0", EPS, a2.start)
    res.add_transition("s0", EPS, b2.start)
    return res


def concat(a: Automaton, b: Automaton) -> Automaton:
    """[Chap4 - Định lý 3] ε-chuyển từ mọi trạng thái chấp nhận của a tới đầu của b."""
    a2, _ = rename_states(a, "a")
    b2, _ = rename_states(b, "b")
    res = _merge(a2, b2, a2.start, b2.accepting)
    for f in a2.accepting:
        res.add_transition(f, EPS, b2.start)
    return res


def star(a: Automaton) -> Automaton:
    """[Chap4 - Định lý 3] Bao đóng Kleene L*: đầu mới (chấp nhận ε) + ε-chuyển vòng lại."""
    a2, _ = rename_states(a, "a")
    res = a2.copy()
    res.states.add("s0")
    res.start = "s0"
    res.accepting = a2.accepting | {"s0"}
    res.add_transition("s0", EPS, a2.start)
    for f in a2.accepting:
        res.add_transition(f, EPS, a2.start)
    return res


def reverse_automaton(a: Automaton) -> Automaton:
    """Automaton nhận ngôn ngữ đảo L^R (đảo cạnh, đổi vai trò trạng thái đầu/chấp nhận).
    [Chap2: phép nghịch đảo ngôn ngữ]"""
    new_start = "s_rev"
    while new_start in a.states:
        new_start += "'"
    res = Automaton(set(a.states) | {new_start}, set(a.alphabet), {}, new_start, {a.start})
    for (p, x), qs in a.delta.items():
        for q in qs:
            res.add_transition(q, x, p)
    for f in a.accepting:
        res.add_transition(new_start, EPS, f)
    return res


def complement(a: Automaton, alphabet=None) -> Automaton:
    """[Chap4 - Định lý 4; Chap2: L̄ = Σ* − L] DFA ĐẦY ĐỦ (có trạng thái bẫy) rồi đảo F."""
    alpha = set(alphabet or ()) | set(a.alphabet)
    d = complete_dfa(to_dfa(a), alpha)
    d.accepting = d.states - d.accepting
    return d


def intersection(a: Automaton, b: Automaton) -> Automaton:
    """[Chap4 - Định lý 5; Chap6 - Định lý 6.5] Tích trạng thái [p,q], chạy song song.
    Chỉ sinh các cặp đạt tới được từ [p0,q0]."""
    alpha = a.alphabet | b.alphabet
    da, db = complete_dfa(to_dfa(a), alpha), complete_dfa(to_dfa(b), alpha)

    def name(p, q):
        return f"[{p},{q}]"

    start = name(da.start, db.start)
    res = Automaton({start}, set(alpha), {}, start, set())
    queue, seen = deque([(da.start, db.start)]), {(da.start, db.start)}
    while queue:
        p, q = queue.popleft()
        if p in da.accepting and q in db.accepting:
            res.accepting.add(name(p, q))
        for x in sorted(alpha):
            p2, q2 = da.step(p, x), db.step(q, x)
            res.add_transition(name(p, q), x, name(p2, q2))
            if (p2, q2) not in seen:
                seen.add((p2, q2))
                queue.append((p2, q2))
    return res
