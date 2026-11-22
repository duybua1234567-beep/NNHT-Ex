"""analysis.py - Phân tích ngôn ngữ của automaton: rỗng/vô hạn, tương đương (bước 18, 19).

[Chap4] Định lý 6: L(M) (M có n trạng thái) KHÔNG RỖNG <=> chấp nhận chuỗi độ dài < n;
        VÔ HẠN <=> chấp nhận chuỗi độ dài l với n <= l < 2n.
[Chap4] Định lý 7: có giải thuật xác định hai automaton tương đương.
[Chap1] Đồ thị có hướng: đường đi, chu trình (cách làm thứ hai, nhanh hơn).
Cả hai cách được cài để đối chứng lẫn nhau.
"""
from __future__ import annotations

from collections import deque

from core.models import Automaton
from conversion.nfa_to_dfa import complete_dfa, to_dfa


def _successors(aut: Automaton) -> dict:
    adj = {s: set() for s in aut.states}
    for (p, _), qs in aut.delta.items():
        adj[p] |= qs
    return adj


def reachable(aut: Automaton) -> set:
    adj, seen, queue = _successors(aut), {aut.start}, deque([aut.start])
    while queue:
        for r in adj[queue.popleft()]:
            if r not in seen:
                seen.add(r)
                queue.append(r)
    return seen


def coreachable(aut: Automaton) -> set:
    radj = {s: set() for s in aut.states}
    for (p, _), qs in aut.delta.items():
        for q in qs:
            radj[q].add(p)
    seen, queue = set(aut.accepting), deque(aut.accepting)
    while queue:
        for r in radj[queue.popleft()]:
            if r not in seen:
                seen.add(r)
                queue.append(r)
    return seen


# ---------- cách 1: theo đồ thị
def is_empty_graph(aut: Automaton) -> bool:
    return not (reachable(aut) & aut.accepting)


def is_infinite_graph(aut: Automaton) -> bool:
    """Vô hạn <=> trong DFA đã cắt tỉa (đạt tới từ đầu và còn đến được trạng thái chấp nhận) có chu trình."""
    d = to_dfa(aut)
    keep = reachable(d) & coreachable(d)
    adj = {s: [q for a in d.alphabet for q in d.delta.get((s, a), ())] for s in keep}
    color = {s: 0 for s in keep}
    for root in keep:
        if color[root]:
            continue
        color[root] = 1
        stack = [(root, iter(adj[root]))]
        while stack:
            node, it = stack[-1]
            for nxt in it:
                if nxt not in keep:
                    continue
                if color[nxt] == 1:
                    return True
                if color[nxt] == 0:
                    color[nxt] = 1
                    stack.append((nxt, iter(adj[nxt])))
                    break
            else:
                color[node] = 2
                stack.pop()
    return False


# ---------- cách 2: theo Định lý 6
def _layers(d: Automaton, upto: int) -> list:
    """layers[l] = tập trạng thái đạt được sau ĐÚNG l ký hiệu (từ mọi chuỗi độ dài l)."""
    cur, out = {d.start}, [{d.start}]
    for _ in range(upto):
        nxt = set()
        for a in d.alphabet:
            nxt |= d.move(cur, a)
        cur = nxt
        out.append(cur)
    return out


def is_empty_theorem(aut: Automaton) -> bool:
    """Không rỗng <=> có chuỗi chấp nhận độ dài l < n."""
    d = to_dfa(aut)
    n = len(d.states)
    layers = _layers(d, n)
    return not any(layers[l] & d.accepting for l in range(n))


def is_infinite_theorem(aut: Automaton) -> bool:
    """Vô hạn <=> có chuỗi chấp nhận độ dài l với n <= l < 2n."""
    d = to_dfa(aut)
    n = len(d.states)
    layers = _layers(d, 2 * n)
    return any(layers[l] & d.accepting for l in range(n, 2 * n))


# ---------- tương đương
def equivalent(a: Automaton, b: Automaton):
    """[Chap4 - Định lý 7] Duyệt tích trạng thái của hai DFA đầy đủ từ [p0,q0];
    gặp cặp mà đúng một bên chấp nhận => không tương đương, trả về chuỗi phản chứng NGẮN NHẤT.
    Trả về (True, None, None) hoặc (False, chuỗi, 'a'/'b' là bên chấp nhận chuỗi đó)."""
    alpha = a.alphabet | b.alphabet
    da, db = complete_dfa(to_dfa(a), alpha), complete_dfa(to_dfa(b), alpha)
    start = (da.start, db.start)
    parent, queue = {start: None}, deque([start])
    while queue:
        p, q = queue.popleft()
        pa, qa = p in da.accepting, q in db.accepting
        if pa != qa:
            word, cur = [], (p, q)
            while parent[cur] is not None:
                cur, sym = parent[cur]
                word.append(sym)
            return False, "".join(reversed(word)), ("a" if pa else "b")
        for x in sorted(alpha):
            nxt = (da.step(p, x), db.step(q, x))
            if nxt not in parent:
                parent[nxt] = ((p, q), x)
                queue.append(nxt)
    return True, None, None
