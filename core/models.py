"""models.py - Kiểu dữ liệu dùng chung cho toàn bộ đồ án.

[Chap2]   Văn phạm cấu trúc G = (V, T, P, S): định nghĩa 1, quy ước ký hiệu.
[Chap4]   Automaton M = (Q, Σ, δ, q0, F) (slide "Quy tắc chuyển VPCQ thành FA").
[Chap2_1] Hàm chuyển δ đa trị => automata không đơn định; đơn trị => đơn định.
[Chap1]   ε-bao đóng dùng ý tưởng bao đóng phản xạ bắc cầu R*; sơ đồ FA là đồ thị có hướng.
"""
from __future__ import annotations

from dataclasses import dataclass

EPS = "ε"


def fmt_symbols(symbols) -> str:
    """Chuỗi ký hiệu -> văn bản; chuỗi rỗng in là ε."""
    if not symbols:
        return EPS
    if all(len(s) == 1 for s in symbols):
        return "".join(symbols)
    return " ".join(symbols)


# ---------------------------------------------------------------- Grammar
@dataclass(frozen=True)
class Production:
    """Luật sinh α -> β. [Chap2: P gồm các luật dạng α -> β, α chứa ít nhất một biến]"""
    lhs: tuple
    rhs: tuple

    def __str__(self) -> str:
        return f"{fmt_symbols(self.lhs)} → {fmt_symbols(self.rhs)}"


@dataclass
class Grammar:
    """G = (V, T, P, S). [Chap2 - Định nghĩa 1]"""
    variables: set
    terminals: set
    productions: list
    start: str

    def rules_of(self, var: str) -> list:
        return [p for p in self.productions if p.lhs == (var,)]

    def to_text(self) -> str:
        order, groups = [], {}
        for p in self.productions:
            if p.lhs not in groups:
                groups[p.lhs] = []
                order.append(p.lhs)
            groups[p.lhs].append(fmt_symbols(p.rhs))
        return "\n".join(f"{fmt_symbols(l)} → {' | '.join(groups[l])}" for l in order)


# -------------------------------------------------------------- Automaton
@dataclass
class Automaton:
    """M = (Q, Σ, δ, q0, F).  δ: (trạng thái, ký hiệu hoặc ε) -> TẬP trạng thái.
    DFA chỉ là trường hợp đặc biệt (không có ε, mỗi tập có <= 1 phần tử)."""
    states: set
    alphabet: set
    delta: dict
    start: str
    accepting: set

    # ---- xây dựng
    def add_transition(self, p: str, a: str, q: str) -> None:
        self.delta.setdefault((p, a), set()).add(q)
        self.states.add(p)
        self.states.add(q)
        if a != EPS:
            self.alphabet.add(a)

    def copy(self) -> "Automaton":
        return Automaton(set(self.states), set(self.alphabet),
                         {k: set(v) for k, v in self.delta.items()},
                         self.start, set(self.accepting))

    # ---- hàm chuyển
    def step(self, q: str, a: str):
        """Dùng cho DFA: trả về trạng thái kế hoặc None."""
        t = self.delta.get((q, a))
        return next(iter(t)) if t else None

    def move(self, S, a: str) -> set:
        out = set()
        for q in S:
            out |= self.delta.get((q, a), set())
        return out

    def eps_closure(self, S) -> set:
        """ε-bao đóng. [Chap1 - bao đóng phản xạ bắc cầu R*]"""
        closure, stack = set(S), list(S)
        while stack:
            q = stack.pop()
            for r in self.delta.get((q, EPS), ()):
                if r not in closure:
                    closure.add(r)
                    stack.append(r)
        return closure

    def has_epsilon(self) -> bool:
        return any(a == EPS for (_, a) in self.delta)

    def is_deterministic(self) -> bool:
        """[Chap2_1 - hàm chuyển đơn trị]"""
        return (not self.has_epsilon()) and all(len(v) <= 1 for v in self.delta.values())

    # ---- hiển thị
    def ordered_states(self) -> list:
        return [self.start] + sorted(self.states - {self.start}, key=str)

    def transitions(self) -> list:
        return sorted(((p, a, q) for (p, a), qs in self.delta.items() for q in qs),
                      key=lambda t: (str(t[0]), t[1], str(t[2])))

    def describe(self) -> str:
        lines = [f"Q  = {{{', '.join(self.ordered_states())}}}",
                 f"Σ  = {{{', '.join(sorted(self.alphabet))}}}",
                 f"q0 = {self.start}",
                 f"F  = {{{', '.join(sorted(self.accepting, key=str))}}}",
                 "δ:"]
        for p, a, q in self.transitions():
            lines.append(f"   {p} --{a}--> {q}")
        return "\n".join(lines)

    def to_table(self) -> str:
        syms = sorted(self.alphabet) + ([EPS] if self.has_epsilon() else [])

        def label(s):
            return ("→" if s == self.start else " ") + ("*" if s in self.accepting else " ") + s

        rows = [["δ"] + syms]
        for s in self.ordered_states():
            row = [label(s)]
            for a in syms:
                t = self.delta.get((s, a))
                row.append("-" if not t else (next(iter(t)) if len(t) == 1
                                              else "{" + ",".join(sorted(t, key=str)) + "}"))
            rows.append(row)
        widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
        out = [" | ".join(c.ljust(w) for c, w in zip(r, widths)) for r in rows]
        out.insert(1, "-+-".join("-" * w for w in widths))
        return "\n".join(out) + "\n(→ trạng thái đầu, * trạng thái chấp nhận)"

    def to_dot(self, name: str = "FA") -> str:
        """Xuất Graphviz DOT để vẽ sơ đồ. [Chap1 - đồ thị có hướng G=(V,E)]"""
        lines = [f"digraph {name} {{", "  rankdir=LR;", '  __start [shape=point];']
        for s in self.ordered_states():
            shape = "doublecircle" if s in self.accepting else "circle"
            lines.append(f'  "{s}" [shape={shape}];')
        lines.append(f'  __start -> "{self.start}";')
        merged = {}
        for p, a, q in self.transitions():
            merged.setdefault((p, q), []).append(a)
        for (p, q), labs in merged.items():
            lines.append(f'  "{p}" -> "{q}" [label="{",".join(sorted(labs))}"];')
        lines.append("}")
        return "\n".join(lines)
