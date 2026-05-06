# Dockerfile building blocks for OpenClaw, Hermes and more.
# Mix and match like LEGO to compose your own Docker images.

# Quick start
# 1. Choose a base image from `base/`
# 2. Add optional layers from `layers/` (e.g. setup)
# 3. Set env vars from `env/` (e.g. noninteractive)
# 4. Install tools from `tools/` (node, git, uv)
# 5. Configure mirrors from `mirrors/` (apt, npm, pnpm, uv)
# 6. Add services from `services/` (openclaw, hermes)
# 7. Mix and match in `examples/`

# Directory structure
```
# dockerfile-stacks/
# ├── README.md
# ├── base/                      # Base OS images
# │   ├── Ubuntu.24.04.Dockerfile
# │   └── Ubuntu.22.04.Dockerfile
# ├── layers/                    # Patch layers (apt update, base tools)
# │   └── setup.Dockerfile
# ├── env/                       # Environment variables
# │   └── noninteractive.Dockerfile
# ├── tools/                     # Language runtimes & CLIs
# │   ├── node.Dockerfile        # ARG NODE_VERSION=22
# │   ├── git.Dockerfile
# │   └── uv.Dockerfile          # ARG PYTHON_VERSION=3.11
# ├── mirrors/                   # Chinese mirror sources
# │   ├── apt/   / aliyun.Dockerfile
# │   ├── npm/   / aliyun.Dockerfile
# │   ├── pnpm/  / aliyun.Dockerfile
# │   └── uv/    / aliyun.Dockerfile
# ├── services/                  # Service installers (TBD)
# │   └── (openclaw, hermes)
# └── examples/                  # Composed Dockerfile examples
```

# Usage
# Build a composed image:
#   docker build -f examples/my-image.Dockerfile -t my-image .

# Or use docker compose:
#   docker compose -f examples/docker-compose.yml build
