# 00 - Hiện trạng môi trường (kiểm tra ngày 2026-10-21)

Mục đích: ghi lại **bằng chứng thực tế** để biết cần sửa gì trước khi làm Lab01/Lab02.

## 1. Máy host

| Thành phần | Kết quả kiểm tra | Đánh giá |
|---|---|---|
| Hệ điều hành | Windows, PowerShell 5.1 | OK |
| Ổ đĩa làm việc | `F:` còn trống ~589 GB | Đủ chỗ |
| VirtualBox | 7.2.20 r175154 | OK |
| Docker Desktop | 29.1.3 (build f52814d), service `com.docker.service` = Stopped | Engine chưa chạy |
| Docker Compose | v2.40.3-desktop.1 | OK |
| WSL | `Ubuntu` (Stopped, v2), `docker-desktop` (Stopped, v2) | OK |
| nmap trên Windows | Không có | Phải dùng trong VM |
| Wireshark trên Windows | Không có | Phải dùng trong VM |

## 2. Máy ảo hiện có

Lệnh: `VBoxManage list vms`

```
"<inaccessible>" {4de6c562-0f31-40ff-bd7c-2b80a39598b7}
"<inaccessible>" {b45be1f1-0fb6-4a2c-8fd3-98e48f10d429}
"NguyenMachine"  {3356c55d-3ce8-4bb8-a63c-a1866c2b2677}
"Server3"        {e19d0ec3-1095-4c77-865c-a114fc1142b1}
```

| VM | Đĩa | Dung lượng | Trạng thái | Vai trò thực tế |
|---|---|---|---|---|
| `NguyenMachine` | `F:\2.VirtualMachine\1.VirtualBox\Attack\Attack.vdi` | 6.72 GB | `aborted` | Máy **Attack** của Lab01 |
| `Server3` | `F:\2.VirtualMachine\1.VirtualBox\Server\Ubuntu_DNS_Server-disk1.vdi` | 2.59 GB | `poweroff` | Máy **Server** của Lab01 |
| 2 VM `<inaccessible>` | không rõ | - | lỗi | Rác, nên unregister |

Thông số chung 2 VM: `ostype="Ubuntu (64-bit)"`, `memory=2048`, `nic1="hostonly"`, `hostonlyadapter1="VirtualBox Host-Only Ethernet Adapter"`.

Kết luận: **hạ tầng Lab01 đã có đủ**, không cần tải lại `.vdi` (file zip `Attack.zip` 2.22 GB và `Server.zip` 0.85 GB chỉ là bản nén dự phòng).

## 3. Mạng Host-only - điểm lệch quan trọng

Lệnh: `VBoxManage list hostonlyifs` và `VBoxManage list dhcpservers`

```
Name:      VirtualBox Host-Only Ethernet Adapter
IPAddress: 169.254.27.230
NetworkMask: 255.255.0.0
DHCP: Enabled

Dhcpd IP:       192.168.117.2
LowerIPAddress: 192.168.117.3
UpperIPAddress: 192.168.117.254
NetworkMask:    255.255.255.0
```

Vấn đề: DHCP server đã cấu hình cho `192.168.117.0/24` nhưng **card mạng host-only lại tự lấy IP APIPA `169.254.x.x`**. Hệ quả:

- Host Windows không ping được VM, VM có thể không nhận DHCP.
- nmap từ VM Attack quét `192.168.117.0/24` có thể không thấy Server.

Cách sửa (Giai đoạn A0):

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter" --ip 192.168.117.1 --netmask 255.255.255.0
```

Sau khi sửa, kiểm tra lại bằng `VBoxManage list hostonlyifs` (phải thấy `IPAddress: 192.168.117.1`, `NetworkMask: 255.255.255.0`).

## 4. Nguồn tài liệu hiện có

| File | Dùng cho |
|---|---|
| `Lab01_Huong_dan_thiet_lap_moi_truong.pdf` | Đã thực hiện; xem lại mục 2, 3 để biết IP đặt cho 2 VM |
| `Lab01_Huong_dan_TH.pdf` | Đề Lab01: mục 2 (luyện tập) và mục 3 (4 task trên lớp) |
| `Lab02_LAN_Attacks.pdf` | Đề Lab02: mục 4.1 -> 4.5 |
| `Lab02_BC.pdf` | Mẫu báo cáo Lab02 (10 điểm) |

**Thiếu so với yêu cầu Lab02:**

- `~/it4263lab/lab02/docker-compose.yml`
- `~/it4263lab/lab02/attack/scenario1.py`, `scenario2.py`, `mitm.py`
- Tiện ích `dockps`, `docksh`
- VM Ubuntu 20.04 (đề ghi: máy ảo cấp tại phòng thực hành)

Đã tìm trong `F:\3.Laptrinh\2.Learning\Antoanmang`, `Downloads`, `Desktop`: chỉ có 4 PDF, không có source.

## 5. Khoảng trống so với yêu cầu từng lab

| Yêu cầu | Lab01 | Lab02 |
|---|---|---|
| Hệ điều hành | Ubuntu 12.04 (Attack/Server VM) | Ubuntu 20.04 + Docker |
| Công cụ | nmap, Wireshark | Docker, docker-compose, Wireshark, Python3, tcpdump, netcat |
| Mạng | `192.168.117.0/24`, Attack `.10`, Server `.13` | subnet Docker theo `x` (2 số cuối mã lớp) và `y` (số nhóm) |
| Source | không cần | **bắt buộc có** |
| Trạng thái | Làm được ngay sau khi sửa IP host-only | **Bị chặn** |

## 6. Rủi ro đã xác định

1. VM `NguyenMachine` ở trạng thái `aborted` (crash) - lần đầu nên chọn **Start -> Normal Start**, không resume saved state.
2. Ubuntu 12.04 đã hết hỗ trợ: `apt-get update` sẽ lỗi 404. Không cài thêm gói trừ khi đổi `sources.list` sang `old-releases.ubuntu.com`.
3. Nếu dùng Docker Desktop trên Windows thay vì VM phòng lab: interface `br-...` nằm trong WSL2, Wireshark trên Windows không bắt được -> phải dùng `tcpdump` trong container. Đây là phương án dự phòng, không phải phương án chính.
4. Lab02 không thể bắt đầu khi chưa có `docker-compose.yml` của giảng viên (IP, tên container, interface phụ thuộc file này).

## 7. Cập nhật sau khi thực hiện (2026-10-21)

Đã sửa và kiểm chứng:

| Việc | Kết quả |
|---|---|
| Host-only adapter | `192.168.117.1/24`, `Status: Up` |
| VM rác | Đã unregister 2 VM `<inaccessible>` |
| Attack (`NguyenMachine`) | Boot OK, SSH OK, IP `192.168.117.10` trên card **`eth14`** (không phải `eth0`) |
| Server (`Server3`) | Boot OK, SSH OK, IP `192.168.117.13` trên `enp0s3`; thực tế **Ubuntu 16.04.2 LTS** |
| Autologin GUI Attack | Bật qua `/etc/lightdm/lightdm.conf` (drop-in không có tác dụng trên 12.04) |
| Chụp ảnh màn hình Attack | `gnome-screenshot -d 1` lưu vào `~/Pictures/Screenshot from <time>.png` (không hỗ trợ `-f/--file`) |
| VM Ubuntu 20.04 | Tạo `Ubuntu2004` (4 GB RAM, 2 CPU, 40 GB, NAT + host-only), cài tự động bằng `VBoxManage unattended install` |

Công cụ trong từng VM:

| Công cụ | Attack (12.04) | Server (16.04) |
|---|---|---|
| nmap | `/usr/bin/nmap` (5.21) | Không |
| Wireshark GUI | Có | Không |
| tcpdump | `/usr/sbin/tcpdump` | Có (dùng được với sudo) |
| python | `python2` | `python3` |
| sshd | Có (`/usr/sbin/sshd`) | Có |
| bind9 / telnetd | - | Có (53, 23) |

Kết nối điều khiển: dùng `plink.exe` (PuTTY 0.81) với `-hostkey` cố định; `sudo` cần mật khẩu `bkcs` qua `sudo -S`.
