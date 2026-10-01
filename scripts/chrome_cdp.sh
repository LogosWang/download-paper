#!/bin/bash
# Start / stop the real Chrome that every *_cdp.py script attaches to.
#   chrome_cdp.sh start [profile_dir]   -> launches Chrome with --remote-debugging-port=9222 (idempotent)
#   chrome_cdp.sh stop
# The profile must have Default/Preferences with always_open_pdf_externally=true so PDFs download instead of opening the viewer.
PROFILE="${2:-$(dirname "$0")/../chrome_profile}"
case "$1" in
  start)
    if curl -s -m 3 http://127.0.0.1:9222/json/version >/dev/null; then echo "chrome already up"; exit 0; fi
    mkdir -p "$PROFILE/Default"
    python3 - "$PROFILE/Default/Preferences" <<'PY'
import json,sys,os
p=sys.argv[1]; d=json.load(open(p)) if os.path.exists(p) else {}
d.setdefault("plugins",{})["always_open_pdf_externally"]=True
d.setdefault("download",{})["prompt_for_download"]=False
json.dump(d,open(p,"w"))
PY
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 \
      --user-data-dir="$PROFILE" --no-first-run --no-default-browser-check >/dev/null 2>&1 &
    for i in $(seq 1 15); do sleep 1; curl -s -m 2 http://127.0.0.1:9222/json/version >/dev/null && { echo "chrome up ($(curl -s http://127.0.0.1:9222/json/version | grep -o '"Browser": "[^"]*"'))"; exit 0; }; done
    echo "chrome failed to start"; exit 1;;
  stop) pkill -f "remote-debugging-port=9222" 2>/dev/null; echo "chrome stopped";;
  *) echo "usage: chrome_cdp.sh start|stop [profile_dir]"; exit 2;;
esac
