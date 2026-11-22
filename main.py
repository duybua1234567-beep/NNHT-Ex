"""main.py - Menu tương tác cho đồ án Finite Automaton và Grammar.

Chạy:  python main.py            (mặc định: mở giao diện; thiếu tkinter thì dùng menu dòng lệnh)
       python main.py --menu     (menu dòng lệnh)
       python main.py --demo     (chạy tuần tự cả 22 bước)
       python main.py --checks   (chỉ chạy bộ kiểm tra chéo A..L)
       python main.py --gui      (giao diện Tkinter, tương đương python main.py --gui)
"""
from __future__ import annotations

import argparse
import sys

import verification.examples as ex
from analysis.language_analysis import equivalent, is_empty_graph, is_empty_theorem, is_infinite_graph, is_infinite_theorem
from verification.cross_checks import run_all
from demo import run_demo
from operations.fa_ops import complement, concat, intersection, star, union
from conversion.fa_to_grammar import fa_to_left_linear, fa_to_right_linear
from simulation.generator import derive_all, format_derivation, language_up_to, sigma_star
from core.grammar_parser import GrammarError, classify, describe_kind, parse_grammar
from conversion.grammar_to_nfa import NotRegularGrammar, grammar_to_nfa
from conversion.nfa_to_dfa import to_dfa
from analysis.non_regular_proof import LANGS, prove
from analysis.pda_demo import format_ids, is_deterministic, pda_accepts, pda_anbn, pda_wcwr, pda_wwr
from analysis.pumping import format_pump, pump_report
from simulation.simulator import accepts, format_trace, simulate

MENU = """
================ FINITE AUTOMATON & GRAMMAR ================
 1. Chọn ví dụ có sẵn / nhập văn phạm        [Chap2]
 2. Phân loại + chuẩn hóa văn phạm           [Chap2, Chap4]
 3. Chuyển Grammar → NFA, hiển thị           [Chap4]
 4. Mô phỏng một chuỗi (từng bước)           [Chap2_1, Chap6]
 5. Đối chứng L(G) với NFA tới độ dài k      [Chap2, Chap4 Đ.lý 1]
 6. NFA → DFA                                [Chap3_1]
 7. FA → Grammar (phải / trái)               [Chap4 Đ.lý 2]
 8. Phép toán: hợp, nối, Kleene, bù, giao    [Chap4 Đ.lý 3-5]
 9. Phân tích: rỗng/vô hạn, tương đương      [Chap4 Đ.lý 6-7]
10. Thử bơm trên DFA                         [Chap4 Bổ đề Bơm]
11. Chứng minh không chính quy (Bơm)         [Chap4 bài tập 4-5]
12. Demo PDA (aⁿbⁿ, wcwᴿ, wwᴿ)               [Chap6]
13. Chạy bộ kiểm tra chéo A..L
14. Chạy demo toàn bộ 22 bước
 0. Thoát
"""


class Session:
    def __init__(self):
        self.grammar = None
        self.nfa = None
        self.label = ""
        self.load_example("ab_plus")

    def load_text(self, text: str, label: str):
        g = parse_grammar(text)
        self.grammar, self.label = g, label
        try:
            self.nfa = grammar_to_nfa(g)[0]
        except NotRegularGrammar as err:
            self.nfa = None
            print("Văn phạm KHÔNG phải loại 3, từ chối chuyển sang FA:")
            for r in err.reasons:
                print("  -", r)

    def load_example(self, key: str):
        self.load_text(ex.BY_KEY[key].text, ex.BY_KEY[key].title)

    def need_nfa(self) -> bool:
        if self.nfa is None:
            print("Chưa có NFA (văn phạm hiện tại không phải loại 3). Hãy chọn văn phạm khác ở mục 1.")
            return False
        return True


def ask_int(prompt: str, default: int) -> int:
    s = input(f"{prompt} [{default}]: ").strip()
    return int(s) if s.isdigit() else default


def pick_example(prompt: str = "Chọn ví dụ") -> str:
    for i, e in enumerate(ex.EXAMPLES, 1):
        print(f"  {i:>2}. {e.title:<42} {e.note[:60]}")
    n = ask_int(prompt, 1)
    return ex.EXAMPLES[min(max(n, 1), len(ex.EXAMPLES)) - 1].key


def do_choose(s: Session):
    print("  0. Nhập văn phạm mới (mỗi dòng 'A -> aB | b | ε', kết thúc bằng dòng trống)")
    for i, e in enumerate(ex.EXAMPLES, 1):
        print(f"  {i:>2}. {e.title:<42} {e.note[:60]}")
    n = ask_int("Chọn", 1)
    if n == 0:
        lines = []
        while True:
            line = input("  > ")
            if not line.strip():
                break
            lines.append(line)
        s.load_text("\n".join(lines), "văn phạm nhập tay")
    else:
        s.load_example(ex.EXAMPLES[min(max(n, 1), len(ex.EXAMPLES)) - 1].key)
    print("Văn phạm hiện tại:\n" + s.grammar.to_text())


def do_classify(s: Session):
    kind, reasons = classify(s.grammar)
    print("Loại:", describe_kind(kind))
    for r in reasons:
        print("  -", r)
    if kind != "not-regular":
        _, info = grammar_to_nfa(s.grammar)
        print("\nVăn phạm sau chuẩn hóa (tuyến tính phải):\n" + info.normalized.to_text())
        print("\nNhật ký:\n  " + "\n  ".join(info.log))


def do_nfa(s: Session):
    if s.need_nfa():
        print(s.nfa.describe() + "\n\n" + s.nfa.to_table() + "\n\n" + s.nfa.to_dot())


def do_simulate(s: Session):
    if not s.need_nfa():
        return
    w = input("Nhập chuỗi (để trống = ε): ").strip()
    try:
        print(format_trace(simulate(s.nfa, w), w))
    except ValueError as err:
        print("Lỗi:", err)


def do_compare(s: Session):
    if not s.need_nfa():
        return
    k = ask_int("Độ dài tối đa k", 6)
    derived = derive_all(s.grammar, k)
    for w in language_up_to(s.grammar, k)[:15]:
        print(f"  {w or 'ε':<8}: {format_derivation(derived[w])}")
    words = list(sigma_star(s.grammar.terminals, k))
    mism = [w for w in words if (w in derived) != accepts(s.nfa, w)]
    print(f"Đã so sánh {len(words)} chuỗi; văn phạm sinh {len(derived)} chuỗi => "
          + ("KHỚP HOÀN TOÀN với NFA (L(G) = L(M) trên Σ^≤k)" if not mism else f"LỆCH: {mism[:10]}"))


def do_dfa(s: Session):
    if s.need_nfa():
        d = to_dfa(s.nfa)
        print(d.describe() + "\n\n" + d.to_table())


def do_fa_to_grammar(s: Session):
    if s.need_nfa():
        print("Tuyến tính phải:\n" + fa_to_right_linear(s.nfa).to_text())
        print("\nTuyến tính trái:\n" + fa_to_left_linear(s.nfa).to_text())


def other_nfa(s: Session):
    key = pick_example("Chọn ví dụ thứ hai")
    try:
        g = parse_grammar(ex.BY_KEY[key].text)
        return g, grammar_to_nfa(g)[0]
    except NotRegularGrammar:
        print("Ví dụ đó không phải loại 3.")
        return None, None


def do_ops(s: Session):
    if not s.need_nfa():
        return
    g2, n2 = other_nfa(s)
    if n2 is None:
        return
    alpha = s.grammar.terminals | g2.terminals
    k = ask_int("Hiển thị chuỗi tới độ dài", 5)
    for name, aut in (("hợp", union(s.nfa, n2)), ("nối", concat(s.nfa, n2)), ("Kleene L1*", star(s.nfa)),
                      ("bù L1", complement(s.nfa, alpha)), ("giao", intersection(s.nfa, n2))):
        words = [w or "ε" for w in sigma_star(alpha, k) if accepts(aut, w)]
        print(f"  {name:<11} {len(aut.states):>3} trạng thái, {len(words)} chuỗi: {words[:12]}")


def do_analysis(s: Session):
    if not s.need_nfa():
        return
    print(f"Rỗng : đồ thị={is_empty_graph(s.nfa)}, Định lý 6={is_empty_theorem(s.nfa)}")
    print(f"Vô hạn: đồ thị={is_infinite_graph(s.nfa)}, Định lý 6={is_infinite_theorem(s.nfa)}")
    if input("So sánh tương đương với ví dụ khác? (y/n) ").strip().lower() == "y":
        _, n2 = other_nfa(s)
        if n2 is not None:
            ok, w, who = equivalent(s.nfa, n2)
            print("Tương đương" if ok else f"KHÔNG tương đương; chuỗi phản chứng ngắn nhất {w!r} "
                  f"(chỉ ngôn ngữ {'hiện tại' if who == 'a' else 'thứ hai'} chấp nhận)")


def do_pump(s: Session):
    if s.need_nfa():
        reports, note = pump_report(s.nfa, max_i=4, per_length=2)
        for r in reports:
            print(format_pump(r))
        print(note or f"=> {sum(r['ok'] for r in reports)}/{len(reports)} chuỗi bơm thành công")


def do_nonregular(s: Session):
    for i, lang in enumerate(LANGS, 1):
        print(f"  {i}. {lang.title}")
    lang = LANGS[min(max(ask_int("Chọn ngôn ngữ", 1), 1), len(LANGS)) - 1]
    ok, log = prove(lang, range(1, 7))
    print(lang.title + f"\n  ý tưởng: {lang.note}\n" + "\n".join(log))
    print("=> " + ("Mọi cách chia đều bị bác bỏ: L KHÔNG chính quy" if ok else
                   "Có cách chia không bị bác bỏ: không thể dùng chuỗi này để chứng minh (L thực tế chính quy)"))


def do_pda(s: Session):
    pdas = {"1": ("w c wᴿ", pda_wcwr, "001c100"), "2": ("w wᴿ", pda_wwr, "001100"), "3": ("aⁿbⁿ", pda_anbn, "aaabbb")}
    for k, (name, _, _) in pdas.items():
        print(f"  {k}. {name}")
    name, mk, default = pdas.get(input("Chọn [1]: ").strip() or "1", pdas["1"])
    pda = mk()
    w = input(f"Chuỗi nhập [{default}]: ").strip() or default
    ok, ids = pda_accepts(pda, w)
    print(f"PDA {name}: {'đơn định (DPDA)' if is_deterministic(pda) else 'KHÔNG đơn định (NPDA)'}")
    print(("CHẤP NHẬN (Stack rỗng) - dãy hình thái:\n" + format_ids(ids)) if ok else "TỪ CHỐI")


ACTIONS = {"1": do_choose, "2": do_classify, "3": do_nfa, "4": do_simulate, "5": do_compare, "6": do_dfa,
           "7": do_fa_to_grammar, "8": do_ops, "9": do_analysis, "10": do_pump, "11": do_nonregular, "12": do_pda,
           "13": lambda s: run_all(ask_int("Độ dài tối đa k", 6)), "14": lambda s: run_demo()}


def menu():
    s = Session()
    while True:
        print(MENU)
        print(f"Văn phạm hiện tại: {s.label}")
        try:
            choice = input("Chọn chức năng: ").strip()
        except EOFError:
            return
        if choice == "0":
            return
        action = ACTIONS.get(choice)
        if not action:
            print("Lựa chọn không hợp lệ.")
            continue
        try:
            action(s)
        except (GrammarError, ValueError) as err:
            print("Lỗi:", err)


def main():
    ap = argparse.ArgumentParser(description="Đồ án Finite Automaton và Grammar")
    ap.add_argument("--demo", action="store_true", help="chạy tuần tự 22 bước")
    ap.add_argument("--checks", action="store_true", help="chạy bộ kiểm tra chéo A..L")
    ap.add_argument("--gui", action="store_true", help="mở giao diện Tkinter (mặc định khi không có tham số)")
    ap.add_argument("--menu", action="store_true", help="dùng menu dòng lệnh thay vì giao diện")
    ap.add_argument("--example", default="ab_plus", help="khóa ví dụ cho --demo")
    ap.add_argument("-k", type=int, default=6, help="độ dài tối đa khi đối chứng")
    args = ap.parse_args()
    if args.demo:
        run_demo(args.example, args.k)
    elif args.checks:
        sys.exit(0 if run_all(args.k) else 1)
    elif args.menu:
        menu()
    else:  # bấm Run / python main.py / --gui: mở giao diện
        try:
            from ui.app import main as gui_main
        except ImportError as err:
            if args.gui:
                sys.exit(f"Không mở được giao diện ({err}). Linux: sudo apt install python3-tk")
            print(f"Không mở được giao diện ({err}); chuyển sang menu dòng lệnh. "
                  "Linux: sudo apt install python3-tk")
            menu()
        else:
            gui_main()


if __name__ == "__main__":
    main()
