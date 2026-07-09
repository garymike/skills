# MCP Security Assessment Report — authoring and rendering

The report is **data-first**. You author one schema-valid data file; a renderer
produces the styled report. Do not hand-format prose reports — author the data and
render, so every assessment is identical in shape and comparable across servers.

## Pipeline

```
assessment.json                         # you author this — the single source of truth
   │   validates against ../schema/assessment.schema.json (draft 2020-12)
   │
   │   python ../scripts/render_report.py assessment.json \
   │          --html report.html --md report.md
   ▼
report.html   (styled, print/PDF-ready)   +   report.md   (Markdown)
```

1. **Author `assessment.json`** to `../schema/assessment.schema.json`. The schema is
   the field-by-field contract (required keys, enums, conditional rules); read it as
   you fill the data. Top-level: `meta`, `verdict`, `overall_risk`,
   `executive_summary`, `findings`, `technical_assessment`, `risk_rating`,
   `recommendations`, `limitations` (optional `provenance`).
2. **Render.** `render_report.py` is stdlib-only. If `jsonschema` is installed it
   pre-flight-validates and fails closed on a schema violation; otherwise it renders
   and you validate separately. Never ship a report whose source did not validate.
3. **Gate.** The output must pass `report-quality-rubric.md` (the must-pass list and
   the do-not-reintroduce list). That rubric, not taste, is the ship gate.

**Export formats.** `--html` (default) is the readable deliverable — the appendix (full
`assessment.json`) is **collapsed** so the report stays scannable on screen. `--pdf out.pdf`
produces a shareable PDF via headless Chrome/Edge with the appendix **expanded**, so the
machine-readable record is actually captured — a collapsed `<details>` prints empty and the
record would be lost. `--md` is the plaintext twin. Pick HTML for reading, PDF for forwarding;
the renderer handles the appendix state for each so you don't have to.

The renderer fixes the section order so "findings lead" is structural: the executive
summary (verdict-first, severity counts, top findings) sits at the top, recommendations
next, descriptive sections below, full findings after, and the machine-readable
`assessment.json` is embedded in a collapsed appendix. You control content, not layout.

## Authoring rules the schema cannot enforce

- **Every field gets a value or an explicit "unknown, because …".** Security-relevant
  unknowns raise the risk score, never lower it. Do not omit a field to hide a gap.
- **Automatic-Critical triggers** (set severity `critical`): hardcoded secrets or
  credentials in code/config, token passthrough, poisoned tool descriptions
  (cross-server priority language, data-harvesting parameters), a known-exploited CVE
  in the pinned version, fetch-and-execute install scripts.
- **Redacted evidence on every Critical/High finding.** The schema requires `evidence`
  there; you must also redact it — location + type + masked value, never a live
  secret/token in the report. Keep `secret_masked: true` honest.
- **Remediation cross-links to controls.** Each fix references the `secure-mcp-builder`
  control ID(s) that implement it (`remediation.control_ids`).
- **CVSS only where it fits.** Attach a CVSS 4.0 vector only to genuine software-vuln
  findings; never to governance, composition, or provenance findings.
- **Verification honesty.** Every finding carries `reasoned` / `observed` / `confirmed`,
  and `limitations.verification_note` ties to it and points at the validator path.
- **Excess permissions are findings** (usually Moderate; High when write/destructive),
  mapped to the capability that needs them.
- **Data masking as a fallback.** Where sensitive data flows to the server, recommend
  masking at a gateway (SSNs, account numbers, etc.) so a successful exfiltration
  yields masked values.
- **Limitations always present.** Point-in-time scope, methodology bounds, not-a-warranty,
  and `checks_not_performed` (tool gaps) — coverage bounds what findings can claim.

## Worked examples

`../evals/reference-outputs/1-assess-oss-package-arxiv.assessment.json` (moderate,
connect-with-conditions) and `2-critical-findings-crm.assessment.json` (critical,
do-not-connect) are complete, schema-valid sources with their rendered `.html`. Read
them for shape and rigor; do not copy their point-in-time specifics.
