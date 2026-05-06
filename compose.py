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
    --out         output Dockerfile path        (default: my-image.Dockerfile)
"""

import argparse
import sys
from pathlib import Path

BLOCKS_DIR = Path(__file__).parent / "blocks"
VALID_BASES = ["ubuntu-24.04", "ubuntu-22.04"]
VALID_ENVS = ["noninteractive"]
VALID_LAYERS = ["setup"]
VALID_TOOLS = ["node", "git", "uv"]
VALID_MIRRORS = ["apt", "npm", "pnpm", "uv"]


def load_block(block_path: Path) -> str:
    """Load a block file, return empty string if not found."""
    if not block_path.exists():
        return ""
    content = block_path.read_text()
    # Strip leading/trailing whitespace but keep structure
    return content.strip()


def build_header(base: str) -> str:
    """Build the FROM line."""
    os_map = {
        "ubuntu-24.04": "ubuntu:24.04",
        "ubuntu-22.04": "ubuntu:22.04",
    }
    return f"FROM {os_map[base]}\n"


def build_body(env: list, layer: list, tools: list, mirrors: list, node_version: str, python_version: str) -> str:
    """Build the body sections from requested blocks."""
    lines = []
    lines.append("# ── Env ───────────────────────────────────────────────────────────────")
    for e in env:
        block = load_block(BLOCKS_DIR / "env" / f"{e}.txt")
        if block:
            lines.append(block)
            lines.append("")

    lines.append("# ── Mirrors (Aliyun) ────────────────────────────────────────────────")
    for m in mirrors:
        block = load_block(BLOCKS_DIR / "mirrors" / m / "aliyun.txt")
        if block:
            # Add comment header for mirror
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

    return "\n".join(lines)


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
                        help="Python version for uv (default: 3.11)")
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

    # Build Dockerfile
    sections = []
    sections.append(build_header(args.base))
    sections.append(build_body(args.env, args.layer, tools, mirrors, args.node_version, args.python_version))
    content = "\n".join(sections)

    # Substitute ARG values inline for blocks that need them
    content = content.replace("ARG NODE_VERSION=22", f"ARG NODE_VERSION={args.node_version}")
    content = content.replace("ARG PYTHON_VERSION=3.11", f"ARG PYTHON_VERSION={args.python_version}")

    output_path = Path(args.out)
    output_path.write_text(content + "\n")

    print(f"✓ Generated: {output_path}")
    print(f"\nBuild with:")
    print(f"  docker build -f {output_path} -t my-image .")
    if "node" in tools or "uv" in tools:
        print(f"\nOr with custom versions:")
        build_args = []
        if "node" in tools:
            build_args.append(f"NODE_VERSION={args.node_version}")
        if "uv" in tools:
            build_args.append(f"PYTHON_VERSION={args.python_version}")
        if build_args:
            print(f"  docker build -f {output_path} --build-arg {' --build-arg '.join(build_args)} -t my-image .")


if __name__ == "__main__":
    main()
