#!/usr/bin/env python3
"""Tao DNS Query tho (IP + UDP + DNS) cho Lab03."""
import os
import random
import socket
import struct


def checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


def encode_name(name: str) -> bytes:
    out = b""
    for label in name.rstrip(".").split("."):
        out += bytes([len(label)]) + label.encode()
    return out + b"\x00"


def main() -> None:
    src_ip = os.environ.get("SRC_IP", "10.11.1.30")
    dst_ip = os.environ.get("DST_IP", "10.11.1.20")
    src_port = int(os.environ.get("SRC_PORT", "12345"))
    dst_port = int(os.environ.get("DST_PORT", "53"))
    qname = os.environ.get("QNAME", "abcxyz.example.com")

    dns_id = random.randint(0, 0xFFFF)
    dns = struct.pack("!HHHHHH", dns_id, 0x0100, 1, 0, 0, 0)
    dns += encode_name(qname) + struct.pack("!HH", 1, 1)  # A, IN

    udp = struct.pack("!HHHH", src_port, dst_port, 8 + len(dns), 0)
    ip = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0, 20 + len(udp), random.randint(0, 0xFFFF), 0, 64, 17, 0,
        socket.inet_aton(src_ip), socket.inet_aton(dst_ip),
    )
    ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
    packet = ip + udp + dns
    with open("ip_req.bin", "wb") as f:
        f.write(packet)

    print("src=%s:%d dst=%s:%d qname=%s dns_id=%d len=%d" % (
        src_ip, src_port, dst_ip, dst_port, qname, dns_id, len(packet)))


if __name__ == "__main__":
    main()
