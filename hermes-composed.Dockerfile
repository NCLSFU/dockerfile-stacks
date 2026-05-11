FROM ubuntu:24.04

# ── Hermès Environment ───────────────────────────────────────────
# Hermes environment variables
ENV HERMES_HOME=/root/.hermes
ENV INSTALL_DIR=/root/.hermes/hermes-agent
ENV VIRTUAL_ENV=/root/.hermes/hermes-agent/venv
ENV PYTHON_VERSION=3.11
ENV NODE_VERSION=22
SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV NEEDRESTART_MODE=a

# ── Mirrors ──────────────────────────────────────────────────────────────
# APT mirror
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' \
    /etc/apt/sources.list.d/ubuntu.sources \
    && sed -i 's|http://security.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' \
    /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get update \
    && rm -rf /var/lib/apt/lists/*

# NPM mirror
RUN npm config set registry https://registry.npmmirror.com

# ── Layers ────────────────────────────────────────────────────────────
# setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    tzdata \
    git \
    build-essential \
    python3-dev \
    libffi-dev \
    ripgrep \
    ffmpeg \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# ── Tools: uv ─────────────────────────────────────────────────────────
# uv (install only, python handled separately)
ARG PYTHON_VERSION=3.11
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://astral.sh/uv/install.sh | bash \
    && mv /root/.local/bin/uv /usr/local/bin/uv

# ── Tools: Python via uv ────────────────────────────────────────────
ARG PYTHON_VERSION=3.11
RUN uv python install 3.11 && uv python list

# ── Hermès: Clone ───────────────────────────────────────────────────
ARG HERMES_BRANCH=main
RUN git clone --branch ${HERMES_BRANCH} https://github.com/NousResearch/hermes-agent.git "${INSTALL_DIR}"
WORKDIR ${INSTALL_DIR}

# ── Hermès: venv ─────────────────────────────────────────────────────
ARG PYTHON_VERSION=3.11
WORKDIR ${INSTALL_DIR}
RUN uv venv venv --python 3.11

# ── Hermès: Python deps ──────────────────────────────────────────────
# Install Hermes Python dependencies (requires venv already created)
RUN . venv/bin/activate && uv pip install -e ".[all]"

# ── Tools: Node.js (tarball) ─────────────────────────────────────────
ARG NODE_VERSION=22
RUN ARCH=$(uname -m) && \
    case "$ARCH" in \
        x86_64) NODE_ARCH="x64" ;; \
        aarch64|arm64) NODE_ARCH="arm64" ;; \
        armv7l) NODE_ARCH="armv7l" ;; \
        *) echo "Unsupported arch: $ARCH" && exit 1 ;; \
    esac && \
    INDEX_URL="https://nodejs.org/dist/latest-v22.x/" && \
    TARBALL=$(curl -fsSL "$INDEX_URL" | grep -oE "node-v22\.[0-9]+\.[0-9]+-linux-${NODE_ARCH}\.tar\.xz" | head -1) && \
    curl -fsSL "${INDEX_URL}${TARBALL}" -o /tmp/node.tar.xz && \
    mkdir -p /root/.local/hermes-node && \
    tar -xf /tmp/node.tar.xz -C /tmp && \
    mv /tmp/node-v22*-linux-${NODE_ARCH}/* /root/.local/hermes-node/ && \
    rm -rf /tmp/node.tar.xz /tmp/node-v22* && \
    mkdir -p /root/.local/bin && \
    ln -sf /root/.local/hermes-node/bin/node /root/.local/bin/node && \
    ln -sf /root/.local/hermes-node/bin/npm /root/.local/bin/npm && \
    ln -sf /root/.local/hermes-node/bin/npx /root/.local/bin/npx && \
    node --version

# ── Tools: Playwright ────────────────────────────────────────────────
# Requires: uv tool (installs playwright in the venv)
# Needs: Node.js, Python venv already set up
# NOTE: This block is Hermes-specific; it assumes VIRTUAL_ENV is already set.
RUN . /root/.hermes/hermes-agent/venv/bin/activate && \
    npm install --silent && \
    npx playwright install --with-deps chromium

# ── Hermès: Init ─────────────────────────────────────────────────────
# Create Hermes directories and sync skills (requires hermes-agent already cloned)
RUN mkdir -p /root/.hermes/{sessions,logs,cron,pairing,hooks,image_cache,audio_cache,memories,skills} && \
    cp -n tools/soul.md.example /root/.hermes/SOUL.md 2>/dev/null || true && \
    . venv/bin/activate && python tools/skills_sync.py || true

# ── PATH ──────────────────────────────────────────────────────────────
ENV PATH="/root/.local/bin:/root/.local/hermes-node/bin:/root/.hermes/hermes-agent/venv/bin:${PATH}"
RUN echo 'export PATH="/root/.local/bin:/root/.local/hermes-node/bin:/root/.hermes/hermes-agent/venv/bin:$PATH"' >> /root/.bashrc

# ── Launcher ──────────────────────────────────────────────────────────
# hermes
# Launcher: Hermes Agent (built from source)
# Validates hermes is available then runs bash (keeps container alive)
RUN . venv/bin/activate && hermes --version 2>/dev/null || true
CMD ["/bin/bash"]
