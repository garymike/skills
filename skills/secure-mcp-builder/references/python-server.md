# Python MCP Server Guide (default stack)

Stack: official `mcp` SDK (FastMCP API), Python 3.11+, `pydantic` for models, `httpx` for outbound calls, `uv` or pip-tools for pinned deps. Before coding, fetch current SDK docs: https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md (APIs move; verify signatures).

## Project layout

```
myserver/
├── pyproject.toml            # pinned deps, tool config (ruff, mypy, pytest, pip-audit)
├── uv.lock
├── src/myserver/
│   ├── server.py             # FastMCP app, transport wiring only
│   ├── tools/                # one module per tool group
│   ├── auth.py               # token validation, principal mapping (remote)
│   ├── clients.py            # downstream API clients, SSRF-safe fetcher
│   ├── config.py             # pydantic-settings, fail-closed validation
│   └── logging.py            # structured audit logger, redaction
├── tests/                    # unit + abuse cases from the threat model
├── docs/threat-model.md
└── README.md                 # config, scopes, deployment, inventory entry
```

## Core patterns

**Server and tools.** Register tools with typed signatures; pydantic models give the schema. Keep handlers thin: validate → authorize → call client → shape result.

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("acme-tickets")

class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=200, description="Free-text search, e.g. 'login failures'")
    limit: int = Field(default=10, ge=1, le=50)
    cursor: str | None = None

@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def tickets_search_issues(params: SearchIn, ctx) -> str:
    principal = require_principal(ctx)                 # AUTH-4/5
    audit.info("tool_call", tool="tickets_search_issues", user=principal.sub,
               params=redact(params))
    rows = await tickets.search(principal, params)     # entitlement enforced in client
    return render_concise(rows, params.limit)
```

**Config, fail closed (SEC-2).**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    issuer: str
    audience: str
    tickets_base_url: str
    # no defaults for security-relevant values; missing -> startup crash

settings = Settings()  # raises if incomplete
```

**Token validation (remote, AUTH-1).** Use a maintained JOSE lib (`joserfc`/`pyjwt` with JWKS caching). Validate signature, `iss`, `exp`, `nbf`, and `aud == settings.audience`; extract `sub` and `scope`; enforce scopes per tool. Serve RFC 9728 metadata and the 401 `WWW-Authenticate` challenge. Never authenticate via session (ST-1).

**SSRF-safe fetch (INP-5).** Central fetcher in `clients.py`: HTTPS-only, allowlist hosts where the tool's purpose permits, resolve DNS then connect to the pinned IP, reject private/reserved/link-local/metadata ranges using the `ipaddress` stdlib on every resolved address, cap redirects and validate each hop, `timeout=`, `max_bytes` streaming cap. No tool calls `httpx.get` directly.

**Subprocess (INP-3).** Avoid. If forced: `subprocess.run([BINARY, *args], shell=False, timeout=..., env=minimal_env)` with `BINARY` a constant absolute path and every arg validated against an allowlist pattern.

**Paths (INP-4).** `resolved = (ROOT / user_path).resolve(); resolved.relative_to(ROOT)` inside try/except; reject on failure; check `is_symlink()` policy explicitly.

**Audit logging (LOG-1/2/4).** `structlog` JSON. Destination depends on transport: **stdio servers must never write logs to stdout** (it corrupts the JSON-RPC stream); log to stderr or a file. HTTP servers log JSON to stdout for the collector. A `redact()` helper strips values for keys matching token/secret/password/authorization patterns before logging; security denials use a distinct event name.

**Errors.** Raise a domain error; a single exception handler converts to agent-actionable messages (tool-design.md) and logs the full detail server-side only.

## Transports

- **stdio (local):** `mcp.run(transport="stdio")`. No listener. Credentials via env (SEC-1).
- **Streamable HTTP (remote):** run stateless (`stateless_http=True` where the SDK supports it) behind TLS. No in-memory per-session dicts; cross-call state is signed, user-bound, expiring handles (ST-2).

## Lifecycle and persistence

Local servers must not outlive the client. Handle shutdown signals (SIGTERM/SIGINT), terminate child processes and background tasks, and never register autostart/daemon persistence a user did not ask for. A server that keeps running after the client stops is a resource drain and a compromise-persistence foothold. Expose a health/liveness signal so orphaned processes are detectable.

## Testing

- Unit tests per tool: happy path, each validation bound, authz denial.
- Abuse tests generated from threat-model section 5: SSRF probes (metadata IP, redirect-to-internal, DNS-rebind stub), traversal payloads, oversized inputs, SQL/command injection strings, wrong-audience JWT, expired token, missing scope.
- `pip-audit`, `ruff`, `mypy --strict`, and `bandit` in CI; lockfile drift fails the build (SUP-1).
