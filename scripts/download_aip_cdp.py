#!/usr/bin/env python3
"""AIP (pubs.aip.org, Silverchair) PDF via CDP Chrome: waits for the JS-rendered article-pdf link.
Usage: download_aip_cdp.py <doi-or-url> <dest.pdf>"""
import sys, os, re
from playwright.sync_api import sync_playwright
url, dest = sys.argv[1], sys.argv[2]
if not url.startswith("http"): url = "https://doi.org/" + url
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    dl = []; ctx.on("download", lambda d: dl.append(d))
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try: page.goto(url, wait_until="domcontentloaded", timeout=90000)
    except Exception as e: print("goto:", str(e)[:70])
    page.bring_to_front()
    try:
        page.wait_for_selector("a[href*='article-pdf']", timeout=120000)
    except Exception:
        print("no article-pdf link after 120s; title:", page.title(), "| url:", page.url[:120])
        print(page.inner_text("body")[:600].replace("\n", " ")); sys.exit(1)
    hrefs = page.eval_on_selector_all("a[href*='article-pdf']", "els => els.map(e => e.href)")
    # AIP lists the CHORUS accepted manuscript first; prefer the typeset version of record
    vor = [h for h in hrefs if not re.search(r"accepted_manuscript|/am/|_am\.pdf", h, re.I)]
    href = (vor or hrefs)[0]
    if href.startswith("/"):
        from urllib.parse import urlsplit; u = urlsplit(page.url); href = f"{u.scheme}://{u.netloc}" + href
    print("pdf link:", href[:140], flush=True)
    try: page.goto(href, wait_until="domcontentloaded", timeout=90000)
    except Exception as e: print("goto pdf:", str(e)[:50])
    for _ in range(90):
        if dl: break
        page.wait_for_timeout(2000)
    if not dl: print("FAILED: no download; url:", page.url[:120]); sys.exit(1)
    dl[-1].save_as(dest)
ok = open(dest, "rb").read(5) == b"%PDF-"
print(("SUCCESS " if ok else "NOT-PDF ") + f"{dest} ({os.path.getsize(dest)//1024} KB)")
