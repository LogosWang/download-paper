#!/usr/bin/env python3
"""Open URL in CDP Chrome, click the element whose text matches, save resulting download.
Usage: click_download_cdp.py <url> <text-regex> <dest> [wait_min=6]"""
import sys, os, re
from playwright.sync_api import sync_playwright
url, txt, dest = sys.argv[1], sys.argv[2], sys.argv[3]; wait_min = float(sys.argv[4]) if len(sys.argv) > 4 else 6
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    dl = []; ctx.on("download", lambda d: dl.append(d))
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try: page.goto(url, wait_until="domcontentloaded", timeout=90000)
    except Exception as e: print("goto:", str(e)[:60])
    page.bring_to_front(); page.wait_for_timeout(4000)
    loc = page.get_by_text(re.compile(txt, re.I)).first
    if loc.count() == 0:
        print("no element matching", txt, "| title:", page.title()); sys.exit(1)
    print("clicking:", loc.evaluate("e => e.outerHTML.slice(0,160)"), flush=True)
    try: loc.click(timeout=15000)
    except Exception as e: print("click:", str(e)[:80])
    for _ in range(int(wait_min * 30)):
        if dl: break
        page.wait_for_timeout(2000)
    if not dl:
        print("no download; url:", page.url[:120]); print(page.inner_text("body")[:500].replace("\n"," ")); sys.exit(1)
    d = dl[-1]; print("download:", d.suggested_filename, flush=True)
    d.save_as(dest); print("SAVED", dest, os.path.getsize(dest)//1024, "KB")
