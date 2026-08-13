#!/bin/bash
# Mirror the entire live host to a local snapshot, so any change can be undone.
#
# WHY A FULL MIRROR AND NOT JUST "THE REPO IS THE BACKUP"
#
# The repo does reproduce the document root — `bash deploy.sh` rebuilds the live
# site from it. But that only restores what the repo knows about. It does not
# restore anything that exists on the host and nowhere else, and tonight proved
# that category is not empty: 22 guide pages under an older naming scheme, test
# leftovers, and a whole stale public_html/ tree.
#
# It also does not help if the repo itself is the thing that turns out to be
# wrong. A snapshot taken before a destructive operation is the only thing that
# lets you put the host back exactly as it was.
#
# WHAT IT DOES
#
# Walks every directory over FTP and downloads every file, preserving paths,
# into ../fashionhotspot-host-backup-<UTC>-full/. Prints a manifest with sizes
# so the result can be checked rather than trusted, and writes RESTORE.txt
# explaining how to put files back.
#
# Existing files are re-downloaded rather than skipped: a partial file from an
# interrupted run is worse than no file, because it looks like a backup.
#
#   ./tools/backup_host.sh
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .env.ftp

DEST="$ROOT/../fashionhotspot-host-backup-$(date -u +%Y%m%d-%H%M%S)-full"
FTP="ftp://$FTP_HOST"
# No -v: curl's verbose FTP trace is how a password leaked once already.
C=(curl -sS --connect-timeout 20 --max-time 120 -u "$FTP_USER:$FTP_PASS")

FILES=(); DIRS=()
walk() {
  local dir="$1" line name url
  # Root is "" — joining it naively yields ftp://host// . Build the URL so the
  # listing target always ends in exactly one slash.
  if [ -z "$dir" ]; then url="$FTP/"; else url="$FTP/$dir/"; fi
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    name="${line##* }"
    [ "$name" = "." ] || [ "$name" = ".." ] && continue
    local path
    if [ -z "$dir" ]; then path="$name"; else path="$dir/$name"; fi
    if [[ "$line" == d* ]]; then
      DIRS+=("$path"); walk "$path"
    else
      FILES+=("$path")
    fi
  # TRAILING SLASH IS LOAD-BEARING. "ftp://host/images" asks curl to retrieve a
  # FILE called images; "ftp://host/images/" asks for a directory listing. Without
  # it every subdirectory silently returns nothing, and the walk reports success
  # having descended into none of them — a backup that looks fine and contains
  # 55 files instead of 1,300.
  done < <("${C[@]}" "$url" 2>/dev/null | tr -d '\r')
}

echo "Walking the live host..."
walk ""
echo "  found ${#FILES[@]} files in $(( ${#DIRS[@]} + 1 )) directories"

mkdir -p "$DEST"
echo "Mirroring to $DEST"

ok=0; fail=0; failed=()
for f in "${FILES[@]}"; do
  mkdir -p "$DEST/$(dirname "$f")"
  if "${C[@]}" --fail -o "$DEST/$f" "$FTP/$f" 2>/dev/null && [ -s "$DEST/$f" ]; then
    ok=$((ok + 1))
  else
    # A zero-byte file on the host is legitimate; only count a real failure.
    if "${C[@]}" --fail -I "$FTP/$f" >/dev/null 2>&1; then
      ok=$((ok + 1))
    else
      fail=$((fail + 1)); failed+=("$f")
    fi
  fi
  [ $(( (ok + fail) % 100 )) -eq 0 ] && echo "  ... $((ok + fail))/${#FILES[@]}"
done

{
  echo "Snapshot of https://fashionhotspot.site taken $(date -u '+%Y-%m-%d %H:%M UTC')"
  echo "Source: $FTP  (FTP login directory IS the document root)"
  echo "Files:  $ok downloaded, $fail failed, ${#FILES[@]} listed"
  echo
  echo "TO RESTORE EVERYTHING:"
  echo "  cd fashionhotspot-site && bash deploy.sh"
  echo "     rebuilds the live site from the repo — the normal path."
  echo
  echo "TO RESTORE A SINGLE FILE FROM THIS SNAPSHOT:"
  echo "  cd <this directory>"
  echo "  source /path/to/fashionhotspot-site/.env.ftp"
  echo "  curl --ftp-create-dirs -u \"\$FTP_USER:\$FTP_PASS\" -T ./PATH ftp://\$FTP_HOST/PATH"
  echo
  echo "NOTE: DELE and RMD take a path relative to the login directory."
  echo "  Correct:   -Q \"DELE public_html/x.html\"  with the URL as ftp://host/"
  echo "  Wrong:     -Q \"DELE x.html\"              with the URL as ftp://host/public_html/"
  echo "  curl sends quote commands before changing directory, so the wrong form"
  echo "  deletes x.html from the DOCUMENT ROOT. That mistake removed 53 live"
  echo "  pages once; they were restored with deploy.sh."
  [ "$fail" -gt 0 ] && { echo; echo "FAILED TO DOWNLOAD:"; printf '  %s\n' "${failed[@]}"; }
} > "$DEST/RESTORE.txt"

echo
echo "  downloaded : $ok"
echo "  failed     : $fail"
echo "  size       : $(du -sh "$DEST" 2>/dev/null | cut -f1)"
echo "  snapshot   : $DEST"
[ "$fail" -gt 0 ] && printf '  FAILED: %s\n' "${failed[@]:0:10}"
exit 0
