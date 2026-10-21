# 03 - Checklist báo cáo Lab02 (đối chiếu `Lab02_BC.pdf`)

Dùng tài liệu này khi điền báo cáo: mỗi dòng của mẫu ứng với một việc phải làm. Cột **Ảnh** là ảnh chụp bắt buộc (tên gợi ý), cột **Trả lời** là nội dung tối thiểu phải có.

## A. Phần đầu báo cáo

| Ô của mẫu | Nội dung cần điền | Ghi chú |
|---|---|---|
| Tiêu đề | **BÁO CÁO BÀI THỰC HÀNH SỐ 2 - PHÂN TÍCH MỘT SỐ KỸ THUẬT TẤN CÔNG TRONG MẠNG LAN** | Không dùng tiêu đề Lab01 |
| Sinh viên 1 | Họ tên + MSSV | Bài làm theo nhóm 2 người |
| Sinh viên 2 | Họ tên + MSSV | Nếu làm 1 mình: ghi rõ và hỏi giảng viên |
| Yêu cầu kết quả thực hành | Ghi lại: nộp `NhomX_Lab02_BaoCao.zip` gồm báo cáo + 3 pcap <= 1 MB | Không để trống mục này |

## B. Thông số container trước khi tấn công (1 điểm)

| Ô | Nội dung | Ảnh |
|---|---|---|
| Máy User: IP | `10.x.y.10` (theo compose) | `L02-B1-user.png` |
| Máy User: MAC | MAC `eth0` (dạng `02:42:...`) | |
| Máy User: bảng ARP | Chép nguyên bảng `arp -n` (IP, MAC, interface) | |
| Máy Server: IP | `10.x.y.20` | `L02-B1-server.png` |
| Máy Server: MAC | MAC `eth0` | |
| Máy Server: bảng ARP | Chép nguyên bảng | |
| Máy Attacker: IP | `10.x.y.51` | `L02-B1-attacker.png` |
| Máy Attacker: MAC | MAC `eth0` | |

Kiểm tra chéo trước khi nộp: 4 byte cuối MAC phải là hex của IP (ví dụ IP `10.11.1.20` -> MAC kết thúc `...:01:14`). Nếu lệch, ghi sai hoặc môi trường chưa đúng.

## C. Kịch bản 1 (2 điểm)

| Câu hỏi của mẫu | Trả lời tối thiểu | Ảnh |
|---|---|---|
| Gói tin Attacker gửi để poison (1đ) | Ảnh Wireshark mở rộng phần Ethernet + ARP, thấy rõ các trường | `L02-B2-kb1-wireshark.png` |
| No. | Số thứ tự gói poison đầu tiên | |
| Địa chỉ nguồn | **MAC nguồn = MAC Attacker**; **ARP sender IP = IP Server** (bị giả) | |
| Địa chỉ đích | IP/MAC của User | |
| ARP Request hay Reply? | **ARP Reply** (gratuitous Reply, không có Request tương ứng) | |
| Đặc điểm khác thường | IP Server đi kèm MAC của Attacker -> cặp IP-MAC không khớp thực tế mạng | |
| Máy nào bị tấn công? Hậu quả? (1đ) | **User** bị poison; cache ARP đổi IP Server -> MAC Attacker; mọi lưu lượng User -> Server bị chuyển sang Attacker (nghe lén, sửa, chặn). Nếu Attacker không forwarding thì mất kết nối. | `L02-B2-kb1-arp-user.png`, `L02-B2-kb1-arp-server.png` |

## D. Kịch bản 2 (2 điểm)

| Câu hỏi | Trả lời tối thiểu | Ảnh |
|---|---|---|
| Gói tin poison (1đ) | Như KB1, nhưng nêu rõ **số gói** và **chiều poison** (một chiều hay hai chiều) | `L02-B3-kb2-wireshark.png` |
| No. / nguồn / đích | Nêu từng gói tiêu biểu nếu poison 2 chiều (một gói tới User, một gói tới Server) | |
| Request/Reply | Theo đúng gói quan sát (Reply hoặc Request tùy script) | |
| Đặc điểm bất thường | MAC không khớp IP; nếu 2 chiều thì cả hai máy đều bị lừa | |
| Máy bị tấn công + hậu quả (1đ) | Nêu cả User và Server nếu poison 2 chiều; hậu quả: toàn bộ luồng hai chiều đi qua Attacker | `L02-B3-kb2-arp-user.png`, `L02-B3-kb2-arp-server.png` |

## E. Kịch bản 3 - MITM (3 điểm)

| Câu hỏi | Trả lời tối thiểu | Ảnh |
|---|---|---|
| Các gói ARP poison (1đ) | Ảnh Wireshark có ít nhất 2 gói: Attacker -> User và Attacker -> Server | `L02-B4-kb3-wireshark-arp.png` |
| Hậu quả trên nạn nhân (1đ) | Bảng ARP của User và Server đều trỏ về MAC Attacker; luồng `nc` đi qua Attacker | `L02-B4-kb3-arp-user.png`, `L02-B4-kb3-arp-server.png` |
| Thông điệp Server nhận khác gì? (1đ) | So sánh chuỗi gốc và chuỗi sau khi qua `mitm.py`; chỉ ra byte/từ bị sửa | 4 ảnh: `...-user-gui-truoc.png`, `...-server-nhan-truoc.png`, `...-user-gui-sau.png`, `...-server-nhan-sau.png` |
| Giải thích thay đổi | `mitm.py` nhận gói, sửa payload, tính lại checksum rồi gửi tiếp; User và Server không phát hiện vì không có xác thực tầng 2/3 | |

Cách chụp 4 ảnh so sánh: dùng Wireshark -> chuột phải gói -> **Follow -> TCP Stream**, chụp phần nội dung; hoặc chụp cửa sổ `nc` ở hai đầu (trước và sau).

## F. Phòng chống tấn công (2 điểm)

| Ô | Nội dung | Ảnh |
|---|---|---|
| Lệnh định nghĩa ánh xạ ARP cố định (0.5đ) | Chép đúng lệnh: `sudo arp -s <Server_IP> <Server_MAC>` | `L02-B5-lenh-arp-s.png` |
| Kết quả tấn công (1.5đ) | Bảng `arp -n` sau khi tấn công lại: entry Server vẫn là MAC thật, cờ **M**; giải thích entry permanent không bị ARP Reply ghi đè | `L02-B5-arp-n-co-M.png`, `L02-B5-ket-qua-tan-cong-lai.png` |

Kết luận nên có: giải pháp chỉ hiệu quả với cặp IP-MAC đã khai báo, không mở rộng được cho mạng lớn; không chống DHCP/DNS spoofing.

## G. Danh sách ảnh tối thiểu (13 ảnh)

1. `L02-B1-docker-compose-up.png`
2. `L02-B1-user.png`
3. `L02-B1-server.png`
4. `L02-B1-attacker.png`
5. `L02-B2-kb1-wireshark.png`
6. `L02-B2-kb1-arp-user.png` (hoặc chung với ảnh 2 nếu chụp sau tấn công)
7. `L02-B2-kb1-arp-server.png`
8. `L02-B3-kb2-wireshark.png`
9. `L02-B3-kb2-arp-user.png`
10. `L02-B3-kb2-arp-server.png`
11. `L02-B4-kb3-wireshark-arp.png`
12. `L02-B4-kb3-user-gui-truoc.png` + `L02-B4-kb3-server-nhan-truoc.png`
13. `L02-B4-kb3-user-gui-sau.png` + `L02-B4-kb3-server-nhan-sau.png`
14. `L02-B5-lenh-arp-s.png`
15. `L02-B5-arp-n-co-M.png`

## H. Lỗi tuyệt đối phải tránh

- Thiếu **Kịch bản 2** hoặc **Kịch bản 3** (mất 5 điểm).
- Dùng tiêu đề của Lab01.
- Gọi container là "máy ảo".
- Chỉ ghi IP nguồn mà không ghi MAC nguồn (Wireshark hiển thị MAC ở cột Source).
- Không chép lệnh `arp -s` vào mục 4.5.
- Giải thích sai bản chất `ip_forward`:
  - Đúng: `net.ipv4.ip_forward` là sysctl **theo network namespace**; container mặc định = 0. Nếu = 1 thì do image/compose/script bật, không phải "kế thừa từ Docker host".
  - ICMP Redirect **không** phải cơ chế làm gói tin tới đích; gói tới được đích là nhờ IP forwarding.
- Nộp thiếu zip/pcap hoặc pcap > 1 MB.
- Không ghi tên 2 sinh viên.
