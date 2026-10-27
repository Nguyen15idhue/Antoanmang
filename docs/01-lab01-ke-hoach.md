# 01 - Kế hoạch chi tiết Lab01 (Do thám hệ thống bằng nmap)

Nguồn: `Lab01_Huong_dan_TH.pdf` (mục 2 - luyện tập, mục 3 - yêu cầu thực hành trên lớp).
Đầu ra: `task1.pcap`, `task2.pcap`, `task3.pcap`, `task4.pcap` + bảng CVE.

## 1. Mô hình mạng

| Vai trò | VM hiện có | IP | Ghi chú |
|---|---|---|---|
| Máy do thám (Attack) | `NguyenMachine` | `192.168.117.10` | Theo tài liệu thực hành |
| Máy mục tiêu (Server) | `Server3` | `192.168.117.13` | Chạy DNS/Telnet/SSH theo tài liệu |
| Gateway (host-only) | card `VirtualBox Host-Only Ethernet Adapter` | `192.168.117.1/24` | Phải sửa từ `169.254.x` |
| DHCP server | - | pool `192.168.117.3-254` | Đã cấu hình sẵn |

Tài khoản VM: `bkcs` / `bkcs`.

## 2. A0 - Sửa hạ tầng (15 phút)

Mục tiêu: card host-only đúng dải `192.168.117.0/24`, dọn VM rác, chụp snapshot sạch.

```powershell
$vbm = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

# 1. Sửa IP card host-only
& $vbm hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter" --ip 192.168.117.1 --netmask 255.255.255.0

# 2. Kiểm tra lại
& $vbm list hostonlyifs | Select-String "IPAddress|NetworkMask"

# 3. Dọn 2 VM lỗi (chỉ unregister, KHÔNG xoá đĩa)
& $vbm unregistervm "{4de6c562-0f31-40ff-bd7c-2b80a39598b7}"
& $vbm unregistervm "{b45be1f1-0fb6-4a2c-8fd3-98e48f10d429}"
```

Tuỳ chọn: đổi tên hiển thị cho dễ nhìn (không ảnh hưởng bài làm)

```powershell
& $vbm setextradata "NguyenMachine" "GUI/LastItemSelected" ""   # bỏ qua nếu không cần
```

Bằng chứng A0: ảnh `VBoxManage list hostonlyifs` có `IPAddress: 192.168.117.1`.
Điều kiện đạt: ping được từ Windows tới `192.168.117.10` và `.13` sau khi VM bật.

## 3. A1 - Khởi động và kiểm tra 2 VM (20 phút)

1. Mở VirtualBox -> chọn `NguyenMachine` -> **Start -> Normal Start** (máy đang `aborted`, không resume).
2. Chọn `Server3` -> Start.
3. Đăng nhập `bkcs` / `bkcs` ở cả hai.
4. Trên **Attack**, kiểm tra địa chỉ:
   ```bash
   ifconfig
   ```
   Kỳ vọng: card `eth0` (hoặc `enp0s3`) có `inet 192.168.117.10`.
   Nếu sai: mở Network Connections -> Wired connection 1 -> IPv4 Settings -> Manual -> `192.168.117.10/24`, Gateway `192.168.117.1`.
5. Trên **Server**:
   ```bash
   ifconfig
   ```
   Kỳ vọng: `inet 192.168.117.13`. Nếu chưa đúng, sửa `/etc/network/interfaces` (mục 3 của tài liệu thiết lập) rồi:
   ```bash
   sudo ip addr flush dev enp0s8 && sudo systemctl restart networking
   ```
6. Kiểm tra kết nối hai chiều:
   ```bash
   ping -c 4 192.168.117.13     # từ Attack
   ping -c 4 192.168.117.10     # từ Server
   ```
7. Kiểm tra công cụ có sẵn trên Attack:
   ```bash
   nmap -V
   wireshark -v
   tcpdump --version
   sudo -v        # xác nhận có quyền sudo
   ```

Bằng chứng A1: ảnh `ifconfig` hai máy + ảnh `ping` thành công.
Điều kiện đạt: ping thông 2 chiều, `nmap -V` chạy được, Wireshark mở được.

## 4. A2 - Task 1: `nmap -sn` (30 phút)

Mục tiêu: nhận diện **ARP Ping Scan**; lưu `task1.pcap`.

Trình tự:

1. Trên Attack, mở Wireshark, chọn card host-only (`eth0`), bấm Start.
2. Mở terminal thứ 2, chạy:
   ```bash
   nmap -sn 192.168.117.0/24
   ```
3. Dừng capture ngay sau khi nmap kết thúc.
4. Lưu file: File -> Save As -> `task1.pcap` (định dạng **pcap**, không phải pcapng), lưu vào `~/lab01/`.
5. Bộ lọc phân tích:
   ```
   arp
   arp.opcode == 2
   ```

Nội dung phân tích cần viết:

- Máy Attack gửi hàng loạt **ARP Request** broadcast (`Who has 192.168.117.x? Tell 192.168.117.10`).
- Các máy đang sống trả **ARP Reply** (`192.168.117.13 is at <MAC>`).
- Không có gói ICMP Echo Request -> nmap không dùng ICMP khi quét cùng mạng LAN.
- Kết luận: kỹ thuật được dùng là **ARP Ping Scan**.

Bằng chứng: `task1.pcap` + ảnh Wireshark lọc `arp.opcode == 2` + ảnh kết quả terminal của nmap.

## 5. A3 - Task 2: `nmap -sS -F` (30 phút)

1. Wireshark bắt trên `eth0`.
2. Chạy:
   ```bash
   sudo nmap -sS -F 192.168.117.13
   ```
3. Dừng capture, lưu `task2.pcap`.
4. Bộ lọc:
   ```
   tcp && ip.addr == 192.168.117.13
   tcp.flags.syn == 1 && tcp.flags.ack == 0
   ```

Nội dung phân tích cần viết:

- nmap gửi **TCP SYN** tới 100 cổng phổ biến (`-F`).
- Cổng mở -> SYN/ACK; cổng đóng -> RST/ACK.
- **Không có gói ACK** hoàn tất bắt tay 3 bước, kết nối không được thiết lập.
- Kết luận: **TCP SYN Scan** (half-open scan), cần quyền root.

Bằng chứng: `task2.pcap` + ảnh Wireshark + ảnh kết quả nmap (danh sách cổng mở).

## 6. A4 - Task 3: `nmap -sA -F` (30 phút)

1. Wireshark bắt trên `eth0`.
2. Chạy:
   ```bash
   sudo nmap -sA -F 192.168.117.13
   ```
3. Dừng capture, lưu `task3.pcap`.
4. Bộ lọc:
   ```
   tcp.flags.ack == 1 && tcp.flags.syn == 0
   tcp.flags.reset == 1
   ```

Nội dung phân tích cần viết:

- nmap gửi **TCP ACK** tới từng cổng.
- Máy đích trả **RST** cho mọi cổng (cả mở và đóng) -> nmap báo `unfiltered`.
- Không phân biệt được cổng mở/đóng; mục đích là **phát hiện firewall** (có firewall thì một số cổng bị drop, không trả RST).
- Kết luận: **TCP ACK Scan**.

Bằng chứng: `task3.pcap` + ảnh Wireshark + ảnh kết quả nmap.

## 7. A5 - Task 4: thu thập thông tin hệ thống + CVE (60 phút)

1. Tìm nút cung cấp dịch vụ email:
   ```bash
   sudo nmap -p 25,110,143,993,995 192.168.117.0/24
   ```
2. Quét sâu máy tìm được:
   ```bash
   sudo nmap -sV -O -p- 192.168.117.x
   # hoặc: sudo nmap -A 192.168.117.x
   ```
3. Bắt lưu lượng bằng Wireshark trong suốt quá trình quét, lưu `task4.pcap`.
4. Ghi lại: tên dịch vụ, phần mềm, phiên bản, hệ điều hành.
5. Tra CVE tại `https://www.cvedetails.com/` và điền bảng:

| Phần mềm dịch vụ (tên dịch vụ, phần mềm, phiên bản) | Số CVE | Mô tả ngắn gọn |
|---|---|---|
| (ví dụ) OpenSSH 5.9p1 | CVE-... | ... |
| (ví dụ) ISC BIND 9.x | CVE-... | ... |
| (ví dụ) telnetd ... | CVE-... | ... |

Lưu ý quan trọng:

- Đề ghi mạng `192.168.100.0/24` ở mục 3.2 nhưng môi trường luyện tập là `192.168.117.0/24`. **Khi làm ở nhà dùng `.117`; khi lên lớp dùng đúng dải giảng viên công bố** (ghi rõ giả định này vào bài).
- Nếu quét không thấy dịch vụ email nào: ghi nhận "không có nút nào mở cổng email", sau đó dùng các dịch vụ thực tế tìm được (DNS/SSH/Telnet) để lập bảng CVE và hỏi lại giảng viên.

Bằng chứng: `task4.pcap` + ảnh kết quả `-sV -O` + bảng CVE.

## 8. A6 - Tổng hợp bằng chứng

| File | Nội dung | Kích thước mục tiêu |
|---|---|---|
| `task1.pcap` | ARP Request/Reply của `nmap -sn` | < 1 MB (nên lọc `arp` khi lưu) |
| `task2.pcap` | TCP SYN Scan | < 1 MB |
| `task3.pcap` | TCP ACK Scan | < 1 MB |
| `task4.pcap` | Quét dịch vụ + OS | < 5 MB |

Cách giảm kích thước (nếu cần):

```bash
editcap -c 5000 task1_full.pcap task1.pcap
# hoặc lọc chỉ giữ ARP:
tshark -r task1_full.pcap -Y "arp" -w task1.pcap
```

## 9. Checklist hoàn thành Lab01

- [ ] A0: host-only = `192.168.117.1/24`, đã dọn VM rác
- [ ] A1: 2 VM boot, IP đúng, ping 2 chiều, nmap/Wireshark chạy được
- [ ] A2: `task1.pcap` + kết luận ARP Ping Scan
- [ ] A3: `task2.pcap` + kết luận TCP SYN Scan
- [ ] A4: `task3.pcap` + kết luận TCP ACK Scan
- [ ] A5: `task4.pcap` + bảng dịch vụ + bảng CVE
- [ ] A6: đã kiểm tra mở lại 4 pcap bằng Wireshark, dung lượng hợp lý

## 10. Kết quả đã chạy (2026-10-21)

Điều chỉnh so với kế hoạch:

- Card mạng của Attack là **`eth14`**, không phải `eth0`; mọi lệnh `tcpdump` phải dùng `-i eth14`.
- Không có `dumpcap`; dùng `tcpdump` (cần `sudo`).
- `nmap` trên Attack là bản 5.21, `-sS/-sA` cần `sudo`.
- Chạy lệnh từ host qua `plink -m script.sh` để tránh lỗi quoting.

Kết quả:

| Task | Lệnh | Kết quả | pcap |
|---|---|---|---|
| 1 | `nmap -sn 192.168.117.0/24` | 4-5 host up; 512 dòng ARP -> **ARP Ping Scan** | `task1.pcap` (37 KB) |
| 2 | `nmap -sS -F 192.168.117.13` | mở 22, 23; không hoàn tất bắt tay -> **TCP SYN Scan** | `task2.pcap` (19 KB) |
| 3 | `nmap -sA -F 192.168.117.13` | 100/100 cổng `unfiltered` -> **TCP ACK Scan** | `task3.pcap` (18 KB) |
| 4 | `nmap -p 25,110,143,993,995 192.168.117.0/24` + `-sV -O` | Không có dịch vụ email trong mạng lab; thu được OpenSSH 7.2p2, telnetd, BIND 9.10.3-P4-Ubuntu | `task4.pcap` (214 KB) |

Ghi chú cho bài nộp: dải `192.168.100.0/24` trong đề mục 3.2 không tồn tại trong môi trường Lab01 (mạng là `192.168.117.0/24`). Cần hỏi giảng viên và ghi rõ giả định; bảng CVE lập cho ssh/telnet/dns tìm được.
