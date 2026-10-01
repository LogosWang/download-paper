#!/usr/bin/env python3
"""Google Scholar search in the CDP-attached Chrome; prints result titles/links.
Usage: scholar_cdp.py "<query>" """
import sys, urllib.parse
from playwright.sync_api import sync_playwright
q = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://scholar.google.com/scholar?hl=en&q=" + urllib.parse.quote(q), wait_until="domcontentloaded", timeout=60000)
    page.bring_to_front()
    for _ in range(90):
        if page.locator(".gs_r, #gs_res_ccl_mid, .gs_alrt").count() > 0: break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(1500)
    print("title:", page.title())
    for r in page.locator(".gs_r.gs_or").all()[:8]:
        t = r.locator(".gs_rt").first.inner_text().strip()
        href = r.locator(".gs_rt a").first.get_attribute("href") if r.locator(".gs_rt a").count() else "-"
        meta = r.locator(".gs_a").first.inner_text().strip() if r.locator(".gs_a").count() else ""
        pdf = r.locator(".gs_or_ggsm a").first.get_attribute("href") if r.locator(".gs_or_ggsm a").count() else "-"
        print(f"\n* {t}\n  {meta}\n  link: {href}\n  pdf:  {pdf}")
    if page.locator(".gs_r.gs_or").count() == 0:
        print("no results; body:", page.inner_text("body")[:400].replace("\n"," "))
