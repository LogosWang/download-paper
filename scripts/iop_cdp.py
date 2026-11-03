"""IOP via CDP: open article page, wait for Radware captcha to be cleared by the human, click the PDF link, save download.
Usage: iop_cdp.py <outdir> "<doi>::<file>" ..."""
import sys, os, time
from playwright.sync_api import sync_playwright
outdir = sys.argv[1]; items = [a.split("::") for a in sys.argv[2:]]
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    dl = []; ctx.on("download", lambda d: dl.append(d))
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    for doi, name in items:
        dest = os.path.join(outdir, name)
        if os.path.exists(dest): print("  skip", name, flush=True); continue
        try: page.goto(f"https://iopscience.iop.org/article/{doi}", wait_until="domcontentloaded", timeout=60000)
        except Exception as e: print("  goto:", str(e)[:60], flush=True)
        page.bring_to_front()
        for i in range(60):
            t = (page.title() or "").lower()
            if "captcha" not in t and "radware" not in t and t.strip(): break
            if i == 0: print("  CAPTCHA shown — please click it in the Chrome window…", flush=True)
            page.wait_for_timeout(2000)
        print("  title:", (page.title() or "")[:80], flush=True)
        n0 = len(dl)
        loc = page.locator("a[href*='/pdf']").first
        if loc.count() == 0: print("  no-link", name, flush=True); continue
        try: loc.click(timeout=15000)
        except Exception as e: print("  click:", str(e)[:60], flush=True)
        for _ in range(45):
            if len(dl) > n0: break
            page.wait_for_timeout(2000)
        if len(dl) > n0:
            dl[-1].save_as(dest); print("  ok", name, os.path.getsize(dest)//1024, "KB", flush=True)
        else: print("  no-download", name, "| url:", page.url[:100], flush=True)
