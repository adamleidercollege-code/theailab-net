# Course Website Code Review — IPHS 400: Frontiers in AI

**Repo:** `theailab-net` (public site repo) · **Branch:** `main` · **Date:** 2026-09-10
**Scope:** all HTML/CSS/JS under the site root, the pytest suite in `tests/`, and the repo's own documentation (`README.md`), as checked out at the time of review (see [Snapshot caveat](#0-snapshot-caveat)).

## Summary

The site is a clean, dependency-free static build with a genuinely good test suite for what it checks (structure, nav consistency, link integrity). The most serious problem is not in the marketing pages — it's that **six pages of authentication UI (`login`, `register`, `forgot-password`, `reset-password`, `account`, `core/admin.html`) call a backend that no longer exists in this repo**, and nothing in the README, the tests, or the pages themselves says so. Beyond that headline issue, there's real content duplicated across three pages with no shared source, one CSS/HTML naming mismatch that silently drops a "content not yet published" banner, a chunk of fully dead CSS, and a handful of accessibility and client-validation gaps that are cheap to fix.

Findings are ordered roughly by severity/impact, not by file.

---

## 0. Snapshot caveat

At the moment of this review, `git status` shows **staged deletions** of `netlify.toml`, the entire `netlify/functions/` and `netlify/edge-functions/` trees, `package.json`, and the two `.github/workflows/*netlify*` / `*public-guard*` files, alongside an already-edited `.github/sync/public.allow` and `README.md` that both stop referencing Netlify. In other words, someone (possibly in an earlier session on this same repo) is mid-way through deliberately removing the Netlify backend and re-describing the project as a pure static site. This review treats that as the intended direction, and evaluates the working tree as it would look **if that staged deletion were committed as-is** — which is also exactly what a visitor hitting the live site would see once this state is deployed. Findings below assume that's the outcome; if the deletions are actually meant to be reverted instead, most of §1 doesn't apply, but the underlying question ("does this repo intend to ship the auth pages or not?") still needs an explicit answer either way.

---

## 1. Broken authentication UI — dead code shipping as if it were live (Critical)

Ten `fetch()` calls across nine files hit endpoints under `/.netlify/functions/*`:

| File | Endpoint(s) called |
|---|---|
| `login.html` | `/.netlify/functions/login` |
| `register.html` | `/.netlify/functions/register` |
| `forgot-password.html` | `/.netlify/functions/forgot-password` |
| `reset-password.html` | `/.netlify/functions/reset-password` |
| `account.html` | `/.netlify/functions/session`, `/.netlify/functions/change-password` |
| `core/admin.html` | `/.netlify/functions/admin-users`, `/.netlify/functions/admin-decide` |
| `css/auth-nav.js` (loaded on **every** page) | `/.netlify/functions/session`, `/.netlify/functions/logout` |

With `netlify/functions/`, `netlify.toml`, and the Netlify deploy workflow removed, none of these endpoints exist anywhere the site is described as being served. Concretely:

- Every page load runs `auth-nav.js`, which does a `fetch("/.netlify/functions/session")` on page load. With no function and no `netlify.toml` rewrite, that request 404s (or, if hosted somewhere with SPA-style fallback, silently returns HTML instead of JSON, which would throw in `res.json()`). The failure is swallowed by an empty `.catch(function () {})`, so nothing renders — but it's a wasted network request executed on **every single page view**, forever, for a login state that can never succeed.
- `login.html`, `register.html`, `forgot-password.html`, `reset-password.html`, and `account.html`'s change-password flow are fully non-functional: a visitor can fill out any of these forms, submit, and will always land on "Network error. Please try again." (or a JSON-parse failure surfaced as the same generic message).
- `auth-nav.js` injects `<a href="/admin">Admin Dashboard</a>` for admin users. That `/admin` friendly URL only ever existed via a `netlify.toml` redirect (`from = "/admin" to = "/core/admin.html"`), which is also being deleted. Even if a backend somehow existed elsewhere, this link would 404.
- The old `netlify.toml` also carried the site's only security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`). Removing it drops those headers with no replacement, on top of removing the auth backend itself.

**Why this matters beyond "a feature is down":** `README.md`'s own repository-structure diagram and prose ("plain static HTML/CSS site with no build step... no deploy pipeline") **do not mention `login.html`, `register.html`, `forgot-password.html`, `reset-password.html`, `account.html`, `core/admin.html`, or `css/auth-nav.js` at all** — six pages and a script that exist on disk, are exercised by the test suite (see §7), and will be visible/clickable to any real visitor. The documentation describes the site as if these files aren't there; the test suite asserts they must be there and structurally valid; and the pages themselves silently fail at runtime. All three artifacts disagree with each other about whether this site has authentication.

**Recommendation:** pick one and make it explicit everywhere:
1. **Site has no accounts.** Delete `login.html`, `register.html`, `forgot-password.html`, `reset-password.html`, `account.html`, `core/admin.html`, `css/auth-nav.js`, the `<script src=".../auth-nav.js">` tag on every remaining page, the `.main-nav a.admin-dashboard-link` CSS rule, and the corresponding test expectations (`EXPECTED_TOTAL_PAGES`, `EXPECTED_CORE_FILES`, `UNLINKED_AUTH_PAGES` in `tests/test_e2e_site.py`).
2. **Site still has accounts,** just on a different backend. Stand up the replacement (or restore the Netlify pieces) before shipping this deletion, and update the README to describe the real architecture.

Either is fine; shipping neither — the current state — means real users will hit dead forms.

---

## 2. Content duplicated verbatim across pages, with no shared source (High)

The site has no templating layer or includes (every page is a hand-written, fully self-contained HTML file — see §8), so duplicated prose isn't just wasteful, it actively drifts:

- **`core/about.html` and `core/syllabus.html`** contain byte-for-byte identical "Course Description" and "Course Goals and Learning Outcomes" sections (verified with `diff`; zero output).
- **`core/policies.html` and `core/syllabus.html`** both carry a "Secrets Hygiene and Agent Safety" section with the same four bullet points, but already **out of sync** in small ways — `policies.html` uses `<h2>` and a plain `<ul>`, `syllabus.html` uses `<h3>` and `<ul class="item-list">`. That's a live demonstration of the exact failure mode this pattern invites: two copies of "the same" content that have already started to diverge, with nothing to flag it.
- **`core/assignments.html` and `core/syllabus.html`** both carry the full "Summary of Assignments and Weights" table (verified identical field-for-field).

**Recommendation:** either (a) shorten `about.html` to a brief description plus a link to `syllabus.html` for the canonical text, or (b) if a build step is ever introduced, extract these blocks into includes. At minimum, pick one page as the source of truth per fact (dates, weights, policy text) and have the others link rather than restate.

---

## 3. CSS/markup mismatch drops the "not yet published" banner (Medium)

`weeks/_skeleton.html.tmpl` (the template used to scaffold new week pages) emits:

```html
<div class="notice notice-pending"><strong>PENDING</strong> — content for {{TITLE}} is not yet published.</div>
```

and 13 of the 15 week pages currently ship this exact markup (only weeks 01 and 03 are "live"). But `css/style.css` defines no `.notice` or `.notice-pending` rule anywhere — it only defines `.placeholder-notice` (a differently-named, unused class; `grep -n "notice" css/style.css` returns exactly two matches, both `.placeholder-notice`). The result: on 13 pages, the "PENDING" banner renders as an unstyled block of bold text with no visual distinction from body copy, instead of the dashed-border/orange-background treatment `.placeholder-notice` was clearly designed to provide.

Worth noting: `tests/test_unit_html_structure.py::TestNoLeftoverBranding::test_no_placeholder_notice` actively **asserts `.placeholder-notice` must not appear on any page** — so the old class was deliberately retired in favor of `.notice`/`.notice-pending`, and the CSS rename just never happened. This is a one-line miss, not a design disagreement.

**Recommendation:** rename the `.placeholder-notice` CSS block to `.notice.notice-pending` (or add `.notice-pending` as an alias), matching what the template and 13 live pages already emit.

---

## 4. Client-side form validation is decorative, not functional (Medium)

Every form on the site (`login-form`, `register-form`, `forgot-form`, `reset-form`, `change-password-form`) is declared `<form ... novalidate>`, which explicitly disables the browser's built-in constraint validation. The inputs still carry `required`, `minlength="8"`, `maxlength="40"`, and (on `register.html`) a `pattern` attribute — but because of `novalidate`, none of these are enforced by the browser, and none of the submit handlers call `form.checkValidity()` / `reportValidity()` before firing `fetch()`. A user can submit any of these forms completely empty (or with a 1-character username, or a password that doesn't match the stated pattern), and the code will send it straight to the network layer regardless. In the current broken-backend state (§1) this is moot, but it would be a real defect the moment the backend comes back: the `required`/`minlength`/`pattern` attributes exist only as inert documentation, giving a false impression that input is being validated.

Related, smaller gaps in the same forms:
- `register.html` has no "confirm password" field — a typo in the password field is only caught later, at login.
- `reset-password.html` passes the reset `token` as a URL query parameter (`?username=...&token=...`). That's a common pattern but means the token lands in browser history and (if the page ever loads any external resource) in `Referer` headers; worth a one-line comment or a decision to accept the risk, since password-reset tokens are typically single-use/short-TTL specifically because of this exposure.

**Recommendation:** either drop `novalidate` and let native validation run, or keep `novalidate` and call `form.reportValidity()` (or equivalent manual checks) at the top of each submit handler before hitting the network.

---

## 5. Dead CSS: unused "featured image" hero variant (Low/Medium — housekeeping)

`css/style.css` carries a substantial block (`~30` lines: `.site-header.has-featured-image`, `.featured-media`, `.featured-media img`, `.featured-media::after`, plus the matching mobile-breakpoint overrides) implementing a full-viewport duotone hero-image header. `grep -rl "has-featured-image"` across every HTML file in the repo returns nothing — every single page uses `no-featured-image` instead. This is leftover surface area from the stylesheet's origin (per the README, adapted wholesale from a prior WordPress-theme-derived course site) that was never exercised here.

**Recommendation:** either delete the unused block, or keep it only if there's a near-term plan to add a hero image to some page (e.g., the homepage) — in which case say so in a comment so a future reader doesn't have to run the same grep to find out it's unused.

---

## 6. Accessibility gaps (Medium)

- **No skip-to-content link.** Every page repeats the same ~20-line header/nav block before `<main>`; a keyboard or screen-reader user has no way to bypass it. A single `<a class="skip-link" href="#main">Skip to content</a>` plus `id="main"` on `<main class="content-wrapper">` would fix this site-wide.
- **Current nav item uses `class="active"` only, never `aria-current="page"`.** Sighted users get the underline; assistive tech gets nothing indicating which nav item corresponds to the current page. This is a one-attribute addition (`aria-current="page"` alongside `class="active"`) on every page's nav markup.
- **No `<html lang>` region changes needed** (this one's fine — `lang="en"` is present and consistent everywhere), but no page declares a `<meta name="description">`, which is both an SEO gap and means screen-reader users navigating by search-result summaries, and social-media unfurls, get nothing useful.
- `role="status"` is used correctly for the five inline form-feedback paragraphs (`login-message`, `register-message`, etc.) — this is a genuine strength, not a gap; calling it out so it isn't accidentally "fixed" into something worse.

---

## 7. Test suite: solid coverage of what it checks, but the coverage has a blind spot (Medium)

`tests/` (30 tests, all currently passing) does a good job of validating structural invariants: DOCTYPE presence, title suffix, stylesheet resolvability, header/footer/hero presence, nav-label consistency, internal link resolution (including the root-relative-vs-relative distinction needed for `core/admin.html`'s `/admin`-redirect design — nicely handled, see `test_resolve_href.py`), exact page counts, and full reachability from `index.html`.

What it doesn't (and structurally can't, being pure static-HTML analysis) catch:
- That the ten `fetch()` calls in §1 point at endpoints that don't exist in the repo. A lightweight test asserting "if any page fetches `/.netlify/functions/*`, the corresponding function file must exist under `netlify/functions/`" (or, once the backend question in §1 is resolved, an assertion that *no* page contains an `/.netlify/` reference) would have caught this automatically and would keep catching it on every future edit.
- That CSS classes referenced in HTML (`notice`, `notice-pending`) are actually defined in `css/style.css` — see §3. A test that extracts every `class="..."` token used across `parsed_pages` and every selector defined in `style.css`, and flags classes used-but-never-defined, would be cheap to add given the existing `parsed_pages` fixture and would have caught §3 directly.
- Content duplication (§2) — harder to test generically, but a targeted test asserting the syllabus/policies "Secrets Hygiene" section text matches between the two pages would at least keep those two copies from drifting further apart than they already have.

None of this is a knock on the existing suite's design — `conftest.py`'s shared `parsed_pages`/`nav_pages` fixtures make all three of the above additions straightforward to bolt on.

---

## 8. Architecture: no templating layer, by design, with a symptom already visible (Informational)

The README is explicit that this is "a plain static HTML/CSS site with no build step, no JS framework... Every page shares one stylesheet and a common header/nav/hero/footer skeleton" — meaning that ~20-line header/nav block, plus the footer, is hand-copy-pasted into all 28 HTML files. That's a defensible choice for a small, slow-changing course site, and the test suite's nav-consistency checks (§7) are a reasonable mitigation. But it does mean every nav change is a 28-file find-and-replace with no compiler to catch a missed spot, and it's exactly the mechanism that produced the divergence in §2. If the page count grows much past its current size (weeks 04–15 are still "pending" per `weeks/manifest.json` and will each need this same block), it may be worth revisiting — even a minimal server-side-include or a five-line Python templating script run at commit time (outside the site's own runtime, so the "no build step, no JS framework" claim about the *shipped* site still holds) would remove the copy-paste failure mode without adding any client-side complexity.

---

## 9. Minor / nitpick items

- **`.gitignore` diff in progress** (`M .gitignore`) removes the `Node / Netlify Functions` ignore block — consistent with §1's direction, just flagging it's part of the same in-flight change and should land in the same commit as the rest of the Netlify removal, not separately.
- **`weeks/manifest.json`** entries for "live" weeks include `"by": null, "published_at": null` fields that are never populated for weeks 01–03 despite those weeks being marked `"state": "live"` — either populate them at publish time or drop the fields until the automation that fills them exists, since `null` placeholders that are never used elsewhere in the repo (no code reads `manifest.json`'s `by`/`published_at`) are dead schema.
- No `robots.txt`, `sitemap.xml`, or `CNAME` file exists anywhere in the tree, and the README has no deployment/hosting section at all — reasonable for a course site with a small, known audience, but worth a one-line README note on how (and where) the site is actually served, since that context is currently missing entirely and would otherwise have to be reverse-engineered from `.github/sync/*` (which governs a private-dev → this-public-repo sync process, not the final hosting step).
- Inline `style="display:none;"` / `style.display = "block"` toggling in `account.html` (rather than a CSS class toggle) is a minor inconsistency with the rest of the site's separation of concerns — everywhere else styling lives in `css/style.css`. Low priority given it's one element on one page.

---

## Priority checklist

1. **Resolve the auth-pages question (§1)** — either finish removing them (pages, script, nav injection, CSS rule, test expectations) or restore/replace the backend before this deletion ships. This is the one item that will visibly break for real users.
2. **Fix the `.notice`/`.notice-pending` CSS gap (§3)** — one CSS rule, restores the pending-week banner on 13 pages.
3. **De-duplicate the About/Syllabus/Policies content (§2)** — pick a source of truth per section.
4. **Add `aria-current="page"` and a skip link (§6)** — cheap, sitewide accessibility wins.
5. **Fix or remove the dead `novalidate` + validation-attribute combination (§4)** on all five forms.
6. **Delete the unused `.has-featured-image` CSS block (§5)**, or document why it's being kept.
7. **Extend the test suite** to catch dangling `/.netlify/` references and undefined CSS classes (§7), so items like #1 and #2 above can't silently recur.
