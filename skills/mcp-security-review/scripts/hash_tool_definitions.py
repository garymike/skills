#!/usr/bin/env python3
"""Deterministic SHA-256 hashing of an MCP server's tool-definition set.

Both secure-mcp-builder (publishing a per-release manifest, SUP-6) and
mcp-security-review (recording and later re-checking the definition hash for
rug-pull detection, Part B / onboarding-monitoring) must compute *byte-identical*
hashes for the same definitions, or the post-approval-mutation control is
meaningless. This module pins the canonicalization so any two parties agree.

IMPORTANT: this file is duplicated verbatim in both skills' `scripts/` folders.
The two copies MUST stay identical; if you change the algorithm here, change it
there too and bump ALGORITHM.

Canonicalization (do not change without bumping ALGORITHM):
  1. For each tool keep exactly the security-relevant fields, when present:
     name, description, inputSchema, outputSchema, annotations. (Annotations are
     included on purpose: an annotation flip, e.g. destructiveHint true -> false,
     is a rug-pull signal and must change the hash.)
  2. Serialize with sorted keys (recursively), UTF-8, and no insignificant
     whitespace: json.dumps(obj, sort_keys=True, separators=(",", ":"),
     ensure_ascii=False). This is JSON-Canonicalization-style; for cross-language
     interop prefer a full RFC 8785 (JCS) implementation, but every party using
     THIS script agrees, which is the requirement here.
  3. Sort tools by name; the set form is the JSON array of the per-tool canonical
     objects, serialized the same way.
  4. SHA-256 the UTF-8 bytes; report as "sha256:<hex>".

Input: a JSON document that is either an MCP tools/list result
({"tools": [...]}), a bare array of tool objects, or a single tool object.
Reads stdin when no path is given.

Usage:
  python hash_tool_definitions.py tools.json
  python hash_tool_definitions.py --set-hash-only tools.json
  some_mcp_client --list-tools | python hash_tool_definitions.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ALGORITHM = "sha256-canon-v1"
HASHED_FIELDS = ("name", "description", "inputSchema", "outputSchema", "annotations")


def _canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Reduce a tool object to the security-relevant fields we hash."""
    if not isinstance(tool, dict):
        raise ValueError(f"tool entry is not an object: {tool!r}")
    return {k: tool[k] for k in HASHED_FIELDS if k in tool}


def extract_tools(payload: Any) -> list[dict[str, Any]]:
    """Accept a tools/list result, a bare tool array, or a single tool object."""
    if isinstance(payload, dict) and "tools" in payload:
        tools = payload["tools"]
    elif isinstance(payload, list):
        tools = payload
    elif isinstance(payload, dict) and "name" in payload:
        tools = [payload]
    else:
        raise ValueError(
            "input is not a tools/list result, a tool array, or a tool object"
        )
    if not isinstance(tools, list):
        raise ValueError("'tools' must be an array")
    return tools


def hash_definitions(payload: Any) -> dict[str, Any]:
    raw_tools = extract_tools(payload)
    tools = [canonical_tool(t) for t in raw_tools]
    names = [t.get("name", "") for t in tools]
    tools_sorted = sorted(tools, key=lambda t: t.get("name", ""))
    per_tool = [
        {"name": t.get("name", ""), "hash": _sha256(_canonical_bytes(t))}
        for t in tools_sorted
    ]
    return {
        "algorithm": ALGORITHM,
        "hashed_fields": list(HASHED_FIELDS),
        "tool_count": len(tools_sorted),
        "duplicate_names": sorted({n for n in names if names.count(n) > 1}),
        "tools": per_tool,
        "definition_set_hash": _sha256(_canonical_bytes(tools_sorted)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministically hash an MCP tool-definition set (SUP-6 / review Part B)."
    )
    parser.add_argument(
        "path", nargs="?", type=Path, help="JSON file; reads stdin if omitted"
    )
    parser.add_argument(
        "--set-hash-only",
        action="store_true",
        help="Print only the definition_set_hash",
    )
    args = parser.parse_args()

    try:
        raw = args.path.read_text(encoding="utf-8") if args.path else sys.stdin.read()
        payload = json.loads(raw)
        result = hash_definitions(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.set_hash_only:
        print(result["definition_set_hash"])
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["duplicate_names"]:
        print(
            f"warning: duplicate tool names present, hashes may not disambiguate them: {result['duplicate_names']}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
