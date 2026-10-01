---
name: paywalled-paper-download
description: End-to-end workflow for getting scientific literature onto disk as verified PDFs with EndNote-ready RIS records — journal articles, preprints, and whole textbooks — using the user's UCLA institutional access. Use this whenever the user asks to download, fetch, grab, 下载, 下, 找 a paper, article, reference, DOI, arXiv ID, reading list, bibliography, or textbook/e-book, pastes a citation, or asks "can EndNote read these PDFs". Covers Cloudflare-protected publishers (Elsevier/ScienceDirect, OUP, IEEE, AIP, APS, Taylor & Francis, SSRN, PNAS), open sources (arXiv, Nature, IOP, J-STAGE), institutional e-books (Cambridge Core, ScienceDirect books, T&F eBooks), and the mandatory .ris + PDF-attachment step.
---

# Literature download → verified PDF → RIS

Everything here runs on the user's Mac with UCLA institutional access. Only licensed or open-access sources are used — no Sci-Hub/LibGen; if a source is not licensed, say so and point to ILL/print.

**First time on a machine:** follow `references/install.md` (`scripts/setup.sh` does the automatable part). **Every session:** `scripts/vpn.sh status` — if the exit IP is already a UCLA address (on campus) there is nothing to connect; off-campus, run `scripts/vpn.sh up` only when a paywalled source is actually needed. Open-access routes, metadata lookups and RIS generation never need the VPN.

Scripts live in `scripts/`; run the Python ones with the skill's own venv, `<skill-dir>/venv/bin/python` (has `playwright` + `pypdf`; created by `setup.sh`). Platform quirks are in `references/platforms.md`; whole-book procedures in `references/ebooks.md`. Read those when you hit the platform in question.

## Workflow

### 1. Identify the item precisely
- `scripts/find_doi.py "<citation>"` → Crossref DOI, year, pages, OA PDF URLs (OpenAlex), and the Elsevier PII. Confirm the hit matches the citation's journal/volume/pages before downloading — a near-miss title in the same field is the most common wrong download.
- If Crossref has nothing: OpenAlex `title.search`, then Google Scholar via `scripts/scholar_cdp.py "<title>"` (needs Chrome, step 3). A title that appears nowhere but in a university repository is usually a thesis, not a journal paper — tell the user instead of hunting further.
- For an arXiv ID, check whether a journal version exists (Crossref by title); the user prefers the version of record and the arXiv file only as a supplement.
- For an author's output over a date range, use OpenAlex `author.id` — the same person is often split across two OpenAlex IDs; de-duplicate SSRN preprints against their journal versions.

### 2. Try the cheap paths first
- Open access: `curl -sSL -A "<browser UA>" -o out.pdf <pdf_url>` for arXiv, Nature/npj, IOP (`iopscience.iop.org/article/<DOI>/pdf`), J-STAGE (Crossref gives the `_pdf` link), APS free journals.
- Immediately `head -c 5 out.pdf` must be `%PDF-`; otherwise it is a challenge page — delete it and go to step 3.

### 3. Everything else: attach to a real Chrome over CDP
Playwright's own launch is fingerprinted by Cloudflare (Turnstile spins forever). What works: start Chrome normally and attach.
```
scripts/chrome_cdp.sh start                      # idempotent; profile has always_open_pdf_externally
venv/bin/python scripts/download_cdp.py <outdir> "<url>::<filename.pdf>" ...   # generic: article page or direct PDF url
scripts/chrome_cdp.sh stop                       # always close it when done
```
`download_cdp.py` waits for the challenge to clear, clicks the first `pdfft` / `Delivery.cfm` / `stampPDF` / `article-pdf` / `.pdf` link, and saves the native download. Per-platform URL patterns and the special-case scripts (`download_aip_cdp.py` for JS-rendered Silverchair pages, `page_text_cdp.py` to probe a page, `click_download_cdp.py` to press a named button) are in `references/platforms.md`.

Only one script can use the Chrome session at a time — run CDP jobs sequentially in one shell command, never in parallel tool calls. Long batches: run in the background with `python -u` and no `| tail`, so progress is visible in the output file. If a Turnstile checkbox does appear, the user has said they will click it — bring the window up and wait, don't give up.

### 4. Whole textbooks
Probe access first (`page_text_cdp.py <book_url>` and look for "You have access" / "Full text access" / "Full Access" vs "Get access"), then follow `references/ebooks.md` (Cambridge zip, ScienceDirect chapter merge, T&F e-Reader capture). Always merge chapters into one PDF and report the page count. UCLA has no e-license for several standard texts — the list is in that file; don't retry them.

### 5. Verify every file
`venv/bin/python scripts/verify_pdfs.py <dir>` — checks the magic bytes, page count, prints the first-page text so you can confirm title/authors/journal against the citation, and flags whether a DOI is present. Image-only scans show no text: render page 1 with `qlmanage -t -s 1400 -o <dir> file.pdf` and read the PNG. Never report success on a file you haven't matched to the citation this way; a wrong PII silently gives a different paper.

### 6. RIS in the same folder, PDFs attached — every time, no exceptions
A download is not finished until the folder created for that request contains a `.ris` with one record per PDF and an `L1` line pointing at it. This holds for a single paper as much as for a 20-item list, and regardless of whether the PDF carries a DOI: the user imports folders into EndNote and has been burned by "Import PDF" producing filename-only shells for pre-~2005 articles, arXiv/SSRN preprints, scans, and merged books. Generating the RIS yourself removes that failure mode entirely, so do it as the last step of every download, before reporting.
```
venv/bin/python scripts/make_ris.py <folder>/<folder-name>.ris "<pdf>::<doi>" "<book.pdf>::<book-doi>::BOOK" ...
```
Name the file after the folder. Then fix what Crossref gets wrong (the script prints the gaps): Elsevier book DOIs have no authors, pre-1980 papers lose co-authors, MathML leaks into titles, preprints should carry the journal DOI, merged books must be `TY - BOOK` with the book-level DOI (not a chapter's). Items with no DOI at all get a hand-written record from the verified title page. When a folder gains files later (user adds a book, you add a retry), regenerate the whole RIS so it stays one import.

Tell the user how to import it: 文件 → 导入 → 文件…, Import Option **Reference Manager (RIS)**, Text Translation UTF-8 — and *not* to also "Import PDF" the folder (duplicates). By default EndNote copies each attached PDF into `<Library>.Data/PDF/`; if they want EndNote to link to the originals instead, they must untick "Copy new file attachments to the default file attachment folder" in Preferences → URLs & Links *before* importing, and then never move the folder.

### 7. Deliver
- Naming: `FirstAuthor_Year_JournalAbbrev_Topic.pdf`; books `Author_Year_Title_Publisher.pdf`.
- One folder per request (the user names it or you pick a descriptive one); for a list, add a `README.md` table: item, file, DOI, source, pages, and any correction to the user's citation (wrong author list, preprint vs journal).
- Report per item: obtained or not, size/pages, how verified, source route (OA / VPN+Chrome) — and name the `.ris` file explicitly in the report, since its existence is part of the deliverable. For failures say exactly where it stopped (no license, restricted thesis, challenge) and give the DOI + landing URL.
- Close the debug Chrome and delete temp HTML/zip/chapter directories.

## Known dead ends (don't retry)
curl / curl_cffi / Playwright `request` / `route.fetch` against Cloudflare hosts; the old `pdfft?isDTMRedir` URL; Playwright `launch_persistent_context` even with automation flags stripped; `WebFetch` on Amazon, Cambridge, VitalSource, Kobo (403/500) — use the Chrome session for those pages too.
