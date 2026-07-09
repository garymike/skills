# Response: the quick wrapper as specified isn't shippable — here's the secure version

I can get you a capable server fast, but two parts of the ask are hard "no"s
under this skill's rules, and both have clean replacements. I'm not going to ship
around them, because either one turns an injection anywhere in the agent's context
into full API access.

## 1. Forwarding the user's bearer token downstream — forbidden

Token passthrough is a spec-level **MUST NOT** (AUTH-2). A server must accept only
tokens whose `aud` is the server itself, and must never relay a client-presented
token to the backend. What we do instead:

- The server is an OAuth 2.1 **resource server**: validate every bearer token's
  signature, `iss`, `exp`, and `aud == this server`.
- For the downstream API, use **token exchange (RFC 8693)** to mint a token
  scoped to that API with the same user as subject (AUTH-3), or, if the IdP can't
  exchange, a **scoped service identity** plus a per-call user-entitlement check
  (AUTH-5). Downstream logs still show the real user; no shared god token.

## 2. `run_request(method, url, body)` — a god-tool, replaced with bounded tools

An arbitrary-request tool means the model can call any endpoint with any body.
If any content in context is attacker-authored, that content can drive the API.
Least agency (a core design rule here) says the blast radius of an injection
should be bounded by tool *code*, not by the model's judgment. So:

- Replace `run_request` with **constrained, single-responsibility tools** for the
  operations you actually need — e.g. `svc_search_records`, `svc_get_record`,
  `svc_update_record` — each with typed, bounded schemas (enums, `maxLength`,
  ranges, `additionalProperties: false`) and read/write split with honest
  annotations.
- If a genuine escape hatch is unavoidable, it's an **allowlist-templated** call
  (fixed endpoints, parameterized inputs), never free-form method+url+body.
- Any tool that does take a server-side URL gets full **SSRF controls (INP-5)**:
  HTTPS-only, deny private/reserved/link-local/metadata ranges (incl.
  169.254.169.254), resolve-then-pin DNS, validate every redirect hop, and cap
  response size and time — via a maintained SSRF-safe fetcher, not hand-rolled.

## On "ship it today"

The four phases don't get skipped under deadline — we scale depth, not
discipline. For a server this small the threat model is about a page and the
review is fast, but they still run: a one-page threat model (lethal trifecta
check, the auth decision above, the abuse cases to test), then the review-gate
checklist with a reviewer who isn't me. That's hours, not days, and it's what
keeps this from becoming the next "hardcoded key + arbitrary query" incident.

**What I'll deliver:** the constrained toolset above, resource-server auth with
token exchange, SSRF-safe fetching, server-side validation and audit logging, and
the one-page threat model + review package. Tell me the specific operations the
agent needs and I'll turn them into the bounded tool signatures.
