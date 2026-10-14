# Platform notes (all verified on this machine, Sep 2026)

Use with `download_cdp.py` unless a dedicated script is named. `<V>` = venv python, Chrome already started with `chrome_cdp.sh start`.

| Platform | What to feed `download_cdp.py` | Notes |
|---|---|---|
| **Elsevier / ScienceDirect** | `https://www.sciencedirect.com/science/article/pii/<PII>` | PII from `find_doi.py` (DOI redirect). Script clicks the tokenised `a[href*='<PII>/pdfft']`. After ~15–30 downloads in one session Cloudflare may throw a challenge ("请稍候…"); wait a few minutes or let the user click. Parentheses in old DOIs (`10.1016/0370-1573(74)90023-4`) break shell PII resolution — PII is the DOI's digits: `0370157374900234`. |
| **OUP (academic.oup.com)** incl. Prog. Theor. Phys. | DOI landing page via `download_aip_cdp.py <doi> <dest>` | Silverchair, JS-rendered: wait for `a[href*='article-pdf']`. Challenge clears by itself. Old scans are image-only. |
| **AIP (pubs.aip.org)** | `download_aip_cdp.py <doi> <dest>` | Same Silverchair logic; `page.goto` raising "Download is starting" is normal. AIP puts a CHORUS *accepted manuscript* link first — the script now skips it and takes `…_online.pdf` (version of record); if a JCP download comes back with 50 pages and no journal header, that is the AM. |
| **IEEE Xplore** | `https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=<N>&ref=` | arnumber = last digits of the DOI. curl gets 502. |
| **APS (PRL/PR/RMP, Physics Physique Fizika)** | `https://journals.aps.org/<jrnl>/pdf/<DOI>` | Direct PDF URL downloads natively; if the title stays "Loading", feed the `/abstract/` page instead and let the script click. |
| **Taylor & Francis journals** | `https://www.tandfonline.com/doi/pdf/<DOI>?download=true` | curl 403; direct URL downloads natively over CDP. |
| **PNAS** | `https://www.pnas.org/doi/pdf/<DOI>?download=true` | curl 403; works over CDP. |
| **SSRN** | `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=<N>` | Script clicks `a[href*='Delivery.cfm']`. Check whether the preprint has a journal version first. |
| **Nature / npj, IOP, arXiv, J-STAGE, APS free titles** | plain `curl -A "<browser UA>"` | No browser needed. IOP: `https://iopscience.iop.org/article/<DOI>/pdf`. |
| **Springer** | `https://link.springer.com/content/pdf/<DOI>.pdf` via curl | Allowed with a browser UA on institutional IP. |
| **CityU Scholars / institutional repositories** | usually 403 to curl | Not worth fighting; use the publisher route. |
| **DSpace repositories (DR-NTU etc.)** | REST API `/server/api/pid/find?id=hdl:<handle>` → `bundles` → bitstream `content` | Shows file list and `accessStatus`; `restricted` + HTTP 401 means campus-only — stop and report. |

## Probing a page you don't know
`<V> scripts/page_text_cdp.py <url> [maxchars]` prints title + body text — grep it for access words, prices, or button labels before writing a click.
`<V> scripts/click_download_cdp.py <url> "<button text regex>" <dest>` presses a button and saves whatever download follows.
`<V> scripts/scholar_cdp.py "<query>"` prints Google Scholar results with PDF links.

## Searching Chinese sources
Baidu Xueshu and CNKI block the automated Chrome (captcha / bad cert). If a title with Chinese authors is missing from Crossref/OpenAlex/Scholar, ask the user for the source rather than looping on these.

## E-book prices (if asked)
Amazon/Kobo/Cambridge product pages 403 to WebFetch; load them in the CDP Chrome and read `.a-price .a-offscreen` / `[id^=tmm-grid-swatch]` on Amazon, body text on Kobo/Cambridge.
