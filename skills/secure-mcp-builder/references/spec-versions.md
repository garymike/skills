# MCP Spec Versions and Forward Compatibility

Snapshot as of July 2026. Verify currency at modelcontextprotocol.io before major decisions; this file states what to check, not eternal truth.

## Current state

- **Stable / build target: 2025-11-25.** Streamable HTTP with optional `Mcp-Session-Id`, initialize handshake, elicitation and sampling defined, OAuth 2.1 authorization spec with RFC 9728 + RFC 8707.
- **2026-07-28 (release candidate, locked 2026-05-21; final expected July 28, 2026):** largest revision since launch. Stateless protocol core. Twelve-month deprecation policy applies to what it retires.

## What 2026-07-28 changes (design for this now)

1. **Sessions removed.** `Mcp-Session-Id` and protocol-level sessions are gone; the initialize/initialized handshake is removed. Protocol version, client info, and capabilities travel in `_meta` per request; `server/discover` serves upfront capability fetch.
2. **New required headers.** Every Streamable HTTP request carries `Mcp-Method` and `Mcp-Name`; servers must reject header/body mismatches. Gateways route on these headers. Never map sensitive values into them.
3. **Multi round-trip requests replace long-lived SSE.** Interactive flows return `InputRequiredResult` with an opaque `requestState` the client echoes back. Treat `requestState` and any handle as untrusted client input: integrity-protect (sign/encrypt), user-bind, and expire it (ST-2).
4. **Tasks becomes an extension** with a polling lifecycle (tools/call returns a handle; clients poll `tasks/get`). Task handles are capability tokens: CSPRNG entropy, user-bound, expiring.
5. **MCP Apps extension**: tools can ship HTML UI rendered in sandboxed iframes. If you adopt it: templates are pre-declared, static, reviewed artifacts; treat any UI as an XSS/UI-mimicry surface; no dynamic HTML from upstream data.
6. **Roots, Sampling, Logging deprecated.** Do not build new dependencies on them. Replace sampling with direct LLM API calls from the server; replace roots with explicit parameters/config.
7. **Schemas lifted to full JSON Schema 2020-12** (composition, `$ref`/`$defs`; root stays `type: object` for inputs). Do not auto-dereference external `$ref` URIs; bound schema depth and validation time (DoS defense).
8. **Auth hardening**: `iss` validation per RFC 9207 required in clients; `application_type` required in DCR; CIMD preferred registration.
9. **Error code change**: missing resource is `-32602`, not `-32002`.
10. **Caching**: list/read results carry `ttlMs` and `cacheScope`; never mark per-user data as shareable scope.

## Build rules

- New servers: build on 2025-11-25 with the official SDK, but keep all state out of sessions, all handles explicit/user-bound/expiring, and no reliance on Roots/Sampling/Logging. That makes the 2026 migration a transport update, not a redesign.
- Statelessness is a security posture, not just scalability: it eliminates protocol-level session hijack but moves the burden onto your handles. A predictable or unbound handle is the new hijack.
- Pin the SDK version; track Tier 1 SDK releases during the validation window; migrate on the SDK, never by hand-rolling transport code.
