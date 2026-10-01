#!/bin/bash
# Idempotent environment check / setup for the paywalled-paper-download skill (macOS).
# Run it after copying the skill to a new machine; rerun any time — it only fixes what is missing.
#   setup.sh            check everything, install what can be installed automatically, print what is left for the human
#   setup.sh --check    report only, change nothing
SKILL="$(cd "$(dirname "$0")/.." && pwd)"; CHECK=0; [ "$1" = "--check" ] && CHECK=1
ok(){ printf "  ✓ %s\n" "$1"; }; miss(){ printf "  ✗ %s\n" "$1"; TODO+=("$2"); }; TODO=()
echo "skill dir: $SKILL"

echo "[1] Google Chrome (the real browser every *_cdp.py attaches to)"
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then ok "installed"
elif [ $CHECK = 0 ] && command -v brew >/dev/null; then brew install --cask google-chrome && ok "installed via Homebrew" || miss "install failed" "Install Google Chrome: https://www.google.com/chrome/"
else miss "not found" "Install Google Chrome (brew install --cask google-chrome, or https://www.google.com/chrome/)"; fi

echo "[2] python3 + venv with playwright, pypdf  (no 'playwright install' needed — system Chrome is used over CDP)"
if command -v python3 >/dev/null; then
  if [ ! -x "$SKILL/venv/bin/python" ] && [ $CHECK = 0 ]; then python3 -m venv "$SKILL/venv"; fi
  if [ -x "$SKILL/venv/bin/python" ]; then
    "$SKILL/venv/bin/python" -c "import playwright, pypdf" 2>/dev/null && ok "venv ready" || { [ $CHECK = 0 ] && "$SKILL/venv/bin/pip" install -q playwright pypdf && ok "venv packages installed" || miss "venv missing playwright/pypdf" "$SKILL/venv/bin/pip install playwright pypdf"; }
  else miss "venv absent" "python3 -m venv $SKILL/venv && $SKILL/venv/bin/pip install playwright pypdf"; fi
else miss "python3 not found" "Install Xcode CLT (xcode-select --install) or brew install python"; fi

echo "[3] Chrome profile with PDF-download preference (so PDFs download instead of opening the viewer)"
P="$SKILL/chrome_profile/Default/Preferences"
if [ $CHECK = 0 ]; then mkdir -p "$(dirname "$P")"; python3 - "$P" <<'PY'
import json,sys,os
p=sys.argv[1]; d=json.load(open(p)) if os.path.exists(p) else {}
d.setdefault("plugins",{})["always_open_pdf_externally"]=True; d.setdefault("download",{})["prompt_for_download"]=False
json.dump(d,open(p,"w"))
PY
fi
grep -q always_open_pdf_externally "$P" 2>/dev/null && ok "profile prefs set" || miss "profile prefs missing" "rerun setup.sh without --check"

echo "[4] curl / qlmanage (verification of image-only scans)"
command -v curl >/dev/null && ok "curl" || miss "curl missing" "brew install curl"
command -v qlmanage >/dev/null && ok "qlmanage" || miss "qlmanage missing (not macOS?)" "render scanned PDFs with another tool"

echo "[5] OpenConnect (Homebrew) — the VPN client behind ucla-vpn-on; only needed off-campus"
if [ -x "$(brew --prefix 2>/dev/null)/bin/openconnect" ]; then ok "openconnect $(brew list --versions openconnect 2>/dev/null | awk '{print $2}')"
elif [ $CHECK = 0 ] && command -v brew >/dev/null; then brew install openconnect && ok "openconnect installed" || miss "brew install openconnect failed" "brew install openconnect"
else miss "openconnect not installed" "brew install openconnect   (install Homebrew first: https://brew.sh)"; fi

echo "[6] UCLA VPN scripts in system locations (from assets/vpn/, need sudo once)"
BREWBIN="$(brew --prefix 2>/dev/null)/bin"; NEED=0
for f in sbin/ucla-vpn-on sbin/ucla-vpn-off libexec/openconnect-browser; do
  b=$(basename "$f"); if [ -x "/usr/local/$f" ] && cmp -s "/usr/local/$f" "$SKILL/assets/vpn/$b"; then ok "/usr/local/$f"; else NEED=1; fi
done
if [ $NEED = 1 ]; then
  if [ $CHECK = 0 ]; then
    echo "  installing to /usr/local/{sbin,libexec} (sudo password prompt is expected)…"
    sudo install -d -m 755 /usr/local/sbin /usr/local/libexec \
    && sudo install -m 755 "$SKILL/assets/vpn/ucla-vpn-on" "$SKILL/assets/vpn/ucla-vpn-off" /usr/local/sbin/ \
    && sudo install -m 755 "$SKILL/assets/vpn/openconnect-browser" /usr/local/libexec/ \
    && { [ -d "$BREWBIN" ] && sudo ln -sf /usr/local/sbin/ucla-vpn-on /usr/local/sbin/ucla-vpn-off "$BREWBIN/"; } \
    && ok "ucla-vpn-on / ucla-vpn-off / openconnect-browser installed (+ symlinks in $BREWBIN)" \
    || miss "install failed" "sudo install -m 755 $SKILL/assets/vpn/ucla-vpn-* /usr/local/sbin/ ; sudo install -m 755 $SKILL/assets/vpn/openconnect-browser /usr/local/libexec/ ; sudo ln -sf /usr/local/sbin/ucla-vpn-on /usr/local/sbin/ucla-vpn-off $BREWBIN/"
  else miss "scripts missing or differ from assets/vpn" "rerun setup.sh without --check (needs sudo)"; fi
fi
command -v ucla-vpn-on >/dev/null && ok "ucla-vpn-on on PATH" || miss "ucla-vpn-on not on PATH" "sudo ln -sf /usr/local/sbin/ucla-vpn-on /usr/local/sbin/ucla-vpn-off $BREWBIN/"
if sudo -n true 2>/dev/null || grep -qs "ucla-vpn-on" /etc/sudoers.d/* 2>/dev/null; then ok "sudo without password for the vpn scripts (Claude can run vpn.sh up itself)"
else echo "  · optional: vpn.sh up/down will ask for your sudo password in the terminal; to let Claude run them unattended, see install.md step 3"; fi

echo "[7] Network"
IP=$(curl -s -m 8 https://api.ipify.org); echo "$IP" | grep -qE '^(131\.179|128\.97|149\.142|164\.67)\.' && ok "on a UCLA address ($IP) — paywalled downloads work without connecting" || echo "  · off-campus address ($IP) — scripts/vpn.sh up when a paywalled source is needed; open-access sources work regardless"

echo; if [ ${#TODO[@]} -eq 0 ]; then echo "ALL SET."; else echo "REMAINING STEPS:"; for t in "${TODO[@]}"; do echo "  - $t"; done; fi
