# 04 - Xử lý sự cố thường gặp

Mỗi mục: triệu chứng -> nguyên nhân -> cách xử lý -> cách xác nhận.

## 1. Host-only adapter sai IP (ảnh hưởng Lab01)

Triệu chứng: `VBoxManage list hostonlyifs` trả `169.254.x.x/16`; Windows ping VM không được; VM không nhận DHCP `192.168.117.x`.

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter" --ip 192.168.117.1 --netmask 255.255.255.0
```

Xác nhận: `VBoxManage list hostonlyifs` thấy `IPAddress: 192.168.117.1`. Trong VM: `ip route` phải có `192.168.117.0/24 dev ethX`.

## 2. VM ở trạng thái `aborted`

Nguyên nhân: VM bị crash/tắt đột ngột, còn saved state cũ.

Cách xử lý: mở VirtualBox -> Start -> **Normal Start** (không chọn "Discard" nếu cần giữ dữ liệu; nếu VM không boot được thì mới Discard saved state).

Xác nhận: `VBoxManage showvminfo "NguyenMachine" --machinereadable | Select-String VMState` -> `running`.

## 3. `ifconfig` không có trong Ubuntu

```bash
sudo apt install -y net-tools
```

Hoặc dùng `ip -br addr` / `ip neigh` thay thế.

## 4. Ping giữa 2 VM không thông

Kiểm tra theo thứ tự:

```bash
ip -br addr          # IP đúng dải 192.168.117.x?
ip route             # có route 192.168.117.0/24?
sudo ufw status      # firewall có chặn không
sudo ufw allow from 192.168.117.0/24
```

Nếu VM nhận IP `10.0.2.x` (NAT) thay vì `192.168.117.x`: card mạng đang gắn sai chế độ, sửa Settings -> Network -> Adapter 1 = **Host-only Adapter**.

## 5. Ubuntu 12.04 - `apt-get update` lỗi 404

Nguyên nhân: repo đã chuyển sang kho lưu trữ.

```bash
sudo sed -i 's|http://archive.ubuntu.com|http://old-releases.ubuntu.com|g; s|http://security.ubuntu.com|http://old-releases.ubuntu.com|g' /etc/apt/sources.list
sudo apt-get update
```

Ưu tiên dùng công cụ có sẵn trong VM Attack (nmap, Wireshark thường đã cài) để tránh phải cài thêm.

## 6. Wireshark không bắt được gói / không có quyền

Triệu chứng: mở Wireshark không thấy interface hoặc báo "permission denied".

```bash
sudo dpkg-reconfigure wireshark-common     # chọn Yes
sudo usermod -aG wireshark $USER
newgrp wireshark
```

Hoặc tạm thời: `sudo wireshark`.

## 7. Không thấy card `br-...` của Docker

Trên host VM:

```bash
ip -br link | grep br-
docker network ls
```

Nếu vẫn không thấy: mạng docker chưa được tạo (chưa `docker-compose up`), hoặc đang dùng Docker Desktop trên Windows (card nằm trong WSL2).

Cách bắt thay thế (đúng theo tài liệu Lab02):

```bash
# trong container
tcpdump -i eth0 -n -w /tmp/cap.pcap
# copy ra host
docker cp <container_id>:/tmp/cap.pcap ./cap.pcap
```

## 8. `arp -n` trống hoặc thiếu entry

Nguyên nhân: chưa có lưu lượng tới máy kia nên ARP chưa resolve.

```bash
ping -c 3 <IP_máy_kia>
arp -n
# hoặc
ip neigh show
```

Muốn xoá cache để làm lại:

```bash
sudo ip neigh flush all
```

## 9. Chạy script poison nhưng bảng ARP không đổi

Kiểm tra:

1. Chạy bằng quyền root trong container: `whoami` phải là `root`.
2. Container có capability `NET_ADMIN`:
   ```bash
   grep CapEff /proc/self/status
   capsh --decode=$(grep CapEff /proc/self/status | awk '{print $2}')
   ```
   Nếu thiếu: compose phải có
   ```yaml
   cap_add:
     - NET_ADMIN
   ```
3. Tên interface trong script phải đúng (`eth0`), IP/MAC trong script phải khớp `ifconfig`.
4. Đúng mạng: script phải chạy trong container Attacker, không phải trên host.

Xác nhận: `arp -n` trên nạn nhân đổi MAC sang MAC Attacker.

## 10. Poison xong nhưng ping vẫn thông (dễ hiểu sai)

Nguyên nhân: `net.ipv4.ip_forward = 1` trong container Attacker -> Attacker forward gói tiếp, nên kết nối không đứt.

Đây là hành vi **đúng của MITM** (KB3 cần). Với KB1/KB2, nếu muốn thấy hậu quả rõ:

```bash
sysctl net.ipv4.ip_forward=0
# hoặc
sudo iptables -P FORWARD DROP
```

Lưu ý kỹ thuật (để không viết sai vào báo cáo): `ip_forward` là sysctl theo **network namespace**. Giá trị trên Docker host **không** tự truyền vào container; nếu trong container = 1 thì do image/compose/script bật. ICMP Redirect không phải nguyên nhân làm gói tin tới đích.

## 11. KB3 mất kết nối sau khi poison

Thiếu bước bật forwarding. Trên Attacker:

```bash
sysctl -w net.ipv4.ip_forward=1
sysctl net.ipv4.ip_forward       # xác nhận = 1
```

Sau đó mới chạy `mitm.py`, và kiểm tra `nc` ở User vẫn gửi được.

## 12. File pcap vượt 1 MB

```bash
ls -lh task1.pcap
editcap -c 3000 task1.pcap task1_small.pcap
# hoặc chỉ giữ ARP + TCP
tshark -r task1.pcap -Y "arp or tcp" -w task1_small.pcap
```

Kiểm tra lại bằng Wireshark: file vẫn phải chứa gói poison + phiên `nc` cần phân tích.

## 13. `docker cp` báo không tìm thấy container

Container ID đổi sau khi restart:

```bash
docker ps --format "{{.ID}}  {{.Names}}"
docker cp <ID_mới>:/tmp/cap.pcap ./cap.pcap
```

## 14. `dockps` / `docksh` không tồn tại

Đây là alias do bộ lab cung cấp (thường trong `~/.bashrc` hoặc file env). Nếu chưa có:

```bash
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
docker exec -it <ID> bash
```

## 15. Đóng gói sai

Triệu chứng: zip không đúng tên, thiếu pcap, pcap > 1 MB.

```bash
unzip -l NhomX_Lab02_BaoCao.zip
ls -lh *.pcap
```

Quy tắc: tên `NhomX_Lab02_BaoCao.zip`, bên trong có báo cáo (PDF/DOCX) + `task1.pcap`, `task2.pcap`, `task3.pcap`.
