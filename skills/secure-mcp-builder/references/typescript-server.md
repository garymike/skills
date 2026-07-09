# TypeScript MCP Server Guide

Stack: official `@modelcontextprotocol/sdk`, Node 20+ LTS, `zod` for schemas, strict TypeScript. Before coding, fetch current SDK docs: https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md.

## Project layout

```
myserver/
├── package.json / package-lock.json   # pinned, npm audit in CI
├── tsconfig.json                      # strict: true
├── src/
│   ├── server.ts                      # McpServer + transport wiring
│   ├── tools/                         # one file per tool group
│   ├── auth.ts                        # bearer validation, principal
│   ├── clients.ts                     # downstream clients, SSRF-safe fetch
│   ├── config.ts                      # env parsing, fail closed
│   └── log.ts                         # structured audit logger, redaction
├── test/                              # vitest unit + abuse cases
├── docs/threat-model.md
└── README.md
```

## Core patterns

**Tools with zod (schema = first validation layer, INP-1).**

```ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({ name: "acme-tickets", version: "1.0.0" });

server.registerTool("tickets_search_issues", {
  title: "Search tickets",
  description: "Search tickets by free text. Use for finding issues; NOT for reading a known ticket (use tickets_get_issue). query e.g. 'login failures'. Returns up to `limit` concise rows plus a cursor.",
  inputSchema: {
    query: z.string().min(1).max(200),
    limit: z.number().int().min(1).max(50).default(10),
    cursor: z.string().optional(),
  },
  annotations: { readOnlyHint: true, openWorldHint: true },
}, async (args, extra) => {
  const principal = requirePrincipal(extra);          // AUTH-4/5
  audit("tool_call", { tool: "tickets_search_issues", user: principal.sub, params: redact(args) });
  const rows = await tickets.search(principal, args);
  return { content: [{ type: "text", text: renderConcise(rows, args.limit) }] };
});
```

**Config, fail closed (SEC-2).** Parse `process.env` through a zod schema with no defaults for security values; throw on failure at startup.

**Token validation (remote, AUTH-1).** `jose` with `createRemoteJWKSet`; verify `iss`, `aud === config.audience`, `exp`; map `sub`/`scope` to a principal; per-tool scope checks. Serve RFC 9728 metadata; 401 with `WWW-Authenticate: Bearer resource_metadata="..."`. Sessions never authenticate (ST-1).

**SSRF-safe fetch (INP-5).** One exported `safeFetch()`: HTTPS only; `dns.lookup` all addresses and reject private/reserved/link-local/metadata ranges (use a maintained checker such as `ipaddr.js`, not regex); connect to the vetted IP with correct SNI/Host; `redirect: "manual"` and re-validate each hop; `AbortSignal.timeout()`; streamed byte cap. Tools never call global `fetch` directly.

**Subprocess (INP-3).** Avoid. If forced: `execFile(BINARY, args, { shell: false, timeout })` with constant binary path and allowlist-validated args. Never `exec` with concatenated strings.

**Paths (INP-4).** `const p = path.resolve(ROOT, userPath); if (!p.startsWith(ROOT + path.sep)) reject;` plus explicit symlink policy via `fs.realpath`.

**Audit logging.** `pino` JSON; **stdio servers log to stderr, never stdout** (stdout carries JSON-RPC); HTTP servers log to stdout. Redaction paths for authorization/token/secret keys (LOG-4); distinct event for denials (LOG-2).

## Transports

- **stdio:** `StdioServerTransport`. No listener; env-based credentials.
- **Streamable HTTP:** run stateless (`sessionIdGenerator: undefined` in current SDK) behind TLS. Cross-call state only as signed, user-bound, expiring handles (ST-2). Validate `Origin`/`Host` if anything ever binds locally (DNS rebinding).

## Lifecycle and persistence

Local servers must not outlive the client. Handle SIGTERM/SIGINT, terminate child processes and timers on shutdown, and never register autostart/daemon persistence the user did not request. A server still running after the client stops is a resource drain and a compromise-persistence foothold. Expose a health/liveness signal so orphaned processes are detectable.

## Testing and CI

- vitest: per-tool happy path, bounds, authz denial; abuse cases from threat-model section 5 (metadata-IP fetch, traversal, wrong-audience JWT, oversize input).
- CI: `npm audit --audit-level=high`, `eslint` with security plugin, `tsc --noEmit`, lockfile enforced (SUP-1).
