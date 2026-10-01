#!/usr/bin/env python3
"""Download PDFs by attaching over CDP to a normally-launched real Chrome (beats Cloudflare/IEEE).

Start Chrome first:
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 \
     --user-data-dir=<profile> --no-first-run --no-default-browser-check &
  (profile/Default/Preferences must contain {"plugins":{"always_open_pdf_externally":true}})
Usage: download_cdp.py <outdir> <url::filename> [...]
"""
import sys, os
from playwright.sync_api import sync_playwright

outdir = sys.argv[1]
jobs = [a.split("::", 1) for a in sys.argv[2:]]
results = []

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = browser.contexts[0]
    downloads = []
    ctx.on("download", lambda d: downloads.append(d))
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    for url, name in jobs:
        dest = os.path.join(outdir, name)
        print(f"\n>>> {name}\n    {url}", flush=True)
        if os.path.exists(dest) and open(dest, "rb").read(5) == b"%PDF-":
            print("    already have it"); results.append((name, "skip")); continue
        n0 = len(downloads)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
        except Exception as e:
            print("    goto:", str(e)[:80])
        page.bring_to_front()
        cleared = False
        for _ in range(150):              # up to 5 min; a human may click Turnstile
            if len(downloads) > n0:
                cleared = True; break
            t = page.title() or ""; low = t.lower()
            if t and "请稍候" not in t and "moment" not in low and "robot" not in low \
               and "attention required" not in low and t != "ScienceDirect":
                cleared = True; break
            page.wait_for_timeout(2000)
        print("    cleared:", cleared, "| title:", (page.title() or "")[:70], flush=True)
        if not cleared:
            results.append((name, "challenge-stuck")); continue

        if len(downloads) == n0:          # not a direct-PDF url: find and click the PDF link
            page.wait_for_timeout(2500)
            link = page.locator("a[href*='pdfft'], a[href*='Delivery.cfm'], a[href*='stampPDF'], a[href*='article-pdf'], "
                                "a[href*='/pdf'], a[href$='.pdf']").first
            if link.count() == 0:
                print("    no PDF link on page"); results.append((name, "no-link")); continue
            print("    clicking:", (link.get_attribute("href") or "")[:100])
            try: link.click()
            except Exception as e: print("    click:", str(e)[:70])
            for _ in range(120):
                if len(downloads) > n0: break
                page.wait_for_timeout(2000)
        if len(downloads) <= n0:
            print("    FAILED: no download event; url now:", page.url[:100]); results.append((name, "no-download")); continue
        downloads[-1].save_as(dest)
        ok = open(dest, "rb").read(5) == b"%PDF-"
        print(f"    {'SUCCESS' if ok else 'NOT-PDF'}: {os.path.getsize(dest)//1024} KB", flush=True)
        results.append((name, "ok" if ok else "not-pdf"))

print("\n===== SUMMARY")
for n, s in results: print(f"  {s:16} {n}")
