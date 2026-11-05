$TTL 300
@   IN  SOA ns.attacker32.com. admin.attacker32.com. (
        2026110501 ; serial
        3600       ; refresh
        900        ; retry
        604800     ; expire
        300        ; minimum
)
    IN  NS  ns.attacker32.com.
www IN  A   1.2.3.4
