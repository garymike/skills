#!/usr/bin/env python3
"""Render an mcp-security-review assessment.json into a styled HTML report and a
Markdown twin, both from the same data (the schema is the source of truth).

Stdlib-only so the deliverable has zero dependencies and prints cleanly. If the
`jsonschema` package is present, the input is validated against
schema/assessment.schema.json as a pre-flight; otherwise a light structural
check runs and rendering proceeds with a warning.

Usage:
  python render_report.py assessment.json                 # -> report.html + report.md
  python render_report.py assessment.json -o outdir/      # write into outdir/
  python render_report.py assessment.json --html r.html --md r.md
  python render_report.py assessment.json --pdf r.pdf      # PDF export (needs Chrome/Edge)
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

SEVERITY_ORDER = ["critical", "high", "moderate", "low", "info"]
SEVERITY_LABEL = {s: s.upper() for s in SEVERITY_ORDER}

# Muted, earthy palette — distinguishable, grayscale-legible (always paired with a text label).
SEVERITY_COLOR = {
    "critical": "#6e3b34",
    "high": "#9c5a44",
    "moderate": "#97793d",
    "low": "#5f7150",
    "info": "#8a8075",
}
VERDICT_LABEL = {
    "do_not_connect": "DO NOT CONNECT",
    "connect_with_conditions": "CONNECT WITH CONDITIONS",
    "connect": "CONNECT",
    "reassess": "REASSESS",
}
VERDICT_COLOR = {
    "do_not_connect": "#6e3b34",
    "connect_with_conditions": "#97793d",
    "connect": "#5f7150",
    "reassess": "#8a8075",
}
RATING_COLOR = {
    "critical": "#6e3b34",
    "high": "#9c5a44",
    "moderate": "#97793d",
    "low": "#5f7150",
}
CLASS_COLOR = {"read": "#5f7150", "write": "#97793d", "destructive": "#9c5a44"}


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def disp_id(fid) -> str:
    """Human-facing label for a finding id: F-01 -> Finding-01 (data id stays stable)."""
    s = str(fid or "")
    return s.replace("F-", "Finding-", 1) if s.startswith("F-") else s


LABELS = {
    "purpose": "Purpose", "creator_publisher": "Publisher",
    "maintenance_signals": "Maintenance", "license": "License",
    "auth_client_to_server": "Client auth", "auth_downstream": "Downstream auth",
    "token_passthrough": "Token passthrough", "stored_credential_risk": "Credential risk",
    "notes": "Notes",
}


def label(k) -> str:
    return LABELS.get(k, str(k).replace("_", " ").title())


def fmt_val(v):
    if isinstance(v, bool):
        return "Yes" if v else "No"
    return v


VERIF_DESC = {
    "reasoned": "Identified by static / definition review; not exploited.",
    "observed": "Seen in real behavior or traffic; not weaponized.",
    "confirmed": "Reproduced with a proof-of-concept.",
}
DEPTH_LABEL = {1: "Fast pass", 2: "Standard review", 3: "Full review"}
DEPTH_DESC = {
    1: "Fast pass — provenance and tool-surface review for a low-risk, read-only, public-data server.",
    2: "Standard review — full inspection across provenance, tool surface, code/runtime, and auth/data-flow.",
    3: "Full review — full inspection plus a sandbox behavioral run (local) or vendor security assessment (remote); the deepest scrutiny, warranted by credentialed, write-capable, or sensitive-data exposure.",
}

# Plain-language provenance label derived from the provenance risk factor (1-5) — not a separate score.
PROV_LABEL = {1: "Established", 2: "Reputable", 3: "Known OSS", 4: "Unproven", 5: "Unknown / new"}
PROV_COLOR = {1: "#5f7150", 2: "#5f7150", 3: "#97793d", 4: "#9c5a44", 5: "#6e3b34"}


def human(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 1000:
        return f"{n/1000:.1f}k".replace(".0k", "k")
    return str(n)


def source_link_html(meta: dict) -> str:
    url = str(meta.get("source_url") or "").strip()
    if not url:
        return ""
    base = url if url.startswith(("http://", "https://")) else "https://" + url
    display = base.split("://", 1)[-1].rstrip("/")
    href = base.rstrip("/")
    sha = meta.get("source_commit_sha")
    if sha and "github.com" in base:
        href = href + "/tree/" + str(sha)
        display += f" @ {str(sha)[:7]}"
    return f'<a class="source" href="{esc(href)}">{esc(display)}</a>'


def provenance_parts(a: dict):
    """Returns (label_text_or_None, [signal strings]) shared by HTML and MD."""
    p = a.get("provenance") or {}
    bits = []
    if p.get("stars") is not None:
        bits.append(f'★ {human(p["stars"])}')
    if p.get("forks") is not None:
        bits.append(f'{human(p["forks"])} forks')
    if p.get("is_fork") is True:
        bits.append("fork of " + p["forked_from"] if p.get("forked_from") else "fork")
    elif p.get("is_fork") is False:
        bits.append("original")
    if p.get("owner_type") == "org":
        bits.append("organization")
    if p.get("owner_followers") is not None:
        bits.append(f'{human(p["owner_followers"])} followers')
    if p.get("owner_public_repos") is not None:
        bits.append(f'{human(p["owner_public_repos"])} repos')
    if p.get("account_created"):
        bits.append("since " + str(p["account_created"])[:4])
    if p.get("last_activity"):
        bits.append("updated " + str(p["last_activity"]))
    pv = a.get("risk_rating", {}).get("factor_scores", {}).get("provenance")
    return PROV_LABEL.get(pv), bits, pv


def provenance_html(a: dict) -> str:
    if not a.get("provenance"):
        return ""
    label, bits, pv = provenance_parts(a)
    if not (label or bits):
        return ""
    label_html = (f'<span class="prov-label" style="background:{PROV_COLOR.get(pv, "#8a8075")}">{esc(label)}</span>'
                  if label else "")
    return f'<div class="prov">{label_html}<span class="prov-signals">{" · ".join(esc(b) for b in bits)}</span></div>'


def sev_rank(f: dict) -> int:
    try:
        return SEVERITY_ORDER.index(f.get("severity", "info"))
    except ValueError:
        return len(SEVERITY_ORDER)


def sorted_findings(a: dict) -> list:
    return sorted(a.get("findings", []), key=lambda f: (sev_rank(f), f.get("id", "")))


def severity_counts(a: dict) -> dict:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for f in a.get("findings", []):
        counts[f.get("severity", "info")] = counts.get(f.get("severity", "info"), 0) + 1
    return counts


def compose_disclaimer(a: dict) -> str:
    lim = a.get("limitations", {})
    parts = [lim.get("disclaimer", "").strip()]
    if lim.get("verification_note"):
        parts.append(lim["verification_note"].strip())
    cnp = a.get("meta", {}).get("checks_not_performed") or []
    if cnp:
        parts.append("Checks not performed (coverage gaps): " + ", ".join(cnp) + ".")
    return "\n\n".join(p for p in parts if p)


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #

CSS = """
:root { --paper:#e9e3d6; --panel:#fdfbf7; --ink:#2c2a25; --muted:#6f685c;
        --line:#e4ded2; --accent:#766152; --accent-soft:#efeae0; }
* { box-sizing:border-box; }
body { font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       color:var(--ink); background:var(--paper); margin:0; padding:30px 16px; }
.wrap { max-width:840px; margin:0 auto; }

.cover, .block { background:var(--panel); border:1px solid var(--line); border-radius:10px;
                 padding:24px 28px; margin:0 0 16px; }
.exec { background:#dce3ed; border:2px solid #9bb0cb; }
.recs { background:#e3e9d8; border:2px solid #a7b988; }
h1 { font-size:27px; margin:0 0 2px; letter-spacing:-.01em; }
h2 { font-size:13px; text-transform:uppercase; letter-spacing:.09em; color:var(--muted);
     margin:0 0 14px; display:flex; align-items:center; gap:8px; }
h2::before { content:""; width:9px; height:9px; border-radius:2px; background:var(--accent); }
h3 { font-size:15.5px; margin:0; }
p { margin:0 0 12px; } p:last-child { margin-bottom:0; }
a { color:var(--accent); text-decoration:none; }
small, .muted { color:var(--muted); }
code, pre, .mono { font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
.eyebrow { text-transform:uppercase; letter-spacing:.12em; font-size:11.5px; color:var(--muted); margin:0 0 6px; }
.sub { color:var(--muted); font-size:13.5px; margin:2px 0 0; }
.source { display:inline-block; margin-top:7px; font-size:13px; color:var(--accent);
          font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; word-break:break-all; }
.prov { margin-top:10px; font-size:12.5px; line-height:1.7; }
.prov-label { display:inline-block; color:#fff; font-size:10px; font-weight:700; text-transform:uppercase;
              letter-spacing:.05em; padding:2px 9px; border-radius:20px; margin-right:9px; vertical-align:middle; }
.prov-signals { color:var(--muted); vertical-align:middle; }
.subhead { color:var(--muted); font-size:12px; margin:16px 0 5px; text-transform:uppercase; letter-spacing:.06em; }

.cover-top { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; flex-wrap:wrap; }
.cover-id { flex:1 1 340px; min-width:0; }
.cover-outcome { flex:0 0 auto; display:flex; flex-direction:column; gap:8px; align-items:flex-end; }
.orow { display:flex; align-items:center; gap:10px; }
.olabel { font-size:10.5px; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); }
.pill { display:inline-block; color:#fff; font-weight:700; letter-spacing:.02em; padding:6px 12px;
        border-radius:6px; font-size:12.5px; min-width:130px; text-align:center; }
.profile { display:grid; grid-template-columns:repeat(auto-fit,minmax(195px,1fr)); gap:6px 30px;
           margin:18px 0 0; padding:15px 0 0; border-top:1px solid var(--line); font-size:13.5px; }
.profile .k { color:var(--muted); }
.profile .v { font-weight:600; }

.chips { margin:0 0 14px; }
.chip { display:inline-flex; align-items:center; font-size:12px; font-weight:600; padding:3px 12px 3px 4px;
        border-radius:20px; margin:0 7px 7px 0; border:1px solid var(--line); color:var(--muted); background:#fff; }
.chip.n0 { opacity:.5; }
.chip b { display:inline-flex; align-items:center; justify-content:center; flex:0 0 auto;
          width:18px; height:18px; border-radius:50%; color:#fff; font-size:11px; margin-right:6px; }
.topf-list { list-style:none; margin:0 0 6px; padding:0; }
.topf-list li { display:flex; justify-content:space-between; align-items:baseline; gap:14px; padding:2px 0; }
.topf-ref { white-space:nowrap; }

.anchor { font-size:12.5px; color:var(--muted); border-top:1px solid var(--line); margin-top:14px; padding-top:10px; }
.anchor span { display:inline-block; margin-right:16px; }
.anchor code { color:var(--ink); }

.rec { display:flex; align-items:center; gap:11px; font-size:15px; }
.rec + .rec { margin-top:12px; padding-top:12px; border-top:1px solid #d2dcc0; }
.rec .n { flex:0 0 auto; width:24px; height:24px; border-radius:50%;
          background:var(--accent); color:#fff; font-size:13px; font-weight:700;
          display:flex; align-items:center; justify-content:center; }
.rec .rectext { flex:1; }
.rec .refs { color:var(--muted); font-size:12.5px; }

.finding { background:#fbf9f4; border:1px solid var(--line); border-left-width:5px; border-radius:8px;
           padding:16px 18px; margin:0 0 14px; }
.finding:last-child { margin-bottom:0; }
.finding-head { display:flex; align-items:center; justify-content:space-between; gap:9px; flex-wrap:wrap; margin-bottom:4px; }
.finding-tags { display:flex; gap:7px; flex-wrap:wrap; }
.sev { color:#fff; font-weight:700; font-size:11px; letter-spacing:.05em; padding:3px 8px; border-radius:5px; }
.fid { font-weight:700; color:var(--accent); font-size:13px; letter-spacing:.03em; text-transform:uppercase; }
.finding-title { font-size:15.5px; margin:0 0 12px; }
.finding-div { border:none; border-top:1px solid var(--line); margin:0 0 12px; }
.badge { font-size:11px; padding:2px 8px; border-radius:5px; border:1px solid var(--line);
         color:var(--muted); background:#fff; }
.badge.confirmed { border-color:#5f7150; color:#5f7150; }
.badge.observed { border-color:#97793d; color:#97793d; }
.cvss { font-size:11px; font-weight:600; color:var(--ink); background:var(--accent-soft); padding:2px 8px; border-radius:5px; }
dl.kv { display:grid; grid-template-columns:100px 1fr; gap:7px 14px; margin:0; font-size:14.5px; }
dl.kv dt { color:var(--muted); font-size:13px; }
dl.kv dd { margin:0; }
dl.kv2 { display:grid; grid-template-columns:140px 1fr; gap:7px 14px; margin:0; font-size:14px; }
dl.kv2 dt { color:var(--muted); font-size:13px; }
dl.kv2 dd { margin:0; }
.subsection { margin:16px 0 0; padding:16px 0 0; border-top:1px solid var(--line); }
.subsection:first-child { margin-top:0; padding-top:0; border-top:none; }
.subsection .subhead { margin:0 0 8px; }
.subhead .dot { display:inline-block; width:8px; height:8px; border-radius:2px; margin-right:7px; vertical-align:middle; }
.caps-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px 28px; }
.cap { margin:0; }
.cap-head { display:flex; align-items:center; gap:9px; margin-bottom:2px; }
.cap-head code { font-weight:600; font-size:14px; }
.cap-class { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.05em;
             background:#615a4e; color:#fff; border-radius:4px; padding:2px 8px; }
.cap-class.destructive { background:#7a4a3e; }
.cap-fn { font-size:14px; }
.cap-anno { font-size:12.5px; color:var(--muted); margin-top:2px; }
pre.evidence { background:#efeae0; color:#403a30; border:1px solid #e0d9cb; padding:10px 12px;
               border-radius:6px; font-size:12.5px; overflow-x:auto; white-space:pre-wrap; margin:0; }
.controls code { background:var(--accent-soft); color:#5a4a37; padding:1px 6px; border-radius:4px; font-size:12px; margin-right:4px; }

table { border-collapse:collapse; width:100%; font-size:14px; margin:4px 0; }
th, td { text-align:left; padding:7px 10px; border-bottom:1px solid var(--line); vertical-align:top; }
th { color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
tr:last-child td, tr:last-child th { border-bottom:none; }
.risk-table { table-layout:fixed; }
.risk-table th, .risk-table td { width:50%; }
.composite-row td, .composite-row th { background:#efe9db; border-top:1px solid #d8d0bf; }
.composite-row th { color:var(--ink); font-weight:700; text-transform:none; font-size:14px; letter-spacing:0; }
.composite-row td { font-size:15px; }

.disclaimer { font-size:13px; color:#5c564b; background:#f4f0e7; border:1px solid var(--line); border-radius:8px; padding:14px 16px; }
details.appendix summary { cursor:pointer; color:var(--muted); font-size:13px; font-weight:600; user-select:none; }
details.appendix pre { background:#f6f3ec; border:1px solid var(--line); border-radius:8px; padding:14px;
                       font-size:12px; overflow-x:auto; margin-top:12px; }
.footer { color:var(--muted); font-size:12px; text-align:center; margin:4px 0 0; }

@media print {
  body { background:#fff; padding:0; }
  .cover, .block { border:1px solid #ddd; }
  .finding, table, .disclaimer, .rec, .exec, .recs { break-inside:avoid; }
  h2 { break-after:avoid; }
  details.appendix pre { white-space:pre-wrap; overflow-wrap:anywhere; overflow-x:visible; }
  details.appendix summary { list-style:none; }
  details.appendix summary::-webkit-details-marker { display:none; }
  * { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
}
"""


def _chip(sev: str, n: int) -> str:
    cls = "chip n0" if n == 0 else "chip"
    return (f'<span class="{cls}"><b style="background:{SEVERITY_COLOR[sev]}">{n}</b>'
            f'{SEVERITY_LABEL[sev].title()}</span>')


def _block(title: str, inner: str, cls: str = "") -> str:
    return f'<section class="block {cls}"><h2>{title}</h2>{inner}</section>'


def _finding_html(f: dict) -> str:
    sev = f.get("severity", "info")
    color = SEVERITY_COLOR.get(sev, "#8a8075")
    verif = f.get("verification", "reasoned")
    tags = [f'<span class="sev" style="background:{color}">{SEVERITY_LABEL[sev]}</span>',
            f'<span class="badge {esc(verif)}" title="{esc(VERIF_DESC.get(verif, ""))}">{esc(verif)}</span>']
    cvss = f.get("cvss")
    if cvss:
        tags.append(f'<span class="cvss">CVSS {esc(cvss.get("version"))} {esc(cvss.get("base_score"))}</span>')

    cat = f.get("category", {})
    cat_bits = []
    if cat.get("owasp_mcp_top10"):
        cat_bits.append(esc(cat["owasp_mcp_top10"]))
    if cat.get("review_part"):
        cat_bits.append("Part " + esc(cat["review_part"]))
    ctl = "".join(f"<code>{esc(c)}</code>" for c in cat.get("control_ids", []))
    if ctl:
        cat_bits.append(f'<span class="controls">{ctl}</span>')

    rows = [("Category", " · ".join(cat_bits) or "—"),
            ("Affected", esc(f.get("affected_component"))),
            ("Description", esc(f.get("description"))),
            ("Impact", esc(f.get("impact")))]
    if f.get("likelihood"):
        rows.append(("Likelihood", esc(f["likelihood"])))
    ev = f.get("evidence")
    if ev:
        rows.append(("Evidence", f'<pre class="evidence">{esc(ev.get("location"))} — {esc(ev.get("detail"))}</pre>'))
    rem = f.get("remediation", {})
    rem_ctl = "".join(f"<code>{esc(c)}</code>" for c in rem.get("control_ids", []))
    rem_html = esc(rem.get("summary"))
    if rem_ctl:
        rem_html += f' <span class="controls">{rem_ctl}</span>'
    rows.append(("Remediation", rem_html))
    if f.get("references"):
        rows.append(("References", " · ".join(esc(r) for r in f["references"])))
    rows.append(("Status", esc(f.get("status"))))

    kv = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return (f'<div class="finding" style="border-left-color:{color}">'
            f'<div class="finding-head"><span class="fid">{esc(disp_id(f.get("id")))}</span>'
            f'<span class="finding-tags">{"".join(tags)}</span></div>'
            f'<h3 class="finding-title">{esc(f.get("title"))}</h3>'
            f'<hr class="finding-div">'
            f'<dl class="kv">{kv}</dl></div>')


def render_html(a: dict, expand_appendix: bool = False) -> str:
    meta = a.get("meta", {})
    verdict = a.get("verdict", "reassess")
    rating = a.get("overall_risk", {}).get("rating", "moderate")
    comp = a.get("overall_risk", {}).get("composite")
    exec_ = a.get("executive_summary", {})
    counts = severity_counts(a)
    findings = sorted_findings(a)
    by_id = {f.get("id"): f for f in findings}
    ta = a.get("technical_assessment", {})
    cnp = meta.get("checks_not_performed") or []

    out = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width,initial-scale=1">'
           f'<title>Security Assessment — {esc(meta.get("server_name"))}</title>'
           f'<style>{CSS}</style></head><body><div class="wrap">']

    # Cover — identity + outcome (top row), then compact profile
    rating_txt = rating.upper() + (f' · {comp}' if comp is not None else '')
    ident = [f'<p class="eyebrow">MCP Security Assessment</p>',
             f'<h1>{esc(meta.get("server_name"))}</h1>']
    if meta.get("version_or_endpoint"):
        ident.append(f'<p class="sub">{esc(meta.get("version_or_endpoint"))}</p>')
    src = source_link_html(meta)
    if src:
        ident.append(src)
    prov = provenance_html(a)  # placed full-width below the cover-top row so it fits on one line
    outcome = ('<div class="cover-outcome">'
               '<div class="orow"><span class="olabel">Recommendation</span>'
               f'<span class="pill" style="background:{VERDICT_COLOR.get(verdict,"#8a8075")}">{VERDICT_LABEL.get(verdict, verdict.upper())}</span></div>'
               '<div class="orow"><span class="olabel">Overall risk</span>'
               f'<span class="pill" style="background:{RATING_COLOR.get(rating,"#8a8075")}">{rating_txt}</span></div>'
               '</div>')
    prof = []
    if meta.get("publisher"):
        prof.append(("Publisher", meta["publisher"]))
    hm = ta.get("hosting", {}).get("hosting_model")
    if hm:
        prof.append(("Hosting", hm.replace("_", " ")))
    if meta.get("assessor"):
        prof.append(("Assessor", meta["assessor"]))
    if meta.get("review_modes"):
        prof.append(("Review modes", ", ".join(meta["review_modes"])))
    depth = DEPTH_LABEL.get(meta.get("tier"))
    if depth:
        prof.append(("Assessment depth", depth))
    if meta.get("assessed_date"):
        prof.append(("Assessed", meta["assessed_date"]))
    profile_html = ('<div class="profile">'
                    + "".join(f'<div><span class="k">{esc(k)}:</span> <span class="v">{esc(v)}</span></div>' for k, v in prof)
                    + '</div>')
    out.append('<section class="cover"><div class="cover-top"><div class="cover-id">'
               + "".join(ident) + '</div>' + outcome + '</div>' + prov + profile_html + '</section>')

    # Executive summary
    ex = ['<div class="chips">' + "".join(_chip(s, counts[s]) for s in SEVERITY_ORDER) + '</div>']
    if exec_.get("posture"):
        ex.append(f'<p>{esc(exec_["posture"])}</p>')
    tops = [by_id[i] for i in exec_.get("top_finding_ids", []) if i in by_id]
    if tops:
        ex.append('<p class="subhead">Top findings</p><ul class="topf-list">')
        for f in tops:
            ex.append(f'<li><span class="topf-main"><b style="color:{SEVERITY_COLOR[f["severity"]]}">{SEVERITY_LABEL[f["severity"]]}</b> '
                      f'{esc(f.get("title"))}</span><span class="topf-ref muted">({esc(disp_id(f.get("id")))})</span></li>')
        ex.append('</ul>')
    if verdict == "connect_with_conditions" and exec_.get("conditions"):
        ex.append('<p class="subhead">Conditions to proceed</p><ul style="margin:0">')
        ex.extend(f'<li>{esc(c)}</li>' for c in exec_["conditions"])
        ex.append('</ul>')
    if meta.get("scope_statement"):
        ex.append(f'<p class="sub" style="margin-top:12px"><b>Scope:</b> {esc(meta["scope_statement"])}</p>')
    anc = []
    if meta.get("source_commit_sha"):
        anc.append(f'<span>Source SHA <code>{esc(meta["source_commit_sha"][:12])}</code></span>')
    if meta.get("definition_hash_sha256"):
        anc.append(f'<span>Definition hash <code>{esc(meta["definition_hash_sha256"][:18])}</code></span>')
    if cnp:
        anc.append(f'<span>Checks not performed: <code>{len(cnp)}</code></span>')
    if anc:
        ex.append('<div class="anchor">' + "".join(anc) + '</div>')
    out.append(_block("Executive summary", "".join(ex), "exec"))

    # Recommendations
    recs = a.get("recommendations", [])
    if recs:
        r_html = []
        for r in sorted(recs, key=lambda x: x.get("priority", 99)):
            refs = []
            if r.get("finding_ids"):
                refs.append("findings " + ", ".join(esc(disp_id(i)) for i in r["finding_ids"]))
            if r.get("control_ids"):
                refs.append(" ".join(f"<code>{esc(c)}</code>" for c in r["control_ids"]))
            ref_html = f' <span class="refs">({" · ".join(refs)})</span>' if refs else ""
            r_html.append(f'<div class="rec"><span class="n">{esc(r.get("priority"))}</span><span class="rectext">{esc(r.get("action"))}{ref_html}</span></div>')
        out.append(_block("Recommendations", "".join(r_html), "recs"))

    # Scope & methodology
    meth = []
    if meta.get("scope_statement"):
        meth.append(f'<b>Scope.</b> {esc(meta["scope_statement"])}')
    if meta.get("tier") in DEPTH_DESC:
        meth.append('<b>Assessment depth.</b> ' + esc(DEPTH_DESC[meta["tier"]]))
    if meta.get("review_modes"):
        meth.append('<b>Review modes.</b> ' + esc(", ".join(meta["review_modes"]))
                    + ' (code = source review, live = remote endpoint, sandbox = behavioral run).')
    if cnp:
        meth.append('<b>Not performed.</b> ' + esc(", ".join(cnp))
                    + ' — treated as unknowns that raise risk, never lower it.')
    out.append(_block("Scope &amp; methodology", "<p>" + "<br>".join(meth) + "</p>" if meth else "<p class='muted'>—</p>"))

    # Findings
    if findings:
        out.append(_block("Findings", "".join(_finding_html(f) for f in findings)))
    else:
        out.append(_block("Findings", '<p class="muted">No findings identified at this depth.</p>'))

    # Technical assessment — aligned subsections with color markers
    def subsection(title, color, inner):
        return (f'<div class="subsection"><p class="subhead">'
                f'<span class="dot" style="background:{color}"></span>{title}</p>{inner}</div>')

    def kv2(pairs):
        rows = "".join(f'<dt>{esc(label(k))}</dt><dd>{esc(fmt_val(v))}</dd>'
                       for k, v in pairs if v not in (None, ""))
        return f'<dl class="kv2">{rows}</dl>'

    tech = []
    prof = ta.get("profile", {})
    if prof:
        tech.append(subsection("Profile", "#766152", kv2(prof.items())))
    caps = ta.get("capabilities", [])
    if caps:
        cap_html = []
        for c in caps:
            cls = c.get("class") or ""
            head = f'<code>{esc(c.get("name"))}</code>'
            if cls:
                head += f'<span class="cap-class {esc(cls)}">{esc(cls)}</span>'
            block = f'<div class="cap"><div class="cap-head">{head}</div>'
            if c.get("function"):
                block += f'<div class="cap-fn">{esc(c.get("function"))}</div>'
            if c.get("annotations"):
                block += f'<div class="cap-anno">Annotations: {esc(c.get("annotations"))}</div>'
            cap_html.append(block + '</div>')
        tech.append(subsection("Capabilities", "#5f7150", '<div class="caps-grid">' + "".join(cap_html) + '</div>'))
    auth = ta.get("authentication_and_credential_risk", {})
    if auth:
        tech.append(subsection("Authentication &amp; credential risk", "#9c5a44", kv2(auth.items())))
    comp_a = ta.get("composition", {})
    if comp_a and (comp_a.get("analysis") or comp_a.get("blast_radius")):
        cparts = []
        if comp_a.get("analysis"):
            cparts.append(f'<p>{esc(comp_a["analysis"])}</p>')
        if comp_a.get("blast_radius"):
            cparts.append(f'<p><b>Blast radius.</b> {esc(comp_a["blast_radius"])}</p>')
        tech.append(subsection("Composition", "#97793d", "".join(cparts)))
    if tech:
        out.append(_block("Technical assessment", "".join(tech)))

    # Risk rating
    rr = a.get("risk_rating", {})
    if rr.get("factor_scores"):
        rows = "".join(f'<tr><td>{esc(k.replace("_"," ").title())}</td><td>{esc(v)}</td></tr>'
                       for k, v in rr["factor_scores"].items())
        rows += f'<tr class="composite-row"><th>Composite</th><td><b>{esc(rr.get("composite"))}</b></td></tr>'
        inner = f'<table class="risk-table"><thead><tr><th>Factor</th><th>Score (1–5)</th></tr></thead><tbody>{rows}</tbody></table>'
        if rr.get("overrides_applied"):
            inner += '<p class="sub">Overrides: ' + esc("; ".join(rr["overrides_applied"])) + '</p>'
        out.append(_block("Risk rating", inner))

    # Limitations & disclaimer
    out.append(_block("Limitations &amp; disclaimer",
                      f'<div class="disclaimer">{esc(compose_disclaimer(a)).replace(chr(10)+chr(10), "<br><br>")}</div>'))

    # Appendix — collapsed on screen; expanded for PDF export so the record is captured.
    open_attr = " open" if expand_appendix else ""
    out.append('<section class="block"><h2>Appendix</h2>'
               f'<details class="appendix"{open_attr}><summary>Machine-readable assessment (assessment.json)</summary>'
               '<pre>' + esc(json.dumps(a, indent=2, ensure_ascii=False)) + '</pre></details></section>')

    out.append('<p class="footer">Generated from a schema-validated assessment.json · point-in-time · see Limitations.</p>')
    out.append('</div></body></html>')
    return "".join(out)


# --------------------------------------------------------------------------- #
# Markdown twin
# --------------------------------------------------------------------------- #

def render_md(a: dict) -> str:
    meta = a.get("meta", {})
    verdict = a.get("verdict", "reassess")
    rating = a.get("overall_risk", {}).get("rating", "moderate")
    comp = a.get("overall_risk", {}).get("composite")
    exec_ = a.get("executive_summary", {})
    counts = severity_counts(a)
    findings = sorted_findings(a)
    by_id = {f.get("id"): f for f in findings}
    L = [f"# MCP Security Assessment — {meta.get('server_name','')}",
         f"**{VERDICT_LABEL.get(verdict, verdict.upper())}** · **{rating.upper()} RISK**"
         + (f" ({comp})" if comp is not None else "")]
    src = str(meta.get("source_url") or "").strip()
    if src:
        link = src if src.startswith(("http://", "https://")) else "https://" + src
        sha = meta.get("source_commit_sha")
        if sha and "github.com" in link:
            link = link.rstrip("/") + "/tree/" + str(sha)
        L.append(f"Source: <{link}>")
    _plabel, _pbits, _ = provenance_parts(a)
    if a.get("provenance") and (_plabel or _pbits):
        L.append("Provenance: " + ((_plabel + " — ") if _plabel else "") + " · ".join(_pbits))
    L += ["", "## Executive summary"]
    L.append(" · ".join(f"{counts[s]} {SEVERITY_LABEL[s].title()}" for s in SEVERITY_ORDER))
    if exec_.get("posture"):
        L += ["", exec_["posture"]]
    tops = [by_id[i] for i in exec_.get("top_finding_ids", []) if i in by_id]
    if tops:
        L += ["", "**Top findings**"]
        L += [f"- **{SEVERITY_LABEL[f['severity']]}** {f.get('title','')} ({disp_id(f.get('id',''))})" for f in tops]
    if verdict == "connect_with_conditions" and exec_.get("conditions"):
        L += ["", "**Conditions to proceed**"] + [f"- {c}" for c in exec_["conditions"]]
    if meta.get("scope_statement"):
        L += ["", f"**Scope:** {meta['scope_statement']}"]
    anchor = f"{DEPTH_LABEL.get(meta.get('tier'), '?')} · modes {', '.join(meta.get('review_modes', []))} · {meta.get('assessed_date','')}"
    if meta.get("checks_not_performed"):
        anchor += f" · checks not performed: {len(meta['checks_not_performed'])}"
    L += ["", f"_{anchor}_"]

    recs = a.get("recommendations", [])
    if recs:
        L += ["", "## Recommendations"]
        for r in sorted(recs, key=lambda x: x.get("priority", 99)):
            bits = []
            if r.get("finding_ids"): bits.append("findings " + ", ".join(disp_id(i) for i in r["finding_ids"]))
            if r.get("control_ids"): bits.append(", ".join(r["control_ids"]))
            ref = f" ({' · '.join(bits)})" if bits else ""
            L.append(f"{r.get('priority','-')}. {r.get('action','')}{ref}")

    L += ["", "## Findings"]
    if not findings:
        L.append("None identified at this depth.")
    for f in findings:
        L += ["", f"### {disp_id(f.get('id',''))} — {f.get('title','')}  ·  {SEVERITY_LABEL[f['severity']]}"
              + (f"  ·  CVSS {f['cvss'].get('base_score')}" if f.get("cvss") else "")
              + f"  ·  _{f.get('verification','reasoned')}_"]
        cat = f.get("category", {})
        cbits = [x for x in [cat.get("owasp_mcp_top10"),
                             ("Part " + cat["review_part"]) if cat.get("review_part") else None,
                             ", ".join(cat.get("control_ids", [])) or None] if x]
        if cbits: L.append(f"- **Category:** {' · '.join(cbits)}")
        L.append(f"- **Affected:** {f.get('affected_component','')}")
        L.append(f"- **Description:** {f.get('description','')}")
        L.append(f"- **Impact:** {f.get('impact','')}")
        if f.get("likelihood"): L.append(f"- **Likelihood:** {f['likelihood']}")
        ev = f.get("evidence")
        if ev:
            L.append(f"- **Evidence:** `{ev.get('location','')}`")
            L.append("  ```")
            for line in str(ev.get("detail", "")).splitlines() or [""]:
                L.append("  " + line)
            L.append("  ```")
        rem = f.get("remediation", {})
        rc = (" (" + ", ".join(rem.get("control_ids", [])) + ")") if rem.get("control_ids") else ""
        L.append(f"- **Remediation:** {rem.get('summary','')}{rc}")
        L.append(f"- **Status:** {f.get('status','')}")

    ta = a.get("technical_assessment", {})
    L += ["", "## Technical assessment"]
    if ta.get("profile"):
        L += [f"- **{k.replace('_',' ').title()}:** {v}" for k, v in ta["profile"].items() if v]
    if ta.get("capabilities"):
        L += ["", "| Tool | Function | Class |", "|---|---|---|"]
        L += [f"| `{c.get('name','')}` | {c.get('function','')} | {c.get('class','')} |" for c in ta["capabilities"]]
    auth = ta.get("authentication_and_credential_risk", {})
    if auth:
        L.append("")
        L += [f"- **{k.replace('_',' ').title()}:** {v}" for k, v in auth.items()]

    rr = a.get("risk_rating", {})
    if rr.get("factor_scores"):
        L += ["", "## Risk rating", "| Factor | Score |", "|---|---|"]
        L += [f"| {k.replace('_',' ').title()} | {v} |" for k, v in rr["factor_scores"].items()]
        L.append(f"| **Composite** | **{rr.get('composite')}** |")
        if rr.get("overrides_applied"):
            L.append(f"\nOverrides: {'; '.join(rr['overrides_applied'])}")

    L += ["", "## Limitations & disclaimer", compose_disclaimer(a)]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #

def preflight(a: dict, schema_path: Path) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        required = ["schema_version", "meta", "verdict", "overall_risk",
                    "executive_summary", "findings", "technical_assessment",
                    "risk_rating", "recommendations", "limitations"]
        missing = [k for k in required if k not in a]
        if missing:
            sys.exit(f"error: assessment is missing required keys: {missing}")
        print("warning: jsonschema not installed — ran a light structural check only.", file=sys.stderr)
        return
    if not schema_path.exists():
        print(f"warning: schema not found at {schema_path}; skipping validation.", file=sys.stderr)
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(a),
                    key=lambda e: list(e.path))
    if errors:
        for e in errors[:20]:
            loc = "/".join(str(p) for p in e.path) or "(root)"
            print(f"  schema error at {loc}: {e.message}", file=sys.stderr)
        sys.exit(f"error: assessment.json failed schema validation ({len(errors)} error(s)).")


def _find_browser():
    """Locate a Chromium-family browser for headless PDF export."""
    import shutil, os
    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    for path in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ):
        if os.path.exists(path):
            return path
    return None


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """Print an HTML file to PDF via headless Chrome/Edge (no Python dependency)."""
    browser = _find_browser()
    if browser is None:
        raise RuntimeError(
            "no Chromium browser found — install Chrome or Edge, or open the HTML and "
            "use Print > Save as PDF (searched PATH for chrome/chromium/msedge and the "
            "standard install locations)"
        )
    import subprocess, tempfile, shutil
    profile = Path(tempfile.mkdtemp(prefix="mcp-pdf-profile-"))
    url = html_path.resolve().as_uri()
    tail = ["--disable-gpu", "--no-pdf-header-footer",
            f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}", url]
    res = None
    try:
        for headless in ("--headless=new", "--headless"):
            pdf_path.unlink(missing_ok=True)
            res = subprocess.run([browser, headless, *tail],
                                 capture_output=True, text=True, timeout=120)
            if pdf_path.exists():
                return
        raise RuntimeError(
            f"headless print produced no file: {(res.stderr or res.stdout or '').strip()[:300]}"
        )
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render an assessment.json into report.html + report.md.")
    ap.add_argument("assessment", type=Path)
    ap.add_argument("-o", "--outdir", type=Path, help="Directory for report.html/report.md")
    ap.add_argument("--html", type=Path, help="Explicit HTML output path (appendix collapsed)")
    ap.add_argument("--md", type=Path, help="Explicit Markdown output path")
    ap.add_argument("--pdf", type=Path, help="Export a PDF via headless Chrome/Edge (appendix expanded so it is captured)")
    ap.add_argument("--no-validate", action="store_true", help="Skip the schema pre-flight")
    args = ap.parse_args()

    a = json.loads(args.assessment.read_text(encoding="utf-8"))
    if not args.no_validate:
        schema_path = args.assessment.parent.parent / "schema" / "assessment.schema.json"
        if not schema_path.exists():
            schema_path = Path(__file__).resolve().parent.parent / "schema" / "assessment.schema.json"
        preflight(a, schema_path)

    outdir = args.outdir or args.assessment.parent
    explicit = bool(args.html or args.md or args.pdf)
    written = []

    # HTML / Markdown: with explicit targets, write only what was asked; otherwise both.
    html_path = args.html or (None if explicit else outdir / "report.html")
    md_path = args.md or (None if explicit else outdir / "report.md")
    if html_path:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_html(a), encoding="utf-8")   # collapsed appendix
        written.append(html_path)
    if md_path:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_md(a), encoding="utf-8")
        written.append(md_path)

    # PDF: render a print variant with the appendix EXPANDED (a collapsed <details> is
    # never captured in print), then drive a headless browser to produce the PDF.
    if args.pdf:
        import sys, tempfile, shutil
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        tmpdir = Path(tempfile.mkdtemp(prefix="mcp-report-"))
        (tmpdir / "print.html").write_text(render_html(a, expand_appendix=True), encoding="utf-8")
        try:
            html_to_pdf(tmpdir / "print.html", args.pdf)
            written.append(args.pdf)
        except RuntimeError as e:
            if written:
                print("\n".join(f"wrote {p}" for p in written))
            print(f"PDF export skipped: {e}", file=sys.stderr)
            return 2
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n".join(f"wrote {p}" for p in written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
