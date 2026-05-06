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

## Notes

- All block files (`blocks/*.txt`) contain **pure Dockerfile instructions** (no `FROM` statement — that's added by `--base`)
- `compose.py` concatenates blocks in the correct order and adds the `FROM` at the top
- Blocks with `ARG` in their content (node, uv) accept `--build-arg` at build time
