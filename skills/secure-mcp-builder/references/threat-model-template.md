# MCP Server Threat Model Template

Complete this document in Phase 1 for every server. Fill every section; write "N/A because ..." rather than deleting. The completed file lives in the server repo at `docs/threat-model.md` and is part of the review package.

---

# Threat Model: <server name>

**Owner:** | **Date:** | **Version:** | **Reviewer:**

## 1. System description

- Purpose and target users (who connects, from which clients):
- Deployment model: stdio (local) / streamable HTTP (remote) / both
- Trust boundaries diagram or list. At minimum three boundaries exist: user↔client, client↔this server, server↔downstream systems.
- Downstream systems and the credentials used to reach each:
- Data classification of everything readable/writable through tools (public / internal / confidential / restricted):
- Tool inventory table: name, read/write/destructive, scopes required, annotations.

## 2. Lethal trifecta assessment

| Leg | Present? | Via which tools |
|---|---|---|
| Access to private data | | |
| Exposure to untrusted content | | |
| External communication channel | | |

If all three: state which leg is removed, or list compensating controls (human-in-the-loop on which tools, egress allowlist, recipient allowlist, content inspection) and why they are sufficient.

Check the subtle exfiltration channels explicitly, not just obvious "send" tools:
- **URL smuggling**: any tool that fetches a caller-influenced URL can exfiltrate data in the query string of an otherwise-allowed request (`https://allowed.example/?q=<secret>`). Controls: URL length caps, query-string entropy/size limits, egress allowlists, fetch-after-read alerting.
- **Write-back channels**: comments, tickets, filenames, metadata fields, and log messages visible to other parties are all external communication for trifecta purposes.

## 3. MCP-specific attack classes

For each, record: Applicable (Y/N), attack scenario in one or two sentences for THIS server, and mitigations (reference control IDs from security-requirements.md).

1. **Token passthrough / audience confusion** — Can any path accept or forward a token not issued to this server?
2. **Confused deputy** — Does the server hold privileges exceeding any single caller's? How is per-user entitlement re-checked on every call? If an OAuth proxy: per-client consent, redirect URI, and state handling.
3. **Tool poisoning / schema poisoning / rug pull** — Can descriptions or schemas change outside code review? Can upstream data influence tool metadata?
4. **Prompt injection via tool output / RADE** — Which tools return content an adversary can author (web pages, tickets, emails, documents, filenames, retrieved records)? How is it demarcated? Retrieval-agent-deception (payloads planted in retrieved data) counts here, not just live web content.
   4a. **Sampling/elicitation abuse** — If the server uses sampling, does it request only its own context (never broad `includeContext`)? If it elicits from users, could the prompt phish sensitive data? Prefer direct LLM API calls over sampling (also the 2026 spec direction).
5. **SSRF** — Which parameters become server-side requests? Controls per INP-5.
6. **Session/state hijack and handle replay** — What state or handles cross calls? User binding, expiry, entropy.
7. **Injection (SQL/command/path/LDAP)** — Per tool, which inputs reach interpreters, filesystems, or shells?
8. **Secrets exposure** — Where do credentials live at rest and in memory? Can any tool output or log leak them?
9. **Supply chain** — Notable dependencies, their provenance, pinning, and scanning.
10. **Denial of service / resource abuse** — Expensive tools, amplification paths, quota-consuming downstream calls.
11. **Shadow deployment** — How is this server registered, and how would an unregistered clone be detected?

## 4. STRIDE sweep (conventional surface)

One line each for Spoofing, Tampering, Repudiation, Information disclosure, DoS, Elevation of privilege, covering anything not captured above (network posture, host hardening, CI/CD, admin interfaces).

## 5. Abuse cases to test in Phase 4

List concrete test cases derived from sections 2-4 (e.g. "call `web_fetch` with http://169.254.169.254/latest/meta-data/ and confirm block + security log", "present a token with aud=other-service and confirm 401"). These become automated tests. If rebuilding from reference servers (consolidate-and-rebuild.md), seed this list with every finding from their review reports: each becomes a failing-until-fixed test proving the rebuild does not reintroduce a known flaw.

## 6. Risk decisions

| ID | Risk | Severity | Decision (mitigate/accept/redesign) | Owner | Due |
|---|---|---|---|---|---|

Accepted risks require a named owner and expiry date.
