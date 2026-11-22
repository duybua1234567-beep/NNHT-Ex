"""grammar_to_nfa.py - Văn phạm chính quy -> NFA (bước 6, 7). ĐÂY LÀ LÕI CỦA ĐỒ ÁN.

[Chap4] Slide "Quy tắc chuyển VPCQ thành FA" (5 bước) và Định lý 1 (VPCQ => ngôn ngữ chính quy).
[Chap2] Phân cấp Chomsky: từ chối văn phạm không phải loại 3.
Tuyến tính trái: slide không dạy, tự bổ sung bằng ngôn ngữ đảo (reverse_grammar + reverse_automaton).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from operations.fa_ops import reverse_automaton
from core.grammar_parser import classify
from core.models import EPS, Automaton, Grammar
from core.normalizer import normalize_right_linear, reverse_grammar


class NotRegularGrammar(Exception):
    def __init__(self, reasons):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass
class ConversionInfo:
    kind: str
    normalized: Grammar | None = None
    log: list = field(default_factory=list)


def right_linear_to_nfa(g: Grammar) -> tuple[Automaton, list]:
    """g đã chuẩn hóa (A→aB, A→a, A→ε, A→B). Làm đúng 5 bước của Chap4."""
    log = []
    needs_final = any(len(p.rhs) == 1 and p.rhs[0] not in g.variables for p in g.productions)
    final = None
    if needs_final:
        final = "F"
        while final in g.variables:
            final += "'"
        log.append(f"Bước 1: thêm trạng thái kết {final} vì có luật dạng A → a")
    states = set(g.variables) | ({final} if final else set())
    nfa = Automaton(states, set(g.terminals), {}, g.start, set())
    log.append("Bước 1: mỗi biến thành một trạng thái: " + ", ".join(sorted(g.variables)))
    log.append(f"Bước 2: biến khởi đầu {g.start} thành trạng thái đầu")
    if final:
        nfa.accepting.add(final)
    for p in g.productions:
        A, rhs = p.lhs[0], p.rhs
        if not rhs:
            nfa.accepting.add(A)
            log.append(f"Bước 5: {p} => {A} là trạng thái chấp nhận")
        elif len(rhs) == 1 and rhs[0] in g.variables:
            nfa.add_transition(A, EPS, rhs[0])
            log.append(f"(luật đơn vị) {p} => {A} --ε--> {rhs[0]}")
        elif len(rhs) == 1:
            nfa.add_transition(A, rhs[0], final)
            log.append(f"Bước 4: {p} => {A} --{rhs[0]}--> {final}")
        else:
            nfa.add_transition(A, rhs[0], rhs[1])
            log.append(f"Bước 3: {p} => {A} --{rhs[0]}--> {rhs[1]}")
    return nfa, log


def grammar_to_nfa(g: Grammar) -> tuple[Automaton, ConversionInfo]:
    """Kiểm tra loại -> chuẩn hóa -> chuyển. Văn phạm không phải loại 3 bị từ chối."""
    kind, reasons = classify(g)
    if kind == "not-regular":
        raise NotRegularGrammar(reasons)
    info = ConversionInfo(kind)
    if kind in ("right-linear", "both"):
        norm, log = normalize_right_linear(g)
        nfa, log2 = right_linear_to_nfa(norm)
        info.normalized, info.log = norm, log + log2
        return nfa, info
    # tuyến tính trái: G -> G^R (tuyến tính phải) -> NFA cho L^R -> đảo NFA => NFA cho L
    gr = reverse_grammar(g)
    norm, log = normalize_right_linear(gr)
    nfa_r, log2 = right_linear_to_nfa(norm)
    info.normalized = norm
    info.log = (["Tuyến tính trái: đảo vế phải để được văn phạm tuyến tính phải sinh L^R, "
                 "chuyển sang NFA rồi đảo NFA"] + log + log2)
    nfa = reverse_automaton(nfa_r)
    nfa.alphabet = set(g.terminals)
    return nfa, info
