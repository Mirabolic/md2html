#!/usr/bin/env bash
# install.sh -- set up md2html and md2pdf from this clone.  Safe to re-run.
#
#   ./install.sh                  # fonts for the HTML, commands in ~/.local/bin
#   ./install.sh --system-fonts   # also install the fonts for every app (macOS/Linux)
#   ./install.sh --claude         # also add the md2html note to ~/.claude/CLAUDE.md
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin"
CDN="https://cdn.jsdelivr.net/npm/anthropic-fonts@1.1.0/cdn/v1/fonts"
SYSTEM_FONTS=0
CLAUDE=0
for a in "$@"; do
  case "$a" in
    --system-fonts) SYSTEM_FONTS=1 ;;
    --claude) CLAUDE=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
sha256() { if command -v shasum >/dev/null; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi; }

# 1. pandoc
if ! command -v pandoc >/dev/null; then
  if command -v brew >/dev/null; then say "installing pandoc with Homebrew"; brew install pandoc
  else say "pandoc is required: install it (https://pandoc.org/installing.html) and re-run"; exit 1; fi
fi
say "pandoc: $(pandoc --version | head -1)"

# 2. fonts, pinned by checksum (anthropic-fonts@1.1.0 on npm, via jsDelivr)
mkdir -p "$DIR/fonts"
while read -r stem sum; do
  f="$DIR/fonts/$stem.woff2"
  if [[ -f "$f" && "$(sha256 "$f")" == "$sum" ]]; then say "font $stem: present"; continue; fi
  tmp="$(mktemp)"
  if curl -fsSL "$CDN/$stem@400.woff2" -o "$tmp" && [[ "$(sha256 "$tmp")" == "$sum" ]]; then
    mv "$tmp" "$f"; say "font $stem: downloaded"
  else
    rm -f "$tmp"; say "font $stem: download failed or checksum mismatch; pages will fall back to system fonts"
  fi
done <<'EOF'
AnthropicSans 1c98b0a3e14b9e57436d3a2bcc9c6f0c9483d30ec7356a5368ab6f0828e424b3
AnthropicSerif e96fe97bb7ba2190a9a227d27380e0c79894408bfc6acea5a511774d93a16f69
AnthropicMono 49b8b95c950b0bee7ecdf68cda9dd6908e980283c50dc570c401de1e683a22e5
EOF

# 3. commands
chmod +x "$DIR/md2html.py" "$DIR/md2pdf.py"
mkdir -p "$BIN"
ln -sf "$DIR/md2html.py" "$BIN/md2html"
ln -sf "$DIR/md2pdf.py" "$BIN/md2pdf"
say "commands: $BIN/md2html, $BIN/md2pdf"
case ":$PATH:" in *":$BIN:"*) ;; *) say "NOTE: $BIN is not on your PATH; add it to your shell profile" ;; esac
python3 "$DIR/md2pdf.py" --help >/dev/null
python3 - "$DIR" <<'PY' || say "NOTE: md2pdf needs Chrome, Chromium, Edge or Brave (or set MD2PDF_BROWSER)"
import sys; sys.path.insert(0, sys.argv[1]); import md2pdf
sys.exit(0 if md2pdf.find_browser() else 1)
PY

# 4. optional: fonts for every app
if [[ "$SYSTEM_FONTS" == 1 ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then DEST="$HOME/Library/Fonts"; else DEST="$HOME/.local/share/fonts"; fi
  mkdir -p "$DEST"
  python3 -m venv "$DIR/.venv"
  "$DIR/.venv/bin/pip" -q install fonttools brotli
  "$DIR/.venv/bin/python" - "$DIR/fonts" "$DEST" <<'PY'
import os, sys
from fontTools.ttLib import TTFont
src, dest = sys.argv[1:]
for stem in ("AnthropicSans", "AnthropicSerif", "AnthropicMono"):
    p = os.path.join(src, stem + ".woff2")
    if not os.path.exists(p):
        continue
    t = TTFont(p); t.flavor = None
    out = os.path.join(dest, stem + "-Variable.ttf"); t.save(out); print("system font:", out)
PY
  command -v fc-cache >/dev/null && fc-cache -f "$DEST" >/dev/null || true
fi

# 5. optional: tell Claude Code about it
if [[ "$CLAUDE" == 1 ]]; then
  C="$HOME/.claude/CLAUDE.md"
  mkdir -p "$HOME/.claude"
  if [[ -f "$C" ]] && grep -q "md2html" "$C"; then
    say "~/.claude/CLAUDE.md already mentions md2html; left unchanged (compare with claude-md-snippet.md)"
  else
    { [[ -s "$C" ]] && printf '\n'; cat "$DIR/claude-md-snippet.md"; } >> "$C"
    say "added the md2html note to ~/.claude/CLAUDE.md"
  fi
fi
say "done"
