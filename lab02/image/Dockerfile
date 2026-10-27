FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        iproute2 \
        iputils-ping \
        net-tools \
        tcpdump \
        netcat-openbsd \
        procps \
        tmux \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /attack

CMD ["sleep", "infinity"]
