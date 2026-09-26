# md2html and md2pdf

Render Markdown as a clean, standalone HTML page or PDF in the style of Claude Docs: serif headings, a readable column and tidy tables, in a dark theme (the default) or a light one.

This is an unofficial tool. It is not affiliated with or endorsed by Anthropic.

## Install

```
git clone https://github.com/Mirabolic/md2html.git ~/src/md2html
~/src/md2html/install.sh
```

The script needs pandoc, and installs it with Homebrew if it is missing. It downloads the fonts into the clone and links `md2html` and `md2pdf` into `~/.local/bin`. You can re-run it at any time. Options:

- `--system-fonts` also installs the fonts for every app (macOS or Linux).
- `--claude` adds a note to `~/.claude/CLAUDE.md`, so Claude Code uses these commands for Markdown conversion.

## Use

```
md2html notes.md                # writes notes.html
md2html a.md b.md               # one HTML file per input
md2html notes.md -o page.html
md2html notes.md --theme light  # dark (default), light, or auto (follows the reader's system)

md2pdf notes.md                 # writes notes.pdf (US Letter)
md2pdf notes.md --paper a4 --keep-html
md2pdf notes.md --theme light   # dark (default) or light; the colour fills the whole page
```

`md2pdf` prints through headless Chrome, Chromium, Edge or Brave. To choose a browser, set `MD2PDF_BROWSER`.

## Fonts

Pages use Anthropic Sans for body text and Anthropic Serif for headings; code uses Anthropic Mono. The files come from [`anthropic-fonts@1.1.0`](https://www.npmjs.com/package/anthropic-fonts) on npm.

That package is a third-party repackaging with an MIT label. Anthropic has not published a license for these fonts, so use them at your own judgement.

This repo contains no font files. `install.sh` downloads them and checks them against pinned SHA-256 checksums. Each page looks for fonts in this order:

1. the copy in the clone;
2. the same files on jsDelivr;
3. Georgia and the system sans-serif.

Everything but the typeface works without them.

## License

0BSD: do anything with it, with no conditions. See `LICENSE`.
