# Kế hoạch thực hành An toàn mạng - Lab01 & Lab02

Thư mục làm việc: `F:\3.Laptrinh\2.Learning\Antoanmang`
Ngày lập kế hoạch: 2026-10-21

## 1. Mục tiêu

| Lab | Tên bài | Đầu ra |
|---|---|---|
| Lab01 | Phân tích các kỹ thuật do thám hệ thống (nmap + Wireshark) | `task1.pcap`, `task2.pcap`, `task3.pcap`, `task4.pcap`, bảng CVE |
| Lab02 | Phân tích kỹ thuật tấn công ARP Cache Poisoning | `NhomX_Lab02_BaoCao.zip` gồm báo cáo + 3 file pcap (mỗi file <= 1 MB) |

## 2. Thứ tự thực hiện

1. **Giai đoạn A - Lab01** (làm được ngay): sửa hạ tầng VirtualBox, khởi động 2 VM có sẵn, làm 4 task nmap, lưu pcap, lập bảng CVE.
2. **Giai đoạn B - Lab02** (đang bị chặn): cần **bộ source `it4263lab/lab02`** từ giảng viên và **VM Ubuntu 20.04** của phòng lab. Sau khi có đủ, làm tuần tự 4.1 -> 4.5 và đóng gói.

## 3. Cấu trúc tài liệu

| File | Nội dung |
|---|---|
| `00-hien-trang-moi-truong.md` | Kiểm tra thực tế máy host, VM, Docker, các điểm lệch so với yêu cầu |
| `01-lab01-ke-hoach.md` | Kế hoạch chi tiết Lab01: sửa mạng, 4 task, mẫu phân tích, tiêu chí hoàn thành |
| `02-lab02-ke-hoach.md` | Kế hoạch chi tiết Lab02: setup Docker, 3 kịch bản, phòng chống, đóng gói |
| `03-lab02-checklist-bao-cao.md` | Đối chiếu từng ô của `Lab02_BC.pdf`: điền gì, chụp ảnh gì, thang điểm |
| `04-xu-ly-su-co.md` | Lỗi thường gặp và cách xử lý (ARP, ip_forward, br-, pcap > 1 MB, apt 12.04) |
| `05-tien-do.md` | Bảng theo dõi tiến độ + nhật ký thực hiện |

## 4. Trạng thái hiện tại

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| VirtualBox 7.2.20 | Có | Host-only adapter đang sai IP (`169.254.27.230/16`) |
| VM Attack (`Attack.vdi`) | Có, state `aborted` | Đăng ký dưới tên `NguyenMachine` |
| VM Server (`Ubuntu_DNS_Server-disk1.vdi`) | Có, state `poweroff` | Đăng ký dưới tên `Server3` |
| 2 VM `<inaccessible>` | Rác | Nên unregister |
| Docker Desktop 29.1.3 | Cài, engine đang tắt | Chưa cần cho Lab02 nếu dùng VM phòng lab |
| Source `it4263lab/lab02` | **Chưa có** | Chặn toàn bộ Lab02 |
| VM Ubuntu 20.04 | **Chưa có** | Theo kế hoạch sẽ xin của phòng lab |

Chi tiết bằng chứng: xem `00-hien-trang-moi-truong.md`.

## 5. Quy ước làm việc

- Mỗi bước chỉ được coi là xong khi có **bằng chứng**: ảnh chụp màn hình hoặc file `.pcap`, kèm mô tả ngắn trong `05-tien-do.md`.
- Ảnh đặt tên theo mẫu: `L01-A2-buoc3-wireshark-arp.png`, `L02-B2-kb1-arp-user.png` (tiền tố lab, bước, nội dung).
- File pcap luôn lưu kèm bộ lọc đã dùng và thời điểm capture trong ghi chú.
- Trước mỗi kịch bản Lab02: `docker restart` cả 3 container để xoá ARP cache nhiễm độc.
- Không dùng lại nội dung bài báo cáo mẫu đã có (bài `PhamQuynhChi_223001699_lab2.pdf` thiếu Kịch bản 2 và 3).

## 6. Điều kiện hoàn thành (Definition of Done)

- Lab01: 4 file pcap mở được bằng Wireshark, mỗi file kèm 1 đoạn phân tích nêu đúng kỹ thuật quét + bảng CVE có ít nhất các dịch vụ tìm thấy.
- Lab02: báo cáo điền đủ 100% ô của `Lab02_BC.pdf`, 3 pcap <= 1 MB, zip đúng tên `NhomX_Lab02_BaoCao.zip`, mở lại zip kiểm tra đủ file.
