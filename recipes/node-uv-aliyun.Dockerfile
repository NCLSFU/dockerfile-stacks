# Recipe: Node + uv (Python) + Aliyun mirrors
# Base: Ubuntu 24.04
# Includes: noninteractive env + apt/npm/uv Aliyun mirrors + node + git + uv

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV NEEDRESTART_MODE=a

# Aliyun apt mirror
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' \
    /etc/apt/sources.list \
    && apt-get update \
    && rm -rf /var/lib/apt/lists/*

# Base tools
RUN apt-get update && apt-get install -y \
    curl wget ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

# Git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Node.js
ARG NODE_VERSION=22
RUN curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version

# Aliyun npm mirror
RUN npm config set registry https://registry.npmmirror.com

# uv + Python
ARG PYTHON_VERSION=3.11
RUN curl -fsSL https://astral.sh/uv/install.sh | bash \
    && mv /root/.local/bin/uv /usr/local/bin/uv
RUN uv python install ${PYTHON_VERSION} && uv python list

# Aliyun uv mirror
ENV UV_INDEX_PYTHON_URL=https://pypi.tuna.tsinghua.edu.cn
