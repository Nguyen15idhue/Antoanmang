FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        bind9 bind9utils bind9-dnsutils \
        python3 iproute2 iputils-ping net-tools tcpdump \
        procps nano vim-tiny ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN rndc-confgen -a -c /etc/bind/rndc.key 2>/dev/null || true \
    && mkdir -p /var/cache/bind /run/named \
    && chown -R bind:bind /var/cache/bind /run/named

WORKDIR /attack

CMD ["sleep", "infinity"]
