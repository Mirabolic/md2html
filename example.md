# md2html example

2026-09-26 · @you

A lead paragraph with **bold**, *italic*, `inline code` and a [link](https://pandoc.org).

## A table

| Tool | Output | Needs |
| --- | --- | --- |
| md2html | HTML page | pandoc |
| md2pdf | PDF | pandoc and a Chromium-family browser |

## A list and some code

1. Install with `./install.sh`.
2. Run `md2html example.md`.
    - Nested items work too.

```
md2pdf example.md --paper a4
```

> A block quote, for good measure.
