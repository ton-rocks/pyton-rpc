FROM ubuntu:18.04 as builder
ARG core_count
ENV env_core_count=$core_count

RUN apt-get update && \
	apt-get install -y build-essential cmake clang-6.0 openssl libssl-dev zlib1g-dev gperf wget vim tar git curl chrony ca-certificates gnupg python python3 libmicrohttpd-dev && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /
RUN git clone https://gitlab.com/gram-net/gram-ton.git /ton
RUN cd /ton && git submodule update --init --recursive --remote
RUN mkdir /ton/build && \
	cd /ton/build && \
	cmake -B /ton/build -S /ton -DCMAKE_BUILD_TYPE=Debug

WORKDIR /ton/build
RUN cmake --build /ton/build --target tonlibjson -- -j1

FROM ubuntu:18.04
RUN apt-get update && \
	apt-get install -y openssl wget python3 python3-pip nano mc && \
	rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/ton-work/db && \
	mkdir -p /var/ton-work/db/static

COPY --from=builder /ton/build/tonlib/libtonlibjson.so /usr/local/lib

RUN mkdir -p /var/ton-work
RUN mkdir -p /var/ton-work/logs
RUN mkdir -p /var/ton-work/db

WORKDIR /var/ton-work

COPY ./* ./
RUN chmod +x /var/ton-work/init.sh

RUN pip3 install flask gunicorn

ENTRYPOINT ["/var/ton-work/init.sh"]
