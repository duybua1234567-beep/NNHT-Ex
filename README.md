# Đồ án: Finite Automaton và Grammar

## Chạy (Python 3.9+, không cần thư viện ngoài; chạy từ thư mục này)

    python main.py                       # MẶC ĐỊNH mở giao diện (bấm Run trong IDE cũng vậy); thiếu tkinter thì dùng menu
    python main.py --menu                # menu dòng lệnh
    python main.py --demo                # chạy tuần tự 22 bước (đổi ví dụ: --example left_a_abplus)
    python main.py --checks              # bộ kiểm tra chéo A..L (-k 6: độ dài chuỗi tối đa)
    python main.py --gui                 # giao diện Tkinter (hoặc: python -m ui)
    python -m verification.cross_checks  # chạy riêng bộ kiểm tra chéo
    # Linux thiếu tkinter: sudo apt install python3-tk

## Cấu trúc thư mục (gom theo nhóm chức năng)

    fa_grammar/
    ├── main.py, demo.py          Điểm vào: menu / demo tuần tự 22 bước
    ├── core/                     NỀN TẢNG
    │   ├── models.py             bước 1, 2   | Chap2, Chap4, Chap2_1, Chap1
    │   ├── grammar_parser.py     bước 1, 3, 4| Chap2 (quy ước, Chomsky), Chap4 (tuyến tính trái/phải)
    │   └── normalizer.py         bước 5      | tự bổ sung; Chap2 (ω^R, văn phạm tương đương)
    ├── conversion/               CHUYỂN ĐỔI
    │   ├── grammar_to_nfa.py     bước 6, 7   | Chap4 (quy tắc 5 bước, Định lý 1)  <- LÕI
    │   ├── nfa_to_dfa.py         bước 13     | Chap3_1, Chap2_1, Chap1
    │   └── fa_to_grammar.py      bước 14     | Chap4 Định lý 2
    ├── simulation/               MÔ PHỎNG
    │   ├── simulator.py          bước 8, 9   | Chap2, Chap2_1, Chap6 (ID, ⊢)
    │   └── generator.py          bước 10     | Chap2 (⇒, ⇒*, L(G), bài tập 2.3)
    ├── operations/               PHÉP TOÁN
    │   └── fa_ops.py             bước 15-17  | Chap4 Định lý 3, 4, 5; Chap6 Định lý 6.5
    ├── analysis/                 PHÂN TÍCH & LÝ THUYẾT
    │   ├── language_analysis.py  bước 18, 19 | Chap4 Định lý 6, 7; Chap1
    │   ├── pumping.py            bước 20     | Chap4 Bổ đề Bơm
    │   ├── non_regular_proof.py  bước 21     | Chap4 Bổ đề Bơm, bài tập 4, 5
    │   └── pda_demo.py           bước 22     | Chap6 (PDA), Chap2 (L3 ⊂ L2)
    ├── verification/             KIỂM CHỨNG
    │   ├── examples.py           bước 12     | Chap2 (ví dụ 2.5), Chap4 (ví dụ, bài tập)
    │   └── cross_checks.py       bước 11 + mọi bước | kiểm tra chéo A..L
    └── ui/                       GIAO DIỆN (8 tab, mỗi tab ghi chương áp dụng)
        ├── app.py                cửa sổ Tkinter
        ├── logic.py              phần xử lý, không dính Tk (kiểm thử được)
        ├── draw.py               bố cục và vẽ sơ đồ trạng thái (Chap1: đồ thị có hướng)
        └── __main__.py           python -m ui

## Phần tự bổ sung (slide chưa dạy, nên nêu rõ trong báo cáo)
- Tách luật A → w với |w| > 1 bằng biến phụ (core/normalizer.py).
- Văn phạm tuyến tính trái: dựng qua ngôn ngữ đảo (reverse_grammar + reverse_automaton).
- Thuật toán cụ thể của Định lý 3-7 (slide chỉ phát biểu định lý).
- Luật đơn vị A → B được chuyển thành ε-chuyển.

## Lưu ý khi đối chiếu slide
- Bổ đề Bơm ở Chap4 ghi |z| ≤ n và |xy| < n; code dùng dạng chuẩn |z| ≥ n, |xy| ≤ n.
- Bài tập 5a Chap4 chép là "02n": nếu là 0^(2n) thì L chính quy, nếu là 0^(2^n) thì không (cả hai có trong analysis/non_regular_proof.py).
- Ký hiệu NFA/DFA trong conversion/nfa_to_dfa.py chưa đối chiếu với Chap3_1 và otomat-huu-han.
- Giao diện chưa được chạy thử trên màn hình thật (môi trường phát triển không có tkinter).
