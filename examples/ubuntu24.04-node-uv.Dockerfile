# Example: Ubuntu 24.04 + Node + uv + Python + Aliyun mirrors
# This is a composed Dockerfile using building blocks from dockerfile-stacks/

# ── Base ──────────────────────────────────────────────────────────────
FROM ubuntu:24.04

# ── Env: noninteractive (prevents apt interactive prompts) ───────────
COPY env/noninteractive.Dockerfile /tmp/noninteractive.dockerfile
RUN bash /tmp/noninteractive.dockerfile

# ── Mirrors: Aliyun apt mirror ────────────────────────────────────────
COPY mirrors/apt/aliyun.Dockerfile /tmp/aliyun-apt.dockerfile
RUN bash /tmp/aliyun-apt.dockerfile

# ── Layers: base setup (apt update + essential tools) ─────────────────
COPY layers/setup.Dockerfile /tmp/setup.dockerfile
RUN bash /tmp/setup.dockerfile

# ── Tools ─────────────────────────────────────────────────────────────
# Git (via apt)
COPY tools/git.Dockerfile /tmp/git.dockerfile
RUN bash /tmp/git.dockerfile

# Node.js (ARG NODE_VERSION=22 by default)
COPY tools/node.Dockerfile /tmp/node.dockerfile
RUN bash /tmp/node.dockerfile

# uv + Python 3.11
COPY tools/uv.Dockerfile /tmp/uv.dockerfile
ARG PYTHON_VERSION=3.11
RUN bash /tmp/uv.dockerfile

# ── Mirrors: Aliyun npm + uv ──────────────────────────────────────────
COPY mirrors/npm/aliyun.Dockerfile /tmp/aliyun-npm.dockerfile
RUN bash /tmp/aliyun-npm.dockerfile

COPY mirrors/uv/aliyun.Dockerfile /tmp/aliyun-uv.dockerfile
RUN bash /tmp/aliyun-uv.dockerfile

# ── Verify ────────────────────────────────────────────────────────────
RUN node --version && npm --version && uv python list && git --version
