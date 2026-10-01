# Installing this skill on a new Mac

Everything is idempotent; rerun `scripts/setup.sh` any time. Claude can do all of it; the human is needed only to type the sudo password when prompted and to complete the UCLA SSO/Duo login in the browser on the first `vpn.sh up`.

## 1. Put the skill in place
```
mkdir -p ~/.claude/skills
cp -R <source>/paywalled-paper-download ~/.claude/skills/
rm -rf ~/.claude/skills/paywalled-paper-download/{venv,chrome_profile}      # machine-specific, always rebuilt
```
No absolute paths inside: scripts resolve `venv/`, `chrome_profile/` and `assets/` relative to the skill directory.

## 2. Run the setup script
```
bash ~/.claude/skills/paywalled-paper-download/scripts/setup.sh
```
It does, in order: Google Chrome (Homebrew cask if missing) · `venv/` with `playwright` + `pypdf` (system Chrome is driven over CDP, no browser download) · Chrome profile preference that turns PDF views into downloads · curl/qlmanage check · `brew install openconnect` · copies the three VPN scripts from `assets/vpn/` to `/usr/local/sbin/ucla-vpn-on`, `/usr/local/sbin/ucla-vpn-off`, `/usr/local/libexec/openconnect-browser` and symlinks the first two into `$(brew --prefix)/bin` (one sudo prompt) · reports the exit IP. Its REMAINING STEPS list is what is still open.

What the VPN pieces are: `ucla-vpn-on` runs `openconnect --protocol=anyconnect --external-browser=/usr/local/libexec/openconnect-browser --background https://ssl.vpn.ucla.edu/`; the browser launcher opens the SAML login URL in the console user's default browser (UCLA Logon + Duo), and the pid is kept in `/var/run/ucla-openconnect.pid` so `ucla-vpn-off` can stop it. Cisco Secure Client is *not* required.

## 3. Optional: let Claude run the VPN unattended
`ucla-vpn-on/off` re-exec with sudo, which prompts for a password that Claude's shell cannot answer. If you want `vpn.sh up` to work from inside Claude Code, add a rule for exactly these two scripts (human runs it):
```
echo "$USER ALL=(root) NOPASSWD: /usr/local/sbin/ucla-vpn-on, /usr/local/sbin/ucla-vpn-off" | sudo tee /etc/sudoers.d/ucla-vpn >/dev/null && sudo chmod 440 /etc/sudoers.d/ucla-vpn
```
Without it, run `vpn.sh up` in your own terminal once per session; the skill works the same either way.

## 4. Verify
```
bash scripts/setup.sh --check                   # all ✓
bash scripts/vpn.sh status                      # on/off + IP
bash scripts/chrome_cdp.sh start && bash scripts/chrome_cdp.sh stop
python3 scripts/find_doi.py "Heston 1993 closed-form solution stochastic volatility"
venv/bin/python scripts/verify_pdfs.py <any pdf>
```
Then one end-to-end run on an open-access paper (curl an arXiv PDF into a new folder, `make_ris.py` it, check the RIS) before touching paywalled sources.

## VPN is a tool, not a gate
On a UCLA network the exit IP is already licensed (131.179 / 128.97 / 149.142 / 164.67) and nothing needs connecting — `vpn.sh up` notices and exits. Off-campus, connect only when a paywalled source is actually needed; open-access routes, Crossref/OpenAlex lookups and RIS generation never need it. Decide from `vpn.sh status`, never from assumptions.
