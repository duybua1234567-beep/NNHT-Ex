"""nfa_to_dfa.py - Chuyển NFA -> DFA (bước 13).

[Chap3_1 / otomat-huu-han] Xây dựng tập con (subset construction) - phần này chưa đối chiếu
                          trực tiếp với slide, đây là thuật toán chuẩn.
[Chap2_1] Đơn định vs không đơn định.   [Chap1] Tập lũy thừa 2^A: mỗi trạng thái DFA là một tập con của Q.
"""
from __future__ import annotations

from collections import deque

from core.models import Automaton


def subset_name(S) -> str:
    return "{" + ",".join(sorted(S, key=str)) + "}"


def to_dfa(nfa: Automaton) -> Automaton:
    """DFA có thể THIẾU chuyển (tập rỗng ∅ bị bỏ qua). Chỉ sinh tập đạt tới được."""
    if nfa.is_deterministic():
        return nfa.copy()
    start_set = frozenset(nfa.eps_closure({nfa.start}))
    start_name = subset_name(start_set)
    dfa = Automaton({start_name}, set(nfa.alphabet), {}, start_name, set())
    queue, seen = deque([start_set]), {start_set}
    while queue:
        S = queue.popleft()
        name = subset_name(S)
        if S & nfa.accepting:
            dfa.accepting.add(name)
        for a in sorted(nfa.alphabet):
            T = frozenset(nfa.eps_closure(nfa.move(S, a)))
            if not T:
                continue
            dfa.add_transition(name, a, subset_name(T))
            if T not in seen:
                seen.add(T)
                queue.append(T)
    return dfa


def complete_dfa(dfa: Automaton, alphabet=None) -> Automaton:
    """Thêm trạng thái bẫy để DFA đầy đủ (cần cho phép bù, giao, kiểm tra tương đương)."""
    alpha = set(dfa.alphabet) | set(alphabet or ())
    res = dfa.copy()
    res.alphabet = alpha
    trap = "∅"
    while trap in res.states:
        trap += "'"
    need = False
    for s in list(res.states):
        for a in alpha:
            if res.step(s, a) is None:
                res.add_transition(s, a, trap)
                need = True
    if need:
        for a in alpha:
            res.add_transition(trap, a, trap)
    return res
