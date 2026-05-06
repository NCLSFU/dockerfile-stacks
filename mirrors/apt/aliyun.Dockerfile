# Aliyun apt mirror for Ubuntu
# Works for Ubuntu 22.04 and 24.04

RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' \
    /etc/apt/sources.list \
    && apt-get update \
    && rm -rf /var/lib/apt/lists/*
