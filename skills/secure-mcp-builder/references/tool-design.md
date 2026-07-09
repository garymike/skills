# Designing MCP Tools for Agents

Tools are contracts between deterministic systems and a non-deterministic agent. Optimize for how a model selects, calls, and recovers, not for how a developer would read an API. Read before writing tool signatures (Phase 2).

## Tool selection and shape

- **High leverage over thin wrappers.** Do not mirror every REST endpoint 1:1. Choose the operations agents actually need, and add workflow tools where one call replaces a brittle multi-call dance. When in doubt for wide audiences, favor comprehensive coverage of core operations plus a small number of workflow tools; agents compose the rest.
- **Minimum viable toolset, no god-tools.** If a human engineer cannot say which of two tools applies, the agent cannot either — merge or remove ambiguous tools. Never ship arbitrary-capability tools on wide-audience servers (`run_sql(query)`, `execute_shell(cmd)`, `http_request(anything)`): an injection's blast radius is bounded by the tool's code, so keep each tool single-responsibility and constrained.
- **Search over list-all.** `x_search(query, filters, limit, cursor)` beats `x_list_everything()`. Always paginate; default limits small; return a cursor.
- **Separate reads from writes from destroys.** One tool, one risk class. This lets annotations, scopes, and consent do their job.
- **Segment by sensitivity.** High-sensitivity capability (payments, PII access, credential or auth management) gets its own server with its own credentials, scopes, and review cadence; never mixed into a general-purpose server where a poisoned co-resident tool or over-broad scope can reach it.

## Naming

- Server names: `{service}_mcp` for Python packages, `{service}-mcp-server` for TypeScript; descriptive, no version numbers.
- Tool pattern: `<service>_<verb>_<noun>` (`tix_search_tickets`, `vault_read_secret`). Consistent prefixes across the server; verbs from a small controlled set (get, search, create, update, delete, run).
- Names must be unambiguous across servers a client might co-load. Namespacing is also the defense against tool shadowing by a hostile co-installed server.

## Descriptions (load-bearing prompt engineering)

Include, in this order: one-sentence purpose; when to use it; when NOT to use it (and which tool to use instead); parameter notes with concrete format examples; response shape summary; cost/latency/rate-limit notes for expensive tools. Refine descriptions from evaluation transcripts; small wording changes move success rates materially. Descriptions are static, reviewed, version-controlled artifacts (OUT-3).

## Parameters

- Unambiguous names (`user_id` not `user`; `start_date_iso` with example `2026-07-02`).
- Strict schemas: enums for closed sets, min/max, maxLength, patterns. Stay within JSON Schema draft 2020-12 features supported by mainstream clients; keep the root `type: object`.
- Optional `response_format: "concise" | "detailed"` on read tools; concise default.
- Avoid parameters the agent must guess (internal numeric IDs with no discovery path). Provide a search tool that returns those IDs alongside human-readable fields.

## Results

- Return human-readable context, not bare IDs: names, titles, statuses alongside identifiers.
- Two formatting axes, both useful: verbosity (`concise`/`detailed`) and structure (`markdown` for human-readable defaults, `json` for programmatic processing). Pick the combination that evaluates best; be consistent per server.
- Paginated tools return metadata the agent can act on: `has_more`, `next_cursor`/`next_offset`, `total_count`. Never load an entire dataset into memory to slice it.
- Truncate with an explicit marker and guidance ("50 more results; refine with the `project` filter or pass cursor=...").
- On empty results, say what was searched and suggest the next move.
- Populate `structuredContent`/`outputSchema` when clients can exploit it, mirrored by a text rendering for those that cannot.

## Errors agents can act on

Report tool failures inside the result (`isError: true` with content), not as protocol-level errors; protocol errors are for transport/protocol faults. Bad: `Error 400`. Good: `Invalid date format for start_date_iso: got "07/02/2026", expected YYYY-MM-DD, e.g. 2026-07-02.` State what failed, why, and the corrected call. Keep internals out (OUT-1). Distinguish retryable (rate limit, timeout, include backoff hint) from non-retryable (validation, authorization) so agents do not loop.

## Annotations

Set honestly on every tool: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`, plus a human `title`. Clients build consent UX from these; a write tool marked read-only is a security defect, not a UX bug. The converse also holds: annotations are hints, not guarantees, and nothing enforces that clients honor them. Server-side authorization, validation, and guardrails must stand on their own with zero trust in annotation-driven client behavior.

## Context economy

The agent's context window is a shared, finite production resource. Default-limit result counts and sizes; provide filters; prefer references/handles plus a fetch tool over inlining large blobs; support pagination everywhere. Token bloat degrades agent reasoning and buries injected content where humans will not see it.

## Evaluation-driven iteration

Prototype fast, then build realistic multi-step tasks and measure (see evaluation.md). Read transcripts for where the agent stalls, picks the wrong tool, or misparses output; fix the tool, not the prompt. Re-run. Hold out a test set to avoid overfitting descriptions to your scenarios.
