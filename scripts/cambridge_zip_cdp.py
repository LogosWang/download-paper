#!/usr/bin/env python3
"""Cambridge Core book: tick every chapter checkbox, click 'Download PDF (zip)', save.
Usage: cambridge_zip_cdp.py <book_url> <dest.zip>"""
import sys, os, re
from playwright.sync_api import sync_playwright
url, dest = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    dl = []; ctx.on("download", lambda d: dl.append(d))
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try: page.goto(url, wait_until="domcontentloaded", timeout=90000)
    except Exception as e: print("goto:", str(e)[:60])
    page.bring_to_front(); page.wait_for_timeout(5000)
    n = page.evaluate("""() => { let c=0; document.querySelectorAll("input[type=checkbox]").forEach(e=>{ if(!e.checked){ e.click(); c++; } }); return c; }""")
    print("checkboxes ticked:", n, flush=True); page.wait_for_timeout(1500)
    loc = page.get_by_text(re.compile(r"Download PDF \(zip\)", re.I)).first
    loc.click(timeout=15000)
    for _ in range(300):
        if dl: break
        page.wait_for_timeout(2000)
    if not dl: print("no download; body:", page.inner_text("body")[:300].replace("\n"," ")); sys.exit(1)
    print("download:", dl[-1].suggested_filename, flush=True); dl[-1].save_as(dest)
    print("SAVED", dest, os.path.getsize(dest)//1024, "KB")
