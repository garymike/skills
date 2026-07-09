# Report quality rubric

The gate that keeps "best-in-class" from becoming an infinite subjective loop. A rendered report ships only if it passes every **must-pass** item. The **do-not-reintroduce** list captures refinements the owner has vetoed — never re-add them, even if a later "improvement" suggests it. Calibrate visual polish against the exemplars, not by taste alone.

## Must-pass (objective)

- [ ] **Decision-carrying TLDR.** The executive summary alone lets an approver decide: verdict banner (verdict-first), overall rating, severity-count chips, posture paragraph, top findings, scope line, conditions (if any).
- [ ] **Every finding is complete.** id, title, ordinal severity, category (OWASP MCP + review part + control IDs), affected component, verification badge, description, impact, remediation.
- [ ] **CVSS only where it fits.** A CVSS 4.0 vector appears only on genuine software-vuln findings; never on governance/composition/provenance findings.
- [ ] **Evidence on Critical/High.** Present and **redacted** — location + type + masked value; the report never reproduces a live secret/token.
- [ ] **Remediation cross-linked.** Each fix references the `secure-mcp-builder` control ID(s) that implement it.
- [ ] **Verification honesty.** Every finding carries `reasoned` / `observed` / `confirmed`; the disclaimer ties to it and points at the validator path.
- [ ] **Limitations & disclaimer present.** Point-in-time, methodology bounds, not-a-warranty, coverage gaps (`checks_not_performed`).
- [ ] **Renders clean.** Valid HTML; multi-page PDF with no finding card split across a page break, and the appendix (full `assessment.json`) **expanded in the PDF** so the machine-readable record is captured (a collapsed `<details>` prints empty). HTML keeps the appendix collapsed.
- [ ] **Grayscale-safe.** Severity is legible with color removed (color is always paired with a text label).
- [ ] **Schema-valid.** The source `assessment.json` passes `assessment.schema.json` (renderer fails closed otherwise).

## Visual conventions (agreed)

- Direction: clean modern minimalist. **Muted, earthy palette** (no loud/saturated primaries).
- Sections are **differentiated as bounded panels**, not a flat wall of text.
- Section order: cover → executive summary → recommendations → scope & methodology → findings → technical assessment → risk rating → limitations & disclaimer → appendix.
- Appendix (full `assessment.json`) is **collapsed by default** (expandable).
- Evidence in monospace blocks; control IDs as small chips.

## Rejected refinements — do not reintroduce

*(Appended whenever the owner vetoes something. Do not undo these.)*

- **Bold/saturated severity + verdict colors** (e.g. bright reds `#7f1d1d`/`#b91c1c`, bright blue `#1d4ed8`). Too loud — use muted earthy tones. _(2026-07-03)_
- **Flat, undifferentiated sections** separated only by a hairline rule. Sections must read as distinct bounded panels. _(2026-07-03)_
- **Appendix expanded inline** in the HTML. Keep it collapsed/expandable. _(2026-07-03)_
- **Sparse cover** with only a title and two pills — reads as missing data. The cover must carry identity, a profile grid of the MCP under assessment, and the outcome. _(2026-07-03)_
- **Mismatched verdict vs. rating pill sizes** — the larger verdict pill read as a rendering error. Outcome pills are equal weight/size, each under a small label. _(2026-07-03)_
- **Outcome pills stacked at the bottom of the cover** — put them top-right, using the dead space beside the identity block. _(2026-07-03)_
- **Profile as stacked label-over-value** (dt over dd) — wastes vertical space. Use compact inline `label: value` rows laid out in columns. _(2026-07-03)_
- **Cryptic finding ids in the human-facing report** (e.g. `F-01`). Display as `Finding-01` everywhere shown (card, exec summary, recommendations); the terse data id can stay as the internal key. _(2026-07-03)_
- **Finding ref not right-aligned in the exec-summary top-findings list** — right-justify the `(Finding-NN)` so titles left-align and refs align on the right. _(2026-07-03)_
- **Single-line finding header** cramming id + title + badges together. Use a two-line header (id + tags row, then the title) with a divider before the key/value content. _(2026-07-03)_
- **Wide label column in finding detail** leaving a big gap between field labels and their values. Keep the label column tight (~100px) so values sit close to their labels. _(2026-07-03)_
- **Risk-rating table with uneven columns and an un-emphasized composite** — use equal-width columns and highlight the composite row (darker band, prominent label) so the headline score stands out. _(2026-07-03)_
- **Technical-assessment sub-tables misaligned** (each its own column widths), long wrapping field labels, and raw Python booleans (`False`). Use consistent aligned key/value grids across sub-sections, short labels, boolean formatting (Yes/No), and a colored dot per sub-section as the differentiator. _(2026-07-03)_
- **Recommendation number anchored to the top line** of multi-line items. Vertically center the number against its full content (flex `align-items:center`), so 1/2/3-line recs all look uniform. _(2026-07-03)_
- **Capabilities as a wide horizontal table** (Tool/Function/Class/Annotations columns). List capabilities vertically in a **2-column grid** (they're short — use the width), one block per tool: name + a **filled muted-dark, light-text class chip** (READ/WRITE) — *not* stoplight-colored; `destructive` gets a subtly warmer muted tone to flag it. Then function and annotations. Divide the Technical-assessment sub-sections with a hairline so Profile / Capabilities / Auth / Composition read as distinct. _(2026-07-03)_
- **Left accent bar to distinguish the top sections**, *and* faint tints that land between `--paper` and `--panel` (e.g. `#f4eee1`) — they read as *duller* panels, not standouts. Instead give the two hero sections their own distinct muted-tint tiles, differentiated by **hue** (not just lightness): **Executive summary = warm-blue** (`#dce3ed`, border `#c2cfe0`); **Recommendations = sage-green** (`#e3e9d8`, border `#ccd8b8`). They read as different-in-kind from each other and from the near-white panels; keep each light enough that muted labels stay ≥4:1. _(2026-07-03)_
- **Recommendations as an undivided stack.** Separate each recommendation with a hairline divider (`.rec + .rec` top border) so a multi-item list reads as discrete actions, not a run-on block. _(2026-07-03)_
- **A standalone verification legend** (vertical list, or a horizontal tab/selector strip) explaining `reasoned`/`observed`/`confirmed`. The report is short enough not to need one; the disclaimer defines the scale and each finding's badge carries a native hover `title` tooltip. Do not add a visible legend unless explicitly asked. _(2026-07-03)_
- **"Tier N" in the human-facing report** — unexplained jargon, easily conflated with the risk rating. Show plain-language depth only (`Fast pass` / `Standard review` / `Full review`), explain each in Scope & methodology, and keep the numeric `tier` **only** in the machine block for register comparability. Do not surface "Tier N" in reader-facing text at all. _(2026-07-03)_

## Cover conventions

- **Source link** to the assessed artifact goes as a clickable subtitle under the server name, **pinned to the reviewed commit** (`…/tree/<sha>`) when a commit SHA is present, with a print-usable host/path as the link text.
- **Provenance / trust-at-a-glance strip** under the source link: a plain-language label **derived from the provenance risk factor** (never a separate fabricated score) plus raw signal chips — stars, forks, original-vs-fork (`fork of owner/repo`), owner followers, public repos, account age, last activity. Gate it on the presence of actual `provenance` data; omit entirely for non-repo / remote-SaaS targets (do not show a bare label with no signals). Render the label **inline, leading the signals as one flowing line** (not a flex row that orphans the pill on its own line).
- **Cover outcome pills** (Recommendation / Overall risk) stay pinned **top-right**; the identity block (name, source link, provenance) must shrink/wrap its own content rather than pushing the pills onto a new line. _(2026-07-03)_

## Calibration exemplars

For layout/density only (synthesize, never copy): the app-sec / source-code assessment reports in [juliocesarfort/public-pentesting-reports](https://github.com/juliocesarfort/public-pentesting-reports) — **Cure53, Trail of Bits, Doyensec, Include Security**. Their structure (exec summary → findings with severity/evidence/remediation → appendices) maps 1:1 to this skill.
