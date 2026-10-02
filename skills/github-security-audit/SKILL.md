---
name: github-security-audit
description: Audit GitHub account and repositories for security misconfigurations, then fix findings interactively. Use when user asks to audit GitHub security, check repo security settings, harden GitHub account, review GitHub repos for vulnerabilities, or run a GitHub security check. Also use when user adds new repos and wants to bring them up to baseline.
---

# GitHub Security Audit

## Quick start

```bash
gh api user --jq '{login: .login, name: .name}'
gh repo list <owner> --limit 100 --json name,isPrivate,isArchived,isFork,isSecurityPolicyEnabled,defaultBranchRef,pushedAt,visibility,deleteBranchOnMerge,primaryLanguage
```

Skip archived repos and forks for most checks.

## Cost rule — always apply before fixing

**Before enabling any feature, state whether it's free or paid.** Never enable a paid feature without explicit user confirmation. See the [free vs paid table](REFERENCE.md#free-vs-paid) for the full breakdown. When in doubt: Dependabot, delete-on-merge, gitleaks, and Actions hardening are always free.

## Audit checklist

Run all checks per active non-fork repo. Run in parallel where possible.

### Identity & access (manual — ask user to verify)
- [ ] 2FA enabled with TOTP app or hardware key (not SMS) — github.com/settings/security
- [ ] OAuth apps reviewed and unknown apps revoked — github.com/settings/applications
- [ ] Personal access tokens audited, unused ones revoked — github.com/settings/tokens
- [ ] SSH keys scoped to active machines only — github.com/settings/keys
- [ ] Collaborators reviewed, former contributors removed

### Per-repo automated checks
- [ ] **Dependabot alerts** enabled (`gh api repos/<owner>/<repo>/vulnerability-alerts`)
- [ ] **Dependabot auto-fix** enabled (`gh api repos/<owner>/<repo>/automated-security-fixes`)
- [ ] **Open alerts, all states** — query `open` *and* `auto_dismissed`, never `open` alone. See [alert reality checks](REFERENCE.md#dependabot-alert-reality-checks).
- [ ] **Dependabot updater health** — check the run conclusions of the `Dependabot Updates` workflow. A failing updater invalidates the alert count.
- [ ] **Dependabot ecosystems** — compare declared `package-ecosystem` entries against the manifests present. Security updates fire without one; routine version updates do not.
- [ ] **Secret scanning** — public repos: native (free); private repos: check for gitleaks workflow
- [ ] **Push protection** — public repos only on free plan (blocks secret commits natively)
- [ ] **Branch protection** — public repos: check rules; private repos: note Pro required
- [ ] **Signed commits** enforced on default branch (public repos only on free plan)
- [ ] **Actions default permissions** set to read-only
- [ ] **Action version pinning** — scan `.github/workflows/` for unpinned tags
- [ ] **Delete-branch-on-merge** enabled
- [ ] **SECURITY.md** exists (public repos especially)
- [ ] **CodeQL** analysis enabled (free for public repos)
- [ ] **Sensitive files** in public repos (scan git tree for `.env`, `.pem`, `.key`, credentials)
- [ ] **Visibility intent** — read `.github/repo-metadata.yml`; compare `visibility:` field against actual repo visibility; flag mismatches as a finding. If file is missing, note it and infer intent from README/description as a fallback. If user has explicitly confirmed visibility, treat as acknowledged.
- [ ] **Workflow run health** — a repo can have `security.yml` and still be scanning nothing. Check per trigger, not just the newest run. See [workflow run health](REFERENCE.md#workflow-run-health).

#### Why workflow health needs its own check

Configuration presence is not coverage. Three failure modes hide from a normal glance, and all three have been found in this estate:

- **`startup_failure` is silent.** The workflow never starts, so there are no jobs, no logs, and no annotations — just a bare red X that reads like an infra blip. Most often caused by a reusable workflow requesting a permission the caller withheld: the caller's `permissions:` block is a hard ceiling, and GitHub rejects the mismatch before any job runs.
- **Schedule-gated jobs are invisible on PRs.** A job behind `if: github.event_name == 'schedule'` never runs on push or pull_request, so green PR checks can sit on top of a scheduled job that has failed every week for a month.
- **Stale pins rot silently.** A caller pinned to an old SHA keeps running old logic, including bugs the shared workflow has since fixed. Pinning is still correct — but pins need a refresh cadence, and drifting pins fail in the opposite direction from `@main`.

#### Why the alert count needs its own check

The same lesson one level down: a zero in the alerts list is not the same as nothing to find. Four mechanisms make it understate exposure, and all four have been hit here.

- **`state=open` hides `auto_dismissed`.** A high-severity `nanoid` advisory sat auto-dismissed for seven weeks behind a zero-length `state=open` response. The default auto-triage rule closes anything at `scope=development`, on the premise that dev dependencies never reach production — false for any bundled frontend, where the build output ships to users.
- **A failing updater stops alerts being *created*,** not just PRs being opened. One repo showed 8 open advisories while the true figure was 20; the other 12 appeared seconds after a merge finally gave the updater a clean rescan. A red updater is a reporting outage, not a patching delay.
- **Merging a Dependabot PR need not clear its advisory.** A second copy can sit at a hard pin elsewhere in the tree, so the count does not move. Confirm against the lockfile, not the merge.
- **Sequential lockfile merges can revert a landed fix,** silently, in seconds. Merge one at a time or require up-to-date branches.

### Stale / risky repos
- [ ] Old public repos with no apparent purpose (archive or make private)
- [ ] Public forks that are stale (archive)

## Reporting findings

Always use this exact three-section structure — do not deviate:

### Section 1 — Summary table (repo × check)

One row per active non-fork repo. Columns in this order:

| Repo | Visibility | Dependabot alerts | Auto-fix | Actions perms | Branch protection | Secret scanning | security.yml | Workflow health | SECURITY.md | repo-metadata.yml | Delete-on-merge |

Use ✅ / ❌ / ⚠️ in each cell. Add a short inline note where context helps (e.g. "read-only", "native", "gitleaks", "n/a (Pro)", "mismatch"). Use footnotes (¹ ²) for exceptions that need more explanation. This table is the first thing the user sees.

**Dependabot alerts** is scored on `open` **plus** `auto_dismissed`, and only counts as ✅ when the updater's last run succeeded. Mark ⚠️ with the count where alerts are outstanding, and ❌ where the updater is failing — a zero taken from a red updater is not a zero.

**Workflow health** is scored on the last run of *each* trigger, not the newest run overall. Mark ❌ for `startup_failure` or a failing scheduled run, ⚠️ for a stale pin or a repo whose scheduled run has never fired, ✅ only when both push and schedule are green. Never let a green push run stand in for a scheduled one.

### Section 2 — Findings by severity

After the table, list findings grouped under **High**, **Medium**, and **Low** headers. Each finding is a bullet with: what's wrong, which repos are affected, and one-line explanation of impact. Skip a severity group if there are no findings in it.

Severity definitions:
- **High** — Dependabot off, secrets hardcoded in public repo, 2FA not confirmed, push protection off on public repo, `security.yml` failing at `startup_failure` (present but scanning nothing), an open or auto-dismissed high/critical advisory, a failing Dependabot updater (the alert count cannot be trusted while it is red)
- **Medium** — No branch protection on public repos, gitleaks missing on private repos, Actions permissions not read-only, unpinned action versions, missing `security.yml` on repos that should have it, scheduled security run failing, caller pinned to a SHA with a known-fixed bug, auto-triage rule left on for a repo whose build output ships to users, no required status checks on a repo with CI
- **Low** — Delete-on-merge off, no SECURITY.md, CodeQL not enabled, stale public repos, missing `repo-metadata.yml`, caller pin more than ~4 weeks behind the shared workflow, Dependabot ecosystems missing for manifests that are present (security updates still fire; routine bumps do not)

Report a red Dependabot updater as its own finding, above the alerts it was supposed to raise. Like a broken `security.yml`, it reads as covered on every other check.

Report a broken workflow as its own finding with the failing step named, not as a footnote on the `security.yml` column. "Present but broken" is worse than absent, because it reads as covered on every other check.

### Section 3 — Proposed fixes table

One row per distinct fix. Columns: **Fix** | **Repos** | **Cost**. Only list free fixes unless the user has pre-approved paid ones. End with a one-line note: "Say the word and I'll batch-apply the free fixes (or a subset)."

Then add the account-level manual reminder (2FA, OAuth apps, PATs, SSH keys) as a brief bulleted list after the table.

## Fixing findings

Offer to fix each finding. For every fix:
1. State whether it's free or requires a paid plan
2. Get confirmation before acting on anything paid
3. Apply free fixes in bulk where possible

See [REFERENCE.md](REFERENCE.md) for exact commands for every fix.

## Incremental audit (new repos only)

When user adds a new repo, check only that repo against the same checklist and apply the same fixes. Don't re-run the full audit unless asked.

Also check whether the new repo was created from `garymike/repo-template`. If not, it will be missing `.github/workflows/security.yml` — offer to add the caller workflow so it hooks into the reusable workflows in `garymike/security-workflows`.

## Scheduled routine

This skill should be run on a weekly schedule to catch:
- New repos not created from the template (missing `security.yml`)
- Drift in settings (Dependabot disabled, Actions permissions changed, etc.)
- Account-level items GHA cannot check (OAuth apps, PATs, SSH keys, 2FA method)

The scheduled task (`weekly-github-security-audit`) simply invokes this skill — all logic lives here, not in the task prompt.

## Architecture reference

```
Prevention  →  garymike/repo-template (new repos start with security.yml pre-wired)
Enforcement →  garymike/security-workflows (reusable GHA — runs on every push/PR + weekly)
Detection   →  Claude weekly routine (cross-repo view, account-level, new repo detection)
```

See [garymike/security-workflows](https://github.com/garymike/security-workflows) for the reusable workflow source.
See [garymike/repo-template](https://github.com/garymike/repo-template) for the template all new repos should use.
