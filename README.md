# Skills

My personal [Agent Skills](https://agentskills.io). Straight from my `.claude` directory.

Small, composable skills that encode repeatable engineering and workflow discipline. They work with any model, are easy to adapt, and are meant to be forked and made your own.

Two of these are the assess half of a small security platform: `mcp-security-review` and `skill-security-review` produce the risk-rated reviews that [security-workflows](https://github.com/garymike/security-workflows) turns into a build-failing gate and [security-agents](https://github.com/garymike/security-agents) compiles into a runtime firewall. `secure-mcp-builder` is the build-side counterpart, for building an MCP server securely from the start rather than assessing one after the fact. The rest are general engineering skills, all of them personal and forkable.

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

- **[github-profile](skills/github-profile/SKILL.md)**. Design, build, refresh, and deploy a GitHub profile README (the special `username/username` repo). Runs a style interview, composes from a section and badge library, deploys via the GitHub API behind a confirm gate, and offers opt-in automation add-ons.

- **[github-security-audit](skills/github-security-audit/SKILL.md)**. Audit a GitHub account and all repositories for security misconfigurations, then fix findings interactively. Covers Dependabot, secret scanning, branch protection, Actions permissions, action version pinning, CodeQL, SECURITY.md, and visibility intent. Pairs with [garymike/security-workflows](https://github.com/garymike/security-workflows) (reusable GHA enforcement) and [garymike/repo-template](https://github.com/garymike/repo-template) (pre-wired new repo template) for a full defense-in-depth setup.

### MCP security

**Model-invoked**

- **[mcp-security-review](skills/mcp-security-review/SKILL.md)**. Assess any MCP server (vendor, open-source, or first-party; local or remote) as a security architect and produce a standardized, risk-rated report: identity, capabilities, permissions, auth, credential risk, findings, and a computed rating. Chooses review modes by available access (code / live / sandbox), authors a schema-valid `assessment.json`, and renders it to HTML + Markdown. Pairs with [garymike/security-workflows](https://github.com/garymike/security-workflows) (the `mcp-review-toolbox` it can drive) and the `mcp-reviewer` agent in [garymike/security-agents](https://github.com/garymike/security-agents).

- **[secure-mcp-builder](skills/secure-mcp-builder/SKILL.md)**. Design, threat-model, build, and harden production-grade MCP servers (Python or TypeScript, stdio or remote HTTP). Four phases with a required threat model and review gate, a normative security-requirements catalog mapped to the MCP spec and the OWASP MCP/Agentic Top 10, and a bundled capability-eval harness. The build-side complement to `mcp-security-review`.

### Skill security

**Model-invoked**

- **[skill-security-review](skills/skill-security-review/SKILL.md)**. Assess any agent skill across both execution surfaces: the agent-execution surface (`SKILL.md` + agent-invoked scripts: prompt injection, tool poisoning, memory poisoning) and the developer-execution surface (bundled test files, git hooks, and npm/pip lifecycle scripts that auto-run on `npm test` / `git commit` / `npm install`, outside the agent, with the developer's own permissions, a surface advisory scanners flag but do not gate on). Authors a schema-valid `assessment.json`, findings-first. The methodology behind the `skill-auditor` agent in [garymike/security-agents](https://github.com/garymike/security-agents); escalates from the `skill-testfile-gate` in [garymike/security-workflows](https://github.com/garymike/security-workflows).

More skills land here as I build them.

## Writing your own

Conventions for authoring skills in this repo live in [CLAUDE.md](CLAUDE.md). The short version: one folder per skill under `skills/`, a `SKILL.md` with `name` and `description` frontmatter, and progressive disclosure (keep `SKILL.md` lean, push detail into `references/`). Anthropic's `skill-creator` skill is the fastest way to scaffold and test a new one.

## License

[MIT](LICENSE) covers the skills and their original content.

One bundled component is third-party: the capability-eval harness under
`skills/secure-mcp-builder/scripts/` (`evaluation.py`, `connections.py`,
`example_evaluation.xml`) is adapted from the [`mcp-builder`](https://github.com/anthropics/skills)
skill in `anthropics/skills` and remains under the Apache License 2.0. See
`skills/secure-mcp-builder/scripts/LICENSE.txt`.
