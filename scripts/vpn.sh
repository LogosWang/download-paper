#!/bin/bash
# UCLA VPN wrapper around the user's OpenConnect setup (assets/vpn/*, installed by setup.sh):
#   vpn.sh up       → ucla-vpn-on  : openconnect --protocol=anyconnect, login page opens in your browser (UCLA SSO + Duo)
#   vpn.sh down     → ucla-vpn-off : SIGINT to the pid in /var/run/ucla-openconnect.pid
#   vpn.sh status   → exit IP, and whether it is a UCLA address (131.179 / 128.97 / 149.142 / 164.67)
# Both on/off re-exec themselves with sudo, so a terminal password prompt is normal unless the optional
# NOPASSWD rule from references/install.md is in place.
ON=$(command -v ucla-vpn-on || echo /usr/local/sbin/ucla-vpn-on); OFF=$(command -v ucla-vpn-off || echo /usr/local/sbin/ucla-vpn-off)
ip(){ curl -s -m 8 https://api.ipify.org; }
ucla(){ ip | grep -qE '^(131\.179|128\.97|149\.142|164\.67)\.'; }
case "$1" in
  up)
    if ucla; then echo "already on a UCLA address ($(ip)) — nothing to connect"; exit 0; fi
    [ -x "$ON" ] || { echo "ucla-vpn-on not installed — run scripts/setup.sh"; exit 2; }
    "$ON" || exit $?
    echo "complete the UCLA SSO / Duo login in the browser window…"
    for i in $(seq 1 60); do sleep 3; ucla && { echo "UCLA VPN up ($(ip))"; exit 0; }; done
    echo "still not on a UCLA address after 3 min — check the browser login / sudo prompt"; exit 1;;
  down)
    [ -x "$OFF" ] || { echo "ucla-vpn-off not installed — run scripts/setup.sh"; exit 2; }
    "$OFF"; sleep 2; ucla && echo "still on a UCLA address ($(ip)) — on campus, or another tunnel is up" || echo "VPN down ($(ip))";;
  status|*) a=$(ip); ucla && echo "UCLA VPN: on  ($a)" || echo "UCLA VPN: off ($a)";;
esac
