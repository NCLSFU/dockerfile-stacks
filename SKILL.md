# dockerfile-stacks

**Compose custom Dockerfiles from building blocks — like LEGO for Docker images.**

## What This Project Is

A collection of reusable Dockerfile building blocks for assembling Docker images from modular pieces:
- **base/** — OS base images (Ubuntu 24.04, 22.04)
- **env/** — Environment variable snippets (e.g. noninteractive)
- **layers/** — Patch layers (apt setup, base tools)
- **tools/** — Language runtimes and CLIs (Node.js, Git, uv/Python)
- **mirrors/** — Chinese mirror configurations (Aliyun for apt, npm, pnpm, uv)

## Directory Structure

```
dockerfile-stacks/
├── blocks/                  # Building block snippets
│   ├── base/
│   │   ├── ubuntu-24.04.txt
│   │   └── ubuntu-22.04.txt
│   ├── env/
│   │   └── noninteractive.txt
│   ├── layers/
│   │   └── setup.txt        # apt update + essential tools
│   ├── tools/
│   │   ├── node.txt         # ARG NODE_VERSION=22
│   │   ├── git.txt
│   │   └── uv.txt           # ARG PYTHON_VERSION=3.11
│   └── mirrors/
│       ├── apt/aliyun.txt
│       ├── npm/aliyun.txt
│       ├── pnpm/aliyun.txt
│       └── uv/aliyun.txt
├── compose.py              # Compose a full Dockerfile from blocks
├── SKILL.md                # This file
└── examples/               # Composed Dockerfile examples
```

## How to Use

### Step 1: Generate a Dockerfile

Run `compose.py` with the blocks you need:

```bash
python compose.py \
  --base ubuntu-24.04 \
  --env noninteractive \
  --layer setup \
  --tools node,git,uv \
  --mirrors apt,npm \
  --out my-image.Dockerfile
```

**Available options:**

| Option | Choices | Notes |
|--------|---------|-------|
| `--base` | `ubuntu-24.04`, `ubuntu-22.04` | Required |
| `--env` | `noninteractive` | Optional; prevents apt interactive prompts |
| `--layer` | `setup` | Optional; apt update + base tools |
| `--tools` | `node`, `git`, `uv` | Comma-separated; all optional |
| `--mirrors` | `apt`, `npm`, `pnpm`, `uv` | Comma-separated; Aliyun mirrors for China |
| `--node-version` | e.g. `22`, `20`, `18` | Defaults to `22` |
| `--python-version` | e.g. `3.11`, `3.12` | Defaults to `3.11` |
| `--launcher` | `bash`, `hermes`, `openclaw` | What runs when the container starts; defaults to `bash` |
| `--out` | filename | Output path; defaults to `my-image.Dockerfile` |

### Step 2: Build the Image

```bash
docker build -f my-image.Dockerfile -t my-image .
```

Or with custom versions:

```bash
docker build -f my-image.Dockerfile \
  --build-arg NODE_VERSION=20 \
  --build-arg PYTHON_VERSION=3.12 \
  -t my-image .
```

## How AI Agents Should Use This Project

When a user asks to create a Docker image with specific requirements:

1. **Identify needed blocks** from the request
   - Base OS → `blocks/base/`
   - Dev tools → `blocks/tools/`
   - China mirror → `blocks/mirrors/`
2. **Run `compose.py`** to generate the Dockerfile
3. **Report the result** to the user with the `docker build` command
4. **Offer to build it** if Docker is available

### Example Conversation

**User:** "帮我生成一个带 Node.js 和 uv 的 Ubuntu 镜像"

**Agent:**
```bash
python compose.py \
  --base ubuntu-24.04 \
  --env noninteractive \
  --layer setup \
  --tools node,git,uv \
  --mirrors apt,npm,uv \
  --out ubuntu-node-uv.Dockerfile
```

Then share:
```bash
docker build -f ubuntu-node-uv.Dockerfile -t my-image .
```

## Launchers

Choose what happens when the container starts:

| Launcher | What it does |
|----------|-------------|
| `bash` | Drops into interactive bash shell (default) |
| `hermes` | Installs Hermes Agent and runs `hermes` CLI (NousResearch AI agent) |
| `openclaw` | Installs OpenClaw CLI and starts the gateway |

```bash
# Example: build a dev container with Hermes agent
python compose.py \
  --base ubuntu-24.04 \
  --tools node,git,uv \
  --mirrors apt,uv \
  --launcher hermes \
  --out hermes-dev.Dockerfile

docker build -f hermes-dev.Dockerfile -t hermes-dev .
docker run -it --rm hermes-dev
# → Hermes Agent interactive TUI starts
```

## Image Naming

Use `-t` to name your image and optionally tag it:

```bash
# Basic name (latest tag implied)
docker build -f my-image.Dockerfile -t my-image .

# With version tag
docker build -f my-image.Dockerfile -t my-image:1.0 .

# With registry prefix (for push later)
docker build -f my-image.Dockerfile -t registry.example.com/my-image:1.0 .

# Custom version args
docker build -f my-image.Dockerfile \
  --build-arg NODE_VERSION=20 \
  --build-arg PYTHON_VERSION=3.12 \
  -t my-image:node20-py312 .
```

## Running the Image

### Basic Run

```bash
docker run -it --rm my-image
```

| Flag | Purpose |
|------|---------|
| `-it` | Interactive + TTY (for shell access) |
| `--rm` | Remove container after exit |

### Mounting Volumes

```bash
# Mount a local directory into the container
docker run -it --rm \
  -v /path/on/host:/path/in/container \
  my-image

# Mount with read-only option
docker run -it --rm \
  -v /path/on/host:/path/in/container:ro \
  my-image

# Mount current directory
docker run -it --rm \
  -v $(pwd):/workspace \
  my-image

# Mount and set working directory
docker run -it --rm \
  -v /path/on/host:/workspace \
  -w /workspace \
  my-image
```

### Named Container (Persist)

```bash
# Give container a persistent name (survives exit)
docker run -it --name my-container my-image

# Start existing named container again
docker start -ai my-container

# Remove named container
docker rm my-container
```

### Common Combinations

```bash
# Interactive dev environment with workspace mount
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  --name my-dev \
  my-image

# Detached (background) with port mapping
docker run -d \
  -p 8080:8080 \
  --name my-server \
  my-image

# Override entrypoint (get a shell instead of default cmd)
docker run -it --rm \
  --entrypoint /bin/bash \
  my-image
```

## Notes

- All block files (`blocks/*.txt`) contain **pure Dockerfile instructions** (no `FROM` statement — that's added by `--base`)
- `compose.py` concatenates blocks in the correct order and adds the `FROM` at the top
- Blocks with `ARG` in their content (node, uv) accept `--build-arg` at build time
