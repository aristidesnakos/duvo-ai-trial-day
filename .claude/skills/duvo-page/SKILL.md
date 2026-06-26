---
name: duvo-page
description: Convert a Markdown deliverable (brief, proof pack, case study, runbook) into a self-contained, Duvo-branded HTML page you can hand to a client. Use when the user wants to share an .md file as a styled web page, "make this shareable", "turn this into HTML", or produce a client-facing one-pager. Deterministic, stdlib-only — no dependencies.
---

# duvo-page — Markdown → shareable Duvo-branded HTML

Turns any Markdown deliverable into one self-contained `.html` file (CSS inlined, no
external assets, no JS) styled in the Duvo brand: warm off-white ground, near-black ink,
the Duvo yellow accent, a faint grid, and monospace tabular figures for euros. Safe to
email or drop on a static host.

## When to use

- "Make this shareable / turn this into a page / send this to the client."
- Packaging an FDE deliverable (`PROJECT-BRIEF.md`, `PROOF-PACK.md`, `CASE-STUDY.md`,
  a runbook) as branded HTML.

For a **bespoke, hand-designed** one-pager (custom hero, stat strip, callouts) the
converter is the wrong tool — author the HTML directly. The converter is for fast,
consistent, repeatable output across many documents. `presentation/case-study.html` is
an example of the bespoke kind; this skill produces the repeatable kind.

## Usage

```bash
python3 .claude/skills/duvo-page/md2html.py INPUT.md [-o OUTPUT.html] \
  [--title "..."] [--subtitle "..."] [--eyebrow "..."] [--brand "..."]
```

- `INPUT.md` — the Markdown file. **Read-only**; never modified.
- `-o OUTPUT.html` — output path. Default: `INPUT.html` next to the input. For client
  packets, prefer `presentation/<name>.html`.
- `--title` — page title + `<h1>`. **Default: the document's first `#` H1**, which is
  then removed from the body so it is not rendered twice.
- `--subtitle` — optional one-line lede under the title.
- `--eyebrow` — small uppercase label above the title (default `Duvo`).
- `--brand` — masthead label (default `FDE Deliverable`).

Example (this repo):

```bash
python3 .claude/skills/duvo-page/md2html.py PROOF-PACK.md -o presentation/proof-pack.html \
  --eyebrow "Proof pack · Q1 2026"
```

## What it supports

ATX headings (`#`..`######`), paragraphs, **bold** / *italic* / `inline code`, links,
unordered + ordered lists, GitHub pipe tables (wrapped in a horizontal-scroll container),
fenced code blocks, horizontal rules, and YAML front matter (stripped). Tables get
tabular-nums on every non-first column — ideal for euro figures.

**Not** supported (by design — these deliverables don't need it): nested lists, inline
HTML passthrough, footnotes, images. If a doc relies on those, fall back to authoring HTML.

## After converting

Open the output and check tables rendered, no stray Markdown (`**`, `|`) leaked, and links
resolve. The script is deterministic: same Markdown in → byte-identical HTML out, so it is
safe to regenerate in a build step or re-run after editing the source `.md`.

To change the look, edit the `CSS` string at the top of `md2html.py` — it is the single
source of the theme.
