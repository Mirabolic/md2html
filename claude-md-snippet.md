## Markdown to HTML and PDF

- To render Markdown as HTML, always use `md2html`: `md2html FILE.md [...]` writes `FILE.html` beside each input, and `-o OUT.html` works for a single input.
- For PDF, use `md2pdf FILE.md [...]`. It renders the HTML and prints it with headless Chrome. It takes `--paper letter|a4` and `--keep-html`.
- Both commands default to the dark theme. Use `--theme light`; md2html also accepts `--theme auto`, which follows the system.
- Don't hand-roll CSS or use bare pandoc.
- Both commands are symlinks in `~/.local/bin` into the md2html clone (github.com/Mirabolic/md2html). They need pandoc.
- The output has the Claude Docs look:
  - Anthropic Serif headings and Anthropic Sans body text;
  - a 672 px column on #0b0b0b (dark) or #faf9f5 (light) paper;
  - tables that break out of the column.
- Fonts are looked up in the clone's `fonts/` folder first, then jsDelivr (`anthropic-fonts@1.1.0`), then system fonts.
- Never commit font files to a repo.
