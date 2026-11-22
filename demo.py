"""demo.py - Chạy tuần tự toàn bộ 22 bước trên một ví dụ (không cần nhập tay).

Mỗi mục in rõ bước nào và kiến thức thuộc chương nào.
"""
from __future__ import annotations

import verification.examples as ex
from analysis.language_analysis import equivalent, is_empty_graph, is_empty_theorem, is_infinite_graph, is_infinite_theorem
from verification.cross_checks import run_all
from operations.fa_ops import complement, concat, intersection, star, union
from conversion.fa_to_grammar import fa_to_left_linear, fa_to_right_linear
from simulation.generator import derive_all, format_derivation, language_up_to, sigma_star
from core.grammar_parser import classify, describe_kind, parse_grammar
from conversion.grammar_to_nfa import NotRegularGrammar, grammar_to_nfa
from conversion.nfa_to_dfa import to_dfa
from analysis.non_regular_proof import LANGS, prove
from analysis.pda_demo import format_ids, is_deterministic, pda_accepts, pda_anbn, pda_wcwr, pda_wwr
from analysis.pumping import format_pump, pump_report
from simulation.simulator import accepts, format_trace, simulate


def head(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def run_demo(key: str = "ab_plus", k: int = 6) -> None:
    e = ex.BY_KEY[key]
    head(f"BƯỚC 1-3 | Đọc văn phạm  [Chap2: G=(V,T,P,S), quy ước ký hiệu]\n{e.title} - {e.note}")
    g = parse_grammar(e.text)
    print(g.to_text())
    print(f"V={sorted(g.variables)}  T={sorted(g.terminals)}  S={g.start}")

    head("BƯỚC 4 | Kiểm tra loại văn phạm  [Chap2: Chomsky; Chap4: tuyến tính trái/phải]")
    kind, reasons = classify(g)
    print("Loại:", describe_kind(kind))
    for bad in ex.REJECTED:
        try:
            grammar_to_nfa(parse_grammar(bad.text))
        except NotRegularGrammar as err:
            print(f"Thử văn phạm sai loại '{bad.title}': bị từ chối - {err.reasons[0]}")

    head("BƯỚC 5-7 | Chuẩn hóa và chuyển Grammar → NFA  [Chap4: quy tắc 5 bước; Định lý 1]")
    nfa, info = grammar_to_nfa(g)
    for line in info.log:
        print("  •", line)
    print(nfa.describe())
    print(nfa.to_table())
    print("\nDOT (dán vào graphviz để vẽ):\n" + nfa.to_dot())

    head("BƯỚC 8-9 | Mô phỏng chuỗi  [Chap2_1: cấu hình, move, accepter; Chap6: ID, ⊢]")
    sample = language_up_to(g, 4)
    tests = (sample[:2] + ["", "ba", "abbb"]) if sample else ["", "a"]
    for w in tests:
        try:
            print(format_trace(simulate(nfa, w), w))
        except ValueError as err:
            print(f"Chuỗi {w!r}: {err}")

    head(f"BƯỚC 10-12 | Dẫn xuất và đối chứng L(G) = L(M)  [Chap2: ⇒, ⇒*, L(G), Đ/n 3; Chap4: Định lý 1]")
    derived = derive_all(g, k)
    for w in language_up_to(g, 4)[:5]:
        print(f"  {w or 'ε':<8}: {format_derivation(derived[w])}")
    mism = [w for w in sigma_star(g.terminals, k) if (w in derived) != accepts(nfa, w)]
    n_all = sum(1 for _ in sigma_star(g.terminals, k))
    print(f"Đối chiếu {n_all} chuỗi của Σ* (độ dài <= {k}): {len(derived)} chuỗi do văn phạm sinh, "
          f"{'KHỚP HOÀN TOÀN với NFA' if not mism else 'LỆCH ở ' + str(mism[:5])}")

    head("BƯỚC 13 | NFA → DFA  [Chap3_1; Chap2_1; Chap1: tập lũy thừa]")
    dfa = to_dfa(nfa)
    print(dfa.to_table())

    head("BƯỚC 14 | FA → Grammar  [Chap4: Định lý 2]")
    print("Tuyến tính phải:\n" + fa_to_right_linear(nfa).to_text())
    print("\nTuyến tính trái:\n" + fa_to_left_linear(nfa).to_text())

    head("BƯỚC 15-17 | Hợp, nối, Kleene, bù, giao  [Chap4: Định lý 3, 4, 5; Chap6: Định lý 6.5]")
    g2 = parse_grammar(ex.BY_KEY["a_plus_b_plus"].text)
    n2 = grammar_to_nfa(g2)[0]
    alpha = g.terminals | g2.terminals
    for name, aut in (("L1 ∪ L2", union(nfa, n2)), ("L1 · L2", concat(nfa, n2)), ("L1*", star(nfa)),
                      ("bù L1", complement(nfa, alpha)), ("L1 ∩ L2", intersection(nfa, n2))):
        first = [w for w in sigma_star(alpha, 5) if accepts(aut, w)][:6]
        print(f"  {name:<8} ({len(aut.states)} trạng thái): vài chuỗi đầu tiên = {[w or 'ε' for w in first]}")
    print(f"  (L1 = {e.title}; L2 = a+b+)")

    head("BƯỚC 18 | Rỗng / vô hạn  [Chap4: Định lý 6 (n ≤ l < 2n) và cách duyệt đồ thị  [Chap1]]")
    print(f"  Rỗng : đồ thị={is_empty_graph(nfa)}, định lý={is_empty_theorem(nfa)}")
    print(f"  Vô hạn: đồ thị={is_infinite_graph(nfa)}, định lý={is_infinite_theorem(nfa)}")

    head("BƯỚC 19 | Tương đương  [Chap4: Định lý 7]")
    for kr, kl in ex.SAME_LANGUAGE_PAIRS:
        ok, w, _ = equivalent(grammar_to_nfa(parse_grammar(ex.BY_KEY[kr].text))[0],
                              grammar_to_nfa(parse_grammar(ex.BY_KEY[kl].text))[0])
        print(f"  {kr} (tuyến tính phải) ≡ {kl} (tuyến tính trái): {ok}")
    ok, w, who = equivalent(nfa, n2)
    print(f"  {e.title} ≡ a+b+ ? {ok}" + (f"; chuỗi phản chứng ngắn nhất {w!r}" if not ok else ""))

    head("BƯỚC 20 | Thử bơm trên DFA  [Chap4: Bổ đề Bơm, dạng chuẩn]")
    reports, note = pump_report(nfa, max_i=3, per_length=1)
    for r in reports[:3]:
        print(format_pump(r))
    print(note or f"  => {sum(r['ok'] for r in reports)}/{len(reports)} chuỗi bơm thành công")

    head("BƯỚC 21 | Chứng minh KHÔNG chính quy bằng Bổ đề Bơm  [Chap4: bài tập 4, 5]")
    for lang in LANGS[:3] + LANGS[4:]:
        ok, log = prove(lang, range(2, 5))
        print(lang.title + f"\n  ý tưởng: {lang.note}")
        print("\n".join(log[:2]))
        print("  => " + ("bác bỏ được mọi cách chia => KHÔNG chính quy" if ok
                         else "KHÔNG kết luận được bằng chuỗi này (thực tế L chính quy)"))

    head("BƯỚC 22 | Vì sao CFG/PDA vượt ra ngoài FA  [Chap6: Thí dụ 6.1, 6.3; Chap2: L3 ⊂ L2]")
    for name, pda, w in (("w c wᴿ (đơn định)", pda_wcwr(), "001c100"), ("w wᴿ (KHÔNG đơn định)", pda_wwr(), "001100"),
                         ("aⁿbⁿ", pda_anbn(), "aaabbb")):
        ok, ids = pda_accepts(pda, w)
        print(f"{name}: {'DPDA' if is_deterministic(pda) else 'NPDA'}, chuỗi {w}: {'chấp nhận' if ok else 'từ chối'}")
        if ids:
            print(format_ids(ids))
    print("=> aⁿbⁿ cần Stack để đếm; FA hữu hạn trạng thái không nhớ được n không giới hạn.")

    head("TỔNG KẾT | Kiểm tra chéo A..L")
    run_all(k, verbose=False)


if __name__ == "__main__":
    run_demo()
