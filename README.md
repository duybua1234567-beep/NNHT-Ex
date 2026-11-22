# NNHT
# Al_Trading

## Rules
AE phải push lên nhánh riêng của mình trước khi mình merge vào `main` cho AE.
AE có thể push nhánh của mình, còn nhánh `main` phải tạo Pull Request và được review trước khi merge.

## Lần đầu mang code về và push code lên
Tạo folder chứa
Nhảy vào folder
git clone <url_github>
Nhảy vào folder
git pull origin main
git checkout -b <ten_nhanh_phu_moi>
git add .
git commit -m "first commit"
git push -u origin <ten_nhanh_phu_cua_minh>

## Làm sao để lấy code sau khi 1 người làm xong
Người A làm xong phần đầu, push code lên nhánh riêng, và tạo Pull Request.
Khang sẽ review và merge nó vào `main`.
Người B tiếp tục làm thì lên local, nhảy qua nhánh `main`, `git pull origin main` về, sau đó nhảy qua nhánh phụ để làm tiếp và `git merge main`.

## Và làm tiếp
Đang ở nhánh phụ:
git checkout main
git pull origin main
git checkout <nhánh_phụ>
git merge main

## Để push code của mình lên
Đang ở nhánh phụ:
git add <đúng_folder>
git commit -m "comment gì đó"
git push -u origin <ten_nhanh_phu> (lần đầu)
git push (lần sau)
