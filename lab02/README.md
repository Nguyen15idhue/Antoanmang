# Lab02 - ARP Cache Poisoning (bộ source tự dựng)

Bộ file này thay thế cho `~/it4263lab/lab02` do giảng viên cung cấp, dùng khi chưa nhận được source chính thức. Cấu trúc và tham số bám theo `Lab02_LAN_Attacks.pdf`.

## 1. Giả định tham số

| Tham số | Giá trị mặc định | Ý nghĩa |
|---|---|---|
| `x` | `11` | 2 số cuối mã lớp thực hành |
| `y` | `1` | số thứ tự nhóm |
| `SUBNET` | `10.11.1.0/24` | mạng Docker |
| User | `10.11.1.10` | nạn nhân |
| Server | `10.11.1.20` | máy đích |
| Attacker | `10.11.1.51` | máy tấn công |

Nếu giảng viên công bố `x`, `y` khác: sửa duy nhất file `.env`.

## 2. Cấu trúc

```
lab02/
  docker-compose.yml     3 container: user, server, attacker
  .env                   IP và subnet
  image/Dockerfile       ubuntu:20.04 + python3, net-tools, tcpdump, netcat, ping
  attack/arp.py          thư viện ARP (gửi/nhận frame thô)
  attack/scenario1.py    poison một chiều: nói với User rằng Server nằm ở MAC Attacker
  attack/scenario2.py    poison hai chiều: User và Server đều trỏ về Attacker
  attack/mitm.py         chuyển tiếp + sửa payload TCP (mặc định 'hello' -> 'pwned')
  bin/dockps, bin/docksh tiện ích như tài liệu
  aliases.sh             thêm bin/ vào PATH
```

## 3. Cách chạy

```bash
cd ~/it4263lab/lab02
source aliases.sh
docker-compose build
docker-compose up -d
dockps
```

Kiểm tra trong từng container:

```bash
docksh user
ifconfig
ping -c 3 10.11.1.20
arp -n
exit
```

Kịch bản:

```bash
# Kịch bản 1 - poison User
docksh attacker
cd /attack
python3 scenario1.py --victim 10.11.1.10 --spoof 10.11.1.20

# Kịch bản 2 - poison hai chiều
python3 scenario2.py

# Kịch bản 3 - MITM
python3 scenario2.py --count 0 &      # poison liên tục
python3 mitm.py --client 10.11.1.10 --server 10.11.1.20
```

## 4. Lưu ý kỹ thuật

- `scenario1.py`, `scenario2.py` và `mitm.py` phải chạy bằng root trong container (mặc định container chạy root).
- Container cần `NET_ADMIN` và `NET_RAW` (đã khai báo trong compose).
- `mitm.py` tự đặt `ip_forward=0` để tránh trường hợp kernel chuyển tiếp gói gốc song song với script (gây gửi trùng). Bước `sysctl net.ipv4.ip_forward=1` trong đề vẫn nên thực hiện trước để chứng minh kết nối thông, script sẽ ghi đè lại.
- `mitm.py` yêu cầu chuỗi tìm và chuỗi thay **cùng độ dài** để không phải xử lý lại độ dài gói tin.
- Trước mỗi kịch bản nên `docker restart user server attacker` để xoá ARP cache bị nhiễm.
- Bắt gói: trên host VM chọn card `br-...` (xem `ip -br link | grep br-`) hoặc `tcpdump -i eth0 -w` trong container rồi `docker cp`.
- File pcap nộp bài <= 1 MB: dùng `editcap -c 3000` hoặc `tshark -r in.pcap -Y "arp or tcp" -w out.pcap`.
