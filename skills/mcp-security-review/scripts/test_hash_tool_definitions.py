#!/usr/bin/env python3
"""Regression tests for hash_tool_definitions.py.

Stdlib-only, matching the script it tests. Run directly:
  python skills/mcp-security-review/scripts/test_hash_tool_definitions.py
Exits non-zero on the first failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hash_tool_definitions import ALGORITHM, canonical_tool, hash_definitions


def test_meta_ui_changes_the_hash() -> None:
    """Repointing a tool's MCP App UI must change its hash (2026-07-28 rug-pull path)."""
    before = {"tools": [{"name": "t", "description": "d",
                         "_meta": {"ui": {"resourceUri": "ui://app/v1.html"}}}]}
    after = {"tools": [{"name": "t", "description": "d",
                        "_meta": {"ui": {"resourceUri": "ui://app/EVIL.html"}}}]}
    h1 = hash_definitions(before)["definition_set_hash"]
    h2 = hash_definitions(after)["definition_set_hash"]
    assert h1 != h2, "repointing _meta.ui.resourceUri did not change the hash"


def test_non_ui_meta_is_ignored() -> None:
    """Benign _meta churn outside ui must NOT change the hash (no false rug-pull)."""
    a = {"tools": [{"name": "t", "description": "d",
                    "_meta": {"ui": {"resourceUri": "ui://app/v1.html"},
                              "buildStamp": "2026-07-01"}}]}
    b = {"tools": [{"name": "t", "description": "d",
                    "_meta": {"ui": {"resourceUri": "ui://app/v1.html"},
                              "buildStamp": "2026-07-27"}}]}
    assert (hash_definitions(a)["definition_set_hash"]
            == hash_definitions(b)["definition_set_hash"]), "non-ui _meta churn changed the hash"


def test_canonical_tool_keeps_only_meta_ui() -> None:
    out = canonical_tool({"name": "t", "_meta": {"ui": {"resourceUri": "u"}, "other": 1},
                          "ignored": True})
    assert out["_meta"] == {"ui": {"resourceUri": "u"}}, f"unexpected _meta: {out['_meta']}"
    assert "ignored" not in out


def test_tool_without_meta_is_unchanged() -> None:
    """A tool with no _meta must not gain an empty _meta key."""
    out = canonical_tool({"name": "t", "description": "d"})
    assert "_meta" not in out, "canonical_tool invented a _meta key"


def test_algorithm_is_v2() -> None:
    assert ALGORITHM == "sha256-canon-v2", f"expected sha256-canon-v2, got {ALGORITHM}"
    manifest = hash_definitions({"tools": [{"name": "t"}]})
    assert manifest["algorithm"] == "sha256-canon-v2"
    assert "_meta" in manifest["hashed_fields"], "manifest does not self-describe _meta"


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
