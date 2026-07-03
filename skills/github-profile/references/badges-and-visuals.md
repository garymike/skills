# Badges and visuals

How to make a profile look intentional instead of templated. Design guidance
first, then the badge/icon mechanics.

## Avoiding the generic AI-README look

Most auto-generated profiles share the same tells. Steer away from all of these
unless the user explicitly wants them:

- A rainbow wall of 40 skill badges, many for tools the person barely uses.
- The `Hi 👋 I'm X` header with a waving-hand gif and nothing distinctive under
  it.
- Three live stats cards stacked with no editing, half of them not loading.
- A profile-views counter and a "visitor" badge.
- Generic taglines: "passionate", "aspiring", "love to code", "always learning".

What makes a profile feel senior and human instead:

- **One strong, specific opening line** that says what they build and for whom.
- **Restraint.** Empty space is a feature. A short profile from a strong person
  beats a long one padded with widgets.
- **Curation over completeness.** Show the 4 projects and 8 tools that matter.
- **A consistent accent color** used deliberately, not every color at once.
- **Everything clickable leads somewhere real.**

## Color

Pick one or two accent colors and hold to them across badges and any cards.

- Ask the user for a hex, or match an existing personal brand.
- shields.io badge color is the hex right after `badge/LABEL-` (no `#`), e.g.
  `...badge/Python-3776AB?...` uses `#3776AB`.
- For brand-accurate tech badges, use the tool's real brand color. For a
  themed/monochrome look, set every badge to the same accent hex and rely on the
  logo for recognition; a monochrome badge row looks far more designed than
  full-color chaos.
- Keep contrast readable: pair a dark badge background with `logoColor=white`
  and a light one with `logoColor=black`.

## shields.io badges

Endpoint shape:

```
https://img.shields.io/badge/<LABEL>-<HEXCOLOR>?style=<STYLE>&logo=<SLUG>&logoColor=<COLOR>
```

- `<LABEL>`: the text. Escape spaces as `%20`, and a literal dash as `--`.
- `<HEXCOLOR>`: 6-digit hex, no `#`.
- `style`: `flat` (default, recommended), `flat-square`, `plastic`,
  `for-the-badge` (all-caps, chunky). Pick one style and use it for every badge
  on the page. `flat` reads most professional; `for-the-badge` reads bolder.
- `logo`: a simple-icons slug (see below).
- `logoColor`: usually `white` or `black`.

As-a-link:

```markdown
[![LABEL](https://img.shields.io/badge/LABEL-HEX?style=flat&logo=SLUG&logoColor=white)](TARGET_URL)
```

## Icon slugs (simple-icons)

Both shields.io `logo=` and the `cdn.simpleicons.org` icon wall use
[simple-icons](https://simpleicons.org) slugs. The slug is the brand name
lowercased with spaces and dots removed (e.g. `github`, `visualstudiocode`,
`amazonaws`, `nextdotjs`). If a badge shows no logo, the slug is wrong; check the
name on simpleicons.org. Not every brand is in the set, and some logos were
removed for trademark reasons, so verify rather than guessing.

Direct icon (for an icon wall, no badge frame):

```
https://cdn.simpleicons.org/<slug>            # brand color
https://cdn.simpleicons.org/<slug>/<hexcolor> # forced color
```

## Layout mechanics in GitHub-flavored markdown

- **Centering:** wrap in `<div align="center">...</div>`. There is no CSS.
- **Rows of badges:** put them on one line separated by spaces, or inside a
  `<p>`. A blank line starts a new paragraph.
- **Columns:** use a markdown table. Tables are the only real multi-column tool.
- **Spacing between images:** `&nbsp;` or a couple of spaces; you cannot set
  margins.
- **Light/dark mode images:** use `<picture>` with `prefers-color-scheme` so the
  right asset shows in each theme:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.png">
  <img alt="NAME — TAGLINE" src="assets/banner-light.png">
</picture>
```

- **Collapsible detail** (good for a long tech list without visual weight):

```markdown
<details>
<summary>Full tech stack</summary>

... list ...

</details>
```

## Accessibility and resilience

- Alt text on every image. Screen readers and image-blocked networks depend on
  it, and recruiters often view GitHub through corporate proxies that strip
  external images.
- The page must still read well with all external images and cards failing to
  load. Test by mentally deleting every badge and SVG: is there still a
  coherent profile? If not, add real text.
