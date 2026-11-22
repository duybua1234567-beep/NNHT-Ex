"""examples.py - Bộ ví dụ kiểm thử (bước 12).

Nguồn ghi chú ở từng ví dụ: Chap2 (ví dụ 2.5), Chap4 (ví dụ, bài tập), hoặc TỰ THÊM.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Example:
    key: str
    title: str
    text: str
    note: str
    regular: bool = True


EXAMPLES = [
    Example("ab_plus", "ab+  (S→aA, A→bA|b)", "S -> aA\nA -> bA | b",
            "[Chap4 - ví dụ chuyển VPCQ thành FA] L = {a b^n | n >= 1}"),
    Example("a_plus_b_plus", "a+b+", "S -> aS | aA\nA -> bA | b",
            "[Chap2 - ví dụ 2.5 mục 1; cũng là bài tập Chap4 3b] L = {a^m b^n | m,n >= 1}"),
    Example("contains_000", "Chứa 3 số 0 liên tiếp", "S -> 0S | 1S | 000A\nA -> 0A | 1A | ε",
            "[Chap4 - bài tập 2a] dùng luật có |w| = 3 => thử bước chuẩn hóa (TỰ BỔ SUNG)"),
    Example("ends_00", "Kết thúc bằng 00", "S -> 0S | 1S | 00",
            "[Chap4 - bài tập 2b] luật A → w với |w| = 2, không có biến"),
    Example("ab_star_a", "(ab)*a", "S -> abS | a",
            "[Chap4 - ví dụ tuyến tính phải G2] luật S → abS có |w| = 2"),
    Example("eps_11", "Có luật S → ε", "S -> ε | 1A\nA -> 1B | 1\nB -> 1A",
            "[Chap2 - ví dụ văn phạm chính quy G1] thử bước 5 của quy tắc (A → ε)"),
    Example("unit_rule", "b*a* (luật đơn vị)", "S -> A | bS\nA -> aA | ε",
            "TỰ THÊM: luật đơn vị S → A trở thành ε-chuyển"),
    Example("a_abplus_right", "a(ab)+ (tuyến tính phải)", "S -> aA\nA -> abA | ab",
            "TỰ THÊM: cùng ngôn ngữ với 'left_a_abplus'"),
    Example("left_a_abplus", "a(ab)+ (tuyến tính trái)", "S -> Aab\nA -> Aab | B\nB -> a",
            "[Chap4 - ví dụ tuyến tính trái G1]"),
    Example("left_ends_00", "Kết thúc bằng 00 (tuyến tính trái)", "S -> T00\nT -> T0 | T1 | ε",
            "TỰ THÊM: cùng ngôn ngữ với 'ends_00'"),
    Example("non_anbn", "S → aSb | ab (loại 2)", "S -> aSb | ab",
            "[Chap2 - ví dụ 2.5 mục 2] KHÔNG chính quy => phải bị từ chối", regular=False),
    Example("non_mixed", "Trộn trái và phải", "S -> aS | Sb | a",
            "TỰ THÊM: vừa có aS (phải) vừa có Sb (trái) => không phải văn phạm chính quy", regular=False),
    Example("non_csg", "Văn phạm cảm ngữ cảnh a^n b^n c^n",
            "S -> aSBC | aBC\nCB -> BC\naB -> ab\nbB -> bb\nbC -> bc\ncC -> cc",
            "[Chap2 - ví dụ 2.5 mục 3] vế trái không phải biến đơn => từ chối", regular=False),
]

BY_KEY = {e.key: e for e in EXAMPLES}
REGULAR = [e for e in EXAMPLES if e.regular]
RIGHT_LINEAR = [BY_KEY[k] for k in ("ab_plus", "a_plus_b_plus", "contains_000", "ends_00", "ab_star_a",
                                    "eps_11", "unit_rule", "a_abplus_right")]
LEFT_LINEAR = [BY_KEY[k] for k in ("left_a_abplus", "left_ends_00")]
REJECTED = [e for e in EXAMPLES if not e.regular]
# cặp (văn phạm phải, văn phạm trái) cùng ngôn ngữ - dùng cho kiểm tra tương đương (bước 19)
SAME_LANGUAGE_PAIRS = [("ends_00", "left_ends_00"), ("a_abplus_right", "left_a_abplus")]
# cặp dùng cho giao / hợp / nối (bước 15, 17)
OP_PAIRS = [("ab_plus", "a_plus_b_plus"), ("contains_000", "ends_00")]
