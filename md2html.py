#!/usr/bin/env python3
"""md2html -- render Markdown to a standalone HTML page in the Claude Docs style.

Unofficial; not affiliated with or endorsed by Anthropic.

    md2html FILE.md [FILE.md ...]      # writes FILE.html next to each input
    md2html FILE.md -o OUT.html        # one input, explicit output
    md2html FILE.md --theme light      # dark (default), light, or auto (follows the system)

The look copies the Claude Docs viewer: Anthropic Serif headings (32/22/18 px,
weight 400), Anthropic Sans body at 16 px / 1.5 on #faf9f5 paper with #1f1e1d
ink, a 672 px text column, tables that break out of the column (aligned with
the text when narrow, centred when wide), in a dark or light theme.

Fonts are looked up in order: this machine's copy (~/.local/share/md2html/fonts,
from the npm package anthropic-fonts@1.1.0), the same files on jsDelivr, then
Georgia / the system sans-serif.  No font files are written next to the HTML.
Printing (and md2pdf) keeps the theme and keeps tables on the page.

Needs pandoc on PATH.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys

FONT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
CDN = "https://cdn.jsdelivr.net/npm/anthropic-fonts@1.1.0/cdn/v1/fonts"
FAMILIES = [("Anthropic Sans", "AnthropicSans"), ("Anthropic Serif", "AnthropicSerif"), ("Anthropic Mono", "AnthropicMono")]


def font_faces() -> str:
    out = []
    for family, stem in FAMILIES:
        local = "file://" + os.path.join(FONT_DIR, f"{stem}.woff2")
        out.append(
            f'@font-face{{font-family:"{family}";'
            f'src:url("{local}") format("woff2"),url("{CDN}/{stem}@400.woff2") format("woff2");'
            f"font-weight:300 800;font-style:normal;font-display:swap}}"
        )
    return "\n".join(out)


CSS = r"""
:root{
  --ink:#1f1e1d; --paper:#faf9f5; --line:#e8e5dc; --th:#f5f3ed; --chip:#f0eee6; --muted:#5e5d59;
  --link:#2a78d6; --link-visited:#6a9bcc; --quote:#dbd9d4; --hr:#0b0b0b33;
  --code-ink:#8d2525; --code-bg:#3737340d; --code-line:#1f1f1e40;
  --font-heading:"Anthropic Serif",ui-serif,Georgia,serif;
  --font-body:"Anthropic Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --font-mono:"Anthropic Mono",ui-monospace,"SF Mono",Menlo,monospace;
  --col:min(672px, calc(100vw - 48px)); --break:min(1120px, calc(100vw - 48px));
}
/* Themes: data-theme="dark" or "light" on <html> forces one; no attribute follows the system. */
@media (prefers-color-scheme: dark){
  :root:not([data-theme=light]){--ink:#f0efec; --paper:#0b0b0b; --line:rgba(255,255,255,.10); --th:#1a1a19; --chip:#262624; --muted:#c3c2b7;
        --link:#6a9bcc; --link-visited:#6a9bcc; --quote:rgba(255,255,255,.20); --hr:rgba(255,255,255,.20);
        --code-ink:#f4a9a9; --code-bg:#c3c2b70d; --code-line:#e2e1da40}
}
:root[data-theme=dark]{--ink:#f0efec; --paper:#0b0b0b; --line:rgba(255,255,255,.10); --th:#1a1a19; --chip:#262624; --muted:#c3c2b7;
        --link:#6a9bcc; --link-visited:#6a9bcc; --quote:rgba(255,255,255,.20); --hr:rgba(255,255,255,.20);
        --code-ink:#f4a9a9; --code-bg:#c3c2b70d; --code-line:#e2e1da40}
html,body{margin:0;background:var(--paper);color:var(--ink);-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
main{max-width:672px;margin:64px auto 120px;padding:0 24px;font:16px/1.5 var(--font-body)}
h1{font:400 32px/1.2 var(--font-heading);letter-spacing:-.01em;margin:0 0 .75em;font-feature-settings:"liga" 1}
h2{font:400 22px/1.3 var(--font-heading);margin:1.6em 0 .5em;font-feature-settings:"liga" 1}
h3{font:400 18px/1.35 var(--font-heading);margin:1.4em 0 .4em}
h4{font:600 16px/1.4 var(--font-body);margin:1.3em 0 .3em}
h5{font:600 14px/1.45 var(--font-body);margin:1.2em 0 .25em}
h6{font:500 14px/1.45 var(--font-body);color:var(--muted);margin:1.2em 0 .25em}
p{margin:.6em 0}
strong,b{font-weight:600}
ul,ol{margin:.6em 0;padding-left:1.855em}
ol{list-style-type:decimal} ol ol{list-style-type:lower-alpha} ol ol ol{list-style-type:lower-roman}
li{margin:.25em 0} li>p{margin:0}
a{color:var(--link);text-decoration:none} a:hover{text-decoration:underline} a:visited{color:var(--link-visited)}
blockquote{border-left:3px solid var(--quote);margin:.8em 0;padding:.1em 1em}
hr{border:0;border-top:1px solid var(--hr);margin:1.6em 0}
img{max-width:100%}
code{font-family:var(--font-mono);font-size:.9em;color:var(--code-ink);background:var(--code-bg);
     border:.5px solid var(--code-line);border-radius:.3rem;padding:1px 4px;white-space:pre-wrap}
pre{font:13.5px/1.5 var(--font-mono);background:var(--th);border:1px solid var(--line);border-radius:8px;
    padding:12px 14px;overflow-x:auto;margin:.8em 0}
pre code{color:inherit;background:none;border:0;padding:0;font-size:inherit;white-space:pre}
.byline{margin-top:-.35em}
.chip{display:inline-block;background:var(--chip);border-radius:6px;padding:0 6px;font-size:.94em;line-height:1.5}
.table-wrap{width:var(--break);margin:.6em 0 .6em calc((var(--col) - var(--break))/2);display:flex;overflow-x:auto}
.table-wrap::before{content:"";flex:0 1 calc((var(--break) - var(--col))/2)}
.table-wrap::after{content:"";flex:1 1 calc((var(--break) - var(--col))/2)}
table{flex:none;border-collapse:collapse;width:max-content;font-size:.94em;line-height:1.45}
th,td{vertical-align:top;border:1px solid var(--line);padding:6px 10px;max-width:42ch;text-align:left;overflow-wrap:anywhere}
th{background:var(--th);font-weight:600}
td code,th code{white-space:normal}
@media (max-width:767px){main{margin-top:32px;padding:0 16px} :root{--col:calc(100vw - 32px);--break:calc(100vw - 32px)}}
@media print{
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  main{max-width:none;margin:0;padding:0}
  .table-wrap{display:block;width:auto;margin:.6em 0;overflow:visible}
  .table-wrap::before,.table-wrap::after{content:none}
  table{width:auto;max-width:100%}
  tr,pre,blockquote,img{break-inside:avoid}
  h1,h2,h3,h4,h5,h6{break-after:avoid}
  pre{white-space:pre-wrap;overflow-wrap:anywhere} pre code{white-space:pre-wrap}
}
"""


def render(md_path: str, out_path: str, extra_css: str = "", theme: str = "dark") -> None:
    """theme: "dark" or "light" forces that palette; "auto" follows the reader's system setting."""
    body = subprocess.run(
        ["pandoc", md_path, "-f", "gfm", "-t", "html5", "--no-highlight"],
        check=True, capture_output=True, text=True,
    ).stdout
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    title = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else os.path.splitext(os.path.basename(md_path))[0]
    # A "date · @author" line right under the title becomes chips, as in Claude Docs.
    body = re.sub(r"(</h1>\s*)<p>([^<]{1,40}) · (@[^<\s]{1,40})</p>",
                  r'\1<p class="byline"><span class="chip">\2</span> · <span class="chip">\3</span></p>', body, count=1)
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    page = (
        '<!doctype html>\n'
        + (f'<html lang="en" data-theme="{theme}">\n' if theme in ("dark", "light") else '<html lang="en">\n')
        + '<head>\n<meta charset="utf-8">\n'
        + f'<meta name="color-scheme" content="{ {"dark": "dark", "light": "light"}.get(theme, "light dark") }">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n<style>\n{font_faces()}\n{CSS}{extra_css}</style>\n</head>\n"
        f"<body>\n<main>\n{body}</main>\n</body>\n</html>\n"
    )
    with open(out_path, "w") as fp:
        fp.write(page)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render Markdown to Claude-Docs-styled HTML.")
    ap.add_argument("inputs", nargs="+", help="Markdown files")
    ap.add_argument("-o", "--output", help="output path (only with a single input)")
    ap.add_argument("--theme", choices=["dark", "light", "auto"], default="dark",
                    help="colour theme (default dark; auto follows the reader's system setting)")
    args = ap.parse_args()
    if args.output and len(args.inputs) != 1:
        ap.error("-o needs exactly one input")
    for md in args.inputs:
        out = args.output or os.path.splitext(md)[0] + ".html"
        render(md, out, theme=args.theme)
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
