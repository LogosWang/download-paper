# Whole textbooks through institutional platforms

Always probe first with `page_text_cdp.py <book_url>`; then use the platform script; then merge and verify the page count with `verify_pdfs.py`. Keep the chapter directory until the merged file is verified, then delete it.

## Cambridge Core — "You have access"
`<V> scripts/cambridge_zip_cdp.py <book_url> <dest.zip>`
"Download PDF (zip)" silently does nothing until chapters are selected; the script ticks every `input[type=checkbox]` first. A ~45 MB zip of per-chapter PDFs arrives in ~2 min. Unzip, merge with pypdf (`PdfWriter.append` is fine here).
"Get access" = no UCLA licence (true for Tadmor & Miller *Modeling Materials*, Phillips *Crystals, Defects and Microstructures*, Birks–Meier–Pettit *Introduction to the High-Temperature Oxidation of Metals* 2006). Zwanzig *Nonequilibrium Statistical Mechanics* on Oxford Academic is likewise "Get access" on every chapter.

## ScienceDirect books — "Full text access"
`<V> scripts/sd_book_chapters_cdp.py <book_url> <chapter_dir> <merged.pdf>`
"Download all chapters" is unreliable; the script harvests `a[href*='/science/article/pii/B']` PIIs and runs the normal pdfft flow per chapter, then merges. Cloudflare may interrupt after ~15 chapters — rerun, existing chapters are skipped. Verified: Pathria & Beale 3rd ed., 19 parts, 706 pp.

## Taylor & Francis eBooks — "Full Access: You have full access to download this content"
`<V> scripts/tf_chapters_cdp.py <book_url> <chapter_dir> <merged.pdf>`
There is no whole-book download. Each chapter page has an `a.sideDownload` "DOWNLOAD" link that opens the T&F e-Reader (`/reader/download/<uuid>/chapter/pdf`), whose pdf.js fetches a **pre-signed S3 URL that is effectively single-use**: curl afterwards → 403, Chrome `goto` → no download event, `response.body()` → empty. The script intercepts the request with `page.route` → `route.fetch(headers minus Range, timeout=180000)` → saves the body → `route.fulfill`. It also checks that the captured `/chapters/chapterN.pdf` matches the chapter it is on, because a timed-out fetch from an earlier chapter can complete late and leak into the next one. Chapters are ~8 MB; merge with `PdfWriter.add_page` per page (plain `append` crashes on T&F article threads). Verified: Goldenfeld, 12 chapters, 377 pp.

## Everything else
VitalSource / ProQuest / EBSCO viewers are DRM page renderers — not downloadable; report as unavailable and suggest print/ILL or purchase.

## Confirmed available / unavailable (UCLA)
- ScienceDirect, "Full text access": Young *High Temperature Oxidation and Corrosion of Metals* 2nd ed. (19 chapter PIIs → 722 pp merged), Pathria, Goldenfeld-type Elsevier titles.
- No e-licence (print at SEL only): Laidler *Chemical Kinetics* 3rd ed. (Harper & Row 1987), Atkins *Physical Chemistry* 11th ed. (OUP 2018), Levenspiel *Chemical Reaction Engineering* 3rd ed. (Wiley 1999), Crank *The Mathematics of Diffusion* 2nd ed. (Clarendon 1975; UC Library Search 2026-11-19: every e-record "No Online Access", print QD543 .C851m 1975 at SEL). Report as print-only; never fall back to Sci-Hub/LibGen.
- `sd_book_chapters_cdp.py` takes 15–20 s per chapter; a 19-chapter book exceeds a 170 s cap, so run it 2–3 times — it resumes from the chapter files already in `<outdir>`.
