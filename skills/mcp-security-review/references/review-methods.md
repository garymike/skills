# Review Methods: How to Ingest and Assess a Server

Three modes. Pick by what access you have, then combine as depth allows. They are complementary, not interchangeable: each is blind to what the others catch. State in the report which mode(s) you used, because the mode bounds what the findings can and cannot cover.

## Mode selection

| You have... | Primary mode | Add if possible |
|---|---|---|
| A GitHub/registry link or source | Code/repo review | Sandbox install |
| A live remote endpoint (SaaS connector) | Remote/live review | Code review if source is public |
| A package you can install | Sandbox install | Code review of the package source |
| All of the above | All three; reconcile them | — |

Highest confidence comes from **reconciling modes**: the repo says X, the live endpoint serves Y, the sandbox does Z. Divergence is itself a finding (e.g. published package differs from the repo, or the live server serves tool definitions the source does not produce, a rug pull indicator).

## Mode 1: Code / repository review

Best for: open-source and first-party servers where you have source. Catches hardcoded secrets, dangerous functions, dependency risk, install-script behavior. Blind to: runtime behavior, and what a remote server actually serves at request time.

Ingesting a GitHub link:
1. Clone at a pinned commit/tag; record the commit SHA (this is the point-in-time anchor for the report and for later re-assessment). `git clone --depth 1 <url>` then note `git rev-parse HEAD`.
2. Read the entrypoint and manifest: `SKILL.md`/`README`, `package.json`/`pyproject.toml`, the server bootstrap file. Identify the SDK and transport.
3. Enumerate the tool/resource/prompt definitions from source: names, descriptions, schemas, annotations. This is the definition set you canonicalize and hash (Part B). Read every description for injection (Part B human read).
4. Secret scan: `gitleaks detect --source .` and `trufflehog filesystem . --only-verified`. Any live credential is an automatic Critical (remediate by rotation).
5. Dangerous-function grep: `eval`, `exec`, `child_process`, `subprocess`, `os.system`, dynamic import, `pickle.loads`, template rendering on user input. Trace each to whether user/model input can reach it (Part C).
6. Dependency and integrity: `pip-audit` / `npm audit`, lockfile presence and `lockfile-lint`, Socket.dev for malicious/typosquatted packages. Confirm the package published to PyPI/npm actually builds from this repo (repo↔package correspondence, Part A).
7. Install-script inspection: read any `postinstall`, setup hooks, or `.mcpb`/bundle manifest for fetch-and-execute.

Limits to state in the report: source review cannot prove the *deployed* server matches the source. For remote servers especially, pair with Mode 2.

## Mode 2: Remote / live review

Best for: hosted SaaS connectors and any running endpoint. Catches the actual served tool definitions, auth behavior, real redirect/egress behavior. Blind to: source (inferred, not read) and to whether the repo matches the deployment.

1. Connect with MCP Inspector (`npx @modelcontextprotocol/inspector`) or a scripted client; enumerate the live tool/resource/prompt set. Canonicalize and hash it (Part B) — this live hash is what monitoring re-checks for rug pulls.
2. Proxy the traffic (Burp or an MCP proxy): inspect real request/response, look for appended context, hidden metadata, or content pulled from other tools in returns (Part E traffic interception).
3. Exercise auth: metadata discovery (RFC 9728), token audience behavior, anonymous-access and wrong-audience attempts, OAuth flow quality (Part D, Part E authorization attacks). Do this against a test tenant, never production data.
4. Observe egress and data residency: where does the endpoint send data, what does it return, retention and subprocessor answers from the vendor (Part A/D).
5. Diff live definitions against the repo (if Mode 1 available): mismatch is a rug pull / hidden-behavior finding.

Limits: you are testing the deployment you can reach; a malicious operator can serve different content later (which is exactly why the definition hash goes into monitoring, `onboarding-monitoring.md`).

## Mode 3: Sandbox installation

Best for: local/self-hosted packages, and any Tier 3 server where runtime behavior matters. The only mode that catches fetch-and-execute, background persistence, and real filesystem/network reach. Highest effort; requires isolation.

1. Isolated environment only: disposable container/VM, no real credentials, canary tokens, network egress captured and default-deny with logging. Never a production or credentialed host.
2. Install and capture install-time behavior: what runs, what it writes, what it fetches (ties to Mode 1 step 7).
3. Run and observe: start the server, exercise each tool with benign and malicious inputs (Part E injection/SSRF/authz batteries), watch actual syscalls, file access, and outbound connections against what was disclosed.
4. Persistence check (Part C): stop the client/parent; confirm no lingering processes, daemons, or autostart survive. An ostensibly-stopped server still running is a finding.
5. Raw-vs-delivered diff (Part E): compare backend responses to what reaches the model.
6. Tear down the environment; preserve captured traffic, hashes, and logs as report evidence.

Limits: sandbox behavior may differ from production (feature flags, environment detection, time-delayed payloads). A server that behaves in a sandbox but misbehaves on a timer is why monitoring continues after onboarding.

## Tool availability and graceful degradation

**Fully-provisioned fast path.** A pinned, signed container image bundles these
scanners so you can run them without local installs — locally or in CI. The
companion image built for this workflow is
`ghcr.io/garymike/security-workflows/mcp-review-toolbox` (or build your own, or use
an equivalent); pin it by digest and verify its cosign signature before trusting
it:

```
docker run --rm -v "$PWD:/src:ro" -w /src \
  ghcr.io/garymike/security-workflows/mcp-review-toolbox:latest \
  gitleaks dir /src --no-banner --redact
```

The toolbox is an optional accelerator, never a dependency. The scanners are the
fast path, not the requirement: if the image or any individual tool is missing,
never silently drop the check — the report would look complete while a whole
class went unexamined, which is the dangerous failure. For each unavailable tool:
try to install it (or use the toolbox); if you still cannot run it, do the manual
equivalent, and record the gap on the report's review-mode line as a stated
limitation that lowers confidence. An unrun check is an unknown, and unknowns
raise risk, never lower it.

| Tool (fast path) | If unavailable, manual equivalent |
|---|---|
| `mcp-scan` / `snyk-agent-scan` (tool-surface scan) | The Part B human read of every description and schema is already mandatory — do it, and note the automated scan was skipped. |
| `gitleaks` / `trufflehog` (secret scan) | Grep source and config for key/token patterns and high-entropy strings; lower recall, so state it. |
| `pip-audit` / `npm audit` (dependency CVEs) | Look up the pinned versions in OSV.dev / GitHub Advisories by hand; if there is no network, record the dependency-CVE check as not performed. |
| Socket.dev (malicious-package screen) | Manual provenance and install-script read (Part A / Part C); note the automated screen was not run. |
| Burp / MCP proxy (Part E interception) | If you cannot proxy the traffic, Part E is a stated limitation: lean on static review and say the runtime behavioral check was not done. |

Report a class you could not test as "not assessed (tool unavailable)", never as
"clean".

## Recording the method in the report

The report's assessment-depth line and machine-readable block note which modes were used. A Tier 3 recommendation to connect should generally rest on at least two modes; a code-only review of a remote server, or a live-only review with no source, is a stated limitation, not a silent one.
