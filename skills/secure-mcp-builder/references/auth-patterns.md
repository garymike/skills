# Authorization Patterns for MCP Servers

Decision guide and implementation patterns. Read in Phase 1. Normative controls live in security-requirements.md (AUTH-*).

## Decision tree

1. **Local stdio, single user, no network listener** → No OAuth. Credentials for downstream systems come from the user's environment/secret manager, scoped to that user. Harden per AUTH-9, SEC-*, and the local-compromise guidance below.
2. **Remote HTTP, single organization, users have an IdP** → OAuth 2.1 resource server fronted by your IdP (any OAuth 2.1 / OIDC provider — e.g. Entra ID, Okta, Auth0, Keycloak). This is the default for remote servers. Do not build your own authorization server.
3. **Remote HTTP, acting as a proxy to a third-party API with its own OAuth** → OAuth proxy pattern. Highest-risk shape; implement the confused deputy defenses (AUTH-6) exactly as specified.

## Pattern A: Resource server (default for remote)

The MCP server is an OAuth 2.1 protected resource. It never sees passwords and does not issue tokens. OAuth 2.1 baseline applies throughout: PKCE mandatory on authorization code flows, no implicit grant, exact redirect URIs.

- Serve **Protected Resource Metadata** (RFC 9728) at `/.well-known/oauth-protected-resource`, pointing at the authorization server(s).
- On 401, return `WWW-Authenticate` with the `resource_metadata` URL so clients can discover the AS.
- Validate on every request: signature against AS JWKS (cached with rotation), `iss`, `exp`/`nbf`, and **`aud` equals this server's canonical resource identifier**. Clients send `resource` (RFC 8707) when requesting tokens; you enforce that the resulting audience is you. Reject valid-but-wrong-audience tokens; that is the point.
- Map token claims to an internal principal; enforce per-tool scope checks (`scope` claim) and per-resource entitlement checks (AUTH-5).
- Accept tokens only via `Authorization: Bearer`; never via query strings; never log them.

## Pattern B: Downstream access with user context

The server needs to call downstream APIs as the user. Two acceptable shapes:

1. **Token exchange (RFC 8693)**: exchange the inbound access token at the AS for a new token with `audience` = downstream API, subject = the same user. Preserves identity through every hop; downstream logs show the real user. Preferred whenever the IdP supports it (e.g. Microsoft Entra's On-Behalf-Of flow).
2. **Scoped service identity + enforced user context**: the server uses its own workload identity for the downstream call but passes the verified user identity and re-checks entitlement per call (AUTH-5), and downstream permissions for the service identity are cut to the minimum union actually required. Use only when token exchange is unavailable; document it in the threat model as a confused deputy risk with mitigations.

Never acceptable: forwarding the inbound token to the downstream API (AUTH-2), or one broad credential whose reach exceeds what any single user should touch.

## Pattern C: OAuth proxy to a third-party API

Applies when the server holds a static client ID at a third-party AS while serving many MCP clients.

- Maintain per-user, per-client_id consent records; show a server-owned consent page (client name, scopes, redirect URI) **before** redirecting to the third party.
- Exact string match on redirect URIs; no wildcards, no pattern matching.
- `state`: CSPRNG-generated, stored server-side only after consent approval, single-use, ~10 minute expiry, validated at callback; reject missing/mismatched.
- Consent cookies: `__Host-` prefix, `Secure`, `HttpOnly`, `SameSite=Lax`, signed, bound to client_id.
- Consent page sets `frame-ancestors 'none'` / `X-Frame-Options: DENY`.
- Store third-party refresh tokens encrypted at rest, keyed to the user, never returned to clients.

## Client registration

Prefer **Client ID Metadata Documents (CIMD)** where supported: the client_id is an HTTPS URL to a metadata document, removing the open registration endpoint that legacy Dynamic Client Registration requires. If legacy DCR must be supported, rate-limit it, expire unused registrations, and require `application_type` and exact redirect URIs. Validate `iss` on authorization responses (RFC 9207) in any client-side code.

## Local stdio credential hygiene

- Downstream credentials from env vars injected by the user's secret manager; never a dotfile committed to a repo.
- The server process runs as the user; do not require or use sudo.
- If a helper HTTP port is unavoidable: loopback bind, random per-launch token required on every request, and Host/Origin validation (DNS rebinding defense).
- Document exactly which commands run at startup so client consent screens can display them truthfully.

## Deployment topology: gateway in front, controls still inside

For remote servers, front the fleet with a gateway (API gateway or MCP-aware gateway): central TLS termination, coarse rate limiting, IP/geo policy, request size caps, traffic logging, and a single chokepoint for the SOC. Enforce mutual TLS (mTLS) between the gateway and each server so servers accept traffic only from the gateway (never direct, unauthenticated hits), and have the gateway refuse any server whose image digest isn't on the allowlist. Under the 2026-07-28 spec, gateways route on the `Mcp-Method`/`Mcp-Name` headers, so tool-level policy at the edge gets cheap.

Hard caveat: the gateway complements in-server controls and never replaces them. Token audience validation, per-tool scope checks, per-resource entitlement, input validation, and SSRF controls are the server's job; a gateway cannot see enough context to enforce them, and a gateway bypass (or east-west traffic) must not equal a security bypass. Design every server to be safe if hit directly, then add the gateway as depth.

## Human-in-the-loop

Destructive tools rely on client-side confirmation (elicitation) driven by honest `destructiveHint` annotations. For high-impact operations, add server-side controls that do not trust the client: two-step commit tokens (propose returns a handle, confirm consumes it, handle is user-bound and short-lived), or approval via an out-of-band channel.
