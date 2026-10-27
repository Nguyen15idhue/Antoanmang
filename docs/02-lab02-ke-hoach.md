# 02 - Kế hoạch chi tiết Lab02 (ARP Cache Poisoning + MITM)

Nguồn: `Lab02_LAN_Attacks.pdf` (mục 4.1 -> 4.5) và mẫu báo cáo `Lab02_BC.pdf`.
Đầu ra: `NhomX_Lab02_BaoCao.zip` gồm báo cáo + 3 pcap (mỗi file <= 1 MB).

## 0. Điều kiện tiên quyết (bắt buộc)

| # | Hạng mục | Trạng thái | Cách xử lý |
|---|---|---|---|
| 1 | Bộ source `it4263lab/lab02` | **Chưa có** | Xin giảng viên: `docker-compose.yml`, `attack/scenario1.py`, `attack/scenario2.py`, `attack/mitm.py`, `dockps`, `docksh` |
| 2 | Tham số `x`, `y` | **Chưa có** | `x` = 2 số cuối mã lớp thực hành, `y` = số thứ tự nhóm |
| 3 | VM Ubuntu 20.04 | **Chưa có** | Nhận tại phòng lab (phương án chính). Dự phòng: xem mục 8 |
| 4 | Tài khoản/ quyền sudo trong VM | Chưa xác nhận | Kiểm tra `sudo -v` |

Không có mục 1 thì **không thể làm** vì IP, tên container, interface, tham số script đều nằm trong file của giảng viên.

## 1. Mô hình

```
            Ubuntu 20.04 (host VM)
                     |
        docker network (bridge) 10.x.y.0/24
          |             |             |
      User .10      Server .20    Attacker .51
```

- IP cụ thể lấy từ `docker-compose.yml` sau khi sửa theo `x`, `y`.
- Mỗi container có 1 card `eth0`; bắt gói trên host qua card `br-<id>`.
- Attacker cần quyền `NET_ADMIN` (compose của giảng viên thường đã cấp sẵn; kiểm tra `cap_add`).

## 2. B0 - Chuẩn bị công cụ trong VM (20 phút)

```bash
sudo apt update
sudo apt install -y docker.io docker-compose net-tools tcpdump netcat-openbsd python3 wireshark
sudo usermod -aG docker $USER
sudo usermod -aG wireshark $USER
newgrp docker        # hoặc logout/login
```

Kiểm tra:

```bash
docker -v && docker-compose -v
ifconfig -v | head -1        # net-tools
python3 -V
tcpdump --version
nc -h 2>&1 | head -2
```

Bằng chứng: ảnh phiên bản các công cụ.

## 3. B1 - Mục 4.1: Triển khai hệ thống (1 điểm)

```bash
cd ~/it4263lab/lab02
cp docker-compose.yml docker-compose.yml.bak
nano docker-compose.yml       # sửa IP theo x, y
```

Các việc cần làm trong file compose:

1. Sửa `subnet` của network (theo `x`, `y`).
2. Sửa `ipv4_address` của từng service (User/Server/Attacker) theo quy ước của giảng viên.
3. Ghi lại bảng IP/MAC dự kiến vào `05-tien-do.md`.

Khởi động:

```bash
docker-compose build
docker-compose up            # giữ foreground; hoặc 'up -d' nếu muốn chạy nền
```

Mở terminal khác:

```bash
dockps                        # nếu lệnh không có: docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Networks}}"
docksh <id>                   # nếu không có: docker exec -it <id> bash
```

Trong từng container (User, Server, Attacker):

```bash
ifconfig                      # ghi IP + MAC của eth0
ping -c 3 <IP máy còn lại>    # kiểm tra kết nối
arp -n                        # chụp bảng ARP ban đầu
```

Screenshot bắt buộc cho mục 4.1:

- `L02-B1-docker-compose-up.png` (3 container đang chạy)
- `L02-B1-user-ifconfig+arp.png`
- `L02-B1-server-ifconfig+arp.png`
- `L02-B1-attacker-ifconfig.png`
- `L02-B1-ping.png`

Điều kiện đạt: 3 container `Up`, ping thông, mỗi máy có IP/MAC đúng, bảng ARP đã có entry của máy kia.

## 4. B2 - Kịch bản 1 (2 điểm)

```bash
cd ~/it4263lab/lab02/attack
nano scenario1.py
```

Tham số cần sửa (tên biến tuỳ file, thường gồm):

- IP/MAC của User (nạn nhân)
- IP/MAC của Server (bị giả mạo)
- Interface (`eth0`)
- Số gói / chu kỳ gửi

Quy trình:

1. Trên host VM, lấy tên card bridge:
   ```bash
   ip -br link | grep br-
   ```
2. Mở Wireshark trên host, chọn card `br-...` tương ứng mạng Docker, Start.
3. Trong container Attacker:
   ```bash
   python3 scenario1.py
   ```
4. Trong container User và Server:
   ```bash
   arp -n
   ```
5. Dừng Wireshark, lưu `task1.pcap` (File -> Save As, định dạng pcap).
6. Bộ lọc phân tích:
   ```
   arp
   arp.opcode == 2
   ```

Trả lời (ghi vào báo cáo):

- **No.**: số thứ tự gói poison đầu tiên (bấm vào gói, đọc cột No.).
- **Nguồn**: nêu cả hai giá trị - MAC nguồn trên Ethernet = MAC Attacker; ARP sender IP = IP Server (bị giả).
- **Đích**: IP/MAC của User.
- **Loại**: **ARP Reply** (không phải Request) - gói không yêu cầu mà tự động trả lời.
- **Bất thường**: cặp IP-MAC không khớp thực tế: IP Server nhưng MAC là của Attacker.
- **Nạn nhân**: User; **hậu quả**: bảng ARP của User ánh xạ IP Server -> MAC Attacker, mọi gói tin tới Server bị chuyển sang Attacker (nghe lén/ sửa/ chặn).

Screenshot: `L02-B2-kb1-wireshark-arp.png`, `L02-B2-kb1-arp-user-sau.png`, `L02-B2-kb1-arp-server-sau.png`.

## 5. B3 - Kịch bản 2 (2 điểm)

Lặp lại B2 với `scenario2.py`, lưu `task2.pcap`.

Khác biệt cần chú ý (đọc code trước khi chạy):

- KB2 thường poison **cả hai phía** hoặc dùng **gratuitous ARP/ARP Request** thay vì Reply.
- Nếu poison 2 chiều: cả User và Server đều bị nhiễm; hậu quả là toàn bộ luồng hai chiều đi qua Attacker.
- Trả lời cùng bộ câu hỏi, nhưng phải nêu rõ **số gói** và **những máy bị ảnh hưởng**.

Screenshot: `L02-B3-kb2-wireshark.png`, `L02-B3-kb2-arp-user.png`, `L02-B3-kb2-arp-server.png`.

## 6. B4 - Kịch bản 3: MITM (3 điểm)

Chuẩn bị 3 cửa sổ terminal (User, Server, Attacker) + Wireshark trên host.

1. User: bắt lưu lượng
   ```bash
   tcpdump -i eth0 -n -w /tmp/user.pcap
   ```
2. Server: bắt lưu lượng
   ```bash
   tcpdump -i eth0 -n -w /tmp/server.pcap
   ```
3. Server: mở listener
   ```bash
   nc -lp 10101
   ```
4. User: kết nối và gửi thông điệp **trước khi bị tấn công**
   ```bash
   nc <Server_IP> 10101
   ```
   Gõ một câu bất kỳ, ví dụ: `hello server from user` rồi Enter.
5. Attacker: poison ARP cả 2 chiều (dùng `scenario2.py` hoặc script của giảng viên) cho tới khi mỗi máy gửi dữ liệu đều đi qua Attacker.
6. Attacker: bật chuyển tiếp
   ```bash
   sysctl net.ipv4.ip_forward=1
   ```
   (nếu `sysctl` không ghi được trong container: `sysctl -w` với quyền root hoặc dùng `--privileged`)
7. Attacker: chạy công cụ sửa gói
   ```bash
   python3 mitm.py
   ```
8. User: gửi lại thông điệp **sau khi bị tấn công** (cùng nội dung để dễ so sánh).
9. Dừng `tcpdump` (Ctrl+C) ở cả 2 máy, dừng Wireshark, lưu `task3.pcap`.
10. Copy pcap ra host nếu cần:
    ```bash
    docker cp <user_id>:/tmp/user.pcap ./user.pcap
    docker cp <server_id>:/tmp/server.pcap ./server.pcap
    ```

Phân tích:

- Mở `user.pcap`: tìm gói chứa chuỗi gốc (Follow -> TCP Stream).
- Mở `server.pcap`: tìm gói tương ứng - nội dung đã bị sửa (ví dụ đổi ký tự, thay từ).
- Chỉ ra vị trí byte bị thay đổi và giải thích: `mitm.py` chặn gói ở tầng ứng dụng, sửa payload rồi gửi tiếp nên checksum/IP được tính lại.
- Kết luận: nạn nhân không phát hiện được vì ARP không có xác thực; tính toàn vẹn dữ liệu bị phá vỡ.

Screenshot: `L02-B4-kb3-user-gui-truoc.png`, `L02-B4-kb3-server-nhan-truoc.png`, `L02-B4-kb3-user-gui-sau.png`, `L02-B4-kb3-server-nhan-sau.png`, `L02-B4-kb3-arp-user.png`, `L02-B4-kb3-arp-server.png`, `L02-B4-kb3-wireshark-arp.png`.

## 7. B5 - Mục 4.5: Phòng chống (2 điểm)

Trên **User**:

```bash
sudo arp -s <Server_IP> <Server_MAC>
arp -n
```

Kỳ vọng: entry có cờ **M** (permanent) thay vì **C** (complete/dynamic).

Sau đó:

1. Restart 3 container để xoá cache nhiễm độc:
   ```bash
   docker restart <user_id> <server_id> <attacker_id>
   ```
   (Lưu ý: restart sẽ mất entry static vừa đặt; nếu vậy đặt lại `arp -s` sau khi restart.)
2. Đặt lại static ARP trên User.
3. Chạy lại **một** kịch bản tấn công (KB1 hoặc KB2).
4. Kiểm tra lại `arp -n` trên User + thử `ping`/`nc` User -> Server.

Kết luận cần viết:

- Entry static **không bị ghi đè** bởi ARP Reply giả -> tấn công thất bại với cặp IP-MAC này.
- Hạn chế: phải khai báo thủ công từng cặp, không mở rộng được; không chống được DHCP spoofing, DNS spoofing, hay tấn công vào entry khác chưa đặt static.

Screenshot: `L02-B5-lenh-arp-s.png`, `L02-B5-arp-n-co-M.png`, `L02-B5-ket-qua-tan-cong-lai.png`.

## 8. B6 - Đóng gói (20 phút)

```bash
# 1. Cắt pcap <= 1 MB
editcap -c 3000 task1_full.pcap task1.pcap       # giới hạn số gói
# hoặc lọc gọn:
tshark -r task1_full.pcap -Y "arp or tcp" -w task1.pcap

# 2. Kiểm tra dung lượng
ls -lh task*.pcap

# 3. Đóng gói
mkdir -p NhomX_Lab02_BaoCao
cp BaoCao.pdf task1.pcap task2.pcap task3.pcap NhomX_Lab02_BaoCao/
zip -r NhomX_Lab02_BaoCao.zip NhomX_Lab02_BaoCao/

# 4. Kiểm tra lại
unzip -l NhomX_Lab02_BaoCao.zip
```

Quy tắc:

- Mỗi file pcap **<= 1 MB** (nếu vượt: giảm số gói bằng `-c`, hoặc chỉ giữ `arp` + `tcp`).
- Tên zip đúng mẫu `NhomX_Lab02_BaoCao.zip` (X = số nhóm).
- Báo cáo phải là bản cuối, đã điền đủ theo `03-lab02-checklist-bao-cao.md`.

## 9. Phương án dự phòng: tự dựng VM Ubuntu 20.04

Chỉ dùng khi không nhận được VM của phòng lab.

1. Tải Ubuntu Server 20.04 ISO, tạo VM VirtualBox: RAM 4096 MB, 2 card mạng:
   - Adapter 1: NAT (để cài gói).
   - Adapter 2: Host-only `VirtualBox Host-Only Ethernet Adapter`.
2. Trong VM:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose net-tools tcpdump netcat-openbsd python3 wireshark openssh-server
   sudo usermod -aG docker $USER && sudo usermod -aG wireshark $USER
   ```
3. Copy thư mục `it4263lab` vào `~/`.
4. Làm tiếp từ B1.
5. Lưu ý: nếu dùng Docker Desktop trên Windows thay vì VM, card `br-` nằm trong WSL2 nên Wireshark trên Windows **không bắt được**; phải dùng `tcpdump` trong container và mở file bằng Wireshark. Không khuyến nghị vì lệch hướng dẫn.

## 10. Rủi ro và cách giảm

| Rủi ro | Cách xử lý |
|---|---|
| Poison không ăn | Chạy script bằng root, kiểm tra tên interface trong script, kiểm tra container có `NET_ADMIN` |
| Ping vẫn thông sau khi poison | `ip_forward` đang = 1: đặt `sysctl net.ipv4.ip_forward=0` hoặc `iptables -P FORWARD DROP` để thấy hậu quả rõ (KB1/KB2) |
| KB3 mất kết nối | Phải bật `ip_forward=1` trước khi chạy `mitm.py` |
| Kết quả lần sau sai | Restart 3 container trước mỗi kịch bản |
| pcap quá lớn | `editcap -c` hoặc lọc `arp or tcp` |
| Wireshark không thấy `br-` | Cài Wireshark trên host VM (không phải Windows), thêm user vào group `wireshark`, hoặc chạy `sudo wireshark` |

## 11. Checklist hoàn thành Lab02

- [ ] B0: đủ công cụ, đúng phiên bản
- [ ] B1: compose sửa đúng x/y, 3 container Up, có IP/MAC/ARP + ảnh
- [ ] B2: KB1 chạy, `task1.pcap` <= 1 MB, đủ 5 câu trả lời + 3 ảnh
- [ ] B3: KB2 chạy, `task2.pcap` <= 1 MB, đủ 5 câu trả lời + 3 ảnh
- [ ] B4: KB3 chạy, `task3.pcap` <= 1 MB, có ảnh trước/sau + giải thích
- [ ] B5: `arp -s` + cờ M + ảnh kết quả tấn công lại + kết luận
- [ ] B6: báo cáo đủ ô, zip đúng tên, mở lại kiểm tra

## 12. Cập nhật (2026-10-21): tự dựng bộ source

Do chưa có `it4263lab/lab02` từ giảng viên, bộ source tương đương đã được tạo tại `F:\3.Laptrinh\2.Learning\Antoanmang\lab02`:

| File | Chức năng |
|---|---|
| `docker-compose.yml` + `.env` | 3 container User/Server/Attacker, subnet `10.11.1.0/24` (giả định x=11, y=1) |
| `image/Dockerfile` | Ubuntu 20.04 + python3, net-tools, tcpdump, netcat, ping |
| `attack/arp.py` | Gửi/nhận frame ARP thô bằng `AF_PACKET` |
| `attack/scenario1.py` | Poison một chiều tới User (giả IP Server) |
| `attack/scenario2.py` | Poison hai chiều User <-> Server |
| `attack/mitm.py` | Chuyển tiếp + sửa payload TCP (`hello` -> `pwned`), tự đặt `ip_forward=0` |
| `bin/dockps`, `bin/docksh` | Tiện ích như tài liệu |

Khác biệt cần ghi trong báo cáo: đây là source tự dựng, không phải file của giảng viên; tham số `x`, `y` là giả định, sẽ sửa trong `.env` nếu giảng viên công bố giá trị thật.

Lưu ý `ip_forward`: script MITM đặt `ip_forward=0` để tránh kernel forward song song gây gửi trùng; bước 7 của đề vẫn thực hiện trước để kiểm tra kết nối, sau đó script ghi đè.
