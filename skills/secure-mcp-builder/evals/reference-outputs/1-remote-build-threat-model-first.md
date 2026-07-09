# Build plan: internal ticketing MCP server (remote, multi-user, SSO)

We start with Phase 1 — the threat model — before writing any code. Below is the
Phase 1 output and the design decisions that follow from it. Nothing ships until
you approve this summary and the server clears the review gate.

## Phase 1: Scope and threat model (summary)

**Purpose / users:** Remote, multi-user MCP server exposing an internal ticketing
system to engineering-org agents. Agent-facing tools are **read-only**
(`tix_search_tickets`, `tix_get_ticket`); write-back (`tix_add_comment`) is split
to a separate approval-gated path — see the trifecta decision.
**Deployment:** Streamable HTTP (remote), stateless. Users authenticate through
the org SSO / IdP.
**Data classification:** Internal → Confidential (ticket contents can include
security tickets, customer names). Comments are a write path.

### Lethal trifecta assessment

| Leg | Present? | Via |
|---|---|---|
| Access to private data | YES | `tix_search_tickets`, `tix_get_ticket` (internal ticket contents) |
| Exposure to untrusted content | YES | ticket/comment bodies are authored by many people, some external reporters |
| External communication channel | YES | `tix_add_comment` writes back into a system others read |

**All three legs are present.** The reliable control for a lethal trifecta is to
remove a leg, not to trust the model or an approver to catch every injection, so
mitigations are taken in preference order (mirroring the review skill's
`composition-risks.md` ordering, where human-in-the-loop is the *last* resort,
not the first):

1. **Break the leg — make this agent-facing server read-only (recommended
   default).** Ship `tix_search_tickets` and `tix_get_ticket` only. With no
   write-back tool in the agent's reach, a crafted ticket has nowhere to exfiltrate
   *through this server*: the external-comms leg is gone by construction —
   deterministically, not probabilistically.
2. **If commenting is a confirmed hard requirement, isolate the write path.**
   Deliver `tix_add_comment` as a **separate service the agent cannot call inline
   with the reads** — it enqueues a proposed comment for **out-of-band human
   approval** (a reviewer acts in a separate UI). No single agent session then
   holds read-private + untrusted-content + write-back at once; the chain is
   broken at a deterministic control point rather than at the model.
3. **Only if 1 and 2 are ruled out in writing: inline human-in-the-loop + accept
   residual.** Client-side confirmation on the write tool plus audit logging, with
   the residual stated honestly (confirmation fatigues; a crafted ticket can still
   steer a rushed approver) and signed off by a named risk owner. This is the
   weakest option.

**Recommended for this build: option 1** (read-only), escalating to option 2 only
if the comment requirement is confirmed essential. The decision and its owner go
in the threat model.

### MCP-specific attack classes (headlines)

- **Token passthrough / confused deputy:** the server never forwards the client's
  token to the ticketing backend. It is an OAuth 2.1 resource server; downstream
  calls use token exchange so the backend sees the real user (AUTH-2/3/5).
- **Prompt injection via ticket content:** ticket/comment bodies are returned as
  demarcated, labeled data with instruction-markup stripped; no tool acts on
  instructions found inside them (OUT-2).
- **SSRF:** no user-supplied URLs are fetched; the ticketing base URL is fixed
  config. N/A marked with that reason, not skipped.

## Auth decision (Phase 1) — recorded as an ADR

**OAuth 2.1 resource server fronted by the org IdP.** The server publishes
Protected Resource Metadata (RFC 9728), validates every bearer token's signature,
`iss`, `exp`, and **`aud` == this server's resource identifier**, and maps claims
to a principal. It issues no tokens and never sees passwords.

Downstream ticketing auth depends on how the backend is fronted, and that choice
is the auth ADR:

- **If the backend is IdP-protected** (SSO, exposes an IdP resource): use **token
  exchange** (RFC 8693, e.g. an On-Behalf-Of flow) so the backend sees the real
  user (AUTH-3).
- **If the backend uses its own tokens/PATs** (common for hosted SaaS): the server
  holds a **scoped service identity** and re-checks per-user entitlement on every
  call (AUTH-5; auth-patterns Pattern B, option 2), with downstream permissions
  cut to the minimum union actually required.

Either way there is no token passthrough and no shared "god token" whose reach
exceeds a single user (AUTH-2). (AUTH-1/2/3/4/5.)

ADRs to record in the repo: **language** (Python/FastMCP — thin API proxy, default
stack), **transport** (streamable HTTP, stateless), **auth pattern** (resource
server + downstream user-context: token exchange or scoped service identity). Each
as context / alternatives / rationale / consequences.

## Phase 2: Tool design (preview)

**Primary server (read-only — option 1):**

- `tix_search_tickets(query, project?, status?, limit=20, cursor?)` — search-first,
  paginated, `readOnlyHint: true`, `openWorldHint: true`. Returns concise rows
  (key, summary, status, assignee) plus a cursor; not a dump.
- `tix_get_ticket(ticket_key)` — `readOnlyHint: true`. Returns the ticket with body
  demarcated as untrusted data.

**Write path (only if option 2 is adopted — separate service):**

- `tix_add_comment(ticket_key, body)` — a **separate write tool**,
  `readOnlyHint: false`, that **enqueues for out-of-band approval** rather than
  posting inline. Bounded `body` (`maxLength`); the caller's per-ticket entitlement
  is re-checked server-side before the write (AUTH-5). Kept off the read-only
  server so the two capabilities are never co-resident in one agent session.

Namespaced `tix_*` to prevent cross-server collisions / shadowing. Strict
schemas: bounded `limit`, `maxLength` on `query` and `body`,
`additionalProperties: false`.

## Phase 3/4 posture (forward-compatible + gate)

- **Stateless, forward-compatible:** no server-side per-session state; the only
  cross-call state is the search **pagination cursor**, issued as an opaque,
  signed, user-bound, expiring token (ST-2), never a raw offset. No reliance on
  Roots/Sampling/Logging. This makes the 2026-07-28 migration a transport update,
  not a redesign.
- **Implementation** against the security-requirements catalog: server-side input
  validation beyond schema, per-tool scope + per-ticket entitlement checks,
  structured audit log per call (principal, tool, redacted params, status),
  secrets from the secrets manager with fail-closed startup, pinned deps + SBOM.
- **Ship gate:** the completed threat model, the three ADRs, capability + security
  eval scorecards, and the review-gate checklist (reviewer, not the author) are the
  change-request package. The server is registered in your MCP inventory before
  first use (an unregistered server is a finding, not a convenience).

**Next step:** confirm this threat-model summary and auth decision, and I'll
proceed to Phase 2 tool signatures and the Python scaffold.
