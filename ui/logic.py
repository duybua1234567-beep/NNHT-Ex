"""gui_logic.py - Phần xử lý (không dính Tkinter) cho giao diện: nhận đầu vào, trả về văn bản/dữ liệu.

Tách riêng để kiểm thử được mà không cần màn hình. Mỗi hàm ghi rõ chương áp dụng.
"""
from __future__ import annotations

import io
from contextlib import redirect_stdout
from dataclasses import dataclass

import verification.examples as ex
from analysis.language_analysis import equivalent, is_empty_graph, is_empty_theorem, is_infinite_graph, is_infinite_theorem
from verification.cross_checks import run_all
from operations.fa_ops import complement, concat, intersection, star, union
from conversion.fa_to_grammar import fa_to_left_linear, fa_to_right_linear
from simulation.generator import derive_all, format_derivation, sigma_star
from core.grammar_parser import classify, describe_kind, parse_grammar
from conversion.grammar_to_nfa import NotRegularGrammar, grammar_to_nfa
from core.models import EPS, Automaton
from conversion.nfa_to_dfa import to_dfa
from analysis.non_regular_proof import LANGS, prove
from analysis.pda_demo import PDA_SAMPLES, format_ids, is_deterministic, pda_accepts
from analysis.pumping import format_pump, pump_report
from simulation.simulator import accepts, validate_input


class Workspace:
    """Trạng thái làm việc hiện tại: văn phạm, NFA, nhật ký chuyển đổi."""

    def __init__(self):
        self.grammar = None
        self.nfa = None
        self.info = None

    def load(self, text: str) -> str:
        """[Chap2, Chap4] Đọc + phân loại + chuẩn hóa + chuyển Grammar → NFA. Trả về báo cáo."""
        self.grammar, self.nfa, self.info = None, None, None
        g = parse_grammar(text)
        self.grammar = g
        kind, reasons = classify(g)
        lines = [f"V = {sorted(g.variables)}", f"T = {sorted(g.terminals)}", f"S = {g.start}",
                 f"Loại văn phạm: {describe_kind(kind)}  [Chap2: Chomsky; Chap4: tuyến tính trái/phải]"]
        if kind == "not-regular":
            lines.append("=> TỪ CHỐI chuyển sang FA (chỉ văn phạm loại 3 mới chuyển được). Lý do:")
            lines += [f"   - {r}" for r in reasons]
            lines.append("Gợi ý: ngôn ngữ như aⁿbⁿ cần PDA (tab 7), không có FA nào nhận được [Chap4 Bổ đề Bơm, Chap6].")
            return "\n".join(lines)
        nfa, info = grammar_to_nfa(g)
        self.nfa, self.info = nfa, info
        lines.append("\nVăn phạm tuyến tính phải sau chuẩn hóa (mỗi luật chỉ sinh 1 terminal):")
        lines.append(info.normalized.to_text())
        lines.append("\nCác bước chuyển đổi  [Chap4: quy tắc chuyển VPCQ thành FA]:")
        lines += [f"  • {s}" for s in info.log]
        return "\n".join(lines)


# ------------------------------------------------------------ mô phỏng từng bước
class Stepper:
    """[Chap2_1] Cấu hình và move: mỗi lần step() đọc một ký tự, tập trạng thái mới = ε-bao đóng của move."""

    def __init__(self, aut: Automaton, w: str):
        validate_input(aut, w)
        self.aut, self.w, self.pos = aut, w, 0
        self.cur = aut.eps_closure({aut.start})
        self.lines = [self._line("khởi đầu")]

    def _line(self, what: str) -> str:
        states = ", ".join(sorted(self.cur, key=str))
        return (f"[{what}] đã đọc {self.w[:self.pos] or EPS:<8} còn lại {self.w[self.pos:] or EPS:<8}"
                f" tập trạng thái = {{{states}}}")

    @property
    def done(self) -> bool:
        return self.pos >= len(self.w)

    @property
    def accepted(self) -> bool:
        return self.done and bool(self.cur & self.aut.accepting)

    def step(self) -> None:
        if self.done:
            return
        c = self.w[self.pos]
        self.cur = self.aut.eps_closure(self.aut.move(self.cur, c))
        self.pos += 1
        self.lines.append(self._line(f"đọc {c!r}"))
        if self.done:
            self.lines.append("=> " + ("CHẤP NHẬN (yes)" if self.accepted else "TỪ CHỐI (no)"))


# ------------------------------------------------------------ đối chứng
def compare_rows(ws: Workspace, k: int):
    """[Chap2: dẫn xuất ⇒*, L(G); Chap4 Định lý 1] Mỗi dòng: (chuỗi, G sinh?, NFA nhận?, khớp?, dẫn xuất)."""
    derived = derive_all(ws.grammar, k)
    rows, mism = [], 0
    for w in sigma_star(ws.grammar.terminals, k):
        in_g, in_m = w in derived, accepts(ws.nfa, w)
        mism += in_g != in_m
        rows.append((w or EPS, in_g, in_m, in_g == in_m, format_derivation(derived[w]) if in_g else "(không dẫn xuất được)"))
    summary = (f"So sánh {len(rows)} chuỗi của Σ* (độ dài ≤ {k}): văn phạm sinh {len(derived)} chuỗi, "
               + ("KHỚP HOÀN TOÀN với NFA ⇒ L(G) = L(M) trên Σ^≤k" if not mism else f"LỆCH {mism} chuỗi"))
    return rows, summary


# ------------------------------------------------------------ phép toán
# ------------------------------------------------------------ phân tích
def analysis_text(n1: Automaton, label1: str, n2: Automaton | None = None, label2: str = "") -> str:
    out = [f"Ngôn ngữ L1 = {label1}",
           f"  Rỗng?   theo đồ thị = {is_empty_graph(n1)} | theo Định lý 6 (chuỗi dài < n) = {is_empty_theorem(n1)}",
           f"  Vô hạn? theo đồ thị = {is_infinite_graph(n1)} | theo Định lý 6 (n ≤ dài < 2n) = {is_infinite_theorem(n1)}",
           "  [Chap4 Định lý 6; Chap1 đồ thị: đường đi, chu trình]"]
    if n2 is not None:
        ok, w, who = equivalent(n1, n2)
        out += ["", f"So sánh với L2 = {label2}  [Chap4 Định lý 7]",
                "  => TƯƠNG ĐƯƠNG (cùng ngôn ngữ)" if ok else
                f"  => KHÔNG tương đương. Chuỗi phản chứng ngắn nhất: {w or EPS!r} "
                f"(chỉ L{1 if who == 'a' else 2} chấp nhận)"]
    return "\n".join(out)


def pumping_text(n1: Automaton, max_i: int = 4) -> str:
    reports, note = pump_report(n1, max_i=max_i, per_length=2)
    head = "Thử bơm trên DFA tương đương  [Chap4 Bổ đề Bơm, dạng chuẩn |xy| ≤ n, |y| ≥ 1]"
    if not reports:
        return head + "\n" + note
    body = "\n".join(format_pump(r) for r in reports)
    return f"{head}\n{body}\n=> {sum(r['ok'] for r in reports)}/{len(reports)} chuỗi bơm thành công"

def checks_text(k: int) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_all(k, verbose=True)
    return buf.getvalue()


def grammar_texts(nfa: Automaton) -> str:
    return ("Văn phạm TUYẾN TÍNH PHẢI tương ứng  [Chap4 Định lý 2]:\n" + fa_to_right_linear(nfa).to_text()
            + "\n\nVăn phạm TUYẾN TÍNH TRÁI tương ứng:\n" + fa_to_left_linear(nfa).to_text())


def build_example_nfa(key_or_index) -> tuple:
    e = ex.EXAMPLES[key_or_index] if isinstance(key_or_index, int) else ex.BY_KEY[key_or_index]
    g = parse_grammar(e.text)
    try:
        return e, g, grammar_to_nfa(g)[0]
    except NotRegularGrammar as err:
        raise ValueError(f"Ví dụ '{e.title}' không phải văn phạm loại 3: {err.reasons[0]}")
