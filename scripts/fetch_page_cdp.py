#!/usr/bin/env python3
"""Load a URL in the CDP-attached Chrome, wait for challenge, dump title + all links + html.
Usage: fetch_page_cdp.py <url> <out.html>"""
import sys
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try: page.goto(url, wait_until="networkidle", timeout=90000)
    except Exception as e: print("goto:", str(e)[:80])
    page.bring_to_front()
    for _ in range(90):
        t = (page.title() or "").lower()
        if t and "moment" not in t and "robot" not in t and "请稍候" not in t: break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(3000)
    print("title:", page.title()); print("url:", page.url)
    open(out, "w").write(page.content())
    for h in page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)"):
        if any(k in h.lower() for k in ("bitstream", "download", ".pdf", "restricted", "request")):
            print("  link:", h[:160])
    txt = page.inner_text("body")
    import re
    for kw in ("restrict", "embargo", "access", "Fulltext", "Full text", "Files in this item"):
        for m in re.finditer(kw, txt, re.I):
            s = txt[max(0, m.start()-80): m.end()+120].replace("\n", " ")
            print(f"  [{kw}] …{s}…"); break
