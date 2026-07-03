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
