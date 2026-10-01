#!/usr/bin/env python3
"""Taylor & Francis book (institutional full access): per chapter, open the e-Reader and capture the
body of the pre-signed S3 chapter-PDF response the reader itself fetches; then merge.
Usage: tf_chapters_cdp.py <book_url> <outdir> <merged.pdf>"""
import sys, os, re
from playwright.sync_api import sync_playwright
url, outdir, merged = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(outdir, exist_ok=True)
files = []
S3 = re.compile(r"amazonaws\.com/.*/chapters/.*\.pdf\?", re.I)
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    captured = {}
    def on_route(route):
        req = route.request
        hdrs = {k: v for k, v in req.headers.items() if k.lower() != "range"}
        try:
            resp = route.fetch(headers=hdrs, timeout=180000)
            body = resp.body()
            m = re.search(r"/chapters/chapter(\d+)\.pdf", req.url)
            if body[:5] == b"%PDF-" and "body" not in captured and m and int(m.group(1)) == captured.get("want", -1):
                captured["body"] = body; captured["url"] = req.url
            route.fulfill(status=200, headers={"content-type": "application/pdf", "access-control-allow-origin": "*"}, body=body)
        except Exception as e:
            captured["err"] = str(e)[:80]
            try: route.continue_()
            except Exception: pass
    page.route(re.compile(r"amazonaws\.com/.*/chapters/.*\.pdf\?"), on_route)
    try: page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e: print("goto:", str(e)[:60])
    page.bring_to_front()
    chaps = []
    for _ in range(60):
        chaps = page.eval_on_selector_all("a[href*='/chapters/']", "els => [...new Set(els.map(e=>e.href.split('?')[0]))]")
        if chaps: break
        page.wait_for_timeout(2000)
    chaps = sorted(set(chaps), key=lambda h: int(re.search(r"-(\d+)/", h).group(1)) if re.search(r"-(\d+)/", h) else 0)
    print("chapters:", len(chaps), flush=True)
    for i, ch in enumerate(chaps, 1):
        dest = os.path.join(outdir, f"{i:02d}.pdf")
        if os.path.exists(dest) and open(dest,"rb").read(5)==b"%PDF-": files.append(dest); continue
        captured.clear(); captured["want"] = i
        try: page.goto(ch, wait_until="domcontentloaded", timeout=60000)
        except Exception as e: print("  goto:", str(e)[:40])
        btn = None
        for _ in range(60):
            btn = page.locator("a.sideDownload, a,button").filter(has_text=re.compile(r"download", re.I))
            if btn.count(): break
            page.wait_for_timeout(2000)
        if not btn or not btn.count(): print(f"  {i:02d} no DOWNLOAD button | {page.title()[:50]}", flush=True); continue
        try: btn.first.click(timeout=10000)
        except Exception as e: print(f"  {i:02d} click: {str(e)[:50]}", flush=True)
        for _ in range(120):
            if "body" in captured or "err" in captured: break
            page.wait_for_timeout(2000)
        if "body" not in captured: print(f"  {i:02d} no S3 response captured ({captured.get('err','timeout')}) | {page.url[:70]}", flush=True); continue
        body = captured["body"]
        if body[:5] != b"%PDF-": print(f"  {i:02d} captured non-PDF ({len(body)} B)", flush=True); continue
        open(dest, "wb").write(body); files.append(dest)
        print(f"  {i:02d} {len(body)//1024} KB | {re.search(r'chapters/([^?]+)', captured['url']).group(1)}", flush=True)
if files:
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter(); n = 0
    for f in sorted(files):
        for pg in PdfReader(f).pages: w.add_page(pg); n += 1
    w.write(merged); print("MERGED", merged, os.path.getsize(merged)//1024, "KB |", n, "pages from", len(files), "chapters")
