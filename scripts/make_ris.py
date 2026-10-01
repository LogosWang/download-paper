#!/usr/bin/env python3
"""Build one EndNote-ready RIS for a folder: metadata via DOI content negotiation, L1 = absolute PDF path.
Usage: make_ris.py <out.ris> <pdf>::<doi>[::BOOK] [...]
  - add ::BOOK to force TY - BOOK (merged textbooks, CUP/Elsevier/T&F book DOIs)
  - a record with no DOI: pass ::MANUAL and edit the stub the script writes
After writing, the script validates TY/TI/AU/PY/L1 and prints gaps (CrossRef often lacks authors for
Elsevier books, drops co-authors on pre-1980 papers, and leaves MathML in titles) — patch those by hand.
"""
import sys, os, re, subprocess
out = sys.argv[1]; recs = []
for spec in sys.argv[2:]:
    parts = spec.split("::"); pdf = os.path.abspath(parts[0]); doi = parts[1]; force = parts[2] if len(parts) > 2 else None
    if not os.path.exists(pdf): print("MISSING PDF:", pdf); continue
    if doi == "MANUAL" or force == "MANUAL":
        lines = ["TY  - JOUR", "TI  - <title>", "AU  - <Last, First>", "PY  - <year>", "T2  - <journal>", "VL  - ", "SP  - "]
    else:
        ris = subprocess.run(["curl", "-sSL", "-m", "40", "-H", "Accept: application/x-research-info-systems", "https://doi.org/" + doi], capture_output=True, text=True).stdout.strip()
        if not ris.startswith("TY"): print("NO RIS FROM CROSSREF:", doi, "->", pdf); continue
        lines = [l for l in ris.splitlines() if re.match(r"^[A-Z][A-Z0-9]  - ", l) and not l.startswith(("ER", "L1"))]
        if force: lines = [("TY  - " + force) if l.startswith("TY") else l for l in lines]
    lines += ["L1  - " + pdf, "ER  - "]; recs.append("\n".join(lines))
open(out, "w").write("\n\n".join(recs) + "\n")
print(f"wrote {out}: {len(recs)} records")
for r in recs:
    g = lambda k: [l[6:] for l in r.splitlines() if l.startswith(k + "  -")]
    gaps = [k for k in ("TI", "AU", "PY") if not g(k)]
    print(f"  {g('TY')[0]:5} {(g('PY') or ['????'])[0]} | {(g('TI') or [''])[0][:55]:55} | {len(g('AU'))} au" + (f"  <-- MISSING {gaps}" if gaps else ""))
