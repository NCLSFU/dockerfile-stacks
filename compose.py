#!/usr/bin/env python3
"""
compose.py — Generate a Dockerfile from building blocks.

Usage:
    python compose.py --base ubuntu-24.04 --out my-image.Dockerfile [options]

Options:
    --base        ubuntu-24.04 | ubuntu-22.04   (required)
    --env         noninteractive               (optional)
    --layer       setup                        (optional)
    --tools       node,git,uv                  (comma-separated, optional)
    --mirrors     apt,npm,pnpm,uv              (comma-separated, optional)
    --node-version 22                          (default: 22)
    --python-version 3.11                      (default: 3.11)
    --launcher    bash|hermes|openclaw         (default: bash)
    --workflow    bash|hermes                  (default: bash)
    --out         output Dockerfile path        (default: my-image.Dockerfile)
"""

import argparse
import sys
from pathlib import Path

BLOCKS_DIR = Path(__file__).parent / "blocks"
VALID_BASES = ["ubuntu-24.04", "ubuntu-22.04"]
VALID_ENVS = ["noninteractive"]
VALID_LAYERS = ["setup"]
VALID_TOOLS = ["node", "git", "uv", "node-tarball", "python-uv", "playwright"]
VALID_MIRRORS = ["apt", "npm", "pnpm", "uv"]
VALID_LAUNCHERS = ["bash", "hermes", "openclaw"]
VALID_WORKFLOWS = ["bash", "hermes"]


def load_block(block_path: Path) -> str:
    """Load a block file, return empty string if not found."""
    if not block_path.exists():
        return ""
    return block_path.read_text().strip()


def build_header(base: str) -> str:
    """Build the FROM line."""
    os_map = {
        "ubuntu-24.04": "ubuntu:24.04",
        "ubuntu-22.04": "ubuntu:22.04",
    }
    return f"FROM {os_map[base]}\n"


def build_body_bash(env, layer, tools, mirrors, node_version, python_version, launcher):
    """Build body for standard (bash) workflow: concat of arbitrary blocks."""
    lines = []

    lines.append("# ── Env ───────────────────────────────────────────────────────────────")
    for e in env:
        block = load_block(BLOCKS_DIR / "env" / f"{e}.txt")
        if block:
            lines.append(block)
            lines.append("")

    lines.append("# ── Mirrors ──────────────────────────────────────────────────────────────")
    for m in mirrors:
        if m == "uv":
            python_block = load_block(BLOCKS_DIR / "mirrors" / "uv" / "python.txt")
            if python_block:
                lines.append("# UV_PYTHON mirror")
                lines.append(python_block)
                lines.append("")
            pip_block = load_block(BLOCKS_DIR / "mirrors" / "uv" / "pip.txt")
            if pip_block:
                lines.append("# UV pip mirror")
                lines.append(pip_block)
                lines.append("")
        else:
            block = load_block(BLOCKS_DIR / "mirrors" / m / "aliyun.txt")
            if block:
                lines.append(f"# {m.upper()} mirror")
                lines.append(block)
                lines.append("")

    lines.append("# ── Layers ────────────────────────────────────────────────────────────")
    for l in layer:
        block = load_block(BLOCKS_DIR / "layers" / f"{l}.txt")
        if block:
            lines.append(f"# {l}")
            lines.append(block)
            lines.append("")

    lines.append("# ── Tools ─────────────────────────────────────────────────────────────")
    for t in tools:
        block = load_block(BLOCKS_DIR / "tools" / f"{t}.txt")
        if block:
            lines.append(f"# {t}")
            lines.append(block)
            lines.append("")

    lines.append("# ── Launcher ──────────────────────────────────────────────────────────")
    launcher_block = load_block(BLOCKS_DIR / "launcher" / f"{launcher}.txt")
    if launcher_block:
        lines.append(f"# {launcher}")
        lines.append(launcher_block)

    return "\n".join(lines)


def build_body_hermes(node_version, python_version, launcher):
    """Build body for Hermès workflow: ordered 13-step build."""
    lines = []

    # 0. Hermès env vars
    hermes_env = load_block(BLOCKS_DIR / "tools" / "hermes" / "env.txt")
    if hermes_env:
        lines.append("# ── Hermès Environment ───────────────────────────────────────────")
        lines.append(hermes_env)
        lines.append("")

    # 1. Env: noninteractive (DEBIAN_FRONTEND + NEEDRESTART_MODE)
    env_block = load_block(BLOCKS_DIR / "env" / "noninteractive.txt")
    if env_block:
        lines.append(env_block)
        lines.append("")

    # 2. Mirrors: apt only (npm mirror is set via ENV in node-tarball block)
    lines.append("# ── Mirrors ──────────────────────────────────────────────────────────────")
    apt_block = load_block(BLOCKS_DIR / "mirrors" / "apt" / "aliyun.txt")
    if apt_block:
        lines.append("# APT mirror")
        lines.append(apt_block)
        lines.append("")
    lines.append("# NPM mirror: set via ENV NODE_MIRROR in node-tarball block")
    lines.append("")

    # 3. Layer: base setup (git, build-essential, ffmpeg, etc.)
    lines.append("# ── Layers ────────────────────────────────────────────────────────────")
    layer_block = load_block(BLOCKS_DIR / "layers" / "setup.txt")
    if layer_block:
        lines.append("# setup")
        lines.append(layer_block)
        lines.append("")

    # 4. uv (install only, strip python install - python handled separately)
    lines.append("# ── Tools: uv ─────────────────────────────────────────────────────────")
    uv_block = load_block(BLOCKS_DIR / "tools" / "uv.txt")
    if uv_block:
        lines.append("# uv (install only, python handled separately)")
        lines.append(strip_python_install(uv_block))
        lines.append("")

    # 5. Python via uv (MUST be before clone, needed for venv creation)
    lines.append("# ── Tools: Python via uv ────────────────────────────────────────────")
    python_block = load_block(BLOCKS_DIR / "tools" / "python-uv.txt")
    if python_block:
        lines.append(python_block)
        lines.append("")

    # 6. Git clone hermes-agent
    lines.append("# ── Hermès: Clone ───────────────────────────────────────────────────")
    clone_block = load_block(BLOCKS_DIR / "tools" / "hermes" / "clone.txt")
    if clone_block:
        lines.append(clone_block)
        lines.append("")

    # 7. Create venv
    lines.append("# ── Hermès: venv ─────────────────────────────────────────────────────")
    venv_block = load_block(BLOCKS_DIR / "tools" / "hermes" / "venv.txt")
    if venv_block:
        lines.append(venv_block)
        lines.append("")

    # 8. Install Python deps (AFTER venv created)
    lines.append("# ── Hermès: Python deps ──────────────────────────────────────────────")
    pip_block = load_block(BLOCKS_DIR / "tools" / "hermes" / "pip-install.txt")
    if pip_block:
        lines.append(pip_block)
        lines.append("")

    # 9. Node.js via tarball (AFTER venv, before playwright)
    lines.append("# ── Tools: Node.js (tarball) ─────────────────────────────────────────")
    node_block = load_block(BLOCKS_DIR / "tools" / "node-tarball.txt")
    if node_block:
        lines.append(node_block)
        lines.append("")

    # 10. Playwright (needs node + python venv)
    lines.append("# ── Tools: Playwright ────────────────────────────────────────────────")
    pw_block = load_block(BLOCKS_DIR / "tools" / "playwright.txt")
    if pw_block:
        lines.append(pw_block)
        lines.append("")

    # 11. Hermes init (dirs + skills_sync)
    lines.append("# ── Hermès: Init ─────────────────────────────────────────────────────")
    init_block = load_block(BLOCKS_DIR / "tools" / "hermes" / "init.txt")
    if init_block:
        lines.append(init_block)
        lines.append("")

    # 12. PATH
    lines.append("# ── PATH ──────────────────────────────────────────────────────────────")
    path_block = load_block(BLOCKS_DIR / "tools" / "hermes" / "path.txt")
    if path_block:
        lines.append(path_block)
        lines.append("")

    # 13. Launcher
    lines.append("# ── Launcher ──────────────────────────────────────────────────────────")
    launcher_block = load_block(BLOCKS_DIR / "launcher" / f"{launcher}.txt")
    if launcher_block:
        lines.append(f"# {launcher}")
        lines.append(launcher_block)

    return "\n".join(lines)


def strip_python_install(block_text):
    """Remove the uv python install line from uv.txt block."""
    lines = block_text.splitlines()
    result = []
    skip_next = False
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if "uv python install" in line:
            skip_next = True
            continue
        result.append(line)
    return "\n".join(result)


def substitute_args(content, node_version, python_version):
    """Replace ARG placeholders with actual values."""
    content = content.replace("ARG NODE_VERSION=22", f"ARG NODE_VERSION={node_version}")
    content = content.replace("ARG PYTHON_VERSION=3.11", f"ARG PYTHON_VERSION={python_version}")
    content = content.replace("${NODE_VERSION}", node_version)
    content = content.replace("${PYTHON_VERSION}", python_version)
    return content


def main():
    parser = argparse.ArgumentParser(description="Compose a Dockerfile from building blocks")
    parser.add_argument("--base", required=True, choices=VALID_BASES,
                        help="Base OS image")
    parser.add_argument("--env", action="append", default=[],
                        help=f"Env blocks: {VALID_ENVS}")
    parser.add_argument("--layer", action="append", default=[],
                        help=f"Layer blocks: {VALID_LAYERS}")
    parser.add_argument("--tools", default="",
                        help=f"Tools (comma-separated): {','.join(VALID_TOOLS)}")
    parser.add_argument("--mirrors", default="",
                        help=f"Mirrors (comma-separated): {','.join(VALID_MIRRORS)}")
    parser.add_argument("--node-version", default="22",
                        help="Node.js version (default: 22)")
    parser.add_argument("--python-version", default="3.11",
                        help="Python version (default: 3.11)")
    parser.add_argument("--launcher", default="bash",
                        choices=VALID_LAUNCHERS,
                        help=f"Container launcher: {', '.join(VALID_LAUNCHERS)} (default: bash)")
    parser.add_argument("--workflow", default="bash",
                        choices=VALID_WORKFLOWS,
                        help=f"Workflow: bash (standard blocks) or hermes (ordered steps) (default: bash)")
    parser.add_argument("--out", default="my-image.Dockerfile",
                        help="Output Dockerfile path (default: my-image.Dockerfile)")
    args = parser.parse_args()

    # Parse comma-separated tools and mirrors
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    mirrors = [m.strip() for m in args.mirrors.split(",") if m.strip()]

    # Validate
    for t in tools:
        if t not in VALID_TOOLS:
            print(f"Warning: unknown tool '{t}', skipping", file=sys.stderr)
            tools = [x for x in tools if x != t]
    for m in mirrors:
        if m not in VALID_MIRRORS:
            print(f"Warning: unknown mirror '{m}', skipping", file=sys.stderr)
            mirrors = [x for x in mirrors if x != m]
    if "pip" in mirrors and "uv" not in tools:
        print("Warning: pip mirror requires uv tool, adding uv", file=sys.stderr)
        tools.append("uv")

    # Build Dockerfile
    sections = []
    sections.append(build_header(args.base))

    if args.workflow == "hermes":
        sections.append(build_body_hermes(args.node_version, args.python_version, args.launcher))
    else:
        sections.append(build_body_bash(args.env, args.layer, tools, mirrors, args.node_version, args.python_version, args.launcher))

    content = "\n".join(sections)
    content = substitute_args(content, args.node_version, args.python_version)

    output_path = Path(args.out)
    output_path.write_text(content + "\n")

    print(f"✓ Generated: {output_path}")
    print(f"\nBuild with:")
    print(f"  docker build -f {output_path} -t my-image .")
    print(f"\nRun with:")
    print(f"  docker run -it --rm my-image")


if __name__ == "__main__":
    main()