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

### Stale / risky repos
- [ ] Old public repos with no apparent purpose (archive or make private)
- [ ] Public forks that are stale (archive)

## Reporting findings

Always use this exact three-section structure — do not deviate:

### Section 1 — Summary table (repo × check)

One row per active non-fork repo. Columns in this order:

| Repo | Visibility | Dependabot alerts | Auto-fix | Actions perms | Branch protection | Secret scanning | security.yml | SECURITY.md | repo-metadata.yml | Delete-on-merge |

Use ✅ / ❌ / ⚠️ in each cell. Add a short inline note where context helps (e.g. "read-only", "native", "gitleaks", "n/a (Pro)", "mismatch"). Use footnotes (¹ ²) for exceptions that need more explanation. This table is the first thing the user sees.

### Section 2 — Findings by severity

After the table, list findings grouped under **High**, **Medium**, and **Low** headers. Each finding is a bullet with: what's wrong, which repos are affected, and one-line explanation of impact. Skip a severity group if there are no findings in it.

Severity definitions:
- **High** — Dependabot off, secrets hardcoded in public repo, 2FA not confirmed, push protection off on public repo
- **Medium** — No branch protection on public repos, gitleaks missing on private repos, Actions permissions not read-only, unpinned action versions, missing `security.yml` on repos that should have it
- **Low** — Delete-on-merge off, no SECURITY.md, CodeQL not enabled, stale public repos, missing `repo-metadata.yml`

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
