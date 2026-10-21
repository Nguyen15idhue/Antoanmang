# 05 - Theo dõi tiến độ

Quy ước trạng thái: `[ ]` chưa làm, `[~]` đang làm, `[x]` xong (có bằng chứng).

## Giai đoạn A - Lab01

| # | Việc | Trạng thái | Bằng chứng | Ghi chú |
|---|---|---|---|---|
| A0.1 | Sửa host-only thành `192.168.117.1/24` | [ ] | ảnh `VBoxManage list hostonlyifs` | Đang là `169.254.27.230/16` |
| A0.2 | Unregister 2 VM `<inaccessible>` | [ ] | ảnh `VBoxManage list vms` | Không xoá đĩa |
| A1.1 | Boot Attack (`NguyenMachine`) | [ ] | ảnh desktop VM | State hiện tại `aborted` |
| A1.2 | Boot Server (`Server3`) | [ ] | ảnh desktop VM | State hiện tại `poweroff` |
| A1.3 | Xác nhận IP `.10` / `.13` | [ ] | ảnh `ifconfig` | |
| A1.4 | Ping 2 chiều | [ ] | ảnh terminal | |
| A1.5 | Kiểm tra nmap/Wireshark | [ ] | ảnh `nmap -V`, `wireshark -v` | |
| A2 | Task 1: `nmap -sn` | [ ] | `task1.pcap` + ảnh | Kết luận: ARP Ping Scan |
| A3 | Task 2: `nmap -sS -F` | [ ] | `task2.pcap` + ảnh | Kết luận: TCP SYN Scan |
| A4 | Task 3: `nmap -sA -F` | [ ] | `task3.pcap` + ảnh | Kết luận: TCP ACK Scan |
| A5.1 | Task 4: tìm dịch vụ email | [ ] | ảnh nmap | Dùng `.117` ở nhà, `.100` ở lớp |
| A5.2 | Quét `-sV -O` | [ ] | `task4.pcap` + ảnh | |
| A5.3 | Bảng CVE | [ ] | bảng trong bài | Nguồn cvedetails.com |

## Giai đoạn B - Lab02

| # | Việc | Trạng thái | Bằng chứng | Ghi chú |
|---|---|---|---|---|
| B-1 | Nhận source `it4263lab/lab02` | [ ] | danh sách file | **Đang chặn** |
| B-2 | Nhận tham số `x`, `y` | [ ] | tin nhắn/ thông báo lớp | |
| B-3 | Nhận VM Ubuntu 20.04 | [ ] | ảnh VM chạy | Phòng lab |
| B0 | Cài/kiểm tra công cụ trong VM | [ ] | ảnh phiên bản | |
| B1.1 | Sửa `docker-compose.yml` | [ ] | diff file | |
| B1.2 | `build` + `up` 3 container | [ ] | ảnh `docker ps` | |
| B1.3 | Ghi IP/MAC/ARP 3 máy | [ ] | 3 ảnh | Điền mục đầu báo cáo |
| B1.4 | Ping giữa các container | [ ] | ảnh | |
| B2 | KB1: `scenario1.py` + `task1.pcap` | [ ] | pcap + 3 ảnh | Trả lời 5 câu |
| B3 | KB2: `scenario2.py` + `task2.pcap` | [ ] | pcap + 3 ảnh | Trả lời 5 câu |
| B4 | KB3: MITM + `task3.pcap` | [ ] | pcap + 7 ảnh | Có so sánh trước/sau |
| B5 | Phòng chống `arp -s` | [ ] | 3 ảnh | Cờ M |
| B6.1 | Cắt pcap <= 1 MB | [ ] | `ls -lh` | |
| B6.2 | Điền đủ báo cáo | [ ] | file báo cáo | Theo `03-lab02-checklist-bao-cao.md` |
| B6.3 | Đóng zip đúng tên | [ ] | `unzip -l` | `NhomX_Lab02_BaoCao.zip` |

## Nhật ký thực hiện

| Ngày | Bước | Kết quả | Vấn đề gặp | Cách xử lý |
|---|---|---|---|---|
| 2026-10-21 | Kiểm tra môi trường | Có 2 VM + 2 đĩa; host-only sai IP; Docker engine tắt; thiếu source Lab02 | - | Ghi tại `00-hien-trang-moi-truong.md` |
|  |  |  |  |  |
|  |  |  |  |  |

## Blocker hiện tại

| Blocker | Ảnh hưởng | Cần ai/ cái gì | Hành động |
|---|---|---|---|
| Chưa có source `it4263lab/lab02` | Không thể làm B1 -> B6 | Giảng viên/ lớp | Liên hệ xin file nén kèm hướng dẫn cấu hình IP |
| Chưa có VM Ubuntu 20.04 | Không có môi trường chạy Docker đúng chuẩn | Phòng lab | Đăng ký nhận máy; nếu không có, dùng phương án 9 trong `02-lab02-ke-hoach.md` |
| Chưa có `x`, `y` | Không sửa được compose | Giảng viên | Hỏi kèm mã lớp thực hành |

## Bước tiếp theo đề xuất

1. Chạy A0 + A1 (sửa host-only, boot 2 VM, xác nhận IP) - làm được ngay, không phụ thuộc ai.
2. Làm A2 -> A5 để có 4 pcap và bảng CVE.
3. Song song: gửi giảng viên xin source Lab02 + `x`, `y` + xác nhận VM Ubuntu 20.04.
