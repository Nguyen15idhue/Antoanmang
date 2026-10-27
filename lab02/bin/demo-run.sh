#!/bin/bash
set -u
cd "$(dirname "$0")/.." || exit 1
OUT=${1:-/home/bkcs/cap}
mkdir -p "$OUT"

say() { printf '\n=== %s ===\n' "$*"; }

say "B1 - thong so container"
docker-compose up -d >/dev/null 2>&1
docker exec attacker sysctl -w net.ipv4.ip_forward=0 >/dev/null 2>&1
sleep 2
for c in user server attacker; do
  echo "[$c]"
  docker exec $c sh -c 'ip -br a | grep eth0; cat /sys/class/net/eth0/address; arp -n'
done

say "KB1 - poison mot chieu (User)"
for c in user server attacker; do docker exec $c ip neigh flush all; done
docker exec user ping -c 1 10.11.1.20 >/dev/null 2>&1
docker exec server ping -c 1 10.11.1.10 >/dev/null 2>&1
docker exec user pkill -x tcpdump 2>/dev/null
docker exec -d user sh -c "tcpdump -U -i eth0 -n 'arp or icmp' -w /tmp/kb1.pcap"
sleep 2
docker exec -d attacker sh -c "python3 -u /attack/scenario1.py --count 8 --interval 1 > /tmp/kb1.log 2>&1"
sleep 9
docker exec attacker pkill -f scenario1 2>/dev/null
echo "[arp user]"
docker exec user arp -n
echo "[ping user -> server, ip_forward=0 nen mat goi]"
docker exec user ping -c 3 10.11.1.20 || true
docker exec user pkill -INT tcpdump 2>/dev/null
sleep 2
docker cp user:/tmp/kb1.pcap "$OUT/demo_kb1.pcap"

say "KB2 - poison hai chieu (User + Server)"
for c in user server attacker; do docker exec $c ip neigh flush all; done
docker exec user ping -c 1 10.11.1.20 >/dev/null 2>&1
docker exec server ping -c 1 10.11.1.10 >/dev/null 2>&1
docker exec attacker pkill -x tcpdump 2>/dev/null
docker exec -d attacker sh -c "tcpdump -U -i eth0 -n 'arp' -w /tmp/kb2.pcap"
sleep 2
docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 8 --interval 1 > /tmp/kb2.log 2>&1"
sleep 9
docker exec attacker pkill -f scenario2 2>/dev/null
echo "[arp user]"
docker exec user arp -n
echo "[arp server]"
docker exec server arp -n
docker exec attacker pkill -INT tcpdump 2>/dev/null
sleep 2
docker cp attacker:/tmp/kb2.pcap "$OUT/demo_kb2.pcap"

say "KB3 - MITM sua payload"
docker exec attacker pkill -f mitm.py 2>/dev/null
docker exec attacker pkill -f scenario2 2>/dev/null
docker exec attacker sysctl -w net.ipv4.ip_forward=0
for c in user server attacker; do docker exec $c pkill -x nc 2>/dev/null; docker exec $c pkill -x tcpdump 2>/dev/null; done
docker exec -d attacker sh -c "python3 -u /attack/scenario2.py --count 0 --interval 1 > /tmp/kb3_poison.log 2>&1"
sleep 3
docker exec -d attacker sh -c "python3 -u /attack/mitm.py > /tmp/kb3_mitm.log 2>&1"
docker exec -d user sh -c "tcpdump -U -i eth0 -n 'arp or tcp port 10101' -w /tmp/kb3_user.pcap"
docker exec -d server sh -c "tcpdump -U -i eth0 -n 'arp or tcp port 10101' -w /tmp/kb3_server.pcap"
docker exec -d attacker sh -c "tcpdump -U -i eth0 -n 'arp or tcp port 10101' -w /tmp/kb3.pcap"
sleep 3
echo "[arp user]"
docker exec user arp -n
docker exec server rm -f /tmp/kb3_recv.txt
docker exec -d server sh -c "timeout 25 nc -l 10101 > /tmp/kb3_recv.txt 2>&1"
sleep 2
docker exec user sh -c "echo hello server from user | timeout 6 nc 10.11.1.20 10101"
echo "[server nhan duoc]"
docker exec server cat /tmp/kb3_recv.txt
echo "[mitm log]"
docker exec attacker tail -2 /tmp/kb3_mitm.log
docker exec user pkill -INT tcpdump 2>/dev/null
docker exec server pkill -INT tcpdump 2>/dev/null
docker exec attacker pkill -INT tcpdump 2>/dev/null
sleep 3
docker cp user:/tmp/kb3_user.pcap "$OUT/demo_kb3_user.pcap"
docker cp server:/tmp/kb3_server.pcap "$OUT/demo_kb3_server.pcap"
docker cp attacker:/tmp/kb3.pcap "$OUT/demo_kb3.pcap"
docker exec attacker pkill -f mitm.py 2>/dev/null
docker exec attacker pkill -f scenario2 2>/dev/null
docker exec server pkill -x nc 2>/dev/null
docker exec user pkill -x nc 2>/dev/null

say "Bang chung payload"
echo "[user gui]"
tshark -r "$OUT/demo_kb3_user.pcap" -Y 'tcp.port==10101 and tcp.len>0' -T fields -e ip.src -e tcp.payload 2>/dev/null | tail -2
echo "[server nhan]"
tshark -r "$OUT/demo_kb3_server.pcap" -Y 'tcp.port==10101 and tcp.len>0' -T fields -e ip.src -e tcp.payload 2>/dev/null | tail -2
echo "[attacker thay ca hai]"
tshark -r "$OUT/demo_kb3.pcap" -Y 'tcp.port==10101 and tcp.len>0' -T fields -e eth.src -e eth.dst -e tcp.payload 2>/dev/null | tail -2

say "Xong. pcap trong $OUT"
ls -l "$OUT"/demo_*.pcap
