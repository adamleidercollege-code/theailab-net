# Tech Spec: Website Revision v1 — IPHS 400: Frontiers in AI

**Repo:** `theailab-net` · **Branch:** `main` · **Date:** 2026-09-10
**Source:** synthesized from `docs/report_web-revision_v1_20260910.md` (code review) into actionable, ranked engineering tasks.
**Scope:** all outstanding revisions. Each task below is independently implementable; none depend on another unless noted.

---

## Already resolved — no action needed

These items from the source report are done and are listed here only so this spec isn't read as duplicating completed work:

- **Broken authentication UI (report §1, Critical).** `login.html`, `register.html`, `forgot-password.html`, `reset-password.html`, `account.html`, `core/admin.html`, and `css/auth-nav.js` have been deleted; the `<script src=".../auth-nav.js">` tag was removed from all remaining pages; the `.main-nav a.admin-dashboard-link` CSS rule was removed from `css/style.css`; `.github/sync/public.allow` no longer lists the deleted pages; and `tests/test_e2e_site.py` / `tests/test_resolve_href.py` were updated to match (22 pages total, no `admin.html` in `core/`, no `UNLINKED_AUTH_PAGES` carve-out).
- **`novalidate` / dead client-side validation (report §4, Medium).** Moot — the five forms this applied to (`login-form`, `register-form`, `forgot-form`, `reset-form`, `change-password-form`) lived exclusively on the now-deleted auth pages.
- **`account.html` inline-style toggling (report §9, minor).** Moot — the file is deleted.
- **`.gitignore` Netlify block / README Netlify mentions (report §9, minor).** Already removed in an earlier commit (`05d3e52`); verified absent from both files as of this writing.

---

## High priority

### H1 — Fix the `.notice`/`.notice-pending` CSS gap so the "pending" banner renders

**Description:** `css/style.css` still styles a retired class, `.placeholder-notice`, while `weeks/_skeleton.html.tmpl` (and 13 of the 15 week pages that use it) emit `class="notice notice-pending"`. No CSS rule matches that class, so the "PENDING — content not yet published" banner currently renders as unstyled bold text on 13 of the site's 22 live pages.

**Justification:** This is a live, user-visible rendering defect on the majority of week pages, caused by a one-line naming miss (confirmed: `grep -n "notice" css/style.css` only matches `.placeholder-notice`, and `tests/test_unit_html_structure.py::test_no_placeholder_notice` already asserts the *old* class must never appear in markup — i.e., the class was deliberately renamed in HTML but the CSS rename never happened). Fix is small, isolated, and high-ROI.

**Steps:**
1. Open `css/style.css` and find the `/* Placeholder notice */` block (currently lines 487–500):
   ```css
   .placeholder-notice {
     font-family: var(--fb);
     background: #fff3e0;
     border: 2px dashed var(--draft);
     padding: 1.5rem;
     border-radius: 8px;
     margin: 2rem 0;
     text-align: center;
   }
   .placeholder-notice h3 {
     color: var(--draft);
     margin-top: 0;
   }
   ```
2. Rename the selectors to match the markup actually shipped by `weeks/_skeleton.html.tmpl` (`<div class="notice notice-pending"><strong>PENDING</strong> — ...</div>` — note it uses `<strong>`, not `<h3>`):
   ```css
   .notice.notice-pending {
     font-family: var(--fb);
     background: #fff3e0;
     border: 2px dashed var(--draft);
     padding: 1.5rem;
     border-radius: 8px;
     margin: 2rem 0;
     text-align: center;
   }
   .notice.notice-pending strong {
     color: var(--draft);
   }
   ```
3. Confirm no HTML anywhere still uses `placeholder-notice` (`grep -rl "placeholder-notice" --include=*.html .` should return nothing — it already does, per the existing passing test).
4. Run `pytest tests/ -q` — `test_no_placeholder_notice` should still pass (it checks for the old class in HTML, which was never there), and no other test should regress.
5. Manually open one "pending" week page (e.g. `weeks/week-04.html`) in a browser and confirm the banner now shows the dashed orange-tinted box instead of plain bold text.

---

### H2 — De-duplicate content across About / Syllabus / Policies / Assignments

**Description:** Three blocks of prose/table content are duplicated verbatim (or near-verbatim) across pages with no shared source:
- "Course Description" + "Course Goals and Learning Outcomes" — identical in `core/about.html` and `core/syllabus.html`.
- "Secrets Hygiene and Agent Safety" (4 bullets) — in both `core/policies.html` and `core/syllabus.html`, **already diverged**: `policies.html` uses `<h2>`/plain `<ul>`, `syllabus.html` uses `<h3>`/`<ul class="item-list">`.
- "Summary of Assignments and Weights" table — identical in `core/assignments.html` and `core/syllabus.html`.

**Justification:** The site has no templating layer, so every duplicated block is a second copy that can silently drift — and one already has (Secrets Hygiene). For a syllabus/policies document, drifted copies are a real risk: students and the instructor need one unambiguous source for grading weights and policy text, not two that can disagree at the exact moment a dispute arises.

**Steps:**
1. Designate ownership by page purpose (dedicated page owns the full text; `syllabus.html`, which is meant to be a comprehensive but not sole-source document, links out instead of repeating):
   - `core/about.html` owns "Course Description" and "Course Goals and Learning Outcomes."
   - `core/policies.html` owns "Secrets Hygiene and Agent Safety."
   - `core/assignments.html` owns "Summary of Assignments and Weights."
2. In `core/policies.html`, first fix the existing divergence so the canonical copy is clean: standardize on `<h2>` + plain `<ul>` (matching this page's own heading convention elsewhere) before treating it as the source of truth.
3. In `core/syllabus.html`, replace each of the three duplicated blocks with a short pointer paragraph under the existing heading, e.g.:
   ```html
   <h2>Course Description</h2>
   <p>See the <a href="about.html">About page</a> for the full course description and learning outcomes.</p>
   ```
   ```html
   <h3>Secrets Hygiene and Agent Safety</h3>
   <p>See <a href="policies.html">Policies</a> for the full secrets-hygiene requirements.</p>
   ```
   ```html
   <h2>Summary of Assignments and Weights</h2>
   <p>See <a href="assignments.html">Assignments</a> for the full breakdown and current weights.</p>
   ```
   Keep the existing heading text/level in each spot so the page's table of contents / visual rhythm doesn't change — only the body under each heading is replaced.
4. Run `pytest tests/ -q`, in particular `tests/test_unit_html_structure.py::TestContentNotEmpty` (confirms `.page-content` still clears the 20-character minimum) and `tests/test_integration_links.py::TestAllInternalLinks` (confirms the new `about.html`/`policies.html`/`assignments.html` links from `syllabus.html` resolve — they will, since `syllabus.html` is in `core/` alongside them).
5. Proofread `core/syllabus.html` end-to-end to confirm the shortened sections still read naturally in context.
6. Add a regression test — see **M2** below — so this can't silently re-duplicate.

---

## Medium priority

### M1 — Sitewide accessibility improvements: skip link, `aria-current`, meta description

**Description:** Three related accessibility/SEO gaps, all sitewide because the header/nav is hand-copied into every page:
- No skip-to-content link — keyboard/screen-reader users must tab through the full ~20-line header/nav block on every page.
- The current-page nav item is marked only with `class="active"`; assistive tech gets no signal of which page is current (no `aria-current="page"`).
- No page declares `<meta name="description">` — an SEO gap and a loss for screen-reader users browsing search results and for social-media link unfurls.

(Note: `role="status"` on inline form-feedback messages was flagged in the source report as a genuine strength — that was on the now-deleted auth forms, so it no longer applies to any surviving page; no action needed there.)

**Justification:** Cheap, mechanical, sitewide wins with no design trade-offs. Skip links and `aria-current` are baseline WCAG-adjacent practices; meta descriptions are free SEO/sharing value the site currently forfeits entirely.

**Steps — skip link:**
1. Add CSS to `css/style.css` for an off-screen-until-focused link, e.g.:
   ```css
   .skip-link {
     position: absolute;
     left: -9999px;
     top: 0;
     background: var(--bg);
     color: var(--text);
     padding: 0.75rem 1rem;
     z-index: 100;
   }
   .skip-link:focus {
     left: 0.5rem;
     top: 0.5rem;
   }
   ```
2. In every HTML file (index, 404, 5 `core/*.html`, 15 `weeks/week-*.html` — 22 files), insert `<a class="skip-link" href="#main">Skip to content</a>` as the first element inside `<body>`, immediately before `<header class="site-header ...">`.
3. In every one of those same files, add `id="main"` to the `<main class="content-wrapper">` element.
4. Since this is a uniform, mechanical edit repeated 22 times, do it with a one-off script rather than by hand, e.g.:
   ```bash
   for f in index.html 404.html core/*.html weeks/week-*.html; do
     sed -i 's#<header class="site-header#<a class="skip-link" href="#main">Skip to content</a>\n<header class="site-header#' "$f"
     sed -i 's#<main class="content-wrapper">#<main class="content-wrapper" id="main">#' "$f"
   done
   ```
   Inspect a `git diff` afterward to confirm all 22 files changed identically and no unintended matches occurred (the `content-wrapper` class string doesn't appear anywhere else in the site).

**Steps — `aria-current`:**
1. Confirm `class="active"` is used only on the current-page nav link and nowhere else (`grep -rn 'class="active"' --include=*.html .` — every hit should be inside a `<nav class="main-nav">` block).
2. Run a sitewide replace: `class="active"` → `class="active" aria-current="page"`, across the same 22 files:
   ```bash
   grep -rl 'class="active"' --include=*.html . | xargs sed -i 's/class="active"/class="active" aria-current="page"/'
   ```
3. Spot-check 2–3 pages' `git diff` to confirm exactly one nav `<li>` per page changed.

**Steps — meta description:**
1. Add a `<meta name="description" content="...">` tag to the `<head>` of each of the 22 pages, right after the `<title>` tag. Content must be written per page (not scriptable) — a short 1-sentence summary of that page's purpose. Suggested starting text:
   - `index.html`: course landing page description (course title, term, institution).
   - Each `core/*.html`: one line describing that page's role (e.g., syllabus.html → "Full syllabus for IPHS 400: Frontiers in AI, Kenyon College, Fall 2026.").
   - Each `weeks/week-NN.html`: one line naming that week's topic (pull from the page's own `<h1>`/title text so it stays accurate).
   - `404.html`: a short "page not found" description.
2. Add the new assertion described in **M2** to keep this from regressing.

**Final verification:** run `pytest tests/ -q` after all three changes; then load one page in a browser, tab from a fresh page load to confirm the skip link appears on first `Tab` press and jumps focus to `<main>`.

---

### M2 — Extend the test suite to prevent recurrence of the above

**Description:** The existing suite (`tests/`, currently 30 tests) validates structure well but has three specific blind spots surfaced by this review: (1) CSS classes used in HTML are never checked against what's actually defined in `css/style.css` — the exact gap that caused **H1**; (2) nothing guards against the content duplication fixed in **H2** silently reappearing; (3) nothing guards against dead-backend references (e.g. `/.netlify/`) being reintroduced now that the Netlify integration is fully gone.

**Justification:** Without these, H1's class-name mismatch and H2's content drift are exactly the kind of defect that will recur silently on the next edit — the report explicitly called this out as a blind spot, and `conftest.py`'s existing `parsed_pages`/`nav_pages` fixtures make all three additions cheap.

**Steps:**
1. Add a new test (e.g. in `tests/test_unit_html_structure.py`, or a new `tests/test_css_coverage.py` reusing the `parsed_pages` fixture from `conftest.py`):
   - Parse `css/style.css` and collect every class selector token (regex over lines matching `\.[a-zA-Z][a-zA-Z0-9_-]*` in selector position — simplest robust approach: `re.findall(r'\.([a-zA-Z][\w-]*)', css_text)` gives a superset that's fine for a "used but never defined" check).
   - Collect every `class="..."` token used across `parsed_pages`.
   - Assert every used class also appears in the CSS-defined set. This directly would have caught H1 (`notice`, `notice-pending` used but undefined) had it existed already.
2. Add a content-duplication regression test asserting the specific blocks fixed in H2 don't reappear verbatim in `syllabus.html`, e.g.:
   ```python
   def test_syllabus_does_not_duplicate_about_description(site_root):
       about_text = (site_root / "core" / "about.html").read_text()
       syllabus_text = (site_root / "core" / "syllabus.html").read_text()
       # a distinctive sentence from about.html's Course Description
       marker = "hands-on study of the AI frontier"
       assert marker in about_text
       assert marker not in syllabus_text
   ```
   Repeat the pattern with a distinctive phrase from the Secrets Hygiene bullets (owned by `policies.html`) and from the Assignments weights table (owned by `assignments.html`).
3. Add a dead-backend-reference regression test (new test or appended to `tests/test_e2e_site.py`):
   ```python
   def test_no_netlify_references_remain(all_html_files):
       hits = []
       for f in all_html_files:
           text = f.read_text(encoding="utf-8", errors="replace")
           if "netlify" in text.lower() or "/.netlify/" in text:
               hits.append(str(f))
       assert not hits, f"Files still reference Netlify backend: {hits}"
   ```
   Extend this to also scan `css/*.js` if any JS files exist under `css/` (currently none, since `auth-nav.js` was deleted — this test guards against a similar file being reintroduced).
4. Run `pytest tests/ -q` and confirm the full suite (now ~33+ tests) passes.

---

### M3 — Populate or drop the null `by`/`published_at` fields in `weeks/manifest.json`

**Description:** `weeks/manifest.json` entries for weeks `"01"`, `"02"`, `"03"` are marked `"state": "live"` but carry `"by": null, "published_at": null` — fields that are never read by any code in the repo (`grep -rn "published_at\|manifest\[.*\]\[.by.\]"` over non-JSON files returns nothing) and never populated for the pages that are actually live.

**Justification:** Dead schema with placeholder nulls invites confusion about whether the publish-tracking automation is supposed to exist yet. `git log` shows a real publish convention already in use in commit messages (`publish: week 03 from dev@<sha>`), which is a natural, already-existing source for these values.

**Steps:**
1. Decide between two options and apply it consistently across all 15 entries in `weeks/manifest.json`:
   - **(a) Populate them.** For each `"state": "live"` entry, set `"by"` to the publishing identity used in this repo's commit convention (the `dev@<sha>` pattern seen in commits like `publish: week 03 from dev@04dec37`), and set `"published_at"` to that commit's date, found via `git log --follow --format=%aI -- weeks/week-01.html` (repeat per week, taking the first/earliest publish commit's timestamp).
   - **(b) Drop them.** Remove the `"by"` and `"published_at"` keys entirely from every entry (live and pending alike) until real publish automation exists to populate them, leaving only `"source_sha"` and `"state"`.
2. Whichever option is chosen, apply it uniformly — don't leave some entries with nulls and others populated.
3. Validate the result is well-formed JSON: `python -m json.tool weeks/manifest.json`.
4. Run `pytest tests/ -q` to confirm nothing in the suite reads this file in a way that would be affected (current suite does not reference `manifest.json` at all, so this is a safe, isolated change).

---

## Low priority

### L1 — Remove the dead `.has-featured-image` CSS block

**Description:** `css/style.css` carries a ~30-line unused block implementing a full-viewport duotone hero-image header variant (`.site-header.has-featured-image`, `.featured-media`, `.featured-media img`, `.featured-media::after`, plus a mobile-breakpoint override). Every page in the site uses `no-featured-image` instead; this is leftover surface area from the stylesheet's WordPress-theme-derived origin.

**Justification:** Pure housekeeping — dead code with no functional impact, but it adds noise for anyone reading the stylesheet and slightly bloats `css/style.css`.

**Steps:**
1. Confirm the block is genuinely unused: `grep -rl "has-featured-image" --include=*.html .` should return no results (already verified).
2. In `css/style.css`, delete:
   - The comment + rule block starting `/* --- Featured-image variant: full-viewport duotone hero --- */` through the end of `.featured-media::after { ... }` (currently around lines 69–99).
   - The mobile-breakpoint override inside the `@media` block: `.site-header.has-featured-image { ... }` and the adjacent `.featured-media { display: none; }` (currently around lines 583–590).
3. **Do not** remove the `.site-header.no-featured-image` rules — those are actively used by every page.
4. Run `pytest tests/ -q` (no test inspects CSS content, so this is safe by construction), then load one page in a browser to visually confirm the header still renders correctly.

---

### L2 — Add `robots.txt` / `sitemap.xml`, and document hosting in the README

**Description:** No `robots.txt`, `sitemap.xml`, or `CNAME` exists anywhere in the repo, and `README.md` has no deployment/hosting section — there's currently no documented answer to "how and where does this site actually get served," short of reverse-engineering `.github/sync/*` (which only governs the private-dev → public-repo sync step, not final hosting).

**Justification:** Low urgency for a small, known-audience course site, but cheap to add once a production domain/host is settled, and closes a real documentation gap.

**Steps:**
1. Once the production domain is finalized, add a `robots.txt` at the site root:
   ```
   User-agent: *
   Allow: /
   Sitemap: https://<production-domain>/sitemap.xml
   ```
2. Add a `sitemap.xml` at the site root listing the 22 live page URLs (index + 5 `core/*.html` + 15 `weeks/week-*.html`; exclude `404.html`). This can be generated by hand initially, or scripted later off the same file-enumeration logic the test suite's `all_html_files` fixture already uses.
3. Add a short "Deployment / Hosting" section to `README.md` stating how and where the site is served in production (host, domain, and whether/how `.github/sync/*` feeds into that final step).
4. This task is explicitly deferred/optional until the hosting decision is made — don't block other work on it.

---

### L3 — Revisit the no-templating architecture if the page count grows

**Description:** The header/nav/hero/footer block (~20 lines) is hand-copy-pasted into all 22 HTML files by design (per the README: "no build step, no JS framework"). This is a defensible choice at the current size, and is exactly the mechanism that produced the drift fixed in **H2**. `weeks/manifest.json` shows weeks 04–15 are still `"state": "pending"` and will each need this same block once published.

**Justification:** Not urgent today — the existing nav-consistency tests (`tests/test_integration_links.py::TestNavConsistency`) are a reasonable mitigation at 22 pages. Flagging it now as a forward-looking trigger so it's revisited deliberately rather than discovered again the hard way.

**Steps (when triggered — see trigger condition below):**
1. Write a small commit-time-only Python script (e.g. `scripts/build.py`) that reads one shared header/nav/footer template plus each page's unique body content, and writes out the final static HTML files. This keeps the *shipped* site itself build-step-free (satisfying the README's stated design goal) while removing the copy-paste failure mode at authoring time.
2. Re-run `tests/test_integration_links.py::TestNavConsistency` and the rest of the suite against the generated output before switching any real pages over, to confirm parity with the hand-written version.
3. Migrate pages incrementally (e.g., core pages first, then weeks) rather than all at once, verifying tests pass after each batch.
4. **Trigger condition:** revisit this when weeks 04–15 move from `"pending"` to `"live"` in `weeks/manifest.json` (i.e., more than 2–3 additional pages need the full block), or immediately after the next nav-consistency drift bug is found in production.
