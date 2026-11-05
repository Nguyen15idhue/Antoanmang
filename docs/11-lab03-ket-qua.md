# 11 - Kết quả Lab03: DNS Cache Poisoning (kỹ thuật Kaminsky)

## Thông tin sinh viên

| Hạng mục | Nội dung |
|---|---|
| Họ tên | Phạm Quỳnh Chi |
| MSSV | 223001699 |
| Lớp / mã lớp thực hành | An toàn mạng máy tính |
| Nhóm (`x`, `y`) | Không áp dụng (bài cá nhân) |
| Ngày thực hiện | 2026-11-05 |
| Ngày nộp | 2026-11-05 |

Trạng thái tài liệu: `[ ] Chưa thực nghiệm` / `[x] Đang thực hiện` / `[ ] Hoàn thành`

> Tài liệu này là báo cáo kết quả, điền trực tiếp sau khi làm theo `docs/10-lab03-ke-hoach.md`.
> Mỗi mục dưới đây tương ứng một ô trong mẫu `lab03/Lab03_SttNhom_BaoCao.pdf`.

## 0. Tóm tắt kết quả

| Mục | Điểm tối đa | Trạng thái | Bằng chứng chính |
|---|---|---|---|
| 1. Triển khai hệ thống | 1 | `<đạt/không>` | `L03-B10`, `L03-B11`, `L03-B12` |
| 2. Tạo DNS Query | 2 | `<đạt/không>` | `ip_req.bin`, `L03-C3` |
| 3. Tạo DNS Response giả | 2 | `<đạt/không>` | `ip_resp.bin`, `L03-D5` |
| 4. Thực hiện tấn công | 4 | `<đạt/không>` | `attacker.pcap`, `local_dns_server.pcap`, `L03-E*` |
| 5. Phòng chống | 1 | `<đạt/không>` | `L03-F2`, `L03-F5` |
| **Tổng** | **10** |  |  |

Kết luận nhanh: `<tấn công thành công / thất bại, lý do ngắn>`

---

## 1. Triển khai hệ thống (1 điểm)

### 1.1. Cấu hình IP đã sử dụng

| Container | IP | Vai trò |
|---|---|---|
| Attacker | `10.11.1.30` | Gửi query và response giả |
| Local DNS Server | `10.11.1.20` | Nạn nhân, BIND9 |
| User | `10.11.1.10` | Client |
| Attacker NS (`ns.attacker32.com`) | `10.11.1.40` | Máy chủ tên miền giả |

Các file đã cấu hình (bài cá nhân, không dùng `x`, `y`):

| File | Nội dung sau khi sửa |
|---|---|
| `docker-compose.yml` + `.env` | subnet `10.11.1.0/24`; User `.10`, Local DNS `.20`, Attacker `.30`, Attacker NS `.40` |
| `image_attacker_ns/zone_attacker32.com` | `ns.attacker32.com. A 10.11.1.40` |
| `image_attacker_ns/zone_example.com` | `example.com. NS ns.attacker32.com.`; `www.example.com. A 1.2.3.4` |
| `image_local_dns_server/named.conf` | `forwarders { 8.8.8.8; };`; forward zone `attacker32.com` → `10.11.1.40` |
| `image_user/resolv.conf` | `nameserver 10.11.1.20` |

Bằng chứng: `L03-B-docker-ps.png`, `L03-B-ping.png`.

### 1.2. Kết quả lệnh `dig ns.attacker32.com`

```text
; <<>> DiG 9.18.30-0ubuntu0.20.04.2-Ubuntu <<>> ns.attacker32.com
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 28428
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;ns.attacker32.com.             IN      A

;; ANSWER SECTION:
ns.attacker32.com.      290     IN      A       10.11.1.40

;; SERVER: 10.11.1.20#53(10.11.1.20) (UDP)
```

Ảnh: `L03-B10-dig-ns-attacker32.png`

Nhận xét: trả về đúng IP `10.11.1.40` của Attacker NS; Local DNS phân giải được nhờ forward zone `attacker32.com`.

### 1.3. Kết quả lệnh `dig www.example.com`

```text
; <<>> DiG 9.18.30-0ubuntu0.20.04.2-Ubuntu <<>> www.example.com
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 24444
;; flags: qr rd ra; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;www.example.com.               IN      A

;; ANSWER SECTION:
www.example.com.        290     IN      A       172.66.147.243
www.example.com.        290     IN      A       104.20.23.154

;; SERVER: 10.11.1.20#53(10.11.1.20) (UDP)
```

Ảnh: `L03-B11-dig-www-example.png`

Nhận xét: trước tấn công, `www.example.com` trả về IP thật của Cloudflare (`172.66.147.243`, `104.20.23.154`). Đây là mốc so sánh với kết quả sau tấn công.

### 1.4. Kết quả lệnh `dig @ns.attacker32.com www.example.com`

```text
; <<>> DiG 9.18.30-0ubuntu0.20.04.2-Ubuntu <<>> @ns.attacker32.com www.example.com
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 18565
;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;www.example.com.               IN      A

;; ANSWER SECTION:
www.example.com.        300     IN      A       1.2.3.4

;; SERVER: 10.11.1.40#53(ns.attacker32.com) (UDP)
```

Ảnh: `L03-B12-dig-at-ns-attacker32.png`

Nhận xét: hỏi trực tiếp Attacker NS trả về IP giả `1.2.3.4`, xác nhận zone giả đã hoạt động.

---

## 2. Tạo thông điệp DNS Query truy vấn (2 điểm)

### 2.1. Thông tin trên thông điệp truy vấn (1 điểm)

| Trường | Giá trị |
|---|---|
| Địa chỉ IP nguồn | `10.11.1.30` (container Attacker) |
| Số hiệu cổng nguồn | `12345` |
| Địa chỉ IP đích | `10.11.1.20` (Local DNS Server) |
| Số hiệu cổng đích | `53` |
| Tên miền được truy vấn | `abcxyz.example.com` (A, IN) |

Bằng chứng: file `ip_req.bin` (64 byte) + ảnh `L03-C3-ip-req-bin.png`.

```text
45 00 00 1c c4 ea 00 00 40 11 9f 9f 0a 0b 01 1e   E.......@.......
0a 0b 01 14 30 39 00 35 00 2c 00 00 50 0f 01 00   ....09.5.,..P...
00 01 00 00 00 00 00 00 06 61 62 63 78 79 7a 07   .........abcxyz.
65 78 61 6d 70 6c 65 03 63 6f 6d 00 00 01 00 01   example.com.....
```

Phân tích: IP nguồn `0a0b011e` = 10.11.1.30; IP đích `0a0b0114` = 10.11.1.20; cổng nguồn `0x3039` = 12345; cổng đích `0x0035` = 53; UDP length `0x002c` = 44; DNS ID `0x500f`; question `abcxyz.example.com` type A class IN.

### 2.2. Vì sao truy vấn tới tên miền không tồn tại (1 điểm)

Trả lời: `abcxyz.example.com` là tên miền không tồn tại, Local DNS Server không có bản ghi trong cache nên buộc phải gửi query forward ra server cấp trên (`8.8.8.8`) và chờ trả lời. Trong khoảng thời gian chờ đó, Attacker có thể gửi response giả để "thắng race" (Kaminsky attack). Nếu hỏi một tên đã có trong cache, Local DNS Server trả lời ngay lập tức, không tạo ra khoảng trống để chèn gói giả, nên tấn công không thể thực hiện.

---

## 3. Tạo thông điệp DNS Response giả mạo (2 điểm)

### 3.1. Thông điệp giả mạo gửi đi từ nút mạng nào (0.5 điểm)

> Gợi ý: gửi từ container Attacker, nhưng **giả mạo địa chỉ IP nguồn** của server thật mà Local DNS Server đang chờ trả lời (server nhận query forward ở mục 4).

Trả lời: `<điền>`

Bằng chứng xác định IP server thật: ảnh Wireshark `L03-D1-root-server.png`.

### 3.2. Thông tin trên thông điệp trả lời giả mạo (1 điểm)

| Trường | Giá trị |
|---|---|
| Địa chỉ IP nguồn | `<IP server thật, giả mạo>` |
| Số hiệu cổng nguồn | `53` |
| Địa chỉ IP đích | `<IP Local DNS Server>` |
| Số hiệu cổng đích | `44444` |
| Thông tin tên miền đã giả mạo | `example.com NS ns.attacker32.com` (+ bản ghi A glue cho `ns.attacker32.com`) |

Bằng chứng: file `ip_resp.bin` + ảnh `L03-D5-ip-resp-bin.png`.

### 3.3. Điều kiện để tấn công thành công (0.5 điểm)

> Gợi ý: response phải khớp query đang chờ và đến trước response thật.

Trả lời: `<điền>`

Checklist điều kiện:

- [ ] Đúng IP nguồn = IP server mà Local DNS Server đã gửi query tới.
- [ ] Đúng cổng nguồn `53`.
- [ ] Đúng IP đích = IP Local DNS Server.
- [ ] Đúng cổng đích `44444` (do `query-source port 44444`).
- [ ] Đúng Transaction ID của query đang chờ (flood nhiều ID).
- [ ] Đúng question section (tên miền, type, class).
- [ ] Đúng định dạng DNS, có bản ghi NS giả và glue hợp lệ.
- [ ] Đến trước response thật từ server cấp trên.

---

## 4. Thực hiện tấn công (4 điểm)

### 4.1. Thông điệp DNS Query mà Attacker đã gửi (0.5 điểm)

Mô tả: `<IP nguồn:port -> IP đích:53, tên miền, Transaction ID>`

Ảnh Wireshark: `L03-E-wireshark-query-attacker.png`

### 4.2. Thông điệp DNS Query mà Local DNS Server đã gửi (0.5 điểm)

Mô tả: `<IP nguồn:44444 -> IP đích:53, tên miền>`

Thông điệp này gửi tới máy nào: `<điền IP server cấp trên>`

Ảnh Wireshark: `L03-E-wireshark-query-local-dns.png`

### 4.3. Đặc điểm lưu lượng trên Local DNS Server khi bị tấn công (0.5 điểm)

> Gợi ý: một query hợp lệ đi ra, nhưng có rất nhiều response đến dồn dập từ cùng IP nguồn (giả mạo), với nhiều Transaction ID khác nhau; mật độ gói tăng đột biến.

Mô tả: `<điền>`

Ảnh Wireshark: `L03-E-wireshark-flood.png`

### 4.4. Gói DNS Response giả mạo được Local DNS Server chấp nhận (0.5 điểm)

Mô tả gói: `<Transaction ID, IP nguồn, cổng đích 44444, nội dung NS>`

Tại sao khẳng định được chấp nhận: `<điền, ví dụ: cùng Transaction ID với query, là gói duy nhất có response và cache sau đó chứa ns.attacker32.com>`

Ảnh Wireshark: `L03-E-wireshark-accepted-response.png`

### 4.5. Nội dung bộ đệm dịch vụ của Local DNS Server (0.5 điểm)

Lệnh đã dùng:

```bash
rndc dumpdb -cache /var/cache/bind/dump.db
grep -n "example.com\|attacker32" /var/cache/bind/dump.db
```

Trích đoạn cache:

```text
<dán đoạn cache>
```

Ảnh: `L03-E9-cache-poisoned.png`

Kết luận: `<cache chứa example.com NS ns.attacker32.com, kèm IP của Attacker NS>`

### 4.6. Kết quả tìm kiếm trên máy User (0.5 điểm)

```text
<dán kết quả dig www.example.com>
<dán kết quả dig @ns.attacker32.com www.example.com>
```

Ảnh: `L03-E6-dig-www-sau.png`, `L03-E7-dig-at-ns-sau.png`

Kết luận: `<cả hai đều trả về ns.attacker32.com => Local DNS Server đã bị đầu độc>`

### 4.7. Mô tả ngắn gọn kịch bản tấn công đã xảy ra (0.5 điểm)

> Gợi ý viết 4-6 câu theo đúng 4 bước: Attacker query tên không tồn tại -> Local DNS forward lên server thật -> Attacker flood response giả khớp ID/cổng -> response giả đến trước, cache bị ghi đè -> User nhận IP giả.

Trả lời: `<điền>`

### 4.8. Hậu quả của cuộc tấn công (0.5 điểm)

> Gợi ý: toàn bộ client dùng Local DNS Server bị dẫn tới máy chủ giả; có thể bị phishing, phát tán malware, đánh cắp thông tin đăng nhập, giả mạo dịch vụ; hậu quả kéo dài đến khi cache hết hạn hoặc bị xóa.

Trả lời: `<điền>`

---

## 5. Phòng chống tấn công (1 điểm)

Cấu hình đã thay đổi:

| Trước | Sau |
|---|---|
| `query-source port 44444;` | `<đã xóa dòng>` |

Kết quả tấn công lại: `<thất bại / thành công>`; `dig` trả về: `<IP thật>`.

Ảnh: `L03-F2-named-conf-options.png`, `L03-F4-tan-cong-lai.png`, `L03-F5-dig-sau-phong-chong.png`.

Giải thích vì sao dùng cổng ngẫu nhiên có tác dụng phòng chống:

> Gợi ý: khi cổng nguồn cố định, Attacker chỉ cần đoán 16 bit Transaction ID (2^16 khả năng). Khi cổng nguồn ngẫu nhiên, phải đoán đồng thời cả Transaction ID lẫn cổng nguồn (khoảng 2^16 x 2^15), không gian tăng hàng chục nghìn lần. Với cùng tốc độ flood, xác suất khớp trước response thật gần như bằng 0.

Trả lời: `<điền>`

---

## 6. Checklist đóng gói

- [ ] `docs/11-lab03-ket-qua.md` điền đủ, không còn `<điền>`.
- [ ] Đủ ảnh, đặt tên theo `L03-<bước>-<nội dung>.png`.
- [ ] `attacker.pcap` mở được bằng Wireshark.
- [ ] `local_dns_server.pcap` mở được bằng Wireshark.
- [ ] Đã ghi rõ `x`, `y`, họ tên, MSSV.
- [ ] Zip đúng tên `NhomX_Lab03_BaoCao.zip`.
- [ ] Kiểm tra lại bằng `unzip -l NhomX_Lab03_BaoCao.zip` thấy đủ báo cáo + 2 pcap.
- [ ] Không đưa file `.bin`, source hay ảnh thừa vào zip nếu đề không yêu cầu.

Cấu trúc gợi ý bên trong file nộp:

```text
NhomX_Lab03_BaoCao.zip
├── NhomX_Lab03_BaoCao.pdf        # hoặc .docx xuất từ tài liệu này
├── attacker.pcap
└── local_dns_server.pcap
```

## 7. Phụ lục - Ánh xạ bằng chứng

| Ký hiệu | Nội dung | Mục báo cáo |
|---|---|---|
| `L03-B10-dig-ns-attacker32.png` | `dig ns.attacker32.com` | 1 |
| `L03-B11-dig-www-example.png` | `dig www.example.com` trước tấn công | 1 |
| `L03-B12-dig-at-ns-attacker32.png` | `dig @ns.attacker32.com www.example.com` | 1 |
| `L03-C3-ip-req-bin.png` | Nội dung `ip_req.bin` | 2 |
| `L03-D1-root-server.png` | Xác định server Local DNS forward tới | 3 |
| `L03-D5-ip-resp-bin.png` | Nội dung `ip_resp.bin` | 3 |
| `L03-E-wireshark-query-attacker.png` | Query từ Attacker | 4.1 |
| `L03-E-wireshark-query-local-dns.png` | Query từ Local DNS | 4.2 |
| `L03-E-wireshark-flood.png` | Flood response | 4.3 |
| `L03-E-wireshark-accepted-response.png` | Response giả được chấp nhận | 4.4 |
| `L03-E9-cache-poisoned.png` | Cache bị đầu độc | 4.5 |
| `L03-E6-dig-www-sau.png` | `dig` sau tấn công | 4.6 |
| `L03-E7-dig-at-ns-sau.png` | `dig @ns` sau tấn công | 4.6 |
| `L03-F2-named-conf-options.png` | Đã xóa `query-source` | 5 |
| `L03-F4-tan-cong-lai.png` | Tấn công lại | 5 |
| `L03-F5-dig-sau-phong-chong.png` | `dig` sau phòng chống | 5 |
| `attacker.pcap` | Lưu lượng phía Attacker | 4 |
| `local_dns_server.pcap` | Lưu lượng phía Local DNS | 4 |
