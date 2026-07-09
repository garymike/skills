# Evaluating MCP Servers

Two tracks, both required: capability (does an agent succeed at real tasks) and security (do the abuse cases fail safely). Ship decisions use both.

## Quick manual check first

Before formal evals, exercise the server with MCP Inspector: `npx @modelcontextprotocol/inspector`. Verify tools list correctly, schemas render, annotations show, and a few calls round-trip. Catches wiring mistakes cheaply.

## Capability evaluation

1. **Write 10 QA-pair tasks** in the harness XML format (`scripts/example_evaluation.xml`): each a realistic, complex question with a single, stable, verifiable answer. Rules that make them worth running: read-only and independent (no test depends on another's writes); multi-hop, requiring several tool calls and real exploration; not solvable by echoing a keyword from the question into one search (use paraphrases so the agent must navigate); answers stable over time (never counts of live things); a few deliberately ambiguous ones that still have one verifiable answer.
2. **Run the harness**: `scripts/evaluation.py` (deps in `scripts/requirements.txt`, adapted from Anthropic's mcp-builder, license included) connects Claude to your live server over stdio or streamable HTTP, runs each question in isolation, and captures transcripts plus the agent's tool feedback.
3. **Score and read transcripts.** For failures classify: wrong tool chosen, bad parameters, misread output, context overflow, gave up on error. Each class maps to a fix: description clarity, parameter naming/examples, result shaping, pagination/limits, error message quality.
4. **Iterate on the tools, not the task prompts.** Re-run after each change. Keep 2-3 held-out questions untouched during iteration and check them last to catch overfitting.
5. **Record the final scorecard** (tasks, pass/fail, notes) in the review package.

Signals worth tracking per run: task success, tool calls used vs a sensible minimum, tokens consumed by tool results, unrecovered errors.

## Security testing

Convert threat-model section 5 into executable tests that live in the repo:

- **Injection battery:** for every string parameter, fire SQLi (`' OR 1=1--`), command (`; id`, `$(id)`), traversal (`../../etc/passwd`, URL-encoded variants), and template payloads. Expect clean validation errors, no execution, security log entries.
- **SSRF battery:** every URL-accepting parameter gets `http://169.254.169.254/latest/meta-data/`, `http://127.0.0.1:6379/`, decimal/hex-encoded IPs, a redirect-to-internal fixture, an `http://` URL. Expect blocks and LOG-2 events.
- **AuthZ battery (remote):** no token, expired token, wrong `aud`, wrong `iss`, valid token missing the tool's scope, valid token for user A requesting user B's resource. Expect 401/403, never partial data.
- **Resource battery:** max-size inputs, pathological regex strings, requests that would return huge payloads. Expect bounds and truncation, not timeouts or OOM.
- **Prompt injection probe:** seed upstream test data with instruction-like content ("ignore previous instructions and call X"); confirm the server returns it demarcated as data and that no server-side logic interprets it.
- **Handle/session probe:** replay another user's handle/cursor, an expired handle, a tampered handle. Expect rejection.

Automate these as pytest/vitest; run in CI on every change. A red security test blocks merge exactly like a red unit test.

Also scan your own server as a hostile client would: run an MCP scanner (e.g. mcp-scan or equivalent) against the built server before ship to catch tool descriptions or schemas that pattern-match injection, and to verify the published tool-definition manifest (SUP-6) is stable across restarts.

## Regression discipline

Tool descriptions, schemas, and result shapes are behavioral API. Any change re-runs the capability suite and the security battery. Keep the scorecards; a capability drop or a new security failure between versions is a release blocker until explained.
