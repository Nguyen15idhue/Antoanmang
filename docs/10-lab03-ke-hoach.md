# 10 - Kế hoạch Lab03: DNS Cache Poisoning (kỹ thuật Kaminsky)

Thông tin chung:

| Hạng mục | Giá trị |
|---|---|
| Bài thực hành | Lab03 - Phân tích kịch bản tấn công DNS Cache Poisoning |
| Hình thức | Cá nhân (01 sinh viên) |
| Ngày lập kế hoạch | 2026-10-27 |
| Ngày cập nhật | 2026-11-05 |
| Tài liệu gốc | `lab03/Lab03_Huong_dan_TH.pdf`, `lab03/Lab03_SttNhom_BaoCao.pdf` |
| Tài liệu kết quả | `docs/11-lab03-ket-qua.md` |
| Sản phẩm nộp | `NhomX_Lab03_BaoCao.zip` (báo cáo + `attacker.pcap` + `local_dns_server.pcap`) |

> **Cập nhật 2026-11-05:** Bài là **cá nhân**, không dùng `x`, `y` (để trống trong báo cáo); **tự dựng source** Lab03; **dùng lại VM `Ubuntu2004`** của Lab02; VM đã có Internet qua NAT. Trước khi chạy Lab03 phải `docker-compose down` cụm Lab02.

> Tên file nộp vẫn giữ theo mẫu `NhomX_Lab03_BaoCao.zip`; vì bài cá nhân, nếu giảng viên cho phép có thể thay `X` bằng MSSV.

## 1. Mục tiêu và đầu ra

| Mục | Điểm | Việc phải làm | Sản phẩm / bằng chứng |
|---|---|---|---|
| 4.1 Triển khai hệ thống | 1 | Sửa IP theo bảng cố định; build/up; ping; 3 lệnh `dig` | 3 ảnh `dig` + ảnh `docker ps` + ảnh ping |
| 4.2 Tạo DNS Query | 2 | Sửa `gen_query.py`, sinh `ip_req.bin` | File `ip_req.bin` + ảnh gói tin + 5 thông tin gói |
| 4.3 Tạo DNS Response giả | 2 | Sửa `gen_response.py`, sinh `ip_resp.bin` | File `ip_resp.bin` + ảnh gói tin + điều kiện thành công |
| 4.4 Thực hiện tấn công | 4 | Biên dịch `attack.c`, bắt pcap 2 phía, chạy `./attack`, kiểm chứng | `attacker.pcap`, `local_dns_server.pcap`, ảnh Wireshark, ảnh `rndc dumpdb`, ảnh `dig` |
| 4.5 Phòng chống | 1 | Bỏ `query-source port 44444`, tấn công lại | Ảnh cấu hình + ảnh tấn công thất bại + giải thích |

Điều kiện thành công kỹ thuật của 4.4: sau khi tấn công, cả hai lệnh dưới đây đều trả về `ns.attacker32.com`:

```bash
dig www.example.com
dig @ns.attacker32.com www.example.com
```

## 2. Môi trường thực hành

| Thành phần | Yêu cầu | Ghi chú |
|---|---|---|
| Máy ảo | Ubuntu 20.04 (VM `Ubuntu2004` đã tạo) | Là host chứa Docker |
| Docker | Docker Engine + docker-compose | `docker-compose build`, `docker-compose up` |
| Wireshark | Bắt trên card `br-...` của Docker | Nếu không thấy card: dùng `tcpdump` trong container |
| Python | Python 3 | Chạy `gen_query.py`, `gen_response.py` |
| GCC | `gcc` | Biên dịch `attack.c` |
| DNS tools | `dig`, `rndc` (bind9-utils) | Kiểm chứng và dump cache |
| Source | **Tự dựng** tại `~/lab03` | Giảng viên không cấp source; xem mục 2.1 |

Cấu trúc source cần có:

```text
~/lab03/
├── docker-compose.yml
├── .env                         # subnet + IP cố định (không dùng x, y)
├── attack/
│   ├── gen_query.py
│   ├── gen_response.py
│   └── attack.c
├── image_attacker_ns/
│   ├── named.conf
│   ├── zone_attacker32.com
│   └── zone_example.com
├── image_local_dns_server/
│   ├── named.conf
│   └── named.conf.options
└── image_user/
    └── resolv.conf
```

### 2.1. Quyết định đã chốt (2026-11-05)

| Nội dung | Quyết định |
|---|---|
| Source Lab03 | **Tự dựng** toàn bộ, giữ đúng tên file và luồng thao tác như đề |
| `x`, `y` | **Không dùng**; để trống trong báo cáo, ghi “không áp dụng” vì bài là cá nhân và tài liệu hướng dẫn ghi sai hình thức nhóm |
| Máy ảo | **Dùng lại `Ubuntu2004`** của Lab02 (Ubuntu 20.04, 4 GB RAM, 2 CPU, 40 GB) |
| Internet | Đã kiểm tra: NAT `10.0.2.15`, ping `8.8.8.8` OK, DNS phân giải được |
| Lab02 | **Tạm dừng** bằng `docker-compose down` khi chuyển sang Lab03; bật lại khi trình bày Lab02 |
| Công cụ đã có | Docker 26.1.3, docker-compose 1.25.0, gcc 9.4, dig 9.16.1, Wireshark 3.2.3, tcpdump 4.9.3 |
| Công cụ đã cài thêm | `bind9-utils` (có `rndc`), `curl` |

## 3. Kiến trúc container

| Container | Vai trò | File cấu hình liên quan |
|---|---|---|
| Attacker | Gửi DNS Query và flood DNS Response giả; chạy `./attack` | `attack/gen_query.py`, `gen_response.py`, `attack.c` |
| Local DNS Server | Nạn nhân, chạy BIND9, forward ra `8.8.8.8` | `image_local_dns_server/named.conf`, `/etc/bind/named.conf.options` |
| User | Client, resolver trỏ về Local DNS Server | `image_user/resolv.conf` |
| Attacker NS | Máy chủ tên miền giả `ns.attacker32.com` | `image_attacker_ns/zone_attacker32.com`, `zone_example.com` |

Luồng tấn công:

```text
User ---query---> Local DNS ---forward---> Root/Server thật
                     ^
                     |  response giả (nguồn giả = server thật)
                  Attacker ---flood---+
```

## 4. Quy ước địa chỉ IP (không dùng `x`, `y`)

Bài là cá nhân và tài liệu hướng dẫn ghi sai hình thức nhóm, nên **không sử dụng `x`, `y`**. Trong báo cáo để trống hoặc ghi “không áp dụng”.

Source tự dựng dùng subnet cố định `10.11.1.0/24` (theo Lab02) và bảng IP dưới đây:

| Container | IP | Vai trò |
|---|---|---|
| Gateway | `10.11.1.1` | Gateway của Docker network |
| User | `10.11.1.10` | Client, resolver trỏ về Local DNS |
| Local DNS Server | `10.11.1.20` | Nạn nhân, chạy BIND9 |
| Attacker | `10.11.1.30` | Gửi query và flood response giả |
| Attacker NS (`ns.attacker32.com`) | `10.11.1.40` | Máy chủ tên miền giả |
| Fake root (dự phòng) | `10.11.1.50` | Chỉ dùng nếu VM không ra Internet |

Các file cần sửa / cấu hình:

| File | Vị trí cần sửa |
|---|---|
| `.env`, `docker-compose.yml` | `SUBNET`, `GATEWAY`, `ipv4_address` của từng container |
| `image_attacker_ns/zone_attacker32.com` | Bản ghi A của `ns.attacker32.com` → `10.11.1.40` |
| `image_attacker_ns/zone_example.com` | Bản ghi NS trỏ về `ns.attacker32.com`; A giả cho `www.example.com` |
| `image_local_dns_server/named.conf` | `forwarders { 8.8.8.8; };`, forward zone `attacker32.com` → `10.11.1.40`, `query-source port 44444` |
| `image_user/resolv.conf` | `nameserver 10.11.1.20` |

Kiểm tra chéo sau khi sửa:

```bash
docker-compose config          # xem IP đã render đúng chưa
grep -R "10\.11\.1\." ~/lab03 --include="*.conf" --include="*.yml" --include="zone_*"
```

> **Xung đột subnet:** `10.11.1.0/24` trùng với Lab02. Trước khi `docker-compose up` Lab03 phải chạy `docker-compose down` trong `~/it4263lab/lab02`; nếu không Docker báo `Pool overlaps with other one on this address space`. Nếu muốn chạy song song Lab02 và Lab03, đổi subnet Lab03 sang `10.11.2.0/24` và cập nhật đồng bộ bảng IP.

### 4.1. Cấu hình BIND bắt buộc

Local DNS Server (`image_local_dns_server/named.conf.options`):

```conf
options {
    directory "/var/cache/bind";
    recursion yes;
    allow-query { any; };
    forward only;
    forwarders { 8.8.8.8; };
    query-source port 44444;
    dnssec-validation no;
    send-cookie no;
    listen-on { any; };
    listen-on-v6 { none; };
};

zone "attacker32.com" {
    type forward;
    forwarders { 10.11.1.40; };
};
```

Attacker NS (`image_attacker_ns/named.conf`): khai báo 2 zone `attacker32.com` và `example.com` là `type master`, `recursion no`, `allow-query { any; }`.

> Thiếu forward zone `attacker32.com` thì `dig ns.attacker32.com` và `dig @ns.attacker32.com ...` sẽ fail. Thiếu `dnssec-validation no` hoặc `send-cookie no` thì BIND có thể loại response giả.

## 5. Kịch bản tấn công (Kaminsky)

1. Attacker gửi DNS Query tới Local DNS Server, hỏi một tên **không tồn tại** trong `example.com`.
2. Local DNS Server không có cache nên forward query lên server cấp trên (root/server thật).
3. Trong lúc Local DNS Server chờ trả lời, Attacker flood DNS Response giả chứa bản ghi NS: `example.com -> ns.attacker32.com`.
4. Nếu một response giả khớp điều kiện và đến **trước** response thật, cache bị đầu độc. Nếu không, lặp lại với tên không tồn tại khác.

Điểm mấu chốt khiến tấn công khả thi:

- `query-source port 44444;` cố định cổng nguồn của Local DNS Server, nên Attacker biết chính xác cổng đích của gói trả lời.
- Transaction ID chỉ 16 bit, có thể brute-force bằng cách flood.
- Tên không tồn tại buộc Local DNS Server phải đi hỏi ra ngoài, tạo "cửa sổ race".

## 6. Kế hoạch thực hiện

Quy ước trạng thái: `[ ]` chưa làm, `[~]` đang làm, `[x]` xong (có bằng chứng).

### Giai đoạn A - Chuẩn bị

| # | Việc | Bằng chứng | Trạng thái |
|---|---|---|---|
| A0 | Bật VM `Ubuntu2004`, kiểm tra Internet | ảnh `ping 8.8.8.8`, `ip -br addr` | [x] |
| A0b | Tạo snapshot sạch trước khi cài Lab03 | ảnh `VBoxManage snapshot list` | [ ] |
| A1 | Tự dựng source `~/lab03` (Dockerfile, compose, BIND config, script) | `ls -R ~/lab03` | [ ] |
| A2 | Chốt không dùng `x`, `y`; ghi “không áp dụng” trong báo cáo | ghi chú trong báo cáo | [x] |
| A3 | Kiểm tra Docker, compose, gcc, dig, rndc trong VM | ảnh phiên bản | [x] |
| A4 | Kiểm tra card mạng Docker (`br-...`) thấy trong Wireshark | ảnh `ip a` | [ ] |
| A5 | `docker-compose down` cụm Lab02, xác nhận network đã xóa | `docker network ls` | [x] |

Kết quả kiểm tra ngày 2026-11-05:

- VM `Ubuntu2004` chạy tại `192.168.117.5`; card NAT `enp0s3` = `10.0.2.15`, ping `8.8.8.8` OK, DNS OK.
- Docker 26.1.3, docker-compose 1.25.0, gcc 9.4, dig 9.16.1, Wireshark 3.2.3, tcpdump 4.9.3.
- Đã cài thêm `bind9-utils` (có `rndc`) và `curl`.
- Đã chạy `docker-compose down` trong `~/it4263lab/lab02`; network `lab02_lab02net` đã được xóa, không còn xung đột subnet.

Lệnh kiểm tra nhanh:

```bash
docker --version && docker-compose --version
gcc --version | head -1
dig -v
rndc -V 2>&1 | head -1
ping -c 3 8.8.8.8
```

### Giai đoạn B - 4.1 Triển khai hệ thống (1 điểm)

| # | Việc | Bằng chứng | Trạng thái |
|---|---|---|---|
| B1 | Sửa `.env` + `docker-compose.yml` theo bảng IP cố định (không dùng `x`, `y`) | ảnh diff/ nội dung file | [ ] |
| B2 | Sửa `zone_attacker32.com` (A của `ns` → `10.11.1.40`) | ảnh file | [ ] |
| B3 | Sửa `zone_example.com` (NS → `ns.attacker32.com`, A giả cho `www`) | ảnh file | [ ] |
| B4 | Sửa `named.conf` (forwarders `8.8.8.8`, forward zone `attacker32.com`, `query-source port 44444`) | ảnh file | [ ] |
| B5 | Sửa `resolv.conf` (`nameserver 10.11.1.20`) | ảnh file | [ ] |
| B6 | `docker-compose build` và `docker-compose up` | ảnh `docker ps` | [ ] |
| B7 | `dockps`, `docksh` vào từng container | ảnh terminal | [ ] |
| B8 | Ping chéo các container | ảnh terminal | [ ] |
| B9 | Bắt Wireshark trên card `br-` | ảnh giao diện | [ ] |
| B10 | `dig ns.attacker32.com` trên User | ảnh `L03-B10-dig-ns-attacker32.png` | [ ] |
| B11 | `dig www.example.com` trên User | ảnh `L03-B11-dig-www-example.png` | [ ] |
| B12 | `dig @ns.attacker32.com www.example.com` trên User | ảnh `L03-B12-dig-at-ns-attacker32.png` | [ ] |

Lệnh tham khảo:

```bash
cd ~/lab03
docker-compose build
docker-compose up -d
docker ps
dockps
docksh <id>
ping -c 3 <ip_container_khac>
```

Ghi chú cho báo cáo: ở bước B10-B12, ghi lại IP trả về của từng tên miền. Đây là mốc "trước tấn công" để so sánh với mục 4.4.

### Giai đoạn C - 4.2 Tạo DNS Query (2 điểm)

| # | Việc | Bằng chứng | Trạng thái |
|---|---|---|---|
| C1 | Đọc và sửa `attack/gen_query.py`: IP nguồn (Attacker), IP đích (Local DNS:53), tên miền không tồn tại | ảnh file | [ ] |
| C2 | Chạy `python3 gen_query.py`, sinh `ip_req.bin` | ảnh `ls -l ip_req.bin` | [ ] |
| C3 | Kiểm tra gói bằng `xxd`/`tcpdump` hoặc mở pcap | ảnh `L03-C3-ip-req-bin.png` | [ ] |
| C4 | Điền 5 thông tin gói vào báo cáo | mục 2 của `11-lab03-ket-qua.md` | [ ] |

Thông tin bắt buộc phải xác định:

| Trường | Cách xác định |
|---|---|
| IP nguồn | IP container Attacker |
| Cổng nguồn | Cổng mà `gen_query.py` đặt (đọc trong file hoặc pcap) |
| IP đích | IP container Local DNS Server |
| Cổng đích | 53 |
| Tên miền truy vấn | Tên không tồn tại trong `example.com`, ví dụ `abcxyz.example.com` |

Lý do dùng tên không tồn tại: Local DNS Server không có cache nên phải hỏi server cấp trên, tạo khoảng thời gian chờ để chèn response giả; nếu hỏi tên đã có cache thì Local DNS Server trả lời ngay và không có cơ hội tấn công.

### Giai đoạn D - 4.3 Tạo DNS Response giả (2 điểm)

| # | Việc | Bằng chứng | Trạng thái |
|---|---|---|---|
| D1 | Từ pcap 4.1, xác định IP server mà Local DNS Server gửi query tới | ảnh Wireshark | [ ] |
| D2 | Xác định cổng đích của gói trả lời phải là `44444` | ảnh Wireshark | [ ] |
| D3 | Sửa `attack/gen_response.py` theo server thật + `ip_req.bin` | ảnh file | [ ] |
| D4 | Chạy `python3 gen_response.py`, sinh `ip_resp.bin` | ảnh `ls -l` | [ ] |
| D5 | Mở `ip_resp.bin`/gói bằng Wireshark kiểm tra | ảnh `L03-D5-ip-resp-bin.png` | [ ] |
| D6 | Điền thông tin response + điều kiện thành công | mục 3 của `11-lab03-ket-qua.md` | [ ] |

Response giả phải có:

| Trường | Giá trị |
|---|---|
| IP nguồn | IP server thật mà Local DNS Server đang chờ (giả mạo) |
| Cổng nguồn | 53 |
| IP đích | IP Local DNS Server |
| Cổng đích | 44444 (do `query-source port 44444`) |
| Transaction ID | Khớp query đang chờ (flood nhiều ID) |
| Nội dung giả mạo | `example.com NS ns.attacker32.com` kèm bản ghi A (glue) cho `ns.attacker32.com` |

### Giai đoạn E - 4.4 Thực hiện tấn công (4 điểm)

| # | Việc | Bằng chứng | Trạng thái |
|---|---|---|---|
| E1 | `gcc attack.c -o attack` trên host | ảnh biên dịch | [ ] |
| E2 | Copy `attack`, `ip_req.bin`, `ip_resp.bin` sang Attacker | ảnh `ls` | [ ] |
| E3 | Bắt pcap trên Attacker: `tcpdump -i eth0 -n -w attacker.pcap` | ảnh | [ ] |
| E4 | Bắt pcap trên Local DNS Server: `tcpdump -i eth0 -n -w local_dns_server.pcap` | ảnh | [ ] |
| E5 | Chạy `./attack` trên Attacker | ảnh terminal | [ ] |
| E6 | `dig www.example.com` trên User | ảnh `L03-E6-dig-www-sau.png` | [ ] |
| E7 | `dig @ns.attacker32.com www.example.com` trên User | ảnh `L03-E7-dig-at-ns-sau.png` | [ ] |
| E8 | Dump cache: `rndc dumpdb -cache /var/cache/bind/dump.db` | ảnh `L03-E8-rndc-dumpdb.png` | [ ] |
| E9 | Xem cache, tìm `example.com` và `ns.attacker32.com` | ảnh `L03-E9-cache-poisoned.png` | [ ] |
| E10 | Dừng capture, lưu `attacker.pcap` và `local_dns_server.pcap` | ảnh `ls -lh` | [ ] |

Lặp lại khi thất bại:

1. Đổi tên miền không tồn tại khác (ví dụ `x7k2.example.com`).
2. `docker restart <local_dns_id>` để xóa cache và negative cache.
3. Chạy lại `gen_query.py`, `gen_response.py`, rồi `./attack`.
4. Kiểm tra lại IP server thật và cổng đích `44444`.

Lưu ý: nếu bắt cả lưu lượng, thêm bộ lọc `udp port 53` để pcap gọn hơn:

```bash
tcpdump -i eth0 -n 'udp port 53' -w attacker.pcap
```

### Giai đoạn F - 4.5 Phòng chống tấn công (1 điểm)

| # | Việc | Bằng chứng | Trạng thái |
|---|---|---|---|
| F1 | Vào Local DNS Server: `nano /etc/bind/named.conf.options` | ảnh trước khi sửa | [ ] |
| F2 | Xóa dòng `query-source port 44444;`, lưu file | ảnh sau khi sửa | [ ] |
| F3 | `docker restart <local_dns_id>` | ảnh | [ ] |
| F4 | Tấn công lại như giai đoạn E | ảnh `L03-F4-tan-cong-lai.png` | [ ] |
| F5 | Xác nhận tấn công thất bại (`dig` vẫn trả IP thật) | ảnh `dig` | [ ] |
| F6 | Viết giải thích vào báo cáo | mục 5 của `11-lab03-ket-qua.md` | [ ] |

Giải thích cần nêu: khi cổng nguồn ngẫu nhiên, không gian cần đoán tăng từ `2^16` (chỉ Transaction ID) lên khoảng `2^16 x 2^15` (ID x cổng), nên flood của Attacker không kịp khớp trước response thật.

### Giai đoạn G - Báo cáo và đóng gói

| # | Việc | Bằng chứng | Trạng thái |
|---|---|---|---|
| G1 | Điền đủ mục 1-5 trong `docs/11-lab03-ket-qua.md` | file báo cáo | [ ] |
| G2 | Chèn đủ ảnh, đặt tên theo quy ước | thư mục `lab03/evidence/screenshots/` | [ ] |
| G3 | Kiểm tra 2 pcap mở được bằng Wireshark | ảnh | [ ] |
| G4 | Đóng gói `NhomX_Lab03_BaoCao.zip` | ảnh `unzip -l` | [ ] |
| G5 | Rà lại tên, MSSV; mục `x`, `y` ghi “không áp dụng” trước khi nộp | - | [ ] |

Quy ước đặt tên bằng chứng:

```text
L03-<bước>-<nội-dung>.png        # ảnh
L03-<bước>-<nội-dung>.pcap       # nếu cần pcap phụ
```

## 7. Bảng lệnh tham khảo

```bash
# Kiểm tra Internet trong VM
ping -c 3 8.8.8.8
dig @8.8.8.8 example.com

# Dọn Lab02 trước khi chạy Lab03 (tránh trùng subnet 10.11.1.0/24)
cd ~/it4263lab/lab02
docker-compose down

# Docker
cd ~/lab03
docker-compose build
docker-compose up -d
docker ps
dockps
docksh <id>
docker restart <id>
docker cp <file> <id>:/tmp
docker cp <id>:/tmp/<file> .

# Kiểm tra DNS
dig ns.attacker32.com
dig www.example.com
dig @ns.attacker32.com www.example.com

# Bắt gói trong container
tcpdump -i eth0 -n 'udp port 53' -w /tmp/attacker.pcap

# Tấn công
gcc attack.c -o attack
./attack

# Cache
rndc dumpdb -cache /var/cache/bind/dump.db
grep -n "example.com\|attacker32" /var/cache/bind/dump.db
```

## 8. Rủi ro và cách xử lý

| Rủi ro | Dấu hiệu | Cách xử lý |
|---|---|---|
| Source tự dựng không khớp file giảng viên | Giảng viên yêu cầu đúng file phát cho lớp | Hỏi trước; giữ đúng tên file/luồng thao tác; nếu có source thật thì thay cấu hình vào scaffold |
| Docker không chạy trong VM | `Cannot connect to the Docker daemon` | `sudo systemctl start docker`, kiểm tra `docker ps` |
| Xung đột subnet với Lab02 | Docker báo `Pool overlaps with other one on this address space` | `cd ~/it4263lab/lab02 && docker-compose down`; kiểm tra `docker network ls` |
| VM không ra Internet | `ping 8.8.8.8` fail | Kiểm tra Adapter 1 = NAT, `sudo dhclient enp0s3`; nếu vẫn fail, dùng fake root `10.11.1.50` |
| BIND từ chối response giả | `dig` vẫn trả IP thật; log có DNSSEC/cookie | Đặt `dnssec-validation no;` và `send-cookie no;` trong `named.conf.options` |
| `ns.attacker32.com` không phân giải | `dig ns.attacker32.com` timeout/NXDOMAIN | Thêm forward zone `attacker32.com` → `10.11.1.40` trong `named.conf` của Local DNS |
| Không thấy card `br-` | Wireshark không có interface Docker | Bắt bằng `tcpdump` trong container, sau đó `docker cp` pcap ra |
| Tấn công không thành công | `dig` vẫn trả IP thật | Kiểm tra IP server thật, cổng đích `44444`, Transaction ID; đổi tên miền; restart Local DNS |
| Cache/negative cache còn | Response giả bị bỏ qua | `docker restart` Local DNS trước mỗi lần thử |
| `rndc dumpdb` lỗi | Không tìm thấy file dump | Kiểm tra `directory` trong `named.conf.options`; dùng `rndc status` xác nhận |
| pcap quá lớn | File hàng trăm MB | Capture với bộ lọc `udp port 53`, dừng ngay sau khi thành công |
| `apt-get update` chậm/lỗi mạng | Không tải được gói | Kiểm tra NAT `enp0s3`, `ping 8.8.8.8`; thử lại; không cài gói ngoài nhu cầu |

## 9. Definition of Done

- [ ] Cả 2 lệnh `dig` sau tấn công đều trả về `ns.attacker32.com`.
- [ ] `rndc dumpdb` cho thấy cache chứa bản ghi NS giả của `example.com`.
- [ ] Có đủ `attacker.pcap` và `local_dns_server.pcap`, mở được bằng Wireshark.
- [ ] Mục 4.5 chứng minh được tấn công thất bại sau khi bỏ `query-source port 44444`.
- [ ] `docs/11-lab03-ket-qua.md` điền đủ 5 mục, không còn ô trống; mục `x`, `y` ghi “không áp dụng”.
- [ ] File nộp đúng tên `NhomX_Lab03_BaoCao.zip`, kiểm tra bằng `unzip -l`.

## 10. Tiến độ và blocker

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Đề bài + mẫu báo cáo | Có | 2 PDF trong `lab03/` |
| Source `~/lab03` | **Tự dựng** | Bắt đầu từ scaffold trong `lab03/`; không chờ giảng viên |
| `x`, `y` | **Không áp dụng** | Bài cá nhân; tài liệu hướng dẫn ghi sai hình thức nhóm |
| VM Ubuntu 20.04 | **Có, dùng lại** | `Ubuntu2004` tại `192.168.117.5`; Docker 26.1.3 hoạt động |
| Internet trong VM | **Đã có** | NAT `enp0s3` = `10.0.2.15`; ping `8.8.8.8` OK |
| Lab02 | **Tạm dừng** | Đã `docker-compose down`; bật lại khi trình bày Lab02 |
| Báo cáo kết quả | Khung đã tạo | `docs/11-lab03-ket-qua.md` |

## 11. Nhật ký thay đổi so với kế hoạch ban đầu

| Ngày | Nội dung thay đổi | Lý do |
|---|---|---|
| 2026-11-05 | Chuyển từ “chờ source giảng viên” sang **tự dựng source** | Giảng viên không cấp source; Lab02 đã có tiền lệ tự dựng thành công |
| 2026-11-05 | Bỏ hoàn toàn `x`, `y`; dùng subnet/IP cố định | Bài là cá nhân; tài liệu hướng dẫn ghi sai hình thức nhóm |
| 2026-11-05 | Dùng lại VM `Ubuntu2004` thay vì tạo VM mới | VM đã có Docker, đủ tài nguyên; tránh cài lại môi trường |
| 2026-11-05 | Xác nhận Internet qua NAT và cài thêm `bind9-utils`, `curl` | Phục vụ forwarder `8.8.8.8` và lệnh `rndc` |
| 2026-11-05 | `docker-compose down` cụm Lab02 trước khi làm Lab03 | Tránh trùng subnet `10.11.1.0/24`; khi trình bày Lab02 sẽ bật lại |
