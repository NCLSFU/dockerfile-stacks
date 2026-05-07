# dockerfile-stacks Testing

**Test a dockerfile-stacks combination end-to-end: generate, build, and verify a Docker image.**

## Project Location

```
/home/nls/dockerfile-stacks/
```

## Workflow

When user asks to test or verify a specific combination:

### Step 1: Generate the Dockerfile

Run `compose.py` with the requested blocks:

```bash
cd /home/nls/dockerfile-stacks
python compose.py \
  --base ubuntu-24.04 \
  --env noninteractive \
  --layer setup \
  --tools node,git,uv \
  --mirrors apt,npm,uv \
  --node-version 22 \
  --python-version 3.12 \
  --out /tmp/test-image.Dockerfile
```

### Step 2: Build the Image

```bash
cd /home/nls/dockerfile-stacks
docker build -f /tmp/test-image.Dockerfile \
  --build-arg NODE_VERSION=22 \
  --build-arg PYTHON_VERSION=3.12 \
  -t df-test:latest \
  .
```

> Build errors → report the exact failure line, stop.

### Step 3: Verify the Image

Run a verification container to confirm key tools are present and working:

```bash
# Quick smoke test — check tools exist
docker run --rm df-test:latest \
  bash -c "node --version && git --version && uv --version"

# Test layer setup (if --layer setup was used)
docker run --rm df-test:latest \
  bash -c "which curl wget jq && echo 'layer-tools: OK'"
```

### Step 4: Interactive Test (Optional)

```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  --name df-test-interactive \
  df-test:latest
```

Let user interact, then clean up:

```bash
docker rm -f df-test-interactive 2>/dev/null
```

### Step 5: Clean Up

Always clean up after test:

```bash
docker rmi df-test:latest 2>/dev/null
rm -f /tmp/test-image.Dockerfile
```

## Error Handling

| Situation | Action |
|-----------|--------|
| `compose.py` fails (bad block name) | Report available blocks at `blocks/*/` |
| `docker build` fails | Show last 20 lines of build log |
| `docker run` fails | Report exit code and error message |
| Docker not running | Tell user to start Docker daemon |

## Verification Checklist

After build, confirm:

- [ ] `node --version` succeeds → Node.js works
- [ ] `git --version` succeeds → Git works
- [ ] `uv --version` succeeds → uv works
- [ ] (if layer setup) `curl` or `wget` available → layer tools installed

## Example Conversation

**User:** "测试一下 ubuntu-22.04 + node + uv 的组合"

**Agent:**
```bash
cd /home/nls/dockerfile-stacks
python compose.py \
  --base ubuntu-22.04 \
  --env noninteractive \
  --tools node,uv \
  --mirrors apt,uv \
  --node-version 20 \
  --python-version 3.11 \
  --out /tmp/test-ubuntu22-node-uv.Dockerfile
```
→ Dockerfile generated at `/tmp/test-ubuntu22-node-uv.Dockerfile`

```bash
docker build -f /tmp/test-ubuntu22-node-uv.Dockerfile \
  --build-arg NODE_VERSION=20 \
  --build-arg PYTHON_VERSION=3.11 \
  -t df-test:ubuntu22-node-uv \
  .
```
→ Build succeeded. Running verification...

```bash
docker run --rm df-test:ubuntu22-node-uv \
  bash -c "node --version && git --version && uv --version"
```
→ All tools OK. Cleaning up test image.

**Report:**
- ✅ Build 成功
- ✅ Node.js 20, Git, uv 均可执行
- ✅ 测试镜像已清理

## Custom Blocks

If user requests a block that doesn't exist yet → **stop and ask**:

```
可用 blocks:
  base:     ubuntu-24.04, ubuntu-22.04
  env:      noninteractive
  layer:    setup
  tools:    node, git, uv
  mirrors:  apt, npm, pnpm, uv
  launcher: bash, hermes, openclaw
```

Then offer to create the missing block before proceeding.
