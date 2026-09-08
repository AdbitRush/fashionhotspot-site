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
#   ./deploy.sh --force    # ignore .deploy-manifest and re-upload everything
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
ENV_FILE="$SCRIPT_DIR/.env.ftp"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

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
#
# .md is excluded as a class, not file by file. This listed README.md alone,
# so HANDOFF.md and GROWTH.md were uploaded and served: HANDOFF.md answered on
# https://fashionhotspot.site/HANDOFF.md with the deploy setup and a note that
# an FTP password had leaked. Naming individual files means every new doc is
# public until someone notices it. The rule is now "no .md reaches the host",
# which needs no maintenance.
#
# .sh likewise — deploy.sh was named explicitly while any other script in the
# repo root would have shipped.
# PW.txt was sitting in this directory holding live credentials, and nothing
# here excluded it — deploy.sh walks the whole tree, so the next deploy would
# have published it at https://fashionhotspot.site/PW.txt for anyone to fetch.
# Same class of mistake as HANDOFF.md being served, which is why .md is here.
#
# NOT a blanket *.txt rule: robots.txt has to ship. Credential-shaped names
# only.
#
# api/*.json is excluded because the HOST owns those files, not this repo.
# searches.json, subscribers.json and stats.json are written by PHP at runtime
# and accumulate real visitor data. This script walks the tree and uploads what
# it finds, so a local copy of any of them — downloaded once to look at, or
# created by a local test — would overwrite the live file on the next deploy and
# destroy every record since the file was made. There is no undo: FTP PUT is not
# a merge. Excluding the pattern means that mistake is not available.
# site-config.json is NOT under api/ and still ships; it is build configuration.
EXCLUDE_RE='^\./(\.git|\.github/|tools/|content/|node_modules/|\.env|PW.*\.txt$|.*password.*\.txt$|.*creds.*\.txt$|.*credentials.*\.txt$|.*\.md$|.*\.sh$|.*\.bak$|.*\.py$|api/.*\.json$)'

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
# ---------------------------------------------------------------------------
# Upload.
#
# This used to run one `curl` per file, which meant one FULL FTP LOGIN per
# file: connect, authenticate, CWD, STOR, quit, ~8 seconds each. For ~600
# files that is well over an hour, and on 2026-09-08 it did something worse
# than being slow — Hostinger's anti-abuse blocked this VPS's IP part-way
# through. The run reported "✗" for every file after that point, the live site
# silently kept serving the 2026-08-26 build, and port 21 stopped answering
# from this host entirely while still answering from elsewhere. A deploy that
# fails this way looks identical to a deploy that is merely slow.
#
# Two changes, both aimed at the number of logins:
#
#   1. Skip files whose content has not changed since the last successful
#      upload, tracked by sha256 in .deploy-manifest. Almost every run is a
#      handful of HTML files; images/ is 29MB that had been re-sent in full
#      every single time.
#   2. Batch whatever is left. curl reuses one connection across several -T
#      pairs in a single invocation, so a chunk of 40 files costs one login
#      instead of forty.
#
# --force ignores the manifest and re-uploads everything, for when the live
# host and the manifest have drifted apart.
MANIFEST="$SCRIPT_DIR/.deploy-manifest"
touch "$MANIFEST"

CHANGED=()
SKIPPED=0
for f in "${FILES[@]}"; do
  rel="${f#./}"
  h=$(sha256sum "$f" | cut -d' ' -f1)
  if [ "$FORCE" = 0 ] && grep -qxF "$h  $rel" "$MANIFEST"; then
    SKIPPED=$((SKIPPED + 1))
  else
    CHANGED+=("$rel")
  fi
done

if [ "${#CHANGED[@]}" -eq 0 ]; then
  echo "✅ Nothing to upload — all ${#FILES[@]} files match .deploy-manifest"
  echo "   📍 https://fashionhotspot.site"
  exit 0
fi

echo "   $SKIPPED unchanged, ${#CHANGED[@]} to upload"

# One login per chunk. Kept modest on purpose: a chunk is also the unit of
# failure reporting, because curl cannot tell us WHICH -T in an invocation
# failed, and it is the unit the host sees as a single session.
CHUNK=40
fail=0
uploaded=()
total=${#CHANGED[@]}
for ((i = 0; i < total; i += CHUNK)); do
  args=()
  batch=("${CHANGED[@]:i:CHUNK}")
  for rel in "${batch[@]}"; do
    args+=(-T "./$rel" "ftp://$FTP_HOST/${FTP_PATH:+$FTP_PATH/}$rel")
  done
  n=$((i + ${#batch[@]}))
  printf '   uploading %d-%d of %d ... ' "$((i + 1))" "$n" "$total"
  if curl -sS --fail --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" "${args[@]}" >/dev/null 2>&1; then
    echo "ok"
    uploaded+=("${batch[@]}")
  else
    echo "FAILED"
    # The whole chunk is treated as unsent. Nothing from it enters the
    # manifest, so the next run retries it rather than assuming it landed —
    # the failure mode this replaced was a file recorded as deployed that
    # never arrived.
    fail=$((fail + ${#batch[@]}))
  fi
done

# Rewrite the manifest: keep entries for files we did not touch, replace the
# entries for the ones that just went up.
if [ "${#uploaded[@]}" -gt 0 ]; then
  tmp=$(mktemp)
  cp "$MANIFEST" "$tmp"
  for rel in "${uploaded[@]}"; do
    grep -v "  $rel\$" "$tmp" > "$tmp.n" 2>/dev/null || true
    mv "$tmp.n" "$tmp"
    printf '%s  %s\n' "$(sha256sum "./$rel" | cut -d' ' -f1)" "$rel" >> "$tmp"
  done
  sort -k2 "$tmp" > "$MANIFEST"
  rm -f "$tmp"
fi

echo
if [ "$fail" -gt 0 ]; then
  echo "⚠️  Deploy finished with $fail file(s) unsent out of $total"
  echo "   They are NOT recorded in .deploy-manifest and will retry next run."
  echo "   If port 21 stopped answering mid-run, this host's IP is blocked:"
  echo "     timeout 10 bash -c 'exec 3<>/dev/tcp/$FTP_HOST/21 && head -c 40 <&3'"
  echo "   A banner means it is fine; silence means blocked. Clear it in"
  echo "   hPanel, or wait for the block to expire, then re-run."
  exit 1
fi
echo "✅ Deploy complete — $total uploaded, $SKIPPED unchanged"
echo "   📍 https://fashionhotspot.site"
