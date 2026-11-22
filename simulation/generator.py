"""generator.py - Sinh chuỗi từ văn phạm bằng dẫn xuất (bước 10).

[Chap2] Dẫn xuất trực tiếp ⇒, gián tiếp ⇒*, ngôn ngữ L(G) = {w ∈ T* : S ⇒* w}.
[Chap2 - bài tập 2.3] Thứ tự liệt kê: độ dài tăng dần, cùng độ dài thì theo từ điển.
Độc lập với NFA (không dùng automaton) nên dùng làm "đáp án chuẩn" để đối chứng.
"""
from __future__ import annotations

from collections import deque
from itertools import product

from core.models import Grammar, fmt_symbols


def derive_all(g: Grammar, max_len: int) -> dict:
    """Mọi w ∈ L(G) với |w| <= max_len -> dẫn xuất trái ngắn nhất (list các dạng câu).
    Duyệt BFS trên dạng câu; mở rộng biến ngoài cùng bên trái."""
    start = (g.start,)
    parent, queue, found = {start: None}, deque([start]), {}
    cap = max_len + len(g.variables) + 3
    while queue:
        form = queue.popleft()
        idx = next((i for i, s in enumerate(form) if s in g.variables), None)
        if idx is None:
            w = "".join(form)
            found.setdefault(w, form)
            continue
        for p in g.productions:
            if p.lhs != (form[idx],):
                continue
            new = form[:idx] + p.rhs + form[idx + 1:]
            terms = sum(1 for s in new if s not in g.variables)
            if terms > max_len or len(new) > cap or new in parent:
                continue
            parent[new] = (form, p)
            queue.append(new)
    result = {}
    for w, form in found.items():
        chain, cur = [], form
        while cur is not None:
            chain.append(fmt_symbols(cur))
            cur = parent[cur][0] if parent[cur] else None
        result[w] = list(reversed(chain))
    return result


def language_up_to(g: Grammar, max_len: int) -> list:
    """Các chuỗi của L(G) sắp theo độ dài tăng dần rồi từ điển."""
    return sorted(derive_all(g, max_len), key=lambda s: (len(s), s))


def sigma_star(alphabet, max_len: int):
    """Σ* theo độ dài tăng dần, cùng độ dài thì từ điển. [Chap2: Σ* vô hạn đếm được]"""
    syms = sorted(alphabet)
    for n in range(max_len + 1):
        for tup in product(syms, repeat=n):
            yield "".join(tup)


def format_derivation(forms: list) -> str:
    return " ⇒ ".join(forms)
