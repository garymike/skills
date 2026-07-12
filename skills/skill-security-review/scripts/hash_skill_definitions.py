#!/usr/bin/env python3
"""
hash_skill_definitions.py — a deterministic SHA-256 over a skill's *entire bundled surface*.

A skill's risk lives across two surfaces, so the integrity anchor must cover both: SKILL.md, references/, scripts/,
AND the developer-execution files (test files, git hooks, npm/pip lifecycle scripts) that a rug pull would mutate
after approval. This hashes every file in the skill directory (minus VCS/build noise), path-sorted so the result is
reproducible on re-review. A post-approval change to any file changes the hash -> re-review is triggered.

Sibling of mcp-security-review/scripts/hash_tool_definitions.py; both keep a pinned, documented canonicalization so
a recorded hash means the same thing across the platform. Stdlib-only.

Usage: hash_skill_definitions.py PATH-TO-SKILL-DIR
"""
import hashlib
import os
import sys

# Directories that are not part of the shipped/attack surface (VCS internals, caches, vendored deps).
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build"}


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                # Record the link target, not the (out-of-tree) contents — a symlinked payload is itself a signal.
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                yield rel, ("link:" + os.readlink(full)).encode("utf-8")
                continue
            try:
                with open(full, "rb") as f:
                    yield os.path.relpath(full, root).replace(os.sep, "/"), f.read()
            except OSError:
                continue


def skill_hash(root):
    h = hashlib.sha256()
    for rel, data in sorted(iter_files(root), key=lambda t: t[0]):
        # path \0 length \0 bytes \0 — length-framed so no path/content boundary can be ambiguous.
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(str(len(data)).encode("ascii"))
        h.update(b"\0")
        h.update(data)
        h.update(b"\0")
    return h.hexdigest()


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print("usage: hash_skill_definitions.py PATH-TO-SKILL-DIR", file=sys.stderr)
        sys.exit(2)
    print(skill_hash(sys.argv[1]))


if __name__ == "__main__":
    main()
