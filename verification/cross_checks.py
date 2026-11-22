"""cross_checks.py - Bộ kiểm tra chéo A..L (bước 11 + tổng kết mọi bước mở rộng).

A  văn phạm sinh được <=> NFA chấp nhận                    [Chap2 Đ/n 3; Chap4 Định lý 1]
B  NFA và DFA cho cùng kết quả                              [Chap3_1; Chap2_1]
C  Grammar -> NFA -> Grammar' (phải và trái) cùng ngôn ngữ  [Chap4 Định lý 2]
D  mỗi chuỗi nằm đúng một trong L và L̄                      [Chap4 Định lý 4]
E  giao khớp "chấp nhận cả hai"; bù của bù = gốc            [Chap4 Định lý 5, 4; Chap6 Đ.lý 6.5]
F  rỗng/vô hạn: cách đồ thị = cách Định lý 6                [Chap4 Định lý 6]
G  văn phạm trái và phải của cùng ngôn ngữ tương đương      [Chap4 Định lý 7]
H  bơm: x y^i w vẫn thuộc L                                 [Chap4 Bổ đề Bơm]
I  hợp / nối / Kleene khớp định nghĩa trên ngôn ngữ         [Chap4 Định lý 3; Chap2 phép toán ngôn ngữ]
J  văn phạm không phải loại 3 bị từ chối                    [Chap2 Chomsky; Chap4]
K  chứng minh không chính quy bằng bổ đề bơm                [Chap4 Bổ đề Bơm, bài tập 4, 5]
L  PDA khớp ngôn ngữ; w c w^R là DPDA, w w^R là NPDA        [Chap6]
"""
from __future__ import annotations

import sys

import verification.examples as ex
from analysis.language_analysis import equivalent, is_empty_graph, is_empty_theorem, is_infinite_graph, is_infinite_theorem
from operations.fa_ops import complement, concat, intersection, star, union
from conversion.fa_to_grammar import fa_to_left_linear, fa_to_right_linear
from simulation.generator import derive_all, sigma_star
from core.grammar_parser import parse_grammar
from conversion.grammar_to_nfa import NotRegularGrammar, grammar_to_nfa
from conversion.nfa_to_dfa import to_dfa
from analysis.non_regular_proof import LANGS, prove
from analysis.pda_demo import PDA_SAMPLES, is_deterministic, pda_accepts
from analysis.pumping import pump_report
from simulation.simulator import accepts

K_DEFAULT = 6


def _nfa(key):
    g = parse_grammar(ex.BY_KEY[key].text)
    return g, grammar_to_nfa(g)[0]


def _first_diff(words, f, h):
    for w in words:
        if f(w) != h(w):
            return w
    return None


def check_A(k):
    out = []
    for e in ex.REGULAR:
        g, nfa = _nfa(e.key)
        derived = set(derive_all(g, k))
        bad = _first_diff(sigma_star(g.terminals, k), lambda w: w in derived, lambda w: accepts(nfa, w))
        out.append((e.key, bad is None, f"|L(G)∩Σ^≤{k}|={len(derived)}" if bad is None else f"khác nhau ở {bad!r}"))
    return out


def check_B(k):
    out = []
    for e in ex.REGULAR:
        g, nfa = _nfa(e.key)
        dfa = to_dfa(nfa)
        bad = _first_diff(sigma_star(g.terminals, k), lambda w: accepts(nfa, w), lambda w: accepts(dfa, w))
        out.append((e.key, bad is None, f"NFA {len(nfa.states)} -> DFA {len(dfa.states)} trạng thái"
                    if bad is None else f"khác nhau ở {bad!r}"))
    return out


def check_C(k):
    out = []
    for e in ex.REGULAR:
        g, nfa = _nfa(e.key)
        base = set(derive_all(g, k))
        gr, gl = fa_to_right_linear(nfa), fa_to_left_linear(nfa)
        ok_r, ok_l = set(derive_all(gr, k)) == base, set(derive_all(gl, k)) == base
        out.append((e.key, ok_r and ok_l, f"phải:{'ok' if ok_r else 'LỖI'}, trái:{'ok' if ok_l else 'LỖI'}"))
    return out


def check_D(k):
    out = []
    for e in ex.REGULAR:
        g, nfa = _nfa(e.key)
        comp = complement(nfa)
        bad = _first_diff(sigma_star(g.terminals, k), lambda w: accepts(nfa, w), lambda w: not accepts(comp, w))
        out.append((e.key, bad is None, "đúng một trong L, L̄" if bad is None else f"sai ở {bad!r}"))
    return out


def check_E(k):
    out = []
    for k1, k2 in ex.OP_PAIRS:
        (g1, n1), (g2, n2) = _nfa(k1), _nfa(k2)
        inter = intersection(n1, n2)
        words = list(sigma_star(g1.terminals | g2.terminals, k))
        bad = _first_diff(words, lambda w: accepts(n1, w) and accepts(n2, w), lambda w: accepts(inter, w))
        out.append((f"{k1} ∩ {k2}", bad is None, "khớp 'chấp nhận cả hai'" if bad is None else f"sai ở {bad!r}"))
    # kết quả đã biết: ab+ ∩ a+b+ = ab+
    _, n1 = _nfa("ab_plus")
    _, n2 = _nfa("a_plus_b_plus")
    out.append(("ab+ ∩ a+b+ = ab+", equivalent(intersection(n1, n2), n1)[0], "đối chiếu với kết quả suy bằng tay"))
    for e in ex.REGULAR:
        _, nfa = _nfa(e.key)
        out.append((f"bù(bù({e.key}))", equivalent(complement(complement(nfa)), nfa)[0], "bù hai lần = gốc"))
    return out


def check_F(k):
    out = []
    for e in ex.REGULAR:
        _, nfa = _nfa(e.key)
        er, et = is_empty_graph(nfa), is_empty_theorem(nfa)
        ir, it = is_infinite_graph(nfa), is_infinite_theorem(nfa)
        out.append((e.key, er == et and ir == it,
                    f"rỗng={er}/{et}, vô hạn={ir}/{it} (đồ thị/định lý)"))
    # ngôn ngữ hữu hạn và ngôn ngữ rỗng để thử cả hai nhánh
    fin = grammar_to_nfa(parse_grammar("S -> aA | b\nA -> b"))[0]
    emp = grammar_to_nfa(parse_grammar("S -> aS"))[0]
    for name, a, want_empty, want_inf in (("hữu hạn {b,ab}", fin, False, False), ("rỗng S→aS", emp, True, False)):
        er, et, ir, it = is_empty_graph(a), is_empty_theorem(a), is_infinite_graph(a), is_infinite_theorem(a)
        out.append((name, er == et == want_empty and ir == it == want_inf, f"rỗng={er}/{et}, vô hạn={ir}/{it}"))
    return out


def check_G(k):
    out = []
    for kr, kl in ex.SAME_LANGUAGE_PAIRS:
        ok, w, who = equivalent(_nfa(kr)[1], _nfa(kl)[1])
        out.append((f"{kr} ≡ {kl}", ok, "tương đương" if ok else f"khác ở {w!r}"))
    for e in ex.RIGHT_LINEAR:               # FA -> văn phạm TRÁI -> NFA phải tương đương với NFA gốc
        _, nfa = _nfa(e.key)
        back = grammar_to_nfa(fa_to_left_linear(nfa))[0]
        ok, w, _ = equivalent(nfa, back)
        out.append((f"{e.key} ≡ (FA→trái→NFA)", ok, "tương đương" if ok else f"khác ở {w!r}"))
    # phản ví dụ: hai ngôn ngữ khác nhau phải bị phát hiện
    ok, w, who = equivalent(_nfa("ab_plus")[1], _nfa("a_plus_b_plus")[1])
    out.append(("ab+ ≢ a+b+ (phát hiện)", (not ok) and w == "aab", f"chuỗi phản chứng ngắn nhất: {w!r}"))
    return out


def check_H(k):
    out = []
    for e in ex.REGULAR:
        _, nfa = _nfa(e.key)
        reports, note = pump_report(nfa, max_i=4)
        ok = all(r["ok"] for r in reports)
        out.append((e.key, ok, f"{len(reports)} chuỗi thử" if reports else "bỏ qua: " + note[:60]))
    return out


def check_I(k):
    out = []
    for k1, k2 in ex.OP_PAIRS:
        (g1, n1), (g2, n2) = _nfa(k1), _nfa(k2)
        alpha = g1.terminals | g2.terminals
        words = list(sigma_star(alpha, k))
        u, c = union(n1, n2), concat(n1, n2)
        bad_u = _first_diff(words, lambda w: accepts(n1, w) or accepts(n2, w), lambda w: accepts(u, w))
        bad_c = _first_diff(words, lambda w: any(accepts(n1, w[:i]) and accepts(n2, w[i:])
                                                for i in range(len(w) + 1)), lambda w: accepts(c, w))
        out.append((f"{k1} ∪ {k2}", bad_u is None, "khớp định nghĩa" if bad_u is None else f"sai ở {bad_u!r}"))
        out.append((f"{k1} · {k2}", bad_c is None, "khớp định nghĩa" if bad_c is None else f"sai ở {bad_c!r}"))
    for e in ex.RIGHT_LINEAR[:4]:
        g, n = _nfa(e.key)
        s = star(n)
        memo = {}

        def in_star(w):
            if w == "":
                return True
            if w in memo:
                return memo[w]
            memo[w] = any(accepts(n, w[:i]) and in_star(w[i:]) for i in range(1, len(w) + 1))
            return memo[w]

        bad = _first_diff(sigma_star(g.terminals, k), in_star, lambda w: accepts(s, w))
        out.append((f"({e.key})*", bad is None, "khớp định nghĩa" if bad is None else f"sai ở {bad!r}"))
    return out


def check_J(k):
    out = []
    for e in ex.REJECTED:
        try:
            grammar_to_nfa(parse_grammar(e.text))
            out.append((e.key, False, "lẽ ra phải bị từ chối"))
        except NotRegularGrammar as err:
            out.append((e.key, True, err.reasons[0][:70]))
    return out


def check_K(k):
    out = []
    for lang in LANGS:
        ok, _ = prove(lang)
        out.append((lang.key, ok == (not lang.regular), "bác bỏ được mọi cách chia" if ok
                    else "tồn tại cách chia không bị bác bỏ (đúng, vì L chính quy)" if lang.regular else "LỖI"))
    return out


def check_L(k):
    out = []
    for name, (mk, pred) in PDA_SAMPLES.items():
        pda = mk()
        alpha = sorted(pda.input_alphabet)
        bad = _first_diff(sigma_star(alpha, 7), lambda w: pda_accepts(pda, w)[0], pred)
        out.append((name, bad is None, "khớp ngôn ngữ" if bad is None else f"khác ở {bad!r}"))
    det = {n: is_deterministic(mk()) for n, (mk, _) in PDA_SAMPLES.items()}
    out.append(("DPDA/NPDA", det["wcwR"] and not det["wwR"], f"wcwR đơn định={det['wcwR']}, wwR đơn định={det['wwR']}"))
    return out


CHECKS = [
    ("A", "Văn phạm sinh được ⇔ NFA chấp nhận", check_A), ("B", "NFA ≡ DFA trên mọi chuỗi", check_B),
    ("C", "Grammar → NFA → Grammar' (phải, trái)", check_C), ("D", "Phần bù", check_D),
    ("E", "Phép giao và bù kép", check_E), ("F", "Rỗng/vô hạn: đồ thị vs Định lý 6", check_F),
    ("G", "Tương đương văn phạm trái/phải", check_G), ("H", "Thử bơm trên DFA", check_H),
    ("I", "Hợp / nối / Kleene", check_I), ("J", "Từ chối văn phạm không phải loại 3", check_J),
    ("K", "Bổ đề Bơm: chứng minh không chính quy", check_K), ("L", "PDA: wcwR (DPDA), wwR (NPDA), a^n b^n", check_L),
]


def run_all(k: int = K_DEFAULT, only: str | None = None, verbose: bool = True) -> bool:
    total, failed = 0, 0
    for cid, title, fn in CHECKS:
        if only and cid != only.upper():
            continue
        results = fn(k)
        n_ok = sum(1 for _, ok, _ in results if ok)
        total += len(results)
        failed += len(results) - n_ok
        print(f"\n[{cid}] {title}   ({n_ok}/{len(results)} đạt)")
        for name, ok, detail in results:
            if verbose or not ok:
                print(f"    {'✔' if ok else '✘'} {name:<34} {detail}")
    print(f"\nTỔNG KẾT: {total - failed}/{total} phép kiểm tra đạt" + ("" if not failed else f", {failed} LỖI"))
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all(int(sys.argv[1]) if len(sys.argv) > 1 else K_DEFAULT) else 1)
