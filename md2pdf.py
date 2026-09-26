#!/usr/bin/env python3
"""md2pdf -- render Markdown to PDF in the Claude Docs style (via md2html).

    md2pdf FILE.md [FILE.md ...]         # writes FILE.pdf next to each input
    md2pdf FILE.md -o OUT.pdf            # one input, explicit output
    md2pdf FILE.md --paper a4            # default: letter
    md2pdf FILE.md --theme light         # default: dark
    md2pdf FILE.md --keep-html           # also keep FILE.html

Unofficial; not affiliated with or endorsed by Anthropic.

Each file is rendered to HTML by md2html, then printed by a headless
Chromium-family browser (Chrome, Chromium, Edge or Brave).  Set MD2PDF_BROWSER
to a browser executable to choose one explicitly.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import md2html  # noqa: E402

MAC_APPS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]
NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "brave-browser"]
PAPER = {"letter": "8.5in 11in", "a4": "210mm 297mm"}


def find_browser() -> str | None:
    env = os.environ.get("MD2PDF_BROWSER")
    if env:
        return env
    for p in MAC_APPS + [os.path.expanduser("~" + a) for a in MAC_APPS]:
        if os.path.exists(p):
            return p
    for n in NAMES:
        p = shutil.which(n)
        if p:
            return p
    return None


def to_pdf(md: str, pdf: str, paper: str, keep_html: bool, browser: str, theme: str = "dark") -> None:
    paper_colour = {"dark": "#0b0b0b", "light": "#faf9f5"}[theme]  # fills the page margins too
    page_css = f"@page{{size:{PAPER[paper]};margin:18mm 16mm;background:{paper_colour}}}\n"
    if keep_html:
        html_path = os.path.splitext(pdf)[0] + ".html"
    else:
        fd, html_path = tempfile.mkstemp(suffix=".html", prefix="md2pdf-")
        os.close(fd)
    try:
        md2html.render(md, html_path, extra_css=page_css, theme=theme)
        # No --user-data-dir: with a fresh profile, Chrome writes the PDF but never exits.
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
             "--virtual-time-budget=10000", f"--print-to-pdf={os.path.abspath(pdf)}",
             "file://" + os.path.abspath(html_path)],
            check=True, capture_output=True, timeout=120,
        )
        if not os.path.exists(pdf) or os.path.getsize(pdf) == 0:
            raise RuntimeError(f"the browser did not write {pdf}")
    finally:
        if not keep_html and os.path.exists(html_path):
            os.remove(html_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render Markdown to Claude-Docs-styled PDF.")
    ap.add_argument("inputs", nargs="+", help="Markdown files")
    ap.add_argument("-o", "--output", help="output path (only with a single input)")
    ap.add_argument("--paper", choices=sorted(PAPER), default="letter")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark", help="colour theme (default dark)")
    ap.add_argument("--keep-html", action="store_true", help="keep the intermediate HTML beside the PDF")
    args = ap.parse_args()
    if args.output and len(args.inputs) != 1:
        ap.error("-o needs exactly one input")
    browser = find_browser()
    if browser is None:
        sys.exit("md2pdf: no Chrome, Chromium, Edge or Brave found; install one or set MD2PDF_BROWSER")
    for md in args.inputs:
        out = args.output or os.path.splitext(md)[0] + ".pdf"
        to_pdf(md, out, args.paper, args.keep_html, browser, args.theme)
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
