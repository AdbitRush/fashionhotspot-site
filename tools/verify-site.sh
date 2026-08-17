#!/bin/bash
# Publish a search-engine verification file to the live site root.
#
# Google Search Console and Bing both verify by serving a file whose NAME and
# CONTENTS they generate for your account. Nobody can create that file for you —
# it is account-specific — so this takes the one they give you and puts it where
# they will look, in about four seconds.
#
#   ./tools/verify-site.sh google1a2b3c4d5e6f.html
#       downloads?  no — pass the file you saved from Search Console
#
#   ./tools/verify-site.sh google1a2b3c4d5e6f.html "google-site-verification: google1a2b3c4d5e6f.html"
#       creates the file with that single line, then uploads it
#
# Verified 2026-08-17 that a file at the site root is served correctly (HTTP 200,
# exact contents) — the .htaccess rewrite rules only touch post-*-2026.html, so
# a verification file is not intercepted.
#
# Afterwards, in Search Console:
#   1. Verify
#   2. Sitemaps -> submit  sitemap.xml
#   3. URL inspection -> https://fashionhotspot.site/posts.html -> Request indexing
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

FILE="${1:-}"
BODY="${2:-}"

if [ -z "$FILE" ]; then
  echo "usage: ./tools/verify-site.sh <filename> [file contents]"
  echo
  echo "  Google : Search Console -> Add property -> URL prefix -> HTML file"
  echo "           https://search.google.com/search-console"
  echo "  Bing   : Webmaster Tools -> Add site -> XML file, or import from Google"
  echo "           https://www.bing.com/webmasters"
  exit 1
fi

[ -f "$SCRIPT_DIR/../.env.ftp" ] || { echo "missing .env.ftp"; exit 1; }
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../.env.ftp"

if [ -n "$BODY" ]; then
  printf '%s\n' "$BODY" > "$FILE"
  echo "created $FILE"
elif [ ! -f "$FILE" ]; then
  echo "❌ $FILE not found here, and no contents given as the 2nd argument."
  echo "   Either save the file from Search Console into this folder, or pass its one line."
  exit 1
fi

echo "uploading $FILE ..."
curl -sS --user "${FTP_USER}:${FTP_PASS}" -T "$FILE" --url "ftp://${FTP_HOST}/${FILE}" -o /dev/null
sleep 2

CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://fashionhotspot.site/${FILE}?cb=$RANDOM")
if [ "$CODE" = "200" ]; then
  echo "✅ live: https://fashionhotspot.site/${FILE}"
  echo
  echo "Now, in the console that gave you this file:"
  echo "   1. click Verify"
  echo "   2. Sitemaps -> submit:  sitemap.xml"
  echo "   3. URL inspection -> https://fashionhotspot.site/posts.html -> Request indexing"
else
  echo "❌ not reachable (HTTP $CODE). It uploaded but is not being served — check the name."
  exit 1
fi
