# Lab02 - Tóm tắt các bước thực hiện

Môi trường: 3 container Docker trên mạng `10.11.1.0/24` - User `10.11.1.10`, Server `10.11.1.20`, Attacker `10.11.1.51`.
Mỗi bước gồm: **Mục đích - Lệnh - Kết quả kỳ vọng - Giải thích chi tiết**.

---

## Hiểu nhanh trước khi làm

### ARP là gì?

Trong cùng một mạng LAN, máy tính không gửi gói tin trực tiếp bằng địa chỉ IP. Nó phải biết **địa chỉ MAC** của máy đích để đóng gói frame Ethernet.

- Nếu đã biết MAC: lấy từ **bảng ARP** (ARP cache).
- Nếu chưa biết: gửi ARP Request dạng broadcast: *"Ai có IP `10.11.1.20`? Hãy trả lời cho `10.11.1.10`."*
- Máy sở hữu IP đó gửi ARP Reply kèm MAC của mình.
- Máy gửi lưu cặp `IP -> MAC` vào bảng ARP để dùng lại.

### Vì sao ARP bị lừa được?

ARP **không có cơ chế xác thực**. Bất kỳ máy nào trong LAN cũng có thể gửi ARP Reply, kể cả khi không ai hỏi. Máy nhận thường tin và cập nhật lại bảng ARP.

Attacker lợi dụng điều này để gửi Reply giả:

> "IP `10.11.1.20` (Server) nằm tại MAC của Attacker."

Khi đó, gói tin của User gửi đến Server sẽ được đóng gói Ethernet với MAC đích là **MAC của Attacker**, nên đi vào máy Attacker thay vì đến Server.

### `ip_forward` quyết định "mất mạng" hay "MITM"

Sau khi gói tin đi vào Attacker, kernel Linux xử lý theo `net.ipv4.ip_forward`:

- `ip_forward=0`: Attacker **không chuyển tiếp**. Gói tin bị drop. Kết quả là User mất kết nối tới Server (DoS).
- `ip_forward=1`: Attacker **chuyển tiếp** gói tin sang Server. Kết nối vẫn hoạt động nhưng toàn bộ lưu lượng đi qua Attacker, tạo điều kiện nghe lén/sửa nội dung (MITM).

Trong lab này, container mặc định có `ip_forward=0` (kiểm tra bằng `docker exec attacker sysctl net.ipv4.ip_forward`). Nếu giá trị là `1` - do image/compose/script hoặc thao tác trước đó bật - Attacker sẽ forward gói tiếp, ping vẫn thông và ta **không thấy mất gói**. Vì vậy, trước KB1 cần kiểm tra và đặt về `0`.

### Poison một chiều và hai chiều

- **Một chiều:** chỉ bảng ARP của User bị nhiễm.
  - User -> Server: đi qua Attacker.
  - Server -> User: vẫn đi trực tiếp vì Server còn giữ MAC thật của User.
  - Nếu Attacker drop gói thì User mất kết nối; nếu Attacker forward thì luồng dữ liệu bị lệch một chiều.
- **Hai chiều:** bảng ARP của cả User và Server đều bị nhiễm.
  - User -> Server và Server -> User đều đi qua Attacker.
  - Đây là điều kiện cần để Attacker đứng giữa và sửa nội dung (MITM).

### MAC trong bài lab

Docker sinh MAC theo IP theo quy luật `02:42:0a:0b:01:xx`, trong đó `xx` là octet cuối của IP viết dạng hex:

| Máy | IP | Octet cuối | MAC |
|---|---|---|---|
| User | `10.11.1.10` | `10` = `0a` | `02:42:0a:0b:01:0a` |
| Server | `10.11.1.20` | `20` = `14` | `02:42:0a:0b:01:14` |
| Attacker | `10.11.1.51` | `51` = `33` | `02:42:0a:0b:01:33` |

Hiểu quy luật này giúp kiểm tra nhanh bảng ARP đã bị poison hay chưa.

---

## Bước 0 - Khởi động môi trường

- **Mục đích:** dựng 3 container đúng cấu hình lab.
- **Lệnh:**
  ```bash
  cd ~/it4263lab/lab02
  docker-compose up -d
  docker ps --format '{{.Names}}\t{{.Status}}'
  ```
- **Kết quả:** `user`, `server`, `attacker` đều `Up`.

### Giải thích chi tiết

- `docker-compose up -d` đọc file `docker-compose.yml` và `.env`, tạo network bridge `10.11.1.0/24`, rồi khởi động 3 container ở chế độ nền (`-d`).
- Mỗi container được gán IP tĩnh qua biến môi trường:
  - `USER_IP=10.11.1.10`
  - `SERVER_IP=10.11.1.20`
  - `ATTACKER_IP=10.11.1.51`
- `command: sleep infinity` giữ container chạy mãi để ta có thể `docker exec` vào làm việc.
- `cap_add: NET_ADMIN, NET_RAW` cho phép thao tác cấu hình mạng và gửi/nhận frame thô - cần thiết cho ARP spoofing và tcpdump.
- Container `attacker` có thêm `privileged: true` để chắc chắn có đủ quyền ghi `sysctl`, mở raw socket và chạy công cụ tấn công.
- `docker ps` dùng để xác nhận cả 3 container đang chạy. Nếu có container `Restarting` hoặc `Exited`, xem log bằng `docker-compose logs <tên_container>`.

---

## Bước 1 (B1) - Xem thông số 3 container

- **Mục đích:** xác nhận IP/MAC và bảng ARP ban đầu.
- **Lệnh:**
  ```bash
  for c in user server attacker; do
    echo "[$c]"
    docker exec $c ip -br a | grep eth0
    docker exec $c cat /sys/class/net/eth0/address
    docker exec $c arp -n
  done
  ```
- **Kết quả:** User `10.11.1.10 / 02:42:0a:0b:01:0a`, Server `10.11.1.20 / 02:42:0a:0b:01:14`, Attacker `10.11.1.51 / 02:42:0a:0b:01:33`; bảng ARP ban đầu thường trống hoặc chưa có entry đúng.

### Giải thích chi tiết

- `ip -br a` hiển thị gọn các interface và địa chỉ IP. Ta chỉ cần quan tâm `eth0` vì đó là card mạng kết nối vào lab.
- `cat /sys/class/net/eth0/address` đọc trực tiếp địa chỉ MAC của card mạng.
- `arp -n` xem bảng ARP hiện tại. `-n` nghĩa là không phân giải tên miền, chỉ hiện IP/MAC cho dễ đọc.
- Ban đầu bảng ARP có thể trống vì 3 máy chưa giao tiếp với nhau. Khi ping hoặc gửi dữ liệu, các entry mới xuất hiện.
- Đây là **mốc so sánh**. Sau khi poison, ta sẽ thấy MAC của Server bị thay bằng MAC của Attacker. Nếu không chụp lại bước này, rất khó chứng minh bảng ARP đã bị thay đổi.
- Có thể kiểm tra chéo MAC theo bảng quy luật ở phần "Hiểu nhanh trước khi làm". Ví dụ IP `10.11.1.20` phải có MAC kết thúc bằng `14`.

---

## Bước 2 (KB1) - Poison ARP một chiều tới User

- **Mục đích:** lừa User rằng IP Server nằm tại MAC Attacker, gây mất kết nối (DoS).
- **Lệnh:**
  ```bash
  # 1. Tắt chuyển tiếp IP trên Attacker: gói đến Attacker sẽ bị drop
  docker exec attacker sysctl -w net.ipv4.ip_forward=0

  # 2. Không cho User chấp nhận ICMP Redirect (tránh bị đổi đường đi ngoài ý muốn)
  docker exec user sysctl -w net.ipv4.conf.all.accept_redirects=0 net.ipv4.conf.eth0.accept_redirects=0

  # 3. Xóa bảng ARP cũ để bắt đầu sạch
  for c in user server attacker; do docker exec $c ip neigh flush all; done

  # 4. Tạo ARP entry bình thường trước khi poison
  docker exec user ping -c 1 10.11.1.20 >/dev/null
  docker exec server ping -c 1 10.11.1.10 >/dev/null

  # 5. Bắt gói ARP + ICMP trên User
  docker exec -d user sh -c "tcpdump -U -i eth0 -n 'arp or icmp' -w /tmp/kb1.pcap"
  sleep 2

  # 6. Poison: gửi 8 ARP Reply giả, mỗi giây 1 gói
  docker exec -d attacker sh -c "python3 -u /attack/scenario1.py --count 8 --interval 1"
  sleep 9
  docker exec attacker pkill -f scenario1

  # 7. Kiểm tra bảng ARP và ping
  docker exec user arp -n
  docker exec user ping -c 3 10.11.1.20
  ```
- **Kết quả:** ARP của User có `10.11.1.20 at 02:42:0a:0b:01:33`; ping **100% packet loss**.

### Giải thích chi tiết

#### Vì sao phải tắt `ip_forward` trước?

Đây là điểm quan trọng nhất của KB1.

- Nếu `ip_forward=1`, Attacker nhận gói tin của User rồi **chuyển tiếp** sang Server. Server trả lời trực tiếp cho User. Ping vẫn thông, kết quả là `0% packet loss`.
- Nếu `ip_forward=0`, Attacker nhận gói tin nhưng **không chuyển tiếp**, kernel drop luôn. User không nhận được reply, kết quả là `100% packet loss`.
- Vì vậy, muốn chứng minh ARP poisoning gây mất kết nối, phải đặt `ip_forward=0` **trước khi** poison và kiểm tra ping.

Nếu lần chạy trước vẫn thấy nhận gói tin, gần như chắc chắn là do `ip_forward` vẫn bằng `1`. Có thể kiểm tra bằng:

```bash
docker exec attacker sysctl net.ipv4.ip_forward
```

Giá trị mặc định của container trong lab là `0`. Nếu thấy `1`, đó là do image/compose/script hoặc thao tác trước đó bật, **không phải** kế thừa từ Docker host. `ip_forward` là sysctl theo từng network namespace.

#### Vì sao tắt `accept_redirects` trên User?

**ICMP Redirect** xuất hiện khi Attacker đang bật forward và chuyển gói ra cùng interface; nó là **dấu hiệu** forwarding đang bật, không phải nguyên nhân chính giúp ping thông. Tắt `accept_redirects` để User không cài thêm route chuyển hướng, giúp kết quả test sạch và dễ đọc hơn. Nguyên nhân gốc vẫn là `ip_forward`.

#### Các bước nhỏ diễn ra như thế nào?

1. **Xóa bảng ARP:** `ip neigh flush all` xóa toàn bộ entry cũ, tránh trường hợp entry cũ còn hạn và che mất kết quả poison.
2. **Ping mồi:** User ping Server một lần để học MAC thật của Server. Lúc này bảng ARP của User có `10.11.1.20 -> 02:42:0a:0b:01:14`. Đây cũng là bước chứng minh kết nối ban đầu đang tốt.
3. **Bắt gói:** `tcpdump -U -i eth0 -n 'arp or icmp' -w /tmp/kb1.pcap` ghi lại các gói ARP và ICMP trên card `eth0` của User.
   - `-U`: ghi xuống file ngay khi có gói, tránh mất dữ liệu khi tắt đột ngột.
   - `-n`: không phân giải tên.
   - `-w`: lưu ra file pcap.
4. **Poison:** `scenario1.py` làm hai việc:
   - Phân giải MAC của User.
   - Gửi 8 ARP Reply giả, mỗi giây một gói, nội dung: *"IP `10.11.1.20` nằm tại MAC của Attacker"*.
   Linux của User chấp nhận Reply này và ghi đè entry cũ, nên bảng ARP chuyển thành `10.11.1.20 -> 02:42:0a:0b:01:33`.
5. **Kiểm tra:** `arp -n` phải thấy Server trỏ về MAC Attacker. Sau đó ping Server: gói ICMP đi đến MAC Attacker, bị drop vì `ip_forward=0`, nên ping mất 100% gói.

#### Vì sao đôi khi thấy cả `10.11.1.51` trong bảng ARP của User?

Trong quá trình `scenario1.py` phân giải MAC của User, Attacker gửi ARP Request với IP nguồn `10.11.1.51` và MAC thật của Attacker. User có thể học luôn cặp `10.11.1.51 -> MAC Attacker`. Đây là hiện tượng bình thường, không phải lỗi. Điều quan trọng là entry `10.11.1.20` đã trỏ sai sang MAC Attacker.

#### Đọc file pcap

- Có khoảng 8 ARP Reply giả từ Attacker.
- Có các gói ICMP Echo Request từ User, nhưng đích Ethernet là MAC Attacker.
- Không có ICMP Echo Reply từ Server (vì gói đã bị drop).

#### Lỗi thường gặp

- **Ping vẫn 0% loss:** kiểm tra `ip_forward` trên Attacker; kiểm tra User có nhận ICMP Redirect không; chạy lại bước tắt forward và poison lại.
- **`arp -n` vẫn hiện MAC thật của Server:** ARP Reply giả chưa đến được User. Kiểm tra `--iface eth0`, đúng IP victim, và chạy tcpdump trên User để xem có frame ARP không.
- **Vừa poison xong đã restart container:** cấu hình `ip_forward` và bảng ARP có thể bị reset. Nếu restart, phải làm lại từ đầu.
- **Quên `pkill -f scenario1`:** tiến trình vẫn gửi ARP Reply liên tục. Không sai về kỹ thuật nhưng dễ ảnh hưởng các bước sau; nên dừng đúng lúc.

---

## Bước 3 (KB2) - Poison ARP hai chiều

- **Mục đích:** lừa cả User và Server để toàn bộ lưu lượng đi qua Attacker (điều kiện MITM).
- **Lệnh:**
  ```bash
  # 1. Xóa bảng ARP cũ
  for c in user server attacker; do docker exec $c ip neigh flush all; done

  # 2. Tạo ARP entry bình thường ở cả hai phía
  docker exec user ping -c 1 10.11.1.20 >/dev/null
  docker exec server ping -c 1 10.11.1.10 >/dev/null

  # 3. Bắt gói ARP trên Attacker
  docker exec -d attacker sh -c "tcpdump -U -i eth0 -n 'arp' -w /tmp/kb2.pcap"
  sleep 2

  # 4. Poison hai chiều: User và Server đều trỏ về MAC Attacker
  docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 8 --interval 1"
  sleep 9
  docker exec attacker pkill -f scenario2

  # 5. Kiểm tra bảng ARP hai phía
  docker exec user arp -n
  docker exec server arp -n
  ```
- **Kết quả:** cả hai bảng ARP đều trỏ `10.11.1.10` và `10.11.1.20` về MAC `02:42:0a:0b:01:33`; mỗi giây có một cặp ARP Reply.

### Giải thích chi tiết

#### Vì sao cần poison hai chiều?

- Poison một chiều chỉ khiến **User -> Server** đi qua Attacker. Gói trả lời của Server vẫn đi trực tiếp đến User vì Server còn giữ MAC thật của User.
- Muốn Attacker thấy và sửa được **cả hai chiều**, phải poison cả hai bảng ARP:
  - Nói với User: *"Server `10.11.1.20` nằm ở MAC Attacker."*
  - Nói với Server: *"User `10.11.1.10` nằm ở MAC Attacker."*
- Khi đó, gói từ User đến Server và gói từ Server về User đều đi vào Attacker.

#### `scenario2.py` làm gì?

1. Phân giải MAC thật của User và Server.
2. Tạo hai frame ARP Reply giả:
   - Gửi cho User: IP Server (`10.11.1.20`) ứng với MAC Attacker.
   - Gửi cho Server: IP User (`10.11.1.10`) ứng với MAC Attacker.
3. Mỗi chu kỳ gửi cả hai frame, mặc định cách nhau 1 giây.
4. Với `--count 8`, có 8 chu kỳ, tức khoảng 16 ARP Reply.

#### Kết quả cần thấy

- Trên User: `10.11.1.20 at 02:42:0a:0b:01:33`.
- Trên Server: `10.11.1.10 at 02:42:0a:0b:01:33`.
- Trong pcap: chỉ có ARP (theo filter `arp`), thấy các cặp Reply giả.

#### Lưu ý về thời gian sống của bảng ARP

Entry ARP không tồn tại mãi. Sau một khoảng thời gian (thường vài chục giây), máy có thể xóa hoặc cập nhật lại entry. Vì vậy:

- Nếu chỉ poison 8 gói rồi dừng, sau một lúc bảng ARP có thể trở lại bình thường.
- Với MITM ở bước sau, cần chạy poison liên tục bằng `--count 0`.

#### Lỗi thường gặp

- **Chỉ một bảng ARP bị poison:** kiểm tra output của `scenario2.py` xem có phân giải được MAC của cả hai máy không; thử ping chéo trước khi poison.
- **Đã poison nhưng ping vẫn thông:** nếu `ip_forward=0` thì cả hai chiều sẽ mất; nếu `ip_forward=1` thì Attacker chuyển tiếp nên vẫn thông. Điều này không sai, nhưng cần hiểu rõ mục đích: KB2 chủ yếu chứng minh ARP hai chiều đã bị nhiễm.
- **Chạy xong nhưng bảng ARP đã hết hạn:** chạy lại poison hoặc dùng `--count 0` khi cần duy trì.

---

## Bước 4 (KB3) - MITM sửa nội dung

- **Mục đích:** chặn gói và thay payload `hello` thành `pwned` trước khi tới Server.
- **Lệnh:**
  ```bash
  # 1. Tắt forward để tránh kernel forward song song với script MITM
  docker exec attacker sysctl -w net.ipv4.ip_forward=0

  # 2. Poison liên tục hai chiều (chạy nền)
  docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 0 --interval 1"
  sleep 3

  # 3. Chạy MITM: nghe, chuyển tiếp và sửa payload
  docker exec -d attacker sh -c "python3 -u /attack/mitm.py > /tmp/mitm.log 2>&1"
  sleep 3

  # 4. Server lắng nghe trên cổng 10101
  docker exec -d server sh -c "timeout 25 nc -l 10101 > /tmp/recv.txt 2>&1"
  sleep 2

  # 5. User gửi dữ liệu có chứa chuỗi "hello"
  docker exec user sh -c "echo hello server from user | timeout 6 nc 10.11.1.20 10101"

  # 6. Đọc kết quả
  docker exec server cat /tmp/recv.txt
  docker exec attacker tail -2 /tmp/mitm.log
  ```
- **Kết quả:** Server nhận `pwned server from user`; log `[+] #1 ... 'hello' -> 'pwned'`.

### Giải thích chi tiết

#### Điều kiện để MITM hoạt động

1. Bảng ARP của cả User và Server đều đã bị poison (Bước 3).
2. Attacker phải **chuyển tiếp** gói tin, nếu không kết nối sẽ bị đứt.
3. Attacker phải nhìn thấy payload TCP để sửa, nên cần bắt frame ở lớp Ethernet (raw socket).
4. Chuỗi tìm và chuỗi thay phải **cùng độ dài**, ở đây `hello` và `pwned` đều dài 5 byte.

#### Từng lệnh có tác dụng gì?

- `sysctl -w net.ipv4.ip_forward=0`: tắt forward của kernel. `mitm.py` cũng tự đặt lại giá trị này, nhưng đặt trước cho chắc chắn.
  - Nếu để `ip_forward=1`, kernel có thể tự forward gói gốc song song với script, dẫn đến gói bị gửi trùng hoặc script khó kiểm soát.
- `scenario2.py --count 0 --interval 1`: poison liên tục, không giới hạn số lần. Cần thiết vì bảng ARP có thể tự hết hạn; nếu poison dừng, traffic sẽ quay lại đường trực tiếp và MITM không thấy gói.
- `mitm.py`: script tự chuyển tiếp thay cho kernel. Các bước chính:
  1. Mở raw socket trên `eth0`.
  2. Bỏ qua frame không phải IPv4 hoặc không thuộc cặp User-Server.
  3. Xác định MAC đích thật (User hoặc Server) rồi gửi lại frame.
  4. Với TCP, kiểm tra payload có chứa `hello` không; nếu có thì thay bằng `pwned`.
  5. Tính lại độ dài IP, checksum IP và checksum TCP.
  6. Gửi frame đã sửa cho phía nhận.
- `nc -l 10101`: Server mở cổng 10101 để nhận dữ liệu. `timeout 25` giúp tự kết thúc sau 25 giây, tránh treo.
- `echo ... | nc 10.11.1.20 10101`: User gửi chuỗi `hello server from user` đến Server.

#### Vì sao phải cùng độ dài?

TCP dùng số thứ tự (sequence number) để đảm bảo dữ liệu đến đúng thứ tự. Nếu ta thay một chuỗi dài 5 byte bằng một chuỗi dài 6 byte, phải sửa cả sequence number và cách xử lý các gói sau. Để đơn giản, script yêu cầu hai chuỗi dài bằng nhau; nếu không, script sẽ thoát và báo lỗi.

#### Cách đọc kết quả

- Trên Server, `/tmp/recv.txt` phải có dòng `pwned server from user` thay vì `hello server from user`.
- Trong `/tmp/mitm.log` phải có dòng tương tự:
  ```text
  [+] #1 10.11.1.10:xxxxx -> 10.11.1.20:10101  'hello' -> 'pwned'
  ```
- Nếu bắt pcap ở cả 3 máy, có thể so sánh:
  - User gửi: payload `hello...`
  - Attacker thấy và sửa: payload `pwned...`
  - Server nhận: payload `pwned...`

#### Lỗi thường gặp

- **`nc: Address already in use`:** cổng 10101 còn tiến trình `nc` cũ. Chạy `docker exec server pkill -x nc` rồi thử lại.
- **`Connection refused`:** Server chưa kịp mở cổng. Tăng thời gian `sleep` sau lệnh `nc -l` lên vài giây.
- **Không thấy log sửa payload:** kiểm tra chuỗi gửi có đúng `hello` không; kiểm tra poison còn hiệu lực không; bắt tcpdump trên Attacker để xem gói TCP có đi qua không.
- **Script báo chuỗi không cùng độ dài:** chọn cặp chuỗi khác có cùng số byte, ví dụ `hello` -> `pwned`.
- **Kết nối bị treo:** kiểm tra `mitm.py` còn chạy không; kiểm tra `ip_forward=0` và poison hai chiều còn hoạt động không.
- **Payload bị chia thành nhiều segment TCP:** script chỉ thay khi chuỗi `hello` nằm trọn trong một segment. Với dữ liệu nhỏ trong lab thì thường gặp, nhưng với dữ liệu lớn cần ghép TCP stream.

---

## Bước 5 (B5) - Phòng chống bằng ARP tĩnh

- **Mục đích:** chứng minh ARP entry `PERM` không bị Reply giả ghi đè.
- **Lệnh:**
  ```bash
  # 1. Xóa bảng ARP động
  docker exec user ip neigh flush all

  # 2. Gán cứng IP Server -> MAC thật của Server
  docker exec user arp -s 10.11.1.20 02:42:0a:0b:01:14
  docker exec user arp -n

  # 3. Attacker vẫn cố poison
  docker exec -d attacker sh -c "python3 -u /attack/scenario1.py --count 8 --interval 1"
  sleep 9
  docker exec attacker pkill -f scenario1

  # 4. Kiểm tra lại bảng ARP và ping
  docker exec user arp -n
  docker exec user ping -c 3 10.11.1.20

  # 5. Xóa entry tĩnh để trả lại trạng thái động
  docker exec user arp -d 10.11.1.20
  ```
- **Kết quả:** entry `10.11.1.20 at 02:42:0a:0b:01:14 [ether] PERM`; ping **0% packet loss**.

### Giải thích chi tiết

#### ARP tĩnh hoạt động như thế nào?

- Lệnh `arp -s <IP> <MAC>` tạo một entry **tĩnh** trong bảng ARP.
- Entry này có cờ `PERM` (permanent). Kernel ưu tiên dùng nó và **không cập nhật** từ các ARP Reply không yêu cầu.
- Vì vậy, dù Attacker gửi bao nhiêu ARP Reply giả, User vẫn dùng MAC thật của Server đã gán cứng.
- Kết quả: gói tin vẫn đi đúng đến Server, ping thành công.

#### Phải dùng đúng MAC nào?

Phải dùng MAC **thật của Server**: `02:42:0a:0b:01:14`.

- Nếu dùng MAC của Attacker (`02:42:0a:0b:01:33`), ta đang tự poison máy mình, ping sẽ hỏng.
- Nếu dùng sai MAC, gói tin đi sai đích và cũng mất kết nối.
- Có thể lấy lại MAC thật từ Bước 1 hoặc bằng `docker exec server cat /sys/class/net/eth0/address`.

#### Vì sao đây chỉ là giải pháp tạm?

- ARP tĩnh chỉ phù hợp với mạng nhỏ, số lượng máy ít.
- Khi đổi máy, đổi card mạng hoặc đổi IP, phải cập nhật thủ công.
- Không mở rộng được cho mạng lớn hoặc nhiều subnet.
- Các giải pháp phòng chống thực tế tốt hơn:
  - Dynamic ARP Inspection (DAI) trên switch.
  - DHCP Snooping.
  - Port Security.
  - 802.1X.
  - Giám sát ARP bằng `arpwatch`, IDS/IPS.
  - Dùng TLS/VPN để giảm thiệt hại khi bị MITM.

#### Lỗi thường gặp

- **`arp -s` báo lỗi:** entry đã tồn tại; chạy `ip neigh flush all` trước rồi thêm lại.
- **Ping vẫn hỏng sau khi gán tĩnh:** kiểm tra MAC đã dùng đúng chưa; kiểm tra IP; thử `arp -d` rồi làm lại.
- **Entry tĩnh biến mất sau khi restart container:** cấu hình ARP tĩnh không được lưu vĩnh viễn trong container; cần làm lại sau restart.
- **Dùng `ip neigh` thay vì `arp`:** có thể dùng lệnh tương đương:
  ```bash
  docker exec user ip neigh replace 10.11.1.20 lladdr 02:42:0a:0b:01:14 nud permanent
  ```

---

## Bước 6 - Thu thập bằng chứng và dọn dẹp

- **Mục đích:** lấy pcap/ảnh để nộp báo cáo, trả môi trường về trạng thái sạch.
- **Lệnh:**
  ```bash
  # 1. Dừng tcpdump nhẹ nhàng để ghi xong file pcap
  docker exec user pkill -INT tcpdump
  sleep 2

  # 2. Copy pcap từ container ra máy host
  docker cp user:/tmp/kb1.pcap ~/cap/demo_kb1.pcap
  docker cp attacker:/tmp/kb2.pcap ~/cap/demo_kb2.pcap

  # 3. Dọn tiến trình và bảng ARP
  for c in user server attacker; do
    docker exec $c pkill -x nc 2>/dev/null
    docker exec $c pkill -x tcpdump 2>/dev/null
    docker exec $c ip neigh flush all
  done
  docker exec attacker pkill -f mitm.py 2>/dev/null
  docker exec attacker sysctl -w net.ipv4.ip_forward=0
  ```
- **Kết quả:** có `demo_kb1.pcap`, `demo_kb2.pcap` (và `demo_kb3*.pcap` nếu bắt ở cả 3 container); bảng ARP sạch, không còn tiến trình poison/MITM.

### Giải thích chi tiết

#### Vì sao dùng `pkill -INT` thay vì `pkill -9`?

- `tcpdump` cần thời gian để ghi nốt dữ liệu còn trong buffer và đóng file pcap đúng cách.
- `SIGINT` (`-INT`) giống như nhấn `Ctrl+C`, cho phép tcpdump thoát êm.
- `SIGKILL` (`-9`) có thể làm file pcap bị thiếu dữ liệu hoặc hỏng phần cuối.
- Sau khi gửi `SIGINT`, chờ vài giây rồi mới `docker cp`.

#### Vì sao phải dọn bảng ARP và tiến trình?

- Bảng ARP bị poison còn sót lại sẽ ảnh hưởng các lần test sau, khiến kết quả không còn chính xác.
- Tiến trình `scenario1`, `scenario2`, `mitm.py`, `nc`, `tcpdump` còn chạy nền có thể tiếp tục gửi gói hoặc giữ cổng, gây lỗi khó hiểu.
- Đưa `ip_forward` về `0` giúp môi trường trở lại trạng thái an toàn, tránh vô tình biến Attacker thành router.

#### Kiểm tra sau khi dọn dẹp

Có thể kiểm tra nhanh:

```bash
# Không còn tiến trình tấn công/bắt gói
docker exec attacker pgrep -af 'scenario|mitm|tcpdump|nc'

# Bảng ARP đã sạch
docker exec user arp -n
docker exec server arp -n

# Forward đã tắt
docker exec attacker sysctl net.ipv4.ip_forward
```

Nếu còn tiến trình, kill lại theo tên tương ứng.

#### Giảm kích thước pcap để nộp bài

File pcap có thể rất lớn. Có thể lọc gọn bằng `tshark` hoặc `editcap`:

```bash
# Chỉ giữ ARP, ICMP và TCP cổng 10101
tshark -r in.pcap -Y "arp or icmp or tcp.port == 10101" -w out.pcap

# Hoặc giới hạn số gói mỗi file
editcap -c 3000 in.pcap out.pcap
```

---

## Bảng tóm tắt nhanh

| Bước | Việc chính | Dấu hiệu thành công |
|---|---|---|
| 0 | Dựng 3 container | `docker ps` thấy `user`, `server`, `attacker` đều `Up` |
| 1 | Xem IP/MAC/ARP ban đầu | Đúng IP, MAC theo quy luật Docker |
| 2 | Poison một chiều + tắt forward | User có `10.11.1.20 -> MAC Attacker`; ping mất 100% |
| 3 | Poison hai chiều | Cả User và Server đều trỏ IP còn lại về MAC Attacker |
| 4 | MITM sửa payload | Server nhận `pwned server from user`; log có `'hello' -> 'pwned'` |
| 5 | Gán ARP tĩnh | Entry `PERM`; ping thành công 0% loss |
| 6 | Thu pcap + dọn dẹp | Có file pcap; không còn tiến trình; ARP sạch |
