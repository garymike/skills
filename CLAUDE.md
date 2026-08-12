# Repo conventions

Notes for me (and any agent) on how skills in this repo are built and organized.

## Layout

- One folder per skill under `skills/`, named in kebab-case: `skills/<name>/SKILL.md`.
- Group into category subfolders once the collection grows (`skills/<category>/<name>/SKILL.md`), the way larger skill repos do. Keep it flat until categories earn their keep.
- Everything a skill needs is self-contained in its folder: `SKILL.md`, plus optional `references/`, `assets/`, and `scripts/`.

## SKILL.md

- YAML frontmatter with at least `name` and `description`.
- The `description` is the trigger. Say what the skill does and when to use it, and lean slightly pushy so it fires when it should. No angle brackets in the description (the packager rejects them).
- Progressive disclosure: keep `SKILL.md` lean (aim under 500 lines). Push long catalogs and detail into `references/` and point to them.
- Imperative voice. Explain why a step matters rather than piling on hard rules.

## Invocation model

- **User-invoked**: runs only when I type it. Job is to orchestrate. May call model-invoked skills, never another user-invoked one.
- **Model-invoked**: I can type it, or the agent reaches for it automatically when the task fits. Holds reusable discipline. Give it a strong triggering `description`.
- Record which is which in the README reference list.

## Safety

- Skills can execute code, so anything side-effectful (publishing, pushing, deleting, spending) gets an explicit confirm gate in the skill itself.
- Never handle secrets or tokens in-band. Defer auth to the user's own tooling (for example the `gh` CLI).

## Adding a skill

The fastest path is Anthropic's `skill-creator` skill: it scaffolds `SKILL.md`, helps you test it on real prompts, and packages a `.skill` file. Drop the resulting folder under `skills/`, add a line to the README reference, and bump the version in the two `.claude-plugin/*.json` files.

## Local install — junction, never a copy

Skills in this repo are exposed to Claude Code two ways, and only one of them is safe to hand-edit.

- `.claude-plugin/` makes the repo loadable as the `garymike-skills` plugin, but that only resolves when the working directory is this repo. Fine for repo work, useless for a skill like `github-security-audit` that you run from anywhere.
- `~/.claude/skills/<name>` makes a skill globally available. **This must be a junction into `skills/<name>`, never a copied folder.**

Create it with (no elevation needed — `ln -s` and `mklink /D` both require admin or Developer Mode, `mklink /J` does not):

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\<name>" -Target "<repo>\skills\<name>"
```

Verify nothing is a stray copy:

```powershell
Get-ChildItem "$env:USERPROFILE\.claude\skills" | Select-Object Name, LinkType, Target
```

A `LinkType` of `$null` on a skill this repo owns means someone dropped a real folder there and it is already drifting.

**Why this matters.** `github-security-audit` was a copied folder for weeks and diverged in *both* directions — the repo was ahead in `SKILL.md`, the copy was ahead in `REFERENCE.md`. Nothing warned about it, and the copy is what actually ran, so repo edits silently did nothing while the audit kept using stale guidance. A junction makes divergence structurally impossible: one set of bytes, edited in the repo, reviewed through a PR.

The trade-off to know about: a junction points at the working tree, so a checked-out feature branch is what runs. That is what you want while iterating on a skill; just don't leave a half-finished branch checked out and then wonder why a scheduled run behaved oddly.

## Releases

Track releases so the repo history matches the manifest version:

- The `version` in both `.claude-plugin/*.json` files is the source of truth. Bump it (semver) for any user-facing skill change.
- Record the change in `CHANGELOG.md` under a new version heading (Keep a Changelog format) in the same commit as the bump.
- Tag the release commit `vX.Y.Z` (annotated) so `git tag` matches the manifest. Tag on `main` after the change merges, not on a feature branch.
- Cut a GitHub Release for the tag (`gh release create vX.Y.Z`), reusing that version's `CHANGELOG.md` entry as the notes, so the Releases page mirrors the changelog.
