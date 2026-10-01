#!/usr/bin/env python3
"""Load URL in CDP Chrome, print body text. Usage: page_text_cdp.py <url> [maxchars]"""
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222"); ctx = b.contexts[0]
    page = ctx.new_page()
    try: page.goto(url, wait_until="networkidle", timeout=60000)
    except Exception as e: print("goto:", str(e)[:60])
    page.wait_for_timeout(3000)
    print("title:", page.title(), "| url:", page.url[:120])
    print(page.inner_text("body")[:n])
    page.close()
