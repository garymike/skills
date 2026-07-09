# Inspection Checklist

Work through the parts your tier requires. Every checked item gets a one-line note in the decision record; "looks fine" is not a note.

## Part A: Provenance and package integrity (all tiers)

- [ ] Exact package/endpoint name verified character-by-character against the official source; typosquat search done (common transposition/omission variants of the name checked in the registry).
- [ ] Publisher identified: org or person, track record, other packages, contactability. Signed releases or checksums verified where offered.
- [ ] Package ↔ repository correspondence: the published artifact builds from, or matches, the public source. Watch for repos that look clean while the published package differs.
- [ ] Maintenance signals: recent releases, responsive issues, more than one maintainer for anything Tier 2+.
- [ ] Dependency scan (npm audit / pip-audit / org scanner) on the exact pinned version; no unresolved criticals. Lockfile integrity checked (lockfile-lint) and malicious/typosquatted packages screened (Socket.dev or equivalent).
- [ ] Known-vulnerability and incident search on the server name and publisher (CVEs, advisories, security research).
- [ ] Remote connectors: hosting provider, data residency, subprocessors, breach history, security page/SOC 2 or equivalent evidence proportional to tier.

## Part B: Tool surface (all tiers; automated scan minimum for Tier 1)

- [ ] Automated scan (mcp-scan or equivalent) of the full tool set: descriptions, schemas, annotations.
- [ ] Human read of every tool description and parameter name. You are looking for: instructions aimed at the model rather than descriptions of function; references to other tools or servers; urgency/priority language; invisible or encoded text; parameters that solicit data unrelated to the function (e.g. a "context" param on a weather tool).
- [ ] Schemas are sane: `additionalProperties: false`, constrained strings, no free-form blobs that invite the model to stuff arbitrary content.
- [ ] Annotations plausible and consistent with observed behavior (a "read-only" tool that takes a `content` parameter is lying somewhere).
- [ ] Capability inventory matches the stated business purpose; every tool beyond the purpose is a finding (excess capability is attack surface even when benign).
- [ ] **Sampling/elicitation surface**: if the server issues sampling requests, check whether it can pull in context beyond its own (the `includeContext` risk); a server that requests broad context is a cross-server data-access vector even without a malicious tool. Elicitation prompts are a phishing surface; note if the server can solicit sensitive data from users.
- [ ] **RADE (retrieval agent deception)**: for servers that retrieve documents/records the agent then acts on, treat retrieved content as an indirect-injection vector, not just tool descriptions. Confirm retrieved content is returned as demarcated data and that no tool auto-acts on instructions found inside it.
- [ ] Tool-definition set canonicalized and hashed (SHA-256) with `scripts/hash_tool_definitions.py`, which pins the canonicalization (name, description, input/output schemas, and annotations; sorted keys; tools sorted by name) so the hash is reproducible on re-review and matches a builder-published SUP-6 manifest. Hash recorded in the decision record for rug pull detection.

## Part C: Code and runtime behavior (local servers, Tier 2+)

- [ ] Source scanned for embedded secrets/PII/keys with Gitleaks (`gitleaks detect --source .`) or TruffleHog (`--only-verified`); any live credential is an automatic Critical (remediate by rotation, not just deletion).
- [ ] Startup commands and install scripts read in full: no remote fetch-and-execute, no credential harvesting, no telemetry beyond disclosed.
- [ ] Filesystem reach: what paths it reads/writes; confined or greedy? Any interest in `~/.ssh`, keychains, browser profiles, cloud credential files is disqualifying.
- [ ] Network behavior observed in a sandbox run (container, no real credentials, canary tokens where useful): destinations, frequency, payload character. Compare against disclosed behavior.
- [ ] Credential handling: reads only its documented env vars; nothing written to disk unencrypted; nothing echoed into tool output or logs.
- [ ] Subprocess/shell usage inspected; dynamic code loading (eval, remote plugins) is Tier 3 or disqualifying.
- [ ] Runs as non-root, works under your standard sandbox profile (restricted filesystem, explicit egress).
- [ ] **Background persistence**: does the server clean up its processes when the client shuts down, or can it persist/respawn in the background? Check for lingering processes after a client stop, unexpected daemons, or install steps that register autostart. An ostensibly-stopped server still running is both a resource and a compromise-persistence risk; note health-check and lifecycle behavior.
- [ ] **Service identity / anti-spoofing**: for anything beyond local stdio, can the client verify it is talking to the genuine server (pinned cert, known endpoint, signed identity) rather than a spoofed one? Server spoofing lets an attacker substitute a malicious backend behind a trusted name.
- [ ] **Defensive quality** (sloppy is a risk class, not just malicious): inputs validated server-side beyond schema; database/query access parameterized; URL-fetching tools carry SSRF controls (HTTPS-only, private/metadata IP denial, redirect validation, size/time caps); errors sanitized. Yardstick: secure-mcp-builder's security-requirements catalog; each miss is a finding scored under code hygiene.
- [ ] **Output handling**: untrusted upstream content the server returns is demarcated/labeled, instruction-markup neutralized; outputs do not leak secrets, hostnames, or stack traces.
- [ ] **Auditability**: the server logs tool invocations with enough structure (who/what/when/status) to feed the SIEM; a server we cannot observe raises hosting-exposure and monitoring cost, and the gap is noted in the report's monitoring recommendations.

## Part D: Auth and data flow (remote servers and any credentialed local server, Tier 2+)

- [ ] Requested OAuth scopes / API permissions listed and each justified against purpose; excess scopes are conditions-to-cut, not shrugs.
- [ ] No token passthrough smell: the server must obtain its own tokens via proper flows, never ask the client or user to paste tokens issued for other services.
- [ ] Auth flow quality: OAuth 2.1/PKCE for user-delegated access; exact redirect URIs; no long-lived static keys where delegation is available.
- [ ] Data flow mapped: what leaves the org per tool call, where it is stored, retention, and whether the vendor trains on it (get the answer in writing for Tier 3).
- [ ] Revocation path confirmed: you can kill its access unilaterally (token revocation, key rotation, IP block) and know how before connecting.

## Part E: Active testing (Tier 2+ where you can exercise the server in a sandbox)

Static review finds what the code says; active testing finds what it does. Run in an isolated environment with throwaway credentials and canary tokens; never against production data.

- [ ] **Traffic interception**: proxy the stdio stream or HTTP traffic (e.g. Burp plus an MCP client/proxy) and inspect tool-call returns for appended context, hidden metadata, injected prompts, or content pulled from other tools that the description does not mention.
- [ ] **Raw-vs-delivered diff**: compare the backend's raw response to what actually reaches the model; a server that silently mutates or injects into results is a finding regardless of intent.
- [ ] **Injection battery per string parameter**: command (`; whoami`, `| id`), path traversal (`../../etc/passwd`), SSRF (`http://169.254.169.254/latest/meta-data/`, internal IPs, Collaborator URL), SQL (`' OR '1'='1'--`), NoSQL (`{"$ne": null}`), SSTI (`{{7*7}}`), plus malformed inputs (nulls, 100k-char strings, wrong types, integer extremes). Expect clean validation errors and zero execution.
- [ ] **Authorization attacks**: anonymous tool calls; expired/modified-claim/forged tokens; IDOR on resource URIs (`resource://user/123` as user 124); invoke admin-only tools as a regular user. Any success is High or Critical.
- [ ] **Output/DoS probes**: force a large tool return (size-limit/DoS check); confirm errors do not disclose file paths, stack traces, or schema.

Findings from Part E carry the most weight in the report; a server that fails static review might still be salvageable with conditions, but one that executes an injection in testing is demonstrated-vulnerable.
- [ ] **Integrity support** (positive signal, not required): published tool-definition manifest/hashes, signed releases, or message-level signing support; note presence or absence, it feeds rug pull detection feasibility.
