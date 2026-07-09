# MCP Security Requirements Catalog

Normative control catalog for first-party MCP servers. MUST items block the review gate. SHOULD items require a documented justification to skip. Mappings: [SPEC] = MCP spec 2025-11-25 security best practices / authorization spec, [MCP10] = OWASP MCP Top 10, [ASI] = OWASP Top 10 for Agentic Applications 2026.

## 1. Authentication and authorization

- **AUTH-1 (MUST)** Remote HTTP servers implement OAuth 2.1 protected-resource behavior: publish Protected Resource Metadata (RFC 9728), validate bearer tokens on every request, and reject any token whose audience is not this server. [SPEC]
- **AUTH-2 (MUST)** No token passthrough. Never accept a token issued for another service, and never forward a client-presented token to a downstream API. [SPEC][MCP10]
- **AUTH-3 (MUST)** For downstream access on behalf of a user, use OAuth token exchange (RFC 8693) or an equivalent mechanism that yields a token scoped to the downstream service while preserving the user as subject. No single broad "god token" shared across users. [SPEC]
- **AUTH-4 (MUST)** Authorization is enforced per request, per user, per tool. Sessions are never used for authentication. [SPEC]
- **AUTH-5 (MUST)** Tools execute with the caller's effective permissions, not the server's. If the server holds elevated credentials, every tool call re-checks that the authenticated user is entitled to the specific resource and action (confused deputy defense). [SPEC][ASI-03]
- **AUTH-6 (MUST)** OAuth proxy patterns implement per-client consent before forwarding to a third-party authorization server; exact-match redirect URI validation; cryptographically random, single-use, short-lived `state` values validated at the callback. [SPEC]
- **AUTH-7 (SHOULD)** Prefer Client ID Metadata Documents (CIMD) over open dynamic client registration for client onboarding. Validate `iss` per RFC 9207 in client-side flows. [SPEC 2026 direction]
- **AUTH-8 (MUST)** Scopes follow least privilege: request and grant only what the toolset needs; separate read scopes from write scopes; time-bound elevated access. [MCP10 scope creep]
- **AUTH-9 (MUST, local stdio)** Local servers use stdio transport. If a local HTTP listener is unavoidable, bind to loopback, require an authorization token, and defend against DNS rebinding (validate Origin/Host headers). [SPEC]
- **AUTH-10 (SHOULD)** Filter tool discovery by authorization: `tools/list` returns only tools the caller's scopes permit, so unauthorized capability is not even advertised. Caveat: a scope-filtered list is per-user data; under 2026-07-28 caching, mark it user-scoped (`cacheScope`), never shareable.

## 2. Input handling and injection defense

- **INP-1 (MUST)** Every tool validates all inputs server-side: type, length bounds, range, format (allowlist patterns), and semantic checks. Schemas set `additionalProperties: false` and constrain string fields (`pattern`, `maxLength`, enums) so only declared parameters in valid formats are accepted. JSON schema is the first layer, never the only layer.
- **INP-2 (MUST)** Database access uses parameterized queries or a vetted ORM. No string-built SQL/NoSQL/LDAP/XPath. [MCP10 injection]
- **INP-3 (MUST)** No shell interpolation. Subprocesses use argv arrays, `shell=False`, an allowlisted binary path, and sanitized argument values. Prefer native libraries over subprocesses.
- **INP-4 (MUST)** Path parameters are canonicalized and confined to an explicit root directory; reject traversal, symlinks escaping the root, and absolute paths outside it.
- **INP-5 (MUST)** URL parameters intended for server-side fetching enforce: HTTPS only (loopback exempt in dev), deny private/reserved/link-local ranges including cloud metadata (169.254.169.254), resolve-then-pin DNS to defeat TOCTOU rebinding, validate every redirect hop, and cap response size and time. Use a maintained SSRF-safe fetching layer, not hand-rolled IP parsing. [SPEC SSRF]
- **INP-6 (MUST)** Bound resource consumption per call: max input size, max output size, execution timeout, and concurrency limits.

## 3. Output handling and context safety

- **OUT-1 (MUST)** Tool results never include secrets, tokens, internal hostnames, stack traces, or other environment details. Error messages are actionable but sanitized.
- **OUT-2 (MUST)** Upstream content returned to the model is treated as untrusted data. Wrap fetched content in clear delimiters, label its origin, and strip or escape instruction-markup tags (`<system>`, `<IMPORTANT>`, `<instructions>` and similar) before returning. Remember outputs become inputs: other tools may consume them, so unsanitized output can cause downstream SSRF or command injection, not only prompt injection. Never allow upstream content to alter tool names, descriptions, or schemas at runtime (schema poisoning / rug pull defense). [MCP10 tool poisoning][ASI-01]
- **OUT-3 (MUST)** Tool descriptions and annotations are static, reviewed artifacts under version control. Any change to a tool description is a code change requiring review (defends the description-as-injection-vector).
- **OUT-4 (SHOULD)** Truncate and paginate large results; give the agent filters instead of dumps. Context flooding is both a cost and a security problem (it buries injected content and evades review).
- **OUT-5 (SHOULD)** Minimize what tools return, not just how much: explicit field allowlists per tool (no SELECT-star pass-through of backing records), and DLP-style redaction of PII/secrets patterns in responses where the backing system holds sensitive data beyond the tool's stated purpose. Data the model never sees cannot be exfiltrated by it.

## 4. Sessions, state, and transport

- **ST-1 (MUST)** No security decision ever depends on a session ID. If sessions exist (pre-2026 transports), IDs are generated from a CSPRNG, bound server-side to the authenticated user (key format `user_id:session_id`), expiring, and revocable. [SPEC session hijacking]
- **ST-2 (MUST)** Design stateless-first: any cross-call state is an explicit, opaque handle that is user-bound, expiring, and validated on use. Handles are capability tokens; treat them like credentials. [2026-07-28 direction]
- **ST-3 (MUST)** TLS 1.2+ on all remote transports; HSTS on public endpoints. Where a gateway/proxy fronts the server, or in service-to-service deployments, prefer mutual TLS (mTLS) — both peers present signed certificates — so unauthenticated components cannot reach the server.
- **ST-4 (SHOULD, high-assurance)** Message-level integrity beyond TLS: sign JSON-RPC payloads with an identity-bound asymmetric key, include a unique nonce and timestamp per message, reject duplicates and stale timestamps (replay defense), verify mutually, and fail closed on any verification failure. TLS does not protect against tampering after termination; adopt this where proxies or middleware sit between TLS termination and the server, or where regulatory assurance demands it. Beyond current spec requirements and needs client cooperation; document the decision either way in the threat model.

## 5. Secrets and configuration

- **SEC-1 (MUST)** Secrets come from environment variables or a secrets manager. Never in source, repo config, container images, tool descriptions, or logs. [MCP10 token exposure]
- **SEC-2 (MUST)** Startup validates configuration and fails closed on missing/invalid security-relevant settings.
- **SEC-3 (SHOULD)** Prefer short-lived, automatically rotated credentials (workload identity, managed identity, or secrets-manager dynamic secrets) over static API keys.
- **SEC-4 (MUST)** Distinct credentials per environment (dev/test/prod) AND per server; a downstream credential is never shared across multiple MCP servers. Production credentials never leave production.

## 6. Logging, monitoring, and audit

- **LOG-1 (MUST)** Structured (JSON) audit log per tool invocation: timestamp, authenticated principal, client identity, tool name, parameter summary with secrets/PII redacted, decision (allow/deny), result status, duration.
- **LOG-2 (MUST)** Authorization denials, validation failures, rate-limit hits, and SSRF blocks are logged as security events distinguishable from operational errors.
- **LOG-3 (SHOULD)** Ship logs to the SIEM; include a correlation/trace ID propagated from the client where available (W3C Trace Context in `_meta` under the 2026 spec).
- **LOG-4 (MUST)** Logs never contain bearer tokens, authorization codes, or full request bodies containing sensitive data. [MCP10]
- **LOG-5 (SHOULD)** Detect and alert on instruction-like patterns in tool responses (imperative injection phrasing such as "ignore previous", "send to") as an early tool-poisoning/injection signal.

## 7. Supply chain and deployment

- **SUP-1 (MUST)** Dependencies pinned with a lockfile; automated vulnerability scanning (e.g. pip-audit/npm audit or org scanner) and SAST in CI; builds reproducible.
- **SUP-2 (MUST)** Generate an SBOM per release; sign or hash-attest release artifacts (e.g. Sigstore/cosign, or SLSA provenance) so consumers can verify authorship and pin by digest with an integrity guarantee. CI rejects unsigned artifacts.
- **SUP-3 (MUST)** Containerized servers run as non-root, read-only filesystem where possible, minimal base image, no docker socket, and an explicit default-deny egress allowlist. Disable privilege escalation (`no-new-privileges`, drop Linux capabilities) and attach a seccomp profile (plus AppArmor/SELinux where available) to shrink the kernel syscall surface. Set CPU and memory limits so a compromised server cannot crypto-mine or run up a denial-of-wallet bill.
- **SUP-4 (MUST)** The server is registered in your MCP server inventory with owner, data classification, scopes, and deployment location. Unregistered servers are shadow MCP servers and are treated as incidents. [MCP10 shadow servers]
- **SUP-5 (SHOULD)** Version tools and the server semantically; breaking tool changes follow a deprecation window so clients are not silently retrained onto different behavior (rug pull defense).
- **SUP-6 (SHOULD)** Publish a canonical tool-definition manifest per release: a SHA-256 per tool over its name, description, input/output schemas, and annotations, plus a set hash over all tools. Compute it with `scripts/hash_tool_definitions.py`, which pins the canonicalization (sorted keys, UTF-8, no whitespace, tools sorted by name) so the manifest is reproducible and matches what an assessor recomputes with the identical script in mcp-security-review. Lets clients and gateways pin definitions and detect post-approval mutation, including annotation flips; any manifest change is a versioned, announced release, never a silent update.

## 8. Agentic composition risks

- **AGT-1 (MUST)** Apply the lethal trifecta test (private data + untrusted content + external comms) at design time and whenever tools are added. Document the outcome in the threat model.
- **AGT-2 (MUST)** Destructive or irreversible tools (`destructiveHint: true`) are separate tools, never side effects, and are designed to work with client-side human confirmation.
- **AGT-3 (SHOULD)** Where the server both fetches untrusted content and can write/send, add server-side guardrails (e.g. recipient allowlists, egress restrictions, content checks) rather than relying solely on the model to resist injection. [ASI-01 goal hijack]
- **AGT-4 (SHOULD)** Expose the minimum viable toolset. Every additional tool expands the attack surface a compromised or confused agent can drive.

## Sources and further reading

Primary sources this catalog derives from; consult when a control needs deeper context or you want onboarding material:

- MCP Security Best Practices (official spec): modelcontextprotocol.io/docs/tutorials/security/security_best_practices
- MCP Authorization specification: modelcontextprotocol.io/specification/latest/basic/authorization
- OWASP MCP Security Cheat Sheet: cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html
- OWASP MCP Top 10: owasp.org/www-project-mcp-top-10
- OWASP Top 10 for Agentic Applications 2026: genai.owasp.org
- Wiz, Model Context Protocol (MCP) security best practices (cheat sheet): wiz.io — supply-chain signing, least privilege, sandboxing (non-root/seccomp/egress/quotas), gateway controls (informs SUP-2/3, ST-3)
- OAuth 2.0 Security Best Current Practice: RFC 9700
- Anthropic, Writing effective tools for agents: anthropic.com/engineering/writing-tools-for-agents
