#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.ftp"

# Load credentials
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Missing .env.ftp — create it first!"
  exit 1
fi
source "$ENV_FILE"

if [ "$FTP_PASS" = "your_password_here" ] || [ -z "$FTP_PASS" ]; then
  echo "❌ Please set FTP_PASS in .env.ftp first!"
  exit 1
fi

echo "🚀 Deploying fashionhotspot-site to $FTP_HOST..."

# Upload all static files via FTP
curl -v --ftp-create-dirs \
  -u "$FTP_USER:$FTP_PASS" \
  -T "{index.html,about.html,contact.html,privacy.html,README.md,CNAME,.nojekyll}" \
  "ftp://$FTP_HOST/$FTP_PATH/" 2>&1 | grep -v "Entering\|150\|226"

# Upload API directory
for f in api/*; do
  [ -f "$f" ] || continue
  curl -v --ftp-create-dirs \
    -u "$FTP_USER:$FTP_PASS" \
    -T "$f" \
    "ftp://$FTP_HOST/$FTP_PATH/api/" 2>&1 | grep -v "Entering\|150\|226"
done

echo ""
echo "✅ Deploy complete!"
echo "   📍 http://fashionhotspot.site"
