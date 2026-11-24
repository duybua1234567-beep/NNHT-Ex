"""gui.py - Giao diện Tkinter cho đồ án Finite Automaton và Grammar.

Chạy:  python main.py --gui   (hoặc  python -m ui)
Mỗi tab ghi rõ kiến thức thuộc chương nào. Phần xử lý nằm ở gui_logic.py, phần vẽ ở fa_draw.py.
Linux: nếu báo thiếu tkinter, cài bằng  sudo apt install python3-tk
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import verification.examples as ex
import ui.logic as L
from ui.draw import make_view_class
from core.grammar_parser import GrammarError
from analysis.non_regular_proof import LANGS
from conversion.nfa_to_dfa import to_dfa
from analysis.pda_demo import PDA_SAMPLES

AutomatonView = make_view_class()
MONO = "TkFixedFont"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finite Automaton & Grammar - Ngôn ngữ hình thức")
        self.geometry("1280x800")
        self.minsize(1000, 640)
        self.ws = L.Workspace()
        self.stepper = None
        self.titles = [e.title for e in ex.EXAMPLES]
        self.regular_idx = [i for i, e in enumerate(ex.EXAMPLES) if e.regular]
        self.regular_titles = [ex.EXAMPLES[i].title for i in self.regular_idx]

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        for build, name in ((self._tab_grammar, "1. Văn phạm → NFA"), (self._tab_sim, "2. Mô phỏng chuỗi"),
                            (self._tab_compare, "3. Đối chứng L(G)=L(M)"), (self._tab_dfa, "4. DFA & FA → Grammar"),
                            (self._tab_ops, "5. Phép toán"), (self._tab_analysis, "6. Phân tích"),
                            (self._tab_theory, "7. Không chính quy & PDA"), (self._tab_checks, "8. Kiểm tra chéo")):
            frame = ttk.Frame(nb, padding=8)
            nb.add(frame, text=name)
            build(frame)
        self.example_combo.current(0)
        self.on_load_example()

    # ------------------------------------------------------------ tiện ích
    @staticmethod
    def _banner(parent, text):
        ttk.Label(parent, text=text, foreground="#555555", font=("TkDefaultFont", 9, "italic")).pack(anchor="w", pady=(0, 6))

    @staticmethod
    def _text(parent, height=10, wrap="none"):
        t = ScrolledText(parent, height=height, wrap=wrap, font=MONO)
        return t

    @staticmethod
    def _set(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)

    def _need_nfa(self) -> bool:
        if self.ws.nfa is None:
            messagebox.showwarning("Chưa có NFA", "Văn phạm hiện tại chưa chuyển được sang NFA "
                                   "(chưa nạp hoặc không phải loại 3). Hãy sửa ở tab 1.")
            return False
        return True

    def _second_nfa(self):
        idx = self.regular_idx[self.second_combo.current() if self.second_combo.current() >= 0 else 0]
        return L.build_example_nfa(idx)

    def _guard(self, fn):
        def run(*a):
            try:
                fn(*a)
            except (GrammarError, ValueError) as err:
                messagebox.showerror("Lỗi", str(err))
        return run

    # ------------------------------------------------------------ tab 1
    def _tab_grammar(self, f):
        self._banner(f, "Áp dụng: Chap2 (văn phạm G=(V,T,P,S), Chomsky), Chap4 (văn phạm tuyến tính, quy tắc 5 bước chuyển VPCQ → FA, Định lý 1)")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Ví dụ:").pack(side="left")
        self.example_combo = ttk.Combobox(top, values=self.titles, state="readonly", width=48)
        self.example_combo.pack(side="left", padx=6)
        ttk.Button(top, text="Nạp ví dụ", command=self._guard(self.on_load_example)).pack(side="left")
        ttk.Button(top, text="Phân loại + chuyển sang NFA", command=self._guard(self.on_convert)).pack(side="left", padx=10)
        body = ttk.PanedWindow(f, orient="horizontal")
        body.pack(fill="both", expand=True, pady=6)
        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=2)
        body.add(right, weight=3)
        ttk.Label(left, text="Văn phạm (mỗi dòng: A -> aB | b | ε ; chữ HOA là biến):").pack(anchor="w")
        self.grammar_text = self._text(left, height=9)
        self.grammar_text.pack(fill="x")
        ttk.Label(left, text="Phân loại, chuẩn hóa và nhật ký chuyển đổi:").pack(anchor="w", pady=(8, 0))
        self.info_text = self._text(left, height=14, wrap="word")
        self.info_text.pack(fill="both", expand=True)
        self.view1 = AutomatonView(right, height=320)
        self.view1.pack(fill="both", expand=True)
        ttk.Label(right, text="Bảng chuyển trạng thái δ:").pack(anchor="w", pady=(6, 0))
        self.table_text = self._text(right, height=8)
        self.table_text.pack(fill="x")

    def on_load_example(self):
        i = max(self.example_combo.current(), 0)
        self._set(self.grammar_text, ex.EXAMPLES[i].text)
        self.on_convert()

    def on_convert(self):
        self.stepper = None
        try:
            report = self.ws.load(self.grammar_text.get("1.0", "end"))
        except GrammarError as err:
            self.ws.grammar = self.ws.nfa = None
            self._set(self.info_text, f"Lỗi đọc văn phạm: {err}")
            self.view1.show(None)
            self._set(self.table_text, "")
            return
        self._set(self.info_text, report)
        self.view1.show(self.ws.nfa, caption="NFA thu được (vòng đôi = trạng thái chấp nhận)")
        self._set(self.table_text, self.ws.nfa.to_table() if self.ws.nfa else "")
        self.view2.show(self.ws.nfa)
        self.view4.show(self.ws.nfa)
        self._set(self.trace_text, "")
        self.sim_status.set("")

    # ------------------------------------------------------------ tab 2
    def _tab_sim(self, f):
        self._banner(f, "Áp dụng: Chap2 (chuỗi thuộc Σ*), Chap2_1 (cấu hình, move, accepter yes/no, không đơn định), Chap6 (cách ghi hình thái)")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Chuỗi nhập (để trống = ε):").pack(side="left")
        self.sim_var = tk.StringVar(value="abb")
        ttk.Entry(top, textvariable=self.sim_var, width=26).pack(side="left", padx=6)
        ttk.Button(top, text="Bắt đầu / Reset", command=self._guard(self.on_sim_reset)).pack(side="left")
        ttk.Button(top, text="Bước tiếp", command=self._guard(self.on_sim_step)).pack(side="left", padx=4)
        ttk.Button(top, text="Chạy hết", command=self._guard(self.on_sim_all)).pack(side="left")
        self.sim_status = tk.StringVar()
        ttk.Label(top, textvariable=self.sim_status, font=("TkDefaultFont", 11, "bold")).pack(side="left", padx=14)
        self.view2 = AutomatonView(f, height=320)
        self.view2.pack(fill="both", expand=True, pady=6)
        self.trace_text = self._text(f, height=9)
        self.trace_text.pack(fill="x")

    def on_sim_reset(self):
        if not self._need_nfa():
            return
        self.stepper = L.Stepper(self.ws.nfa, self.sim_var.get().strip())
        self._sim_refresh()

    def on_sim_step(self):
        if not self._need_nfa():
            return
        if self.stepper is None:
            self.on_sim_reset()
            return
        self.stepper.step()
        self._sim_refresh()

    def on_sim_all(self):
        if not self._need_nfa():
            return
        if self.stepper is None:
            self.stepper = L.Stepper(self.ws.nfa, self.sim_var.get().strip())
        while not self.stepper.done:
            self.stepper.step()
        self._sim_refresh()

    def _sim_refresh(self):
        s = self.stepper
        self.view2.show(self.ws.nfa, highlight=s.cur, caption=f"Đã đọc {s.pos}/{len(s.w)} ký tự (ô vàng = tập trạng thái hiện tại)")
        self._set(self.trace_text, "\n".join(s.lines))
        self.sim_status.set(("CHẤP NHẬN" if s.accepted else "TỪ CHỐI") if s.done else f"đang đọc... ({s.pos}/{len(s.w)})")

    # ------------------------------------------------------------ tab 3
    def _tab_compare(self, f):
        self._banner(f, "Áp dụng: Chap2 (dẫn xuất ⇒, ⇒*, L(G), Σ*, Định nghĩa 3), Chap4 (Định lý 1: VPCQ ⇔ FA). Văn phạm sinh chuỗi độc lập với NFA.")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Độ dài tối đa k:").pack(side="left")
        self.k_var = tk.IntVar(value=6)
        ttk.Spinbox(top, from_=1, to=9, textvariable=self.k_var, width=4).pack(side="left", padx=6)
        ttk.Button(top, text="So sánh toàn bộ Σ* tới độ dài k", command=self._guard(self.on_compare)).pack(side="left")
        self.cmp_summary = tk.StringVar()
        ttk.Label(top, textvariable=self.cmp_summary, font=("TkDefaultFont", 10, "bold")).pack(side="left", padx=12)
        cols = ("w", "g", "m", "ok")
        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=14)
        for c, t, w in (("w", "Chuỗi", 260), ("g", "Văn phạm sinh được", 160), ("m", "NFA chấp nhận", 140), ("ok", "Khớp", 80)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="center")
        self.tree.tag_configure("bad", background="#f8c6c6")
        self.tree.tag_configure("yes", background="#d9f2d9")
        self.tree.pack(fill="both", expand=True, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        ttk.Label(f, text="Dẫn xuất của chuỗi đang chọn:").pack(anchor="w")
        self.deriv_text = self._text(f, height=4, wrap="word")
        self.deriv_text.pack(fill="x")
        self._derivs = {}

    def on_compare(self):
        if not self._need_nfa():
            return
        rows, summary = L.compare_rows(self.ws, int(self.k_var.get()))
        self.tree.delete(*self.tree.get_children())
        self._derivs = {}
        for w, in_g, in_m, ok, deriv in rows:
            tag = "bad" if not ok else ("yes" if in_g else "")
            iid = self.tree.insert("", "end", values=(w, "có" if in_g else "không", "có" if in_m else "không",
                                                       "✔" if ok else "✘"), tags=(tag,))
            self._derivs[iid] = deriv
        self.cmp_summary.set(summary)

    def _on_tree_select(self, _event=None):
        sel = self.tree.selection()
        if sel:
            self._set(self.deriv_text, self._derivs.get(sel[0], ""))

    # ------------------------------------------------------------ tab 4
    def _tab_dfa(self, f):
        self._banner(f, "Áp dụng: Chap3_1 / Chap2_1 (NFA → DFA, xây dựng tập con), Chap1 (tập lũy thừa), Chap4 Định lý 2 (FA → văn phạm tuyến tính trái/phải)")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Button(top, text="NFA → DFA", command=self._guard(self.on_dfa)).pack(side="left")
        ttk.Button(top, text="FA → Grammar (phải + trái)", command=self._guard(self.on_fa_to_grammar)).pack(side="left", padx=6)
        ttk.Button(top, text="Hiện lại NFA", command=self._guard(lambda: self.view4.show(self.ws.nfa))).pack(side="left")
        self.view4 = AutomatonView(f, height=300)
        self.view4.pack(fill="both", expand=True, pady=6)
        self.out4 = self._text(f, height=11)
        self.out4.pack(fill="x")

    def on_dfa(self):
        if not self._need_nfa():
            return
        d = to_dfa(self.ws.nfa)
        self.view4.show(d, caption=f"DFA: {len(d.states)} trạng thái (mỗi trạng thái là một tập trạng thái của NFA)")
        self._set(self.out4, f"NFA {len(self.ws.nfa.states)} trạng thái → DFA {len(d.states)} trạng thái\n\n" + d.to_table())

    def on_fa_to_grammar(self):
        if self._need_nfa():
            self._set(self.out4, L.grammar_texts(self.ws.nfa))

    # ------------------------------------------------------------ tab 5
    def _tab_ops(self, f):
        self._banner(f, "Áp dụng: Chap4 Định lý 3 (hợp, nối, Kleene), 4 (bù: DFA đầy đủ), 5 (giao: tích trạng thái), Chap6 Định lý 6.5 (chạy song song)")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="L1 = văn phạm hiện tại (tab 1). L2 =").pack(side="left")
        self.second_combo = ttk.Combobox(top, values=self.regular_titles, state="readonly", width=40)
        self.second_combo.current(1)
        self.second_combo.pack(side="left", padx=6)
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=4)
        for name, label in (("union", "L1 ∪ L2"), ("concat", "L1 · L2"), ("star", "L1*"), ("complement", "bù L1"),
                            ("intersection", "L1 ∩ L2")):
            ttk.Button(bar, text=label, command=self._guard(lambda n=name: self.on_op(n))).pack(side="left", padx=3)
        self.view5 = AutomatonView(f, height=300)
        self.view5.pack(fill="both", expand=True, pady=6)
        self.out5 = self._text(f, height=11)
        self.out5.pack(fill="x")

    # ------------------------------------------------------------ tab 6
    def _tab_analysis(self, f):
        self._banner(f, "Áp dụng: Chap4 Định lý 6 (rỗng/vô hạn), Định lý 7 (tương đương), Bổ đề Bơm (thử trên DFA); Chap1 (đồ thị: đường đi, chu trình)")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Button(top, text="Rỗng / vô hạn", command=self._guard(self.on_empty_inf)).pack(side="left")
        ttk.Label(top, text="   So sánh với L2:").pack(side="left")
        self.cmp_combo = ttk.Combobox(top, values=self.regular_titles, state="readonly", width=40)
        self.cmp_combo.current(1)
        self.cmp_combo.pack(side="left", padx=6)
        ttk.Button(top, text="Kiểm tra tương đương", command=self._guard(self.on_equiv)).pack(side="left")
        ttk.Button(top, text="Thử bơm", command=self._guard(self.on_pump)).pack(side="left", padx=10)
        self.out6 = self._text(f, height=26)
        self.out6.pack(fill="both", expand=True, pady=8)

    def _label1(self):
        return self.titles[self.example_combo.current()] if self.example_combo.current() >= 0 else "văn phạm hiện tại"

    def on_empty_inf(self):
        if self._need_nfa():
            self._set(self.out6, L.analysis_text(self.ws.nfa, self._label1()))

    def on_equiv(self):
        if not self._need_nfa():
            return
        idx = self.regular_idx[self.cmp_combo.current() if self.cmp_combo.current() >= 0 else 0]
        e, _, n2 = L.build_example_nfa(idx)
        self._set(self.out6, L.analysis_text(self.ws.nfa, self._label1(), n2, e.title))

    def on_pump(self):
        if self._need_nfa():
            self._set(self.out6, L.pumping_text(self.ws.nfa))

    # ------------------------------------------------------------ tab 7
    def _tab_theory(self, f):
        self._banner(f, "Áp dụng: Chap4 Bổ đề Bơm (bài tập 4, 5), Chap6 (PDA: Thí dụ 6.1, 6.3), Chap2 (L3 ⊂ L2)")
        a = ttk.Frame(f)
        a.pack(fill="x")
        ttk.Label(a, text="Ngôn ngữ:").pack(side="left")
        self.lang_combo = ttk.Combobox(a, values=[x.title for x in LANGS], state="readonly", width=62)
        self.lang_combo.current(0)
        self.lang_combo.pack(side="left", padx=6)
        ttk.Label(a, text="p tối đa:").pack(side="left")
        self.p_var = tk.IntVar(value=5)
        ttk.Spinbox(a, from_=1, to=8, textvariable=self.p_var, width=4).pack(side="left", padx=4)
        ttk.Button(a, text="Chứng minh bằng Bổ đề Bơm", command=self._guard(self.on_nonregular)).pack(side="left", padx=6)
        b = ttk.Frame(f)
        b.pack(fill="x", pady=6)
        ttk.Label(b, text="PDA:").pack(side="left")
        self.pda_combo = ttk.Combobox(b, values=list(PDA_SAMPLES), state="readonly", width=8)
        self.pda_combo.current(0)
        self.pda_combo.pack(side="left", padx=6)
        ttk.Label(b, text="Chuỗi:").pack(side="left")
        self.pda_var = tk.StringVar(value="001c100")
        ttk.Entry(b, textvariable=self.pda_var, width=24).pack(side="left", padx=6)
        ttk.Button(b, text="Chạy PDA", command=self._guard(self.on_pda)).pack(side="left")
        ttk.Label(b, text="  (wcwR: 001c100 | wwR: 001100 | anbn: aaabbb)").pack(side="left")
        self.out7 = self._text(f, height=26)
        self.out7.pack(fill="both", expand=True)
    # ------------------------------------------------------------ tab 8
    def _tab_checks(self, f):
        self._banner(f, "Áp dụng: toàn bộ chương. Kiểm tra chéo A..L (xem cross_checks.py): văn phạm vs NFA vs DFA, phép toán, tương đương, bơm, PDA")
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Độ dài tối đa k:").pack(side="left")
        self.chk_k = tk.IntVar(value=5)
        ttk.Spinbox(top, from_=1, to=8, textvariable=self.chk_k, width=4).pack(side="left", padx=6)
        ttk.Button(top, text="Chạy toàn bộ kiểm tra A..L", command=self._guard(self.on_checks)).pack(side="left")
        self.out8 = self._text(f, height=30)
        self.out8.pack(fill="both", expand=True, pady=8)

    def on_checks(self):
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            self._set(self.out8, L.checks_text(int(self.chk_k.get())))
        finally:
            self.configure(cursor="")


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
