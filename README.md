# dockerfile-stacks

**Compose custom Dockerfiles from building blocks — like LEGO for Docker images.**

## What This Project Is

A collection of reusable Dockerfile building blocks for assembling Docker images from modular pieces:
- **blocks/base/** — OS base images (Ubuntu 24.04, 22.04)
- **blocks/env/** — Environment variable snippets (e.g. noninteractive)
- **blocks/layers/** — Patch layers (apt setup, base tools)
- **blocks/tools/** — Language runtimes and CLIs (Node.js, Git, uv/Python)
- **blocks/mirrors/** — Chinese mirror configurations (Aliyun for apt, npm, pnpm; UV pip uses Aliyun, UV python uses TUNA)
- **blocks/launcher/** — Container entrypoints (bash shell, Hermes Agent, OpenClaw CLI)

## Directory Structure

```
dockerfile-stacks/
├── blocks/
│   ├── base/
│   │   ├── ubuntu-24.04.txt
│   │   └── ubuntu-22.04.txt
│   ├── env/
│   │   └── noninteractive.txt
│   ├── layers/
│   │   └── setup.txt        # apt update + base tools (curl, wget, ca-certificates, tzdata)
│   ├── tools/
│   │   ├── node.txt         # Node.js (ARG NODE_VERSION, default 22)
│   │   ├── git.txt
│   │   └── uv.txt           # uv + Python (ARG PYTHON_VERSION, default 3.11)
│   ├── mirrors/
│   │   ├── apt/aliyun.txt
│   │   ├── npm/aliyun.txt
│   │   ├── pnpm/aliyun.txt
│   │   └── uv/
│   │       ├── pip.txt        # UV_INDEX_URL → Aliyun (for uv pip install)
│   │       └── python.txt    # UV_INDEX_PYTHON_URL → TUNA (for uv python install)
│   └── launcher/
│       ├── bash.txt         # Default: interactive bash shell
│       ├── hermes.txt       # Hermes Agent (NousResearch AI agent)
│       └── openclaw.txt     # OpenClaw CLI gateway
├── compose.py               # Generate Dockerfile from blocks
├── SKILL.md                # AI agent skill (how to use this project)
├── SKILL_TEST.md           # AI agent testing skill (end-to-end verify a combination)
└── recipes/                # Pre-composed Dockerfiles for common combos
```

## Quick Start

### Step 1: Generate a Dockerfile

```bash
python compose.py \
  --base ubuntu-24.04 \
  --env noninteractive \
  --layer setup \
  --tools node,git,uv \
  --mirrors apt,npm,uv \
  --launcher bash \
  --out my-image.Dockerfile
```

**Available options:**

| Option | Choices | Notes |
|--------|---------|-------|
| `--base` | `ubuntu-24.04`, `ubuntu-22.04` | Required |
| `--env` | `noninteractive` | Optional; prevents apt interactive prompts |
| `--layer` | `setup` | Optional; apt update + base tools |
| `--tools` | `node`, `git`, `uv` | Comma-separated; all optional |
| `--mirrors` | `apt`, `npm`, `pnpm`, `uv` | Comma-separated; Aliyun for apt/npm/pnpm; UV has both pip (Aliyun) and python (TUNA) mirrors |
| `--node-version` | e.g. `22`, `20`, `18` | Defaults to `22` |
| `--python-version` | e.g. `3.11`, `3.12` | Defaults to `3.11` |
| `--launcher` | `bash`, `hermes`, `openclaw` | Container entrypoint; defaults to `bash` |
| `--out` | filename | Output path; defaults to `my-image.Dockerfile` |

### Step 2: Build the Image

```bash
docker build -f my-image.Dockerfile -t my-image .
```

With custom versions:

```bash
docker build -f my-image.Dockerfile \
  --build-arg NODE_VERSION=20 \
  --build-arg PYTHON_VERSION=3.12 \
  -t my-image .
```

### Step 3: Run the Container

```bash
# Interactive shell
docker run -it --rm my-image

# With workspace mount
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  my-image

# Named container (persist between runs)
docker run -it --name my-dev my-image
docker start -ai my-dev   # re-enter later
```

## Launchers

Choose what runs when the container starts:

| Launcher | When to use |
|----------|-------------|
| `bash` | Default. Interactive dev environment, debugging |
| `hermes` | Hermes Agent (NousResearch AI agent, Python-based, self-improving) |
| `openclaw` | OpenClaw CLI gateway (TypeScript/Node.js) |

**Example — build a dev container with Hermes Agent:**

```bash
python compose.py \
  --base ubuntu-24.04 \
  --tools node,git,uv \
  --mirrors apt,uv \
  --launcher hermes \
  --out hermes-dev.Dockerfile

docker build -f hermes-dev.Dockerfile -t hermes-dev .
docker run -it --rm hermes-dev
# → Hermes Agent TUI starts
```

## Image Naming

```bash
# Basic
docker build -f my-image.Dockerfile -t my-image .

# With tag
docker build -f my-image.Dockerfile -t my-image:1.0 .

# With registry prefix (for later push)
docker build -f my-image.Dockerfile -t registry.example.com/my-image:1.0 .
```

## How AI Agents Should Use This Project

When a user asks to create a Docker image:

1. **Read `SKILL.md`** to understand the block system
2. **Identify needed blocks** from the request (base OS, tools, mirrors, launcher)
3. **Run `compose.py`** to generate the Dockerfile
4. **Offer to build it** with `docker build` and verify with smoke tests
5. **Report results** with the `docker run` command

For **automated testing** of a combination, read `SKILL_TEST.md` — it defines the full generate → build → verify → cleanup workflow.

## For AI Agents: Reading SKILL.md

This project includes `SKILL.md` — an AI-readable instruction file. When an AI agent encounters this project, it should:

1. Read `SKILL.md` to understand the block system
2. Ask the user what components they need (base OS, tools, mirrors, launcher)
3. Generate the Dockerfile using `compose.py`
4. Report the build and run commands back to the user
