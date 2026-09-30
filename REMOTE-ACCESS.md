# REMOTE-ACCESS - how to reach everything from a phone (written 2026-09-30)
# גישה מרחוק - איך מגיעים לכל דבר מהטלפון

No passwords, tokens or keys are written in this file. Each secret below says where it is stored.
אין בקובץ הזה סיסמאות, טוקנים או מפתחות. לכל סוד כתוב איפה הוא שמור.

## What was actually verified on 2026-09-30 / מה נבדק בפועל
| Item | Status |
|---|---|
| VPS 178.105.148.72 SSH | `sshd`: port 22, `PasswordAuthentication no`, `PermitRootLogin without-password` = **key-only, no password login at all**; 1 authorized key on root; fail2ban guards it. |
| VPS on Tailscale | yes, `100.100.168.127` (host `ubuntu-4gb-chris06`). Your iPhone appears in the tailnet as `iphone-13-pro-max` but **"offline, last seen 117d ago"** - the Tailscale app on the phone has to be opened and signed in again. |
| Chrome Remote Desktop on the PC | The `chromoting` Windows service is installed and **Running** and the CRD folder exists. **NOT connection-tested**: a real test needs a second device signing in, which I cannot do. Treat it as "installed, untested". |
| Bot dashboard | https://bot-admin.178-105-148-72.sslip.io/ - two logins (below). Verified only up to the login (401 without credentials). |

## 1. Termius / SSH from the phone (needs ONE setup step you cannot do from the phone alone)
The VPS accepts SSH keys only, so a phone needs its own key registered on the server first.
1. Install **Termius**. Keychain -> Generate Key (ed25519). Copy the **public** key (public keys are not secret).
2. The public key must be appended to `/root/.ssh/authorized_keys` on the VPS. That needs an existing login, i.e. the PC (or Chrome Remote Desktop into the PC, then use the PC's terminal): `ssh root@178.105.148.72`, then paste the key line into that file. Nothing on the phone alone can do this - it is key-only by design.
3. In Termius add a Host: address `178.105.148.72` (or the Tailscale address `100.100.168.127` once Tailscale is up on the phone), user `root`, the key from step 1. Port 22.
4. Prefer Tailscale: open the Tailscale app on the phone, sign in with the same account as the PC/VPS (host list shows `ubuntu-4gb-chris06`), then use `100.100.168.127`.
Where the PC's own SSH key lives: `C:\Users\AdBitRush\.ssh\` on the PC (private key stays there - never copy it into chat).

## 2. Chrome Remote Desktop to the PC (untested)
- On the phone: install "Chrome Remote Desktop", sign in with the Google account used on the PC, tap the PC under "Remote devices", enter the **PIN you chose when enabling remote access** (stored only in your head / password manager; Windows cannot show it - if forgotten, re-run remote access setup at remotedesktop.google.com/access).
- The PC must be **on, awake and online**. If it sleeps, CRD shows it offline. If it is offline when you check, nothing on this repo can fix that.

## 3. Bot dashboard
URL: https://bot-admin.178-105-148-72.sslip.io/
- Step 1 (browser pop-up, HTTP Basic Auth): user `or`; the password is the same one as **voyageworthy-admin** (https://voyageworthy-admin.178-105-148-72.sslip.io/admin.html). It is stored in your password manager; on the server only its **hash** is in `/root/caddy/Caddyfile`.
- Step 2 (page login): the dashboard token = `DASHBOARD_TOKEN` in `/opt/whatsapp-deals-bot/.env` on the VPS (root-readable only). If you do not know it, it can only be read/reset through SSH.

## 4. Where every secret is stored (locations only)
| Secret | Location |
|---|---|
| Server index of all credentials (what/where, no values) | `/opt/ops/CREDENTIALS-INDEX.md` on the VPS |
| Bot dashboard token, AliExpress API keys | `/opt/whatsapp-deals-bot/.env` (VPS, root) |
| Gemini key, Gemini free-tier flag | `/etc/deals-bot/env` (VPS, root 0600). **Rotate the two keys pasted into chat.** |
| Telegram bot token (ops agent + cruise notifier) | `/etc/ops-agent/env` (VPS, root) |
| Owner Telegram ID (not secret) | 6449391017 |
| Caddy Basic Auth hash | `/root/caddy/Caddyfile` (VPS) |
| AllyFind FTP credentials | `/opt/allyfind-nightly/` env file (VPS, root) |
| PC SSH key to the VPS | `C:\Users\AdBitRush\.ssh\` (PC) |
| hPanel / Porkbun / Google account | your password manager (I never had these) |

## 5. What you need to click / do (in order of value)
1. Open Tailscale on the phone and sign in (fixes the "offline 117d" phone entry).
2. From the PC (or CRD-into-PC): add the Termius public key to the VPS `authorized_keys` (section 1).
3. Test CRD once from the phone while the PC is on.
4. Log in to the dashboard (section 3) and tell the assistant if either step fails.
5. Confirm the Telegram "notifier is online" hello arrived; test the OpenClaw Telegram lock from a second account.
6. Rotate the two Gemini keys.
7. Pending decisions/approvals live in `fix-queue-specs/MORNING-REPORT-2026-09-30.md` (PC) and HANDOVER.md in both repos: AF-3 deploy, AF-4 go-ahead, BOT-1 answers, VW-1d audit file.

## 6. Emergency
- Site down: https://allyfind.com and https://voyageworthy.com - if either fails, from an SSH session: `systemctl status caddy` is not used (Caddy runs in Docker): `docker ps`, `docker logs caddy --tail 50`.
- Bot down: `systemctl status deals-bot`, `journalctl -u deals-bot -n 50`.
- Never run `sed -i` on the host Caddyfile (bind-mount trap: write through `docker exec caddy`, then `caddy reload`).

## 7. Update 2026-09-30 (late): Termius key added
- The Termius iPhone public key (label `termius-iphone`) was appended to `/root/.ssh/authorized_keys` on the VPS (now 2 keys, mode 600). It was added through the public address `178.105.148.72`, because this PC could not reach the Tailscale address (`100.100.168.127` timed out - the PC is probably not connected to Tailscale).
- Not yet tested from the phone. To test: open Tailscale on the phone and sign in, then in Termius connect to `100.100.168.127` (or `178.105.148.72`), port 22, user `root`, with that key. If it fails, note the exact Termius error.
