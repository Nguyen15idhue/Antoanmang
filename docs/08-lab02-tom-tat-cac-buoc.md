# Lab02 - Tóm tắt các bước thực hiện

Môi trường: 3 container Docker trên mạng `10.11.1.0/24` - User `10.11.1.10`, Server `10.11.1.20`, Attacker `10.11.1.51`.
Mỗi bước gồm: mục đích - lệnh - kết quả kỳ vọng.

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
- **Kết quả:** User `10.11.1.10 / 02:42:0a:0b:01:0a`, Server `10.11.1.20 / 02:42:0a:0b:01:14`, Attacker `10.11.1.51 / 02:42:0a:0b:01:33`; bảng ARP trống.

---

## Bước 2 (KB1) - Poison ARP một chiều tới User

- **Mục đích:** lừa User rằng IP Server nằm tại MAC Attacker, gây mất kết nối (DoS).
- **Lệnh:**
  ```bash
  for c in user server attacker; do docker exec $c ip neigh flush all; done
  docker exec user ping -c 1 10.11.1.20 >/dev/null
  docker exec server ping -c 1 10.11.1.10 >/dev/null
  docker exec -d user sh -c "tcpdump -U -i eth0 -n 'arp or icmp' -w /tmp/kb1.pcap"
  sleep 2
  docker exec -d attacker sh -c "python3 -u /attack/scenario1.py --count 8 --interval 1"
  sleep 9
  docker exec attacker pkill -f scenario1
  docker exec user arp -n
  docker exec user ping -c 3 10.11.1.20
  ```
- **Kết quả:** ARP của User `10.11.1.20 at 02:42:0a:0b:01:33`; ping **100% packet loss**.

---

## Bước 3 (KB2) - Poison ARP hai chiều

- **Mục đích:** lừa cả User và Server để toàn bộ lưu lượng đi qua Attacker (điều kiện MITM).
- **Lệnh:**
  ```bash
  for c in user server attacker; do docker exec $c ip neigh flush all; done
  docker exec user ping -c 1 10.11.1.20 >/dev/null
  docker exec server ping -c 1 10.11.1.10 >/dev/null
  docker exec -d attacker sh -c "tcpdump -U -i eth0 -n 'arp' -w /tmp/kb2.pcap"
  sleep 2
  docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 8 --interval 1"
  sleep 9
  docker exec attacker pkill -f scenario2
  docker exec user arp -n
  docker exec server arp -n
  ```
- **Kết quả:** cả hai bảng ARP đều trỏ `10.11.1.10` và `10.11.1.20` về MAC `02:42:0a:0b:01:33`; mỗi giây có một cặp ARP Reply.

---

## Bước 4 (KB3) - MITM sửa nội dung

- **Mục đích:** chặn gói và thay payload `hello` thành `pwned` trước khi tới Server.
- **Lệnh:**
  ```bash
  docker exec attacker sysctl -w net.ipv4.ip_forward=0
  docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 0 --interval 1"
  sleep 3
  docker exec -d attacker sh -c "python3 -u /attack/mitm.py > /tmp/mitm.log 2>&1"
  sleep 3
  docker exec -d server sh -c "timeout 25 nc -l 10101 > /tmp/recv.txt 2>&1"
  sleep 2
  docker exec user sh -c "echo hello server from user | timeout 6 nc 10.11.1.20 10101"
  docker exec server cat /tmp/recv.txt
  docker exec attacker tail -2 /tmp/mitm.log
  ```
- **Kết quả:** Server nhận `pwned server from user`; log `[+] #1 ... 'hello' -> 'pwned'`.

---

## Bước 5 (B5) - Phòng chống bằng ARP tĩnh

- **Mục đích:** chứng minh ARP entry `PERM` không bị Reply giả ghi đè.
- **Lệnh:**
  ```bash
  docker exec user ip neigh flush all
  docker exec user arp -s 10.11.1.20 02:42:0a:0b:01:14
  docker exec user arp -n
  docker exec -d attacker sh -c "python3 -u /attack/scenario1.py --count 8 --interval 1"
  sleep 9
  docker exec attacker pkill -f scenario1
  docker exec user arp -n
  docker exec user ping -c 3 10.11.1.20
  docker exec user arp -d 10.11.1.20
  ```
- **Kết quả:** entry `10.11.1.20 at 02:42:0a:0b:01:14 [ether] PERM`; ping **0% packet loss**.

---

## Bước 6 - Thu thập bằng chứng và dọn dẹp

- **Mục đích:** lấy pcap/ảnh để nộp báo cáo, trả môi trường về trạng thái sạch.
- **Lệnh:**
  ```bash
  docker exec user pkill -INT tcpdump; sleep 2
  docker cp user:/tmp/kb1.pcap ~/cap/demo_kb1.pcap
  docker cp attacker:/tmp/kb2.pcap ~/cap/demo_kb2.pcap

  for c in user server attacker; do
    docker exec $c pkill -x nc 2>/dev/null
    docker exec $c pkill -x tcpdump 2>/dev/null
    docker exec $c ip neigh flush all
  done
  docker exec attacker pkill -f mitm.py 2>/dev/null
  docker exec attacker sysctl -w net.ipv4.ip_forward=0
  ```
- **Kết quả:** có `demo_kb1.pcap`, `demo_kb2.pcap` (và `demo_kb3*.pcap` nếu bắt ở cả 3 container); bảng ARP sạch, không còn tiến trình poison/MITM.
