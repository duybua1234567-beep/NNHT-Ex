"""non_regular_proof.py - Dùng Bổ đề Bơm để chứng minh ngôn ngữ KHÔNG chính quy (bước 21).

[Chap4] Bổ đề Bơm, 5 bước chứng minh (slide "Cách chứng minh một ngôn ngữ L không phải RL"),
        bài tập 4 (0^n 1^n) và bài tập 5 (a, b, c).
Chương trình không "tự quyết định" một ngôn ngữ có chính quy hay không (bổ đề chỉ là điều kiện cần);
nó chỉ kiểm tra giúp BƯỚC 3-4: với chuỗi chọn w và hằng số bơm p, MỌI cách chia w = xyz
(|xy| <= p, |y| >= 1) đều có một i làm xy^i z ∉ L.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


def _is_prime(n: int) -> bool:
    return n >= 2 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def _next_prime(n: int) -> int:
    while not _is_prime(n):
        n += 1
    return n


def _anbn(s): return bool(re.fullmatch(r"(0+)(1+)", s)) and s.count("0") == s.count("1")


def _b(s):
    m = re.fullmatch(r"(0+)(1+)(0+)", s)
    return bool(m) and len(m.group(3)) == len(m.group(1)) + len(m.group(2))


def _prime(s): return set(s) <= {"0"} and _is_prime(len(s))
def _pow2(s):
    n = len(s)
    return set(s) <= {"0"} and n >= 2 and n & (n - 1) == 0


def _even(s): return set(s) <= {"0"} and len(s) >= 2 and len(s) % 2 == 0


@dataclass
class Lang:
    key: str
    title: str
    member: Callable
    witness: Callable          # p -> chuỗi w ∈ L, |w| >= p
    regular: bool              # thực tế có chính quy không (để đối chiếu kết quả)
    note: str


LANGS = [
    Lang("anbn", "L = {0^k 1^k | k > 0}  [Chap4 - bài tập 4]", _anbn,
         lambda p: "0" * p + "1" * p, False, "chọn w = 0^p 1^p, bơm i = 2 làm thừa số 0"),
    Lang("b", "L = {0^n 1^m 0^(n+m) | n,m > 0}  [Chap4 - bài tập 5b]", _b,
         lambda p: "0" * p + "1" * p + "0" * (2 * p), False, "chọn w = 0^p 1^p 0^(2p), bơm i = 2"),
    Lang("c", "L = {0^n | n nguyên tố}  [Chap4 - bài tập 5c]", _prime,
         lambda p: "0" * _next_prime(p + 1), False, "chọn w = 0^q (q nguyên tố >= p), bơm i = q+1 => độ dài q(m+1) là hợp số"),
    Lang("a_pow2", "L = {0^(2^n) | n >= 1}  [Chap4 - bài tập 5a, nếu đề là 2 mũ n]", _pow2,
         lambda p: "0" * (2 ** max(p, 1)), False, "bơm i = 2 làm độ dài nằm giữa 2^p và 2^(p+1)"),
    Lang("a_2n", "L = {0^(2n) | n > 0} = (00)+  [Chap4 - bài tập 5a, nếu đề là 2n]", _even,
         lambda p: "0" * (2 * p), True, "CHÍNH QUY: có cách chia y = 00 bơm thế nào cũng ở trong L"),
]


def split_results(member, w: str, p: int, max_i: int):
    """Với mọi (x,y,z): |xy| <= p, |y| >= 1 -> các i làm xy^i z ∉ L."""
    out = []
    for xy_len in range(1, min(p, len(w)) + 1):
        for y_len in range(1, xy_len + 1):
            x, y, z = w[:xy_len - y_len], w[xy_len - y_len:xy_len], w[xy_len:]
            bad = [i for i in range(max_i + 1) if not member(x + y * i + z)]
            out.append((x, y, z, bad))
    return out


def prove(lang: Lang, p_values=range(1, 6)) -> tuple[bool, list]:
    """Với từng hằng số bơm p thử: mọi cách chia đều bị bác bỏ? Trả về (đúng cho mọi p, log)."""
    log, all_ok = [], True
    for p in p_values:
        w = lang.witness(p)
        assert lang.member(w), f"chuỗi chọn không thuộc L: {w}"
        res = split_results(lang.member, w, p, max_i=len(w) + 2)
        refuted = all(bad for *_, bad in res)
        all_ok &= refuted
        shown = "; ".join(f"y={y!r}->i={bad[0]}" for _, y, _, bad in res[:4] if bad)
        escape = next(((x, y, z) for x, y, z, bad in res if not bad), None)
        log.append(f"  p={p}: w={w if len(w) <= 24 else w[:10] + '...' + w[-6:]} (|w|={len(w)}), "
                   f"{len(res)} cách chia, "
                   + ("MỌI cách đều bị bác bỏ" if refuted else f"có cách chia KHÔNG bị bác bỏ: y={escape[1]!r}")
                   + (f"  [{shown}]" if refuted else ""))
    return all_ok, log
