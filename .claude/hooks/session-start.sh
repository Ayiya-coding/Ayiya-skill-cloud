#!/bin/bash
set -euo pipefail

# Only run on Claude Code web (remote environment)
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> Installing skill dependencies for Claude Code web..."

# ── Python packages ──────────────────────────────────────────────────────────
# pdf skill: pypdf, pdfplumber, Pillow
# docx skill: python-docx, defusedxml
# xlsx skill: openpyxl
# pptx skill: python-pptx
# create-colleague: pypinyin, requests
# web-access / api-doc: requests, beautifulsoup4, lxml
pip install --quiet --disable-pip-version-check \
  pypdf \
  pdfplumber \
  Pillow \
  python-docx \
  python-pptx \
  openpyxl \
  defusedxml \
  pypinyin \
  requests \
  beautifulsoup4 \
  lxml \
  slack-sdk

echo "  ✓ Python packages installed"

# ── pandoc (docx text extraction) ────────────────────────────────────────────
if ! command -v pandoc >/dev/null 2>&1; then
  apt-get install -y -q pandoc 2>/dev/null && echo "  ✓ pandoc installed" || echo "  ⚠ pandoc install failed (non-fatal)"
else
  echo "  ✓ pandoc already present"
fi

# ── Playwright chromium (browser automation) ─────────────────────────────────
if command -v npx >/dev/null 2>&1; then
  # Install playwright package if not present
  if ! npx --no playwright --version >/dev/null 2>&1; then
    npm install -g playwright --quiet 2>/dev/null || true
  fi
  # Install chromium browser (container already has system deps)
  npx playwright install chromium 2>/dev/null \
    && echo "  ✓ Playwright chromium installed" \
    || echo "  ⚠ Playwright browser install failed (non-fatal)"
else
  echo "  ⚠ npx not found — skipping Playwright install"
fi

echo "==> Skill dependencies ready."
