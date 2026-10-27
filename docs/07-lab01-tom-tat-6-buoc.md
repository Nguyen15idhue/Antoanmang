# Lab01 - Tóm tắt 6 bước thực hiện

Môi trường: máy Attack `192.168.117.10` (Ubuntu 12.04, card `eth14`), mục tiêu Server `192.168.117.13`.
Mỗi bước gồm: mục đích - lệnh - kết quả kỳ vọng.

---

## Bước 0 - Kiểm tra mạng

- **Mục đích:** xác nhận đúng card mạng và IP trước khi quét.
- **Lệnh:**
  ```bash
  ip -br a | grep eth14
  ```
- **Kết quả:** `eth14 UP 192.168.117.10/24`.

---

## Bước 1 - Quét host bằng ARP

- **Mục đích:** tìm máy nào đang sống trong LAN mà không cần ICMP.
- **Lệnh:**
  ```bash
  sudo nmap -sn -PR 192.168.117.0/24
  ```
- **Kết quả:** `Nmap done: 256 IP addresses (4 hosts up)`, thấy `.1`, `.10`, `.13` kèm MAC `08:00:27:...`.

---

## Bước 2 - Quét cổng TCP bằng SYN

- **Mục đích:** phát hiện cổng mở mà không tạo phiên đầy đủ.
- **Lệnh:**
  ```bash
  sudo nmap -sS -p22,23 192.168.117.13
  ```
- **Kết quả:** `22/tcp open ssh`, `23/tcp open telnet`.

---

## Bước 3 - Quét ACK để dò firewall

- **Mục đích:** kiểm tra có thiết bị lọc gói giữa hai máy không.
- **Lệnh:**
  ```bash
  sudo nmap -sA -p1-100 192.168.117.13
  ```
- **Kết quả:** `All 100 scanned ports ... are unfiltered` (không có firewall).

---

## Bước 4 - Nhận diện phiên bản dịch vụ

- **Mục đích:** biết phần mềm + phiên bản để tra CVE.
- **Lệnh:**
  ```bash
  sudo nmap -sV -p22,23,53 192.168.117.13
  ```
- **Kết quả:** `OpenSSH 7.2p2`, `Linux telnetd`, `ISC BIND 9.10.3-P4`.

---

## Bước 5 - Đọc dấu vết gói tin trên Wireshark

- **Mục đích:** chứng minh mỗi kiểu quét để lại dấu vết khác nhau.
- **Lệnh:** `sudo wireshark` (chọn `eth14`) hoặc mở `task1..4.pcap`.
- **Kết quả theo filter:**
  - `arp` -> ARP Request/Reply hàng loạt.
  - `tcp.flags.syn==1 && tcp.flags.ack==0` -> SYN -> SYN-ACK -> RST.
  - `tcp.flags.ack==1 && tcp.flags.syn==0` -> ACK trần -> RST-ACK.
  - `tcp.port==22 && tcp.len>0` -> Follow TCP Stream thấy banner `SSH-2.0-OpenSSH_7.2p2`.

---

## Bước 6 - Kết luận / tra CVE

- **Mục đích:** từ banner suy ra rủi ro thực tế.
- **Lệnh:** không cần (tra bảng CVE trong báo cáo).
- **Kết quả:** OpenSSH 7.2p2 -> CVE-2016-6210, CVE-2016-6515, CVE-2018-15473; BIND 9.10.3-P4 -> CVE-2016-2776, CVE-2017-3136/3137; telnet -> truyền rõ, CVE-2020-10188.
