import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "evidence", "screenshots")
OUT = os.path.join(BASE, "report", "NhomX_Lab02_BaoCao.docx")

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(13)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.3


def para(text="", bold=False, italic=False, size=13, align=None, space_after=6):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        r.font.size = Pt(13)
    r = p.add_run(text)
    r.font.size = Pt(13)
    p.paragraph_format.space_after = Pt(3)
    return p


def h1(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(15)
    r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x73)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    return p


def h2(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(13.5)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    return p


def table(rows, header=True, widths=None):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ""
            p = cells[j].paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(12)
            r.bold = bool(header and i == 0)
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, caption, width=6.2):
    path = os.path.join(IMG, name)
    if not os.path.exists(path):
        para("[Thiếu ảnh: %s]" % name, italic=True)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = c.add_run(caption)
    r.italic = True
    r.font.size = Pt(11)


# ---------------- Trang bìa ----------------
para("TRƯỜNG ĐẠI HỌC BÁCH KHOA HÀ NỘI", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
para("BÁO CÁO BÀI THỰC HÀNH SỐ 2", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=20, space_after=2)
para("PHÂN TÍCH MỘT SỐ KỸ THUẬT TẤN CÔNG TRONG MẠNG LAN",
     bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=15, space_after=18)
para("Môn học: An toàn mạng máy tính", align=WD_ALIGN_PARAGRAPH.CENTER)
para("Sinh viên 1: Phạm Quỳnh Chi - 223001699", align=WD_ALIGN_PARAGRAPH.CENTER)
para("Sinh viên 2: ................................................ - ................",
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
para("Yêu cầu kết quả thực hành: nộp tệp NhomX_Lab02_BaoCao.zip gồm báo cáo và 03 tệp pcap "
     "(task1_full.pcap, task2_full.pcap, task3.pcap), mỗi tệp không quá 1 MB.",
     italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_page_break()

# ---------------- Mở đầu ----------------
h1("1. Môi trường thực hành và thông số container")
para("Bài thực hành được triển khai trên một máy ảo Ubuntu 20.04 (VirtualBox), bên trong chạy Docker "
     "và Docker Compose. Mạng thực hành gồm 03 container (không phải máy ảo) nối vào cùng một bridge "
     "10.11.1.0/24, tương ứng với quy ước 10.x.y.0/24 của đề bài với x = 11, y = 1 "
     "(đề in 192.168.100.0/24 nhưng môi trường thực tế dùng dải 10.x.y.0/24 theo docker-compose).")
para("Ba container dùng chung image lab02-node (Ubuntu 20.04 tối giản, có sẵn python3, tcpdump, "
     "netcat, net-tools):")
table([
    ["Container", "Vai trò", "Địa chỉ IP", "Địa chỉ MAC (eth0)"],
    ["user", "Máy người dùng", "10.11.1.10", "02:42:0a:0b:01:0a"],
    ["server", "Máy chủ dịch vụ", "10.11.1.20", "02:42:0a:0b:01:14"],
    ["attacker", "Máy tấn công", "10.11.1.51", "02:42:0a:0b:01:33"],
], widths=[1.2, 1.7, 1.6, 1.9])
para("Các byte cuối của MAC là biểu diễn hex của 4 byte cuối địa chỉ IP (10.11.1.10 -> 0a:0b:01:0a; "
     "10.11.1.20 -> 0a:0b:01:14; 10.11.1.51 -> 0a:0b:01:33), đúng với địa chỉ do Docker gán, "
     "giúp đối chiếu nhanh khi phân tích ARP.")
figure("L02-B1-docker-compose-up.png", "Hình 1. Kết quả docker-compose up -d: 3 container ở trạng thái Up")
h2("1.1. Thông số máy User")
table([["Thuộc tính", "Giá trị"],
       ["IP", "10.11.1.10/24"],
       ["MAC", "02:42:0a:0b:01:0a"],
       ["Bảng ARP trước tấn công", "(trống - chỉ có địa chỉ quảng bá)"],
       ["Bảng ARP sau tấn công KB1", "10.11.1.20 -> 02:42:0a:0b:01:33 (MAC Attacker)"],
       ], widths=[2.2, 4.2])
figure("L02-B1-user.png", "Hình 2. Thông số IP/MAC của máy User", width=5.6)
h2("1.2. Thông số máy Server")
table([["Thuộc tính", "Giá trị"],
       ["IP", "10.11.1.20/24"],
       ["MAC", "02:42:0a:0b:01:14"],
       ["Bảng ARP trước tấn công", "(trống - chỉ có địa chỉ quảng bá)"],
       ["Bảng ARP sau tấn công KB2", "10.11.1.10 -> 02:42:0a:0b:01:33 (MAC Attacker)"],
       ], widths=[2.2, 4.2])
figure("L02-B1-server.png", "Hình 3. Thông số IP/MAC của máy Server", width=5.6)
h2("1.3. Thông số máy Attacker")
table([["Thuộc tính", "Giá trị"],
       ["IP", "10.11.1.51/24"],
       ["MAC", "02:42:0a:0b:01:33"],
       ], widths=[2.2, 4.2])
figure("L02-B1-attacker.png", "Hình 4. Thông số IP/MAC của máy Attacker", width=5.6)

# ---------------- KB1 ----------------
h1("2. Kịch bản 1 - ARP Cache Poisoning một chiều tới User")
para("Máy Attacker gửi liên tục các ARP Reply giả mạo cho User, khai báo rằng địa chỉ IP của Server "
     "(10.11.1.20) đang gắn với MAC của Attacker (02:42:0a:0b:01:33). Toàn bộ gói tin của User "
     "gửi tới Server sau đó được chuyển tới cổng mạng của Attacker.")
h2("2.1. Gói tin ARP poison")
para("Tệp task1_full.pcap ghi lại trên máy User. Gói poison đầu tiên là gói số 7; các gói 7, 8, 9, 10, 11... "
     "là các ARP Reply lặp lại mỗi giây. Gói số 2 là ARP Reply hợp lệ trước khi tấn công "
     "(10.11.1.20 is-at 02:42:0a:0b:01:14).")
table([["Trường", "Giá trị gói số 7"],
       ["Ethernet - Source", "02:42:0a:0b:01:33 (MAC Attacker)"],
       ["Ethernet - Destination", "02:42:0a:0b:01:0a (MAC User)"],
       ["Loại ARP", "Reply (gratuitous, không có Request tương ứng)"],
       ["Sender MAC address", "02:42:0a:0b:01:33 (MAC Attacker)"],
       ["Sender IP address", "10.11.1.20 (IP Server - bị giả mạo)"],
       ["Target MAC address", "02:42:0a:0b:01:0a (MAC User)"],
       ["Target IP address", "10.11.1.10 (IP User)"],
       ], widths=[2.1, 4.3])
para("Đặc điểm bất thường: cặp IP - MAC không khớp. Trong mạng, 10.11.1.20 phải đi với "
     "02:42:0a:0b:01:14, nhưng gói tin lại khai báo 10.11.1.20 đi với MAC của Attacker. Wireshark "
     "còn đưa ra cảnh báo \"Duplicate IP address detected for 10.11.1.20\" vì cùng một IP xuất hiện "
     "với hai MAC khác nhau trong cùng một đoạn bắt gói.")
figure("L02-B2-kb1-wireshark.png", "Hình 5. Gói ARP Reply giả mạo số 7 và cảnh báo trùng địa chỉ IP")
h2("2.2. Máy bị tấn công và hậu quả")
para("Máy bị tấn công là User. Bảng ARP của User bị ghi đè: 10.11.1.20 -> 02:42:0a:0b:01:33. "
     "Máy Server không bị ảnh hưởng trong kịch bản này (bảng ARP của Server vẫn giữ MAC thật của User). "
     "Hậu quả: mọi lưu lượng User gửi tới Server đều đi qua Attacker, cho phép nghe lén, sửa hoặc chặn. "
     "Trong bài thực hành, Attacker để ip_forward = 0 nên gói tin bị bỏ, kết quả ping từ User tới Server "
     "mất 100% gói.")
figure("L02-B2-kb1-arp-user.png", "Hình 6. Bảng ARP của User sau khi bị poison (10.11.1.20 trỏ về MAC Attacker)", width=5.6)
figure("L02-B2-kb1-arp-server.png", "Hình 7. Bảng ARP của Server vẫn bình thường (MAC thật của User)", width=5.6)

# ---------------- KB2 ----------------
h1("3. Kịch bản 2 - ARP Cache Poisoning hai chiều (User và Server)")
para("Attacker gửi đồng thời hai luồng ARP Reply giả: tới User khai báo IP Server gắn với MAC Attacker, "
     "và tới Server khai báo IP User gắn với MAC Attacker. Nhờ vậy cả hai chiều của kết nối đều đi qua "
     "Attacker.")
h2("3.1. Gói tin ARP poison")
para("Tệp task2_full.pcap: gói số 5 là ARP Reply gửi tới User, gói số 6 là ARP Reply gửi tới Server. "
     "Các cặp gói 5/6, 7/8, 9/10... được lặp lại mỗi giây. Cả hai đều là ARP Reply với MAC nguồn là "
     "MAC của Attacker, chứa IP nguồn bị giả mạo.")
table([["Gói", "Ethernet Source", "Ethernet Destination", "Sender IP (giả)", "Target IP"],
       ["5", "02:42:0a:0b:01:33", "02:42:0a:0b:01:0a", "10.11.1.20", "10.11.1.10"],
       ["6", "02:42:0a:0b:01:33", "02:42:0a:0b:01:14", "10.11.1.10", "10.11.1.20"],
       ], widths=[0.6, 1.7, 1.7, 1.4, 1.4])
para("Đặc điểm bất thường: cả hai máy đều nhận được thông tin sai lệch. Wireshark hiển thị "
     "các gói ARP Reply xen kẽ hai chiều, cùng cảnh báo trùng IP, chứng tỏ Attacker chủ động gửi "
     "cho cả hai phía chứ không phải lưu lượng ARP bình thường.")
figure("L02-B3-kb2-wireshark.png", "Hình 8. Các cặp ARP Reply giả mạo hai chiều trong task2_full.pcap")
h2("3.2. Máy bị tấn công và hậu quả")
para("Cả User và Server đều bị poison. Bảng ARP của User trỏ 10.11.1.20 về 02:42:0a:0b:01:33; "
     "bảng ARP của Server trỏ 10.11.1.10 về 02:42:0a:0b:01:33. Kết quả là toàn bộ luồng hai chiều "
     "User - Server đi qua Attacker. Với ip_forward = 0, ping giữa hai máy mất 100% gói.")
figure("L02-B3-kb2-arp-user.png", "Hình 9. Bảng ARP của User bị poison", width=5.6)
figure("L02-B3-kb2-arp-server.png", "Hình 10. Bảng ARP của Server bị poison", width=5.6)

# ---------------- KB3 ----------------
h1("4. Kịch bản 3 - Tấn công Man-in-the-Middle, sửa nội dung")
para("Trên nền ARP poisoning hai chiều, Attacker bật chương trình mitm.py để chuyển tiếp gói tin "
     "giữa User và Server, đồng thời thay chuỗi \"hello\" bằng \"pwned\" trong payload TCP. "
     "Kịch bản sử dụng netcat: Server lắng nghe cổng 10101, User gửi dòng \"hello server from user\".")
h2("4.1. Gói tin ARP poison")
para("Tệp task3.pcap bắt tại máy Attacker: gói số 1 và 2 là cặp ARP Reply giả mạo đầu tiên "
     "(1: tới User, 2: tới Server); các cặp tiếp theo lặp lại mỗi giây. MAC nguồn luôn là MAC Attacker, "
     "IP nguồn là IP của máy bị giả mạo.")
figure("L02-B4-kb3-wireshark-arp.png", "Hình 11. ARP Reply giả mạo hai chiều trong task3.pcap")
h2("4.2. Hậu quả trên nạn nhân")
para("Bảng ARP của User và Server đều trỏ về MAC Attacker, do đó luồng netcat đi qua Attacker. "
     "Attacker đặt net.ipv4.ip_forward = 0 và tự chuyển tiếp ở mức Ethernet/IP trong mitm.py.")
figure("L02-B4-kb3-arp-user.png", "Hình 12. Bảng ARP của User trong lúc tấn công", width=5.6)
figure("L02-B4-kb3-arp-server.png", "Hình 13. Bảng ARP của Server trong lúc tấn công", width=5.6)
h2("4.3. So sánh thông điệp trước và sau khi qua Attacker")
para("Trước tấn công, Server nhận đúng chuỗi User gửi. Sau khi poison, nội dung đến Server đã bị đổi "
     "từ hello thành pwned, trong khi phía User vẫn hiển thị chuỗi gốc và không hề biết.")
figure("L02-B4-kb3-user-gui-truoc.png", "Hình 14. User gửi \"hello server from user\" (trước tấn công)", width=5.6)
figure("L02-B4-kb3-server-nhan-truoc.png", "Hình 15. Server nhận đúng chuỗi gốc (trước tấn công)", width=5.6)
figure("L02-B4-kb3-user-gui-sau.png", "Hình 16. User vẫn gửi chuỗi gốc (sau tấn công)", width=5.6)
figure("L02-B4-kb3-server-nhan-sau.png", "Hình 17. Server nhận \"pwned server from user\" (sau tấn công)", width=5.6)
para("Trong tệp task3.pcap, gói số 21 là dữ liệu User gửi đi với payload hex "
     "68656c6c6f207365727665722066726f6d20757365720a (hello server from user). "
     "Gói số 22 do Attacker chuyển tiếp tới Server có payload "
     "70776e6564207365727665722066726f6d20757365720a (pwned server from user). "
     "Hai chuỗi có cùng độ dài nên kích thước gói và số thứ tự TCP không đổi, chỉ 5 byte đầu bị thay.")
h2("4.4. Giải thích cơ chế")
bullet("Attacker nhận frame trên eth0 bằng raw socket AF_PACKET, lọc các gói IPv4 có cặp IP User - Server.", "Bắt gói: ")
bullet("Đổi MAC đích thành MAC của phía nhận (User hoặc Server), MAC nguồn thành MAC Attacker, rồi gửi lại ra eth0.", "Chuyển tiếp: ")
bullet("Nếu payload chứa \"hello\", thay bằng \"pwned\" (cùng độ dài), sau đó tính lại checksum IP và checksum TCP.", "Sửa nội dung: ")
bullet("Bắt buộc phải tính lại checksum vì frame đọc từ card mạng có thể mang checksum chưa hoàn thiện do cơ chế "
       "checksum offload của veth; nếu gửi nguyên trạng, Server sẽ loại gói do sai checksum (quan sát qua "
       "Tcp InCsumErrors tăng và không có SYN-ACK).", "Vì sao phải tính lại checksum: ")
bullet("Cả hai máy không phát hiện vì ARP không có xác thực và TCP/IP không kiểm tra tính toàn vẹn nguồn gốc. "
       "Chỉ khi có công cụ như Wireshark bắt tại Attacker mới thấy hai phiên bản payload.", "Vì sao nạn nhân không biết: ")

# ---------------- Phòng chống ----------------
h1("5. Phòng chống tấn công ARP poisoning bằng ARP tĩnh")
para("Trên máy User, khai báo cố định ánh xạ IP - MAC của Server bằng lệnh:")
p = doc.add_paragraph()
r = p.add_run("sudo arp -s 10.11.1.20 02:42:0a:0b:01:14")
r.font.name = "Consolas"
r.font.size = Pt(12)
p.paragraph_format.left_indent = Inches(0.4)
para("Trong container bài thực hành đang đăng nhập bằng root nên có thể bỏ sudo: "
     "arp -s 10.11.1.20 02:42:0a:0b:01:14.")
figure("L02-B5-lenh-arp-s.png", "Hình 18. Đặt ánh xạ ARP tĩnh cho cặp IP - MAC của Server", width=5.8)
para("Sau khi đặt, bảng ARP của User hiển thị cờ M (permanent) cho entry 10.11.1.20. "
     "Chạy lại kịch bản poison một chiều (scenario1.py, 8 gói), entry này không bị ghi đè: ARP Reply giả "
     "bị bỏ qua vì kernel giữ nguyên ánh xạ tĩnh.")
figure("L02-B5-arp-n-co-M.png", "Hình 19. Bảng ARP có cờ M (permanent) sau khi bị poison lại", width=5.8)
para("Kết quả: ping từ User tới Server vẫn đạt 0% mất gói, chứng minh lưu lượng không bị chuyển hướng "
     "sang Attacker. Hình dưới đồng thời cho thấy phía Server (bên phải) đã bị poison và nhận dữ liệu "
     "bị sửa, còn phía User (bên trái) giữ nguyên ARP tĩnh và vẫn kết nối trực tiếp.")
figure("L02-B5-ket-qua-tan-cong-lai.png", "Hình 20. Sau khi poison lại: ARP tĩnh vẫn giữ MAC thật, ping 0% mất gói", width=6.3)
para("Hạn chế: ARP tĩnh chỉ bảo vệ đúng cặp IP - MAC đã khai báo, phải khai báo thủ công trên từng máy, "
     "không mở rộng được cho mạng lớn và không chống được DHCP spoofing hay DNS spoofing. Trong thực tế "
     "cần kết hợp DHCP Snooping, Dynamic ARP Inspection trên switch và giám sát ARP bất thường.")

# ---------------- Kết luận ----------------
h1("6. Kết luận và danh mục tệp nộp")
para("Bài thực hành đã tái hiện đầy đủ ba kịch bản: poison một chiều (User), poison hai chiều "
     "(User và Server) và MITM sửa nội dung bằng netcat. Kết quả cho thấy ARP không có cơ chế xác thực nên "
     "kẻ tấn công trong cùng miền quảng bá có thể chiếm luồng giao thông một cách dễ dàng; biện pháp ARP tĩnh "
     "chỉ là giải pháp tình thế, cần các cơ chế phòng chống ở tầng switch.")
table([["Tệp", "Kích thước", "Nội dung"],
       ["task1_full.pcap", "2.7 KB", "ARP poison một chiều tới User (KB1)"],
       ["task2_full.pcap", "2.7 KB", "ARP poison hai chiều (KB2)"],
       ["task3.pcap", "2.1 KB", "ARP poison + MITM sửa payload (KB3)"],
       ["task3_user.pcap", "1.1 KB", "Phía User: payload gốc hello"],
       ["task3_server.pcap", "1.1 KB", "Phía Server: payload đã sửa pwned"],
       ], widths=[1.8, 1.1, 3.5])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.save(OUT)
print("Saved", OUT)
