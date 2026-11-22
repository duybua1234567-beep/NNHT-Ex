"""grammar_parser.py - Đọc văn phạm từ văn bản và phân loại (bước 1, 3, 4).

[Chap2] Định nghĩa văn phạm, quy ước: chữ HOA = biến, chữ thường/chữ số = terminal,
        "Nhận xét": suy ra V, T, S từ các luật sinh; viết gọn A -> β | γ.
[Chap2] Phân cấp Chomsky: văn phạm loại 3 (chính quy).
[Chap4] Văn phạm tuyến tính trái (A -> Bw | w) và tuyến tính phải (A -> wB | w).
"""
from __future__ import annotations

import re

from core.models import Grammar, Production, fmt_symbols

ARROW = re.compile(r"->|→")
EPS_WORDS = {"ε", "λ", "eps", "epsilon", ""}


class GrammarError(Exception):
    """Lỗi cú pháp khi đọc văn phạm."""


def _tokenize(text: str) -> list:
    """Trả về list (ký hiệu, là_biến). Biến: chữ HOA đơn hoặc <tên_dài>."""
    tokens, i = [], 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
        elif c == "<":
            j = text.find(">", i)
            if j == -1:
                raise GrammarError(f"Thiếu dấu '>' trong {text!r}")
            tokens.append((text[i + 1:j], True))
            i = j + 1
        else:
            tokens.append((c, c.isupper()))
            i += 1
    return tokens


def parse_grammar(text: str, start: str | None = None) -> Grammar:
    """[Chap2] Dòng dạng 'A -> aB | b | ε'. '#' bắt đầu chú thích."""
    prods, variables, terminals = [], set(), set()
    first_lhs = None
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        m = ARROW.search(line)
        if not m:
            raise GrammarError(f"Dòng {no}: thiếu '->' hoặc '→': {raw!r}")
        lhs_tokens = _tokenize(line[:m.start()])
        if not lhs_tokens:
            raise GrammarError(f"Dòng {no}: vế trái rỗng")
        if not any(is_var for _, is_var in lhs_tokens):
            raise GrammarError(f"Dòng {no}: vế trái phải chứa ít nhất một biến [Chap2]")
        for alt in line[m.end():].split("|"):
            alt = alt.strip()
            rhs_tokens = [] if alt in EPS_WORDS else _tokenize(alt)
            lhs = tuple(s for s, _ in lhs_tokens)
            rhs = tuple(s for s, _ in rhs_tokens)
            for s, is_var in lhs_tokens + rhs_tokens:
                (variables if is_var else terminals).add(s)
            prods.append(Production(lhs, rhs))
        if first_lhs is None:
            first_lhs = next(s for s, v in lhs_tokens if v)
    if not prods:
        raise GrammarError("Văn phạm rỗng")
    if start is None:
        start = "S" if "S" in variables else first_lhs
    # loại luật trùng, giữ thứ tự
    seen, uniq = set(), []
    for p in prods:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return Grammar(variables, terminals, uniq, start)


# ------------------------------------------------------------- phân loại
def _right_form(p: Production, variables) -> bool:
    """A -> wB hoặc A -> w  (w ∈ T*): không có biến ở vị trí trừ ký hiệu cuối."""
    return not any(s in variables for s in p.rhs[:-1])


def _left_form(p: Production, variables) -> bool:
    """A -> Bw hoặc A -> w: không có biến ở vị trí trừ ký hiệu đầu."""
    return not any(s in variables for s in p.rhs[1:])


def classify(g: Grammar) -> tuple[str, list]:
    """[Chap2 + Chap4] Trả về (loại, danh sách lý do).
    loại ∈ {'right-linear','left-linear','both','not-regular'}"""
    reasons, right_bad, left_bad = [], [], []
    structural = False
    for p in g.productions:
        if len(p.lhs) != 1 or p.lhs[0] not in g.variables:
            structural = True
            reasons.append(f"Luật '{p}': vế trái không phải một biến đơn "
                           f"(không phải văn phạm loại 2/3 theo Chomsky)")
            continue
        r_ok, l_ok = _right_form(p, g.variables), _left_form(p, g.variables)
        if not r_ok:
            right_bad.append(p)
        if not l_ok:
            left_bad.append(p)
        if not r_ok and not l_ok:
            structural = True
            nvars = sum(1 for s in p.rhs if s in g.variables)
            why = (f"vế phải có {nvars} biến" if nvars >= 2 else "biến nằm giữa chuỗi")
            reasons.append(f"Luật '{p}': {why}, không có dạng A→wB, A→Bw hay A→w")
    if structural:
        return "not-regular", reasons
    if not right_bad and not left_bad:
        return "both", []
    if not right_bad:
        return "right-linear", []
    if not left_bad:
        return "left-linear", []
    reasons.append("Văn phạm trộn lẫn tuyến tính phải ("
                   + ", ".join(str(p) for p in left_bad[:3])
                   + ") và tuyến tính trái ("
                   + ", ".join(str(p) for p in right_bad[:3])
                   + "): theo định nghĩa chương 4 không phải văn phạm chính quy")
    return "not-regular", reasons


def describe_kind(kind: str) -> str:
    return {"right-linear": "tuyến tính phải (loại 3 - chính quy)",
            "left-linear": "tuyến tính trái (loại 3 - chính quy)",
            "both": "chính quy (mọi luật dạng A → w)",
            "not-regular": "KHÔNG phải văn phạm chính quy"}[kind]
