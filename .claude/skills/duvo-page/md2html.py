#!/usr/bin/env python3
"""md2html — convert a Markdown deliverable into a self-contained, Duvo-branded HTML page.

Zero dependencies (stdlib only), deterministic: same Markdown in -> same HTML out.
Designed for FDE deliverables (briefs, proof packs, case studies) you hand to a client.

Usage:
    python3 md2html.py INPUT.md [-o OUTPUT.html] [--title "..."] [--subtitle "..."]

If --title is omitted, the document's first H1 is used (and removed from the body so
it is not rendered twice). If -o is omitted, OUTPUT is INPUT with a .html suffix.

Supported Markdown: ATX headings (#..######), paragraphs, bold/italic/inline-code,
links, unordered + ordered lists, blockquotes, GitHub pipe tables, fenced code blocks
(``` ```), horizontal rules, and YAML front matter (stripped). Nested lists are not
supported — these deliverables use flat lists + tables.
"""
import argparse
import html
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------------- theme
CSS = """
  :root{
    --bg:#f7f6f1; --panel:#ffffff; --ink:#191c20; --ink-soft:#4f545c;
    --ink-faint:#9ba0a6; --rule:#e6e3db; --rule-2:#efede7;
    --accent:#f2d044; --accent-deep:#caa413; --good:#2e7d5b; --risk:#b4503f;
    --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
    --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink-soft);font-family:var(--sans);
    font-size:17px;line-height:1.65;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
    background-image:linear-gradient(var(--rule-2) 1px,transparent 1px),linear-gradient(90deg,var(--rule-2) 1px,transparent 1px);
    background-size:46px 46px;background-position:center;}
  .wrap{max-width:820px;margin:0 auto;padding:clamp(34px,6vw,64px) clamp(20px,5vw,40px) 110px}
  .mast{display:flex;align-items:center;gap:10px;padding-bottom:20px;margin-bottom:clamp(26px,4vw,40px);
    border-bottom:1px solid var(--rule);font-family:var(--mono);font-size:11px;letter-spacing:.16em;
    text-transform:uppercase;color:var(--ink-faint)}
  .mast .dot{width:12px;height:12px;border-radius:3px;flex:none;background:var(--accent)}
  .mast .live{margin-left:auto;color:var(--ink);background:var(--accent);padding:4px 11px;
    border-radius:999px;letter-spacing:.1em;font-weight:700}
  header.doc{margin-bottom:clamp(28px,5vw,44px)}
  header.doc .eyebrow{font-family:var(--mono);font-size:11.5px;font-weight:700;letter-spacing:.18em;
    text-transform:uppercase;color:var(--ink-faint);margin:0 0 14px}
  header.doc h1{margin:0}
  h1{color:var(--ink);font-weight:800;letter-spacing:-.025em;line-height:1.08;
    font-size:clamp(30px,4.6vw,46px);text-wrap:balance}
  h2{color:var(--ink);font-weight:760;letter-spacing:-.015em;line-height:1.2;
    font-size:clamp(22px,2.8vw,30px);margin:clamp(38px,5vw,52px) 0 2px;padding-top:18px;
    border-top:1px solid var(--rule);text-wrap:balance}
  h3{color:var(--ink);font-weight:700;font-size:clamp(17px,1.7vw,20px);margin:30px 0 0;letter-spacing:-.01em}
  h4,h5,h6{color:var(--ink);font-weight:700;font-size:15px;margin:24px 0 0;
    font-family:var(--mono);letter-spacing:.04em}
  p{margin:14px 0 0;max-width:70ch}
  a{color:var(--accent-deep);text-decoration:none;border-bottom:1px solid #caa41355}
  a:hover{border-bottom-color:var(--accent-deep)}
  a:focus-visible{outline:2px solid var(--accent-deep);outline-offset:2px;border-radius:2px}
  strong{color:var(--ink);font-weight:640}
  em{color:var(--ink)}
  ul,ol{margin:14px 0 0;padding-left:1.3em;max-width:70ch}
  li{margin:7px 0}
  li::marker{color:var(--accent-deep)}
  code{font-family:var(--mono);font-size:.88em;background:#1c1f2408;border:1px solid var(--rule);
    border-radius:5px;padding:.08em .4em;color:var(--ink)}
  pre{margin:18px 0 0;background:#16181c;border:1px solid #2a2d33;border-radius:11px;
    padding:18px 20px;overflow-x:auto}
  pre code{background:none;border:0;padding:0;color:#e8eaed;font-size:13.5px;line-height:1.7}
  blockquote{margin:18px 0 0;border-left:3px solid var(--accent);background:var(--panel);
    border-radius:0 11px 11px 0;padding:14px 20px;color:var(--ink-soft);max-width:72ch}
  blockquote p{margin:8px 0 0}blockquote p:first-child{margin-top:0}
  hr{border:0;border-top:1px solid var(--rule);margin:clamp(34px,5vw,48px) 0}
  .table-wrap{overflow-x:auto;margin:20px 0 0;border:1px solid var(--rule);border-radius:11px}
  table{border-collapse:collapse;width:100%;font-size:15px;background:var(--panel)}
  th,td{text-align:left;padding:11px 16px;border-bottom:1px solid var(--rule);vertical-align:top}
  th{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;
    color:var(--ink-faint);font-weight:700;background:#faf9f5;white-space:nowrap}
  tr:last-child td{border-bottom:0}
  td{color:var(--ink-soft)} td strong{color:var(--ink)}
  td:not(:first-child),th:not(:first-child){font-variant-numeric:tabular-nums}
  footer.doc{margin-top:clamp(44px,7vw,68px);padding-top:22px;border-top:1px solid var(--rule);
    font-family:var(--mono);font-size:11.5px;letter-spacing:.03em;color:var(--ink-faint);line-height:1.7}
  @media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

# ------------------------------------------------------------------------ inline pass
_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__")
_ITALIC = re.compile(r"(?<!\*)\*(?!\s)([^*]+?)\*(?!\*)|(?<!_)_(?!\s)([^_]+?)_(?!_)")


def inline(text):
    """Render inline Markdown to HTML. Code spans are protected from other rules."""
    placeholders = []

    def stash(m):
        placeholders.append("<code>" + html.escape(m.group(1)) + "</code>")
        return "\x00%d\x00" % (len(placeholders) - 1)

    text = _INLINE_CODE.sub(stash, text)
    text = html.escape(text, quote=False)
    text = _LINK.sub(
        lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(2), quote=True), m.group(1)),
        text,
    )
    text = _BOLD.sub(lambda m: "<strong>%s</strong>" % (m.group(1) or m.group(2)), text)
    text = _ITALIC.sub(lambda m: "<em>%s</em>" % (m.group(1) or m.group(2)), text)
    if placeholders:  # restore protected code spans by index
        text = re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], text)
    return text


# ------------------------------------------------------------------------- block pass
def strip_front_matter(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:]
    return lines


def is_table_sep(line):
    return bool(re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", line)) and "-" in line


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_aligns(sep_line):
    """Read per-column alignment from a table separator row (:--- / ---: / :--:)."""
    aligns = []
    for cell in split_row(sep_line):
        left, right = cell.startswith(":"), cell.endswith(":")
        aligns.append("center" if left and right else "right" if right else
                      "left" if left else None)
    return aligns


def _align_attr(aligns, idx):
    a = aligns[idx] if idx < len(aligns) else None
    return ' style="text-align:%s"' % a if a else ""


def render(md, title_override):
    lines = strip_front_matter(md.replace("\r\n", "\n").split("\n"))
    out = []
    page_title = title_override
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        # blank
        if not line.strip():
            i += 1
            continue

        # fenced code
        if line.lstrip().startswith("```"):
            buf = []
            i += 1
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf)))
            continue

        # horizontal rule
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level = len(m.group(1))
            content = inline(m.group(2))
            # Capture first H1 as the page title; render it in the header instead.
            if level == 1 and page_title is None:
                page_title = re.sub(r"<[^>]+>", "", content)
                i += 1
                continue
            out.append("<h%d>%s</h%d>" % (level, content, level))
            i += 1
            continue

        # table (header row followed by a separator row)
        if "|" in line and i + 1 < n and is_table_sep(lines[i + 1]):
            header = split_row(line)
            aligns = parse_aligns(lines[i + 1])
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(split_row(lines[i]))
                i += 1
            thead = "".join(
                "<th%s>%s</th>" % (_align_attr(aligns, j), inline(c))
                for j, c in enumerate(header)
            )
            body = []
            for r in rows:
                cells = "".join(
                    "<td%s>%s</td>" % (_align_attr(aligns, j), inline(c))
                    for j, c in enumerate(r)
                )
                body.append("<tr>%s</tr>" % cells)
            out.append(
                '<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
                % (thead, "".join(body))
            )
            continue

        # blockquote (consecutive > lines)
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            paras = [p for p in "\n".join(buf).split("\n\n") if p.strip()]
            inner = "".join("<p>%s</p>" % inline(p.replace("\n", " ")) for p in paras)
            out.append("<blockquote>%s</blockquote>" % inner)
            continue

        # unordered list
        if re.match(r"^\s*[-*+]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*[-*+]\s+", "", lines[i])))
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % it for it in items))
            continue

        # ordered list
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % it for it in items))
            continue

        # paragraph (gather until blank / block starter)
        buf = []
        while i < n and lines[i].strip() and not _starts_block(lines[i], lines, i):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    return page_title or "Document", "\n".join(out)


def _starts_block(line, lines, i):
    if re.match(r"^(#{1,6})\s", line) or line.lstrip().startswith((">", "```")):
        return True
    if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
        return True
    if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
        return True
    if "|" in line and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
        return True
    return False


# -------------------------------------------------------------------------- assembly
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<div class="mast"><span class="dot"></span>{brand}<span style="margin-left:auto"></span><span class="live">Live on Duvo</span></div>
<header class="doc">{eyebrow}<h1>{title}</h1>{subtitle}</header>
{body}
<footer class="doc">Daily Basket × Duvo · generated from {source} · {brand}</footer>
</div>
</body>
</html>
"""


def build(md, title=None, subtitle=None, brand="FDE Deliverable", source="Markdown",
          eyebrow="Duvo"):
    page_title, body = render(md, title)
    eyebrow_html = '<p class="eyebrow">%s</p>' % html.escape(eyebrow) if eyebrow else ""
    subtitle_html = '<p class="lede">%s</p>' % inline(subtitle) if subtitle else ""
    # .lede styling lives only on the bespoke page; reuse a plain paragraph here.
    if subtitle:
        subtitle_html = '<p style="font-size:19px;margin-top:18px">%s</p>' % inline(subtitle)
    return PAGE.format(
        title=html.escape(page_title),
        css=CSS,
        brand=html.escape(brand),
        eyebrow=eyebrow_html,
        subtitle=subtitle_html,
        body=body,
        source=html.escape(source),
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert Markdown to a Duvo-branded HTML page.")
    ap.add_argument("input", help="path to the Markdown file")
    ap.add_argument("-o", "--output", help="output .html path (default: alongside input)")
    ap.add_argument("--title", help="page title (default: first H1 in the document)")
    ap.add_argument("--subtitle", help="optional one-line subtitle under the title")
    ap.add_argument("--eyebrow", default="Duvo", help="small label above the title")
    ap.add_argument("--brand", default="FDE Deliverable", help="masthead brand label")
    args = ap.parse_args(argv)

    src = Path(args.input)
    if not src.is_file():
        print("error: no such file: %s" % src, file=sys.stderr)
        return 1
    md = src.read_text(encoding="utf-8")
    out_html = build(
        md, title=args.title, subtitle=args.subtitle,
        brand=args.brand, eyebrow=args.eyebrow, source=src.name,
    )
    dst = Path(args.output) if args.output else src.with_suffix(".html")
    dst.write_text(out_html, encoding="utf-8")
    print("wrote %s (%d bytes)" % (dst, len(out_html)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
