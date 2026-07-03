# Content blocks

A library of README sections. Each block is copy-paste markdown or HTML. Mix and
match; nothing here is mandatory. Replace every placeholder in `ALL_CAPS` or
`<angle-brackets>`.

## Table of contents

- [Headers and banners](#headers-and-banners)
- [Identity line and about](#identity-line-and-about)
- [Skills and tech stack](#skills-and-tech-stack)
- [Featured projects](#featured-projects)
- [Stats block](#stats-block)
- [Contact and links](#contact-and-links)
- [Footer](#footer)

Note on HTML in READMEs: GitHub allows a safe subset of HTML. `<div align>`,
`<img>`, `<a>`, `<table>`, `<picture>`, `<details>`, `<sub>`/`<sup>`, and `<br>`
all work. `<style>`, `<script>`, class-based CSS, and most attributes are
stripped. Center things with `<div align="center">`, not CSS.

---

## Headers and banners

**Plain, senior-feeling header (no image):**

```markdown
# NAME

**ONE-LINE IDENTITY.** SECOND SENTENCE OF CONTEXT.
```

**Centered header with tagline:**

```html
<div align="center">
  <h1>NAME</h1>
  <p><em>ONE-LINE IDENTITY</em></p>
</div>
```

**Banner image (host it in the repo under `assets/`):**

```markdown
![NAME — TAGLINE](assets/banner.png)
```

Always include descriptive alt text so the header still reads when the image is
blocked. Design a custom banner rather than using a stock template; a distinct
banner is one of the few things that makes a profile memorable. If generating one
is out of scope, prefer no banner over a generic one.

**Typing SVG header (animated, dynamic add-on):** see
`dynamic-addons.md` (readme-typing-svg). Use sparingly.

---

## Identity line and about

The identity line is the most important sentence on the page. Make it concrete.

Weak: `Passionate software engineer who loves coding.`
Strong: `Security architect building adaptive, biology-inspired defenses for
financial-services and critical-infrastructure systems.`

**About block:**

```markdown
## About

IDENTITY LINE.

- Currently: WHAT THEY ARE FOCUSED ON NOW
- Working toward: WHAT THEY WANT MORE OF / A GOAL
- Ask me about: A TOPIC THEY CAN GO DEEP ON
- Off the clock: A HUMAN DETAIL (optional, only if it fits the audience)
```

**Prose "about" (editorial direction):**

```markdown
## About

Two or three tight sentences in the person's own voice. Say what they build,
who it is for, and what they care about getting right. No filler adjectives.
```

**Terminal-style "whoami" (terminal direction):**

````markdown
```bash
$ whoami
NAME — ROLE

$ cat focus.txt
- FOCUS AREA 1
- FOCUS AREA 2
- FOCUS AREA 3
```
````

---

## Skills and tech stack

Keep this honest and relevant. A wall of every tool ever touched reads as noise;
a curated set reads as judgment. Group by category when the list is long.

**Badge row (shields.io + simple-icons), one category:**

```markdown
### Languages

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)
![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)
```

See `badges-and-visuals.md` for badge styles, color rules, and how to find the
correct `logo=` slug for any tool.

**Grouped table (scales to many categories without a giant single row):**

```markdown
## Tech

| | |
|---|---|
| **Languages** | Python, Rust, Go |
| **Cloud** | AWS, Azure |
| **Security** | Threat modeling, IAM, detection engineering |
| **Tooling** | Terraform, GitHub Actions |
```

**Icon wall (simple-icons via CDN, compact):**

```markdown
<p>
  <img src="https://cdn.simpleicons.org/python" height="28" alt="Python" />
  <img src="https://cdn.simpleicons.org/rust" height="28" alt="Rust" />
  <img src="https://cdn.simpleicons.org/go" height="28" alt="Go" />
</p>
```

---

## Featured projects

Show the work, not a wall of every repo. 2 to 5 items, each with a reason to
click. Real links only.

**List form:**

```markdown
## Featured work

- **[PROJECT_NAME](URL)** — ONE LINE ON WHY IT MATTERS OR WHAT IT DOES.
- **[PROJECT_NAME](URL)** — ONE LINE.
```

**Card grid (2-up table):**

```markdown
## Featured work

| | |
|---|---|
| **[PROJECT_A](URL)**<br>What it does in one line. | **[PROJECT_B](URL)**<br>What it does in one line. |
| **[PROJECT_C](URL)**<br>What it does in one line. | **[PROJECT_D](URL)**<br>What it does in one line. |
```

**Pinned-repo cards (dynamic, via github-readme-stats):** see
`dynamic-addons.md`. Useful when the user wants live repo metadata, but static
cards above are more reliable and load faster.

---

## Stats block

Static is the safe default (renders everywhere). Live stats cards are an opt-in
add-on covered in `dynamic-addons.md`; mention that some networks block them.

**Simple static "at a glance":**

```markdown
## At a glance

- N public repositories
- Maintainer of PROJECT
- Writes about TOPIC at LINK
```

If the user wants the familiar live cards (stats, streak, top languages,
trophies), route to `dynamic-addons.md` and place them here.

---

## Contact and links

Only publish what the user approves. Ask before adding email or any handle.

**Badge row:**

```markdown
## Elsewhere

[![Website](https://img.shields.io/badge/Website-000000?style=flat&logo=firefox&logoColor=white)](URL)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](URL)
```

**Plain links (calmer, fits minimal/editorial):**

```markdown
## Elsewhere

- Website: <URL>
- LinkedIn: <URL>
```

---

## Footer

Keep it light or skip it. Avoid the profile-views counter unless the user
specifically wants it; it reads as dated to many viewers.

```markdown
---
<sub>Open to COLLABORATION_TYPE. Reach out via the links above.</sub>
```
