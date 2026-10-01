#!/usr/bin/env python3
"""Verify downloaded PDFs: real PDF? pages? first-page text? DOI present (= EndNote can auto-identify)?
Usage: verify_pdfs.py <dir-or-pdf> [...]
"""
import sys, os, re, glob
from pypdf import PdfReader
DOI = re.compile(r'10\.\d{4,9}/[^\s"<>]+')
paths = []
for a in sys.argv[1:]:
    paths += sorted(glob.glob(os.path.join(a, "*.pdf"))) if os.path.isdir(a) else [a]
for f in paths:
    try:
        if open(f, "rb").read(5) != b"%PDF-": print(f"BAD   not a PDF (challenge page?) | {f}"); continue
        r = PdfReader(f); n = len(r.pages)
        txt = re.sub(r"\s+", " ", " ".join((r.pages[i].extract_text() or "") for i in range(min(2, n))))
        d = DOI.search(txt)
        tag = "DOI " if d else ("noDOI" if len(txt) > 200 else "SCAN ")
        print(f"{tag} | {os.path.getsize(f)//1024:6d} KB | {n:4d} p | {os.path.basename(f)[:60]}")
        print(f"        {txt[:150]}")
    except Exception as e:
        print(f"ERR   {f}: {e}")
