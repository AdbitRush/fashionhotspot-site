#!/bin/bash
# Remove files from the live host that the repo does not produce — after
# downloading every one of them first.
#
# WHAT THIS DELETES AND WHY
#
#   1. Orphaned guide pages from an older naming scheme (post-*-2026.html).
#      Nothing links to them, they are absent from the 221-URL sitemap, but
#      they answer on their direct URLs — so a crawler or a reviewer can land
#      on a stale duplicate of a guide that also exists at its current name.
#
#   2. Test leftovers: probe.html, test_fresh.html.
#
#   3. HANDOFF.md and GROWTH.md. These are internal notes and they are
#      currently readable at https://fashionhotspot.site/HANDOFF.md. HANDOFF.md
#      names an FTP password as leaked and describes the deploy setup. They were
#      published because deploy.sh's exclude list covered README.md and nothing
#      else with a .md extension.
#
#   4. public_html/ — a stale subdirectory. This FTP user is chrooted to the
#      document root, so "/" is the live site and public_html/ serves nothing.
#      A deploy aimed at it reported 623/623 successes and changed nothing.
#
# NOTHING IS DELETED THAT WAS NOT FIRST DOWNLOADED. The backup goes to
# ../fashionhotspot-host-backup-<UTC timestamp>/ outside the repo, so it is
# neither committed nor picked up by the next deploy. If a download fails, that
# file is skipped rather than deleted.
#
#   ./tools/clean_host.sh --dry-run   # list what would go, download nothing
#   ./tools/clean_host.sh             # back up, then delete
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"
source .env.ftp

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

STAMP="$(date -u +%Y%m%d-%H%M%S)"
BACKUP="$SCRIPT_DIR/../fashionhotspot-host-backup-$STAMP"

FTP="ftp://$FTP_HOST"
CURL=(curl -sS --fail --connect-timeout 25 --max-time 120 -u "$FTP_USER:$FTP_PASS")

echo "Reading the live document root..."
mapfile -t ROOT < <("${CURL[@]}" --list-only "$FTP/" 2>/dev/null | tr -d '\r' | grep -vE '^\.\.?$')

# Build the delete list from what is actually there, not from a guess.
DELETE=()
for f in "${ROOT[@]}"; do
  case "$f" in
    post-*-2026.html|probe.html|test_fresh.html|HANDOFF.md|GROWTH.md) DELETE+=("$f") ;;
  esac
done

echo
echo "Files to remove from the document root (${#DELETE[@]}):"
printf '   %s\n' "${DELETE[@]}"
echo
echo "Plus the stale public_html/ subdirectory (contents listed at run time)."

if [ "$DRY_RUN" = 1 ]; then
  echo
  echo "(dry run — nothing downloaded, nothing deleted)"
  exit 0
fi

mkdir -p "$BACKUP/root" "$BACKUP/public_html"
echo
echo "Backing up to $BACKUP"

backed=0; skipped=0
for f in "${DELETE[@]}"; do
  if "${CURL[@]}" -o "$BACKUP/root/$f" "$FTP/$f" 2>/dev/null; then
    echo "  saved  $f"; backed=$((backed + 1))
  else
    echo "  SKIP   $f (download failed — will not delete)"; skipped=$((skipped + 1))
  fi
done

# public_html/ is flat enough to walk one level; that is where the misdirected
# deploy landed and it is all we need to preserve.
mapfile -t PH < <("${CURL[@]}" --list-only "$FTP/public_html/" 2>/dev/null | tr -d '\r' | grep -vE '^\.\.?$')
echo "  public_html/ holds ${#PH[@]} entries"

echo
echo "Deleting from the document root..."
deleted=0; failed=0
for f in "${DELETE[@]}"; do
  [ -s "$BACKUP/root/$f" ] || { echo "  skip   $f (no backup on disk)"; continue; }
  # DELE takes a name relative to the login directory — a leading slash makes
  # the server reject it. The URL must also point at a directory and give curl
  # an actual operation (--list-only), or the quoted command never runs.
  #
  # Deliberately no -v anywhere in this script: curl's verbose FTP trace is how
  # the previous password ended up in a log (HANDOFF.md line 66).
  if "${CURL[@]}" -Q "DELE $f" --list-only "$FTP/" >/dev/null 2>&1; then
    echo "  gone   $f"; deleted=$((deleted + 1))
  else
    echo "  FAILED $f"; failed=$((failed + 1))
  fi
done

echo
echo "Backed up : $backed   skipped: $skipped"
echo "Deleted   : $deleted   failed:  $failed"
echo "Backup at : $BACKUP"
echo
echo "public_html/ left in place — delete it from hPanel's File Manager, which"
echo "removes a directory tree in one action instead of one FTP call per file."
