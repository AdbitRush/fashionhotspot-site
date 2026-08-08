#!/bin/bash
# Publish the static site to the live host over FTP.
#
# The previous version uploaded a hand-written list of seven files. Everything
# added since — the guide posts, the Hebrew pages, images/, sitemap.xml,
# robots.txt, terms.html, the icons — silently never reached the live site.
# This walks the tree instead, so anything committed gets published.
#
#   ./deploy.sh            # upload everything that should be public
#   ./deploy.sh --dry-run  # list what would be uploaded, send nothing
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
ENV_FILE="$SCRIPT_DIR/.env.ftp"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Missing .env.ftp — create it with FTP_HOST, FTP_USER, FTP_PASS, FTP_PATH"
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

if [ -z "${FTP_PASS:-}" ] || [ "$FTP_PASS" = "your_password_here" ]; then
  echo "❌ Set FTP_PASS in .env.ftp first"
  exit 1
fi
FTP_PATH="${FTP_PATH:-}"

# Never publish these, whatever else changes.
EXCLUDE_RE='^\./(\.git/|\.github/|tools/|content/|node_modules/|\.env|deploy\.sh|README\.md|.*\.bak$|.*\.py$)'

mapfile -t FILES < <(
  find . -type f \
    -not -path './.git/*' -not -path './.github/*' \
    -not -path './tools/*' -not -path './content/*' \
    -not -path './node_modules/*' \
  | sed 's|^\./|./|' \
  | grep -Ev "$EXCLUDE_RE" \
  | sort
)

echo "🚀 Deploying ${#FILES[@]} files to ${FTP_HOST}${FTP_PATH:+/$FTP_PATH}"
if [ "$DRY_RUN" = 1 ]; then
  printf '   %s\n' "${FILES[@]}"
  echo "(dry run — nothing uploaded)"
  exit 0
fi

fail=0
for f in "${FILES[@]}"; do
  rel="${f#./}"
  if curl -sS --fail --ftp-create-dirs \
       -u "$FTP_USER:$FTP_PASS" \
       -T "$f" \
       "ftp://$FTP_HOST/${FTP_PATH:+$FTP_PATH/}$rel" >/dev/null 2>&1; then
    echo "  ✓ $rel"
  else
    echo "  ✗ $rel"
    fail=$((fail + 1))
  fi
done

echo
if [ "$fail" -gt 0 ]; then
  echo "⚠️  Deploy finished with $fail failure(s) out of ${#FILES[@]}"
  exit 1
fi
echo "✅ Deploy complete — ${#FILES[@]} files"
echo "   📍 https://fashionhotspot.site"
