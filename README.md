# Skills

My personal [Agent Skills](https://agentskills.io). Straight from my `.claude` directory.

Small, composable skills that encode repeatable engineering and workflow discipline. They work with any model, are easy to adapt, and are meant to be forked and made your own.

## Quickstart

Install with the skills.sh installer and pick what you want:

```bash
npx skills@latest add garymike/skills
```

Or register the repo as a Claude Code plugin marketplace:

```
/plugin marketplace add garymike/skills
/plugin install garymike-skills@garymike-skills
```

Or install a single skill by hand:

```bash
git clone https://github.com/garymike/skills
cp -r skills/skills/github-security-audit ~/.claude/skills/github-security-audit
```

## Reference

Skills split on one axis: who can invoke them. **User-invoked** skills run only when you type them (for example `/some-skill`) and usually orchestrate. **Model-invoked** skills can be typed by you or reached for automatically by the agent when the task fits.

### Developer presence

**Model-invoked**

- **[github-profile](skills/github-profile/SKILL.md)** — Design, build, refresh, and deploy a GitHub profile README (the special `username/username` repo). Runs a style interview, composes from a section and badge library, deploys via the GitHub API behind a confirm gate, and offers opt-in automation add-ons.

- **[github-security-audit](skills/github-security-audit/SKILL.md)** — Audit a GitHub account and all repositories for security misconfigurations, then fix findings interactively. Covers Dependabot, secret scanning, branch protection, Actions permissions, action version pinning, CodeQL, SECURITY.md, and visibility intent. Pairs with [garymike/security-workflows](https://github.com/garymike/security-workflows) (reusable GHA enforcement) and [garymike/repo-template](https://github.com/garymike/repo-template) (pre-wired new repo template) for a full defense-in-depth setup.

More skills land here as I build them.

## Writing your own

Conventions for authoring skills in this repo live in [CLAUDE.md](CLAUDE.md). The short version: one folder per skill under `skills/`, a `SKILL.md` with `name` and `description` frontmatter, and progressive disclosure (keep `SKILL.md` lean, push detail into `references/`). Anthropic's `skill-creator` skill is the fastest way to scaffold and test a new one.

## License

[MIT](LICENSE).
