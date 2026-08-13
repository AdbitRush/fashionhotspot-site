#!/bin/bash
# Remove the stale public_html/ tree from the live host.
#
# WHAT IT IS
#
# This FTP user is chrooted to the document root, so "/" is the live site.
# public_html/ is a leftover subdirectory that serves nothing — but it sits
# inside the docroot, so it IS reachable: https://fashionhotspot.site/public_html/
# returned HTTP 200, a complete second copy of the site. That is duplicate
# content a crawler can index, and it contains guide pages under an older
# naming scheme (post-*-2026.html) that read as outdated versions of pages
# still live at their proper URLs.
#
# It also holds a full 623-file deploy that was aimed here by mistake.
#
# WHAT GETS BACKED UP
#
# Only files the repo does not already contain. The misdirected deploy is
# byte-identical to the working tree, so downloading it again would be copying
# files onto themselves — the repo is its own backup. What is genuinely at risk
# is the older material that exists nowhere else: the -2026 pages and any test
# leftovers. Those are downloaded before anything is removed.
#
# A file that fails to download is not deleted.
#
#   ./tools/purge_public_html.sh --dry-run
#   ./tools/purge_public_html.sh
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .env.ftp

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

BACKUP="$ROOT/../fashionhotspot-host-backup-$(date -u +%Y%m%d-%H%M%S)-public_html"
FTP="ftp://$FTP_HOST"
# No -v, ever: curl's verbose FTP trace is how a password leaked once already.
C=(curl -sS --connect-timeout 20 --max-time 90 -u "$FTP_USER:$FTP_PASS")

# Walk the tree breadth-first, collecting files and directories separately.
FILES=(); DIRS=()
walk() {
  local dir="$1"
  local line name
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    name="${line##* }"
    [ "$name" = "." ] || [ "$name" = ".." ] && continue
    if [[ "$line" == d* ]]; then
      DIRS+=("$dir/$name")
      walk "$dir/$name"
    else
      FILES+=("$dir/$name")
    fi
  done < <("${C[@]}" "$FTP/$dir/" 2>/dev/null | tr -d '\r')
}

echo "Walking public_html/ ..."
walk "public_html"
echo "  files: ${#FILES[@]}   directories: ${#DIRS[@]}"

# Which files exist nowhere in the repo? Those are the ones worth keeping.
UNIQUE=()
for f in "${FILES[@]}"; do
  rel="${f#public_html/}"
  [ -f "$ROOT/$rel" ] || UNIQUE+=("$f")
done

echo "  files not present in the repo (these get backed up): ${#UNIQUE[@]}"
printf '     %s\n' "${UNIQUE[@]:0:25}"
[ "${#UNIQUE[@]}" -gt 25 ] && echo "     ... and $(( ${#UNIQUE[@]} - 25 )) more"

if [ "$DRY_RUN" = 1 ]; then
  echo
  echo "(dry run — nothing downloaded, nothing deleted)"
  exit 0
fi

echo
echo "Backing up to $BACKUP"
saved=0; unsaved=()
for f in "${UNIQUE[@]}"; do
  rel="${f#public_html/}"
  mkdir -p "$BACKUP/$(dirname "$rel")"
  if "${C[@]}" --fail -o "$BACKUP/$rel" "$FTP/$f" 2>/dev/null && [ -s "$BACKUP/$rel" ]; then
    saved=$((saved + 1))
  else
    echo "  SKIP $f (download failed — will not be deleted)"
    unsaved+=("$f")
  fi
done
echo "  backed up $saved of ${#UNIQUE[@]}"

echo
echo "Deleting files..."
deleted=0; failed=0
for f in "${FILES[@]}"; do
  # Never delete something we meant to keep but could not save.
  skip=0
  for u in "${unsaved[@]:-}"; do [ "$f" = "$u" ] && skip=1; done
  [ "$skip" = 1 ] && continue

  # THE FULL PATH GOES IN THE DELE COMMAND. Do not shorten it to the basename
  # and put the directory in the URL.
  #
  # curl sends -Q quote commands straight after login, BEFORE it changes into
  # the directory the URL names. So this:
  #
  #     curl -Q "DELE post-tech.html" ftp://host/public_html/
  #
  # does not delete public_html/post-tech.html. It deletes post-tech.html in
  # the login directory — which for this chrooted account is the live document
  # root. Run against a 649-file listing it deleted 53 real pages off the live
  # site, including posts.html and every post-*.html whose name also existed in
  # the copy, and "failed" 596 times only because those names did not exist at
  # the root to delete. The failures were the safety net, not the successes.
  #
  # DELE with a path relative to the login directory is unambiguous.
  if "${C[@]}" -Q "DELE $f" --list-only "$FTP/" >/dev/null 2>&1; then
    deleted=$((deleted + 1))
  else
    failed=$((failed + 1))
  fi
done
echo "  deleted $deleted   failed $failed"

echo
echo "Removing directories (deepest first)..."
rmd=0
mapfile -t DEEPEST < <(printf '%s\n' "${DIRS[@]}" | awk '{print gsub(/\//,"/"), $0}' | sort -rn | cut -d' ' -f2-)
for d in "${DEEPEST[@]}" "public_html"; do
  # Full path, for the same reason as DELE above.
  "${C[@]}" -Q "RMD $d" --list-only "$FTP/" >/dev/null 2>&1 && rmd=$((rmd + 1))
done
echo "  removed $rmd directories"

echo
echo "Backup at: $BACKUP"
