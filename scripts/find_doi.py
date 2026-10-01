#!/usr/bin/env python3
"""Resolve a citation to DOI + access info.
Usage: find_doi.py "<free-text citation or title>" [...]
Prints: DOI | year | container | pages | title, then OA pdf URLs (Unpaywall/OpenAlex) and the Elsevier PII if any.
"""
import sys, json, re, subprocess, urllib.parse
MAIL = "wanglogos7@gmail.com"
def get(url, headers=None):
    cmd = ["curl", "-sSL", "-m", "40"] + sum((["-H", h] for h in (headers or [])), []) + [url]
    return subprocess.run(cmd, capture_output=True, text=True).stdout
for q in sys.argv[1:]:
    print(f"### {q}")
    cr = json.loads(get("https://api.crossref.org/works?rows=3&mailto=%s&query.bibliographic=%s" % (MAIL, urllib.parse.quote(q))) or "{}")
    items = cr.get("message", {}).get("items", [])
    if not items: print("  no Crossref hit — try OpenAlex title.search or Google Scholar (scholar_cdp.py)"); continue
    for it in items:
        yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
        print(f"  - {it.get('DOI')} | {yr} | {(it.get('container-title') or [''])[0][:45]} | {it.get('volume')} {it.get('page')} | {(it.get('title') or [''])[0][:90]}")
    doi = items[0]["DOI"]
    oa = json.loads(get(f"https://api.openalex.org/works/https://doi.org/{doi}?mailto={MAIL}") or "{}")
    for l in oa.get("locations", []):
        if l.get("pdf_url") or l.get("is_oa"):
            print(f"    OA: {(l.get('source') or {}).get('display_name')} | pdf={l.get('pdf_url')} | {l.get('landing_page_url')}")
    if doi.startswith("10.1016/"):
        eff = subprocess.run(["curl", "-sSI", "-m", "30", "-o", "/dev/null", "-w", "%{url_effective}", "-L", f"https://doi.org/{doi}"], capture_output=True, text=True).stdout
        m = re.search(r"/pii/([A-Z0-9]+)", eff); print("    PII:", m.group(1) if m else eff[-60:])
