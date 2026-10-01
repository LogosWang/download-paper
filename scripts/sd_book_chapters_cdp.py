#!/usr/bin/env python3
"""ScienceDirect book: list chapter PIIs from the book page, download each chapter PDF, merge.
Usage: sd_book_chapters_cdp.py <book_url> <outdir> <merged.pdf>"""
import sys, os, re, subprocess
from playwright.sync_api import sync_playwright
url, outdir, merged = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    dl = []; ctx.on("download", lambda d: dl.append(d))
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try: page.goto(url, wait_until="domcontentloaded", timeout=90000)
    except Exception as e: print("goto:", str(e)[:60])
    page.bring_to_front(); page.wait_for_timeout(5000)
    hrefs = page.eval_on_selector_all("a[href*='/science/article/pii/B']", "els => els.map(e => e.href)")
    piis = []
    for h in hrefs:
        m = re.search(r"/pii/(B[0-9X]+)", h)
        if m and m.group(1) not in piis: piis.append(m.group(1))
    print("chapters:", len(piis), flush=True)
    files = []
    for i, pii in enumerate(piis, 1):
        dest = os.path.join(outdir, f"{i:02d}_{pii}.pdf")
        if os.path.exists(dest) and open(dest,"rb").read(5)==b"%PDF-": files.append(dest); continue
        n0 = len(dl)
        try: page.goto(f"https://www.sciencedirect.com/science/article/pii/{pii}", wait_until="domcontentloaded", timeout=90000)
        except Exception as e: print("  goto:", str(e)[:50])
        for _ in range(60):
            t = page.title() or ""
            if t and "moment" not in t.lower() and "请稍候" not in t and t != "ScienceDirect": break
            page.wait_for_timeout(2000)
        page.wait_for_timeout(2000)
        link = page.locator(f"a[href*='{pii}/pdfft']").first
        if link.count() == 0: print(f"  {i:02d} {pii}: no pdf link ({page.title()[:50]})"); continue
        try: link.click()
        except Exception as e: print("  click:", str(e)[:50])
        for _ in range(90):
            if len(dl) > n0: break
            page.wait_for_timeout(2000)
        if len(dl) <= n0: print(f"  {i:02d} {pii}: no download"); continue
        dl[-1].save_as(dest); files.append(dest); print(f"  {i:02d} {pii}: {os.path.getsize(dest)//1024} KB | {page.title()[:60]}", flush=True)
from pypdf import PdfWriter
w = PdfWriter()
for f in files: w.append(f)
w.write(merged); print("MERGED", merged, os.path.getsize(merged)//1024, "KB from", len(files), "chapters")
