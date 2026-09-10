"""Unit tests: every HTML page has valid structure and required elements."""
import re
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent
STYLE_CSS = SITE_ROOT / "css" / "style.css"

TITLE_SUFFIX = "– IPHS 400: Frontiers in AI"  # en dash
FOOTER_TEXT = "IPHS 400: Frontiers in AI · Kenyon College"


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


class TestDoctype:
    def test_all_pages_have_doctype(self, parsed_pages):
        """Every HTML page must begin with <!DOCTYPE html>."""
        failures = []
        for path, text, _ in parsed_pages:
            if not text.strip().lower().startswith("<!doctype html"):
                failures.append(_rel(path))
        assert not failures, f"Pages missing <!DOCTYPE html>: {failures[:15]}"


class TestTitle:
    def test_all_titles_end_with_course_suffix(self, parsed_pages):
        """Every <title> must end with '{TITLE_SUFFIX}'."""
        failures = []
        for path, _, soup in parsed_pages:
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            if not title.endswith(TITLE_SUFFIX):
                failures.append(f"{_rel(path)}: '{title}'")
        assert not failures, f"Titles not ending with course suffix: {failures[:15]}"


class TestCSSLink:
    def test_all_pages_link_to_resolvable_style_css(self, parsed_pages):
        """Every page must have a <link rel='stylesheet'> to a resolvable css/style.css."""
        failures = []
        for path, _, soup in parsed_pages:
            links = [
                tag for tag in soup.find_all("link", rel="stylesheet")
                if "style.css" in tag.get("href", "")
            ]
            if not links:
                failures.append(f"{_rel(path)}: no stylesheet link")
                continue
            href = links[0]["href"]
            # A leading "/" is site-root-relative (as a browser resolves it against
            # the site origin), not filesystem-root-relative.
            base = SITE_ROOT if href.startswith("/") else path.parent
            target = (base / href.lstrip("/")).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: href '{href}' does not resolve")
        assert not failures, f"CSS link issues: {failures[:15]}"


class TestHeaderFooterHero:
    def test_all_pages_have_site_header(self, parsed_pages):
        """Every page must contain a <header class="site-header">."""
        failures = [_rel(p) for p, _, s in parsed_pages if not s.select_one("header.site-header")]
        assert not failures, f"Pages missing header.site-header: {failures[:15]}"

    def test_all_pages_have_site_footer_with_text(self, parsed_pages):
        """Every page must contain a <footer class="site-footer"> with the course footer text."""
        failures = []
        for path, _, soup in parsed_pages:
            footer = soup.select_one("footer.site-footer")
            if not footer:
                failures.append(f"{_rel(path)}: missing footer.site-footer")
                continue
            if FOOTER_TEXT not in footer.get_text():
                failures.append(f"{_rel(path)}: footer text mismatch")
        assert not failures, f"Footer issues: {failures[:15]}"

    def test_all_pages_have_hero_with_h1(self, parsed_pages):
        """Every page must have a <section class="hero"> containing an <h1>."""
        failures = []
        for path, _, soup in parsed_pages:
            hero = soup.select_one("section.hero")
            if not hero:
                failures.append(f"{_rel(path)}: missing section.hero")
                continue
            if not hero.find("h1"):
                failures.append(f"{_rel(path)}: hero has no h1")
        assert not failures, f"Hero section issues: {failures[:15]}"


class TestNoLeftoverBranding:
    def test_no_programming_humanity_text(self, parsed_pages):
        """No page should contain leftover 'Programming Humanity' template branding."""
        failures = [
            _rel(path) for path, text, _ in parsed_pages
            if "Programming Humanity" in text
        ]
        assert not failures, f"Pages with leftover 'Programming Humanity' text: {failures[:15]}"

    def test_no_placeholder_notice(self, parsed_pages):
        """No page should contain a .placeholder-notice element."""
        failures = [
            _rel(path) for path, _, soup in parsed_pages
            if soup.select_one(".placeholder-notice")
        ]
        assert not failures, f"Pages with .placeholder-notice: {failures[:15]}"

    def test_notice_pending_class_is_styled(self, parsed_pages):
        """Pages using .notice.notice-pending must have that class styled in css/style.css.

        Regression guard for the H1 defect: markup was renamed from
        .placeholder-notice to "notice notice-pending" but the CSS rule was
        never renamed to match, so the banner rendered unstyled.
        """
        used = any(
            soup.select_one(".notice.notice-pending")
            for _, _, soup in parsed_pages
        )
        assert used, "expected at least one page to use .notice.notice-pending"
        css_text = STYLE_CSS.read_text()
        assert re.search(r"\.notice\.notice-pending\s*{", css_text), (
            "css/style.css has no rule for .notice.notice-pending"
        )

    def test_no_stub_or_placeholder_strings(self, parsed_pages):
        """No page should contain literal 'Lorem ipsum', 'TBD', or 'TODO' text."""
        failures = []
        for path, text, _ in parsed_pages:
            hits = [s for s in ("Lorem ipsum", "TBD", "TODO") if s in text]
            if hits:
                failures.append(f"{_rel(path)}: {hits}")
        assert not failures, f"Pages with stub/placeholder strings: {failures[:15]}"


class TestNoDuplicatedOwnedContent:
    """Regression guard for H2: about/policies each own one block of content
    that syllabus.html must link out to, not duplicate; the Summary of
    Assignments and Weights table was later moved the other way (it's now
    owned in full by syllabus.html, and project-overviews.html must not
    duplicate it).
    """

    def test_syllabus_does_not_duplicate_about_description(self, site_root):
        about_text = (site_root / "core" / "about.html").read_text()
        syllabus_text = (site_root / "core" / "syllabus.html").read_text()
        marker = "hands-on study of the AI frontier"
        assert marker in about_text
        assert marker not in syllabus_text

    def test_syllabus_does_not_duplicate_secrets_hygiene(self, site_root):
        policies_text = (site_root / "core" / "policies.html").read_text()
        syllabus_text = (site_root / "core" / "syllabus.html").read_text()
        marker = "The first leaked key is a learning moment"
        assert marker in policies_text
        assert marker not in syllabus_text

    def test_project_overviews_does_not_duplicate_assignment_weights(self, site_root):
        project_overviews_text = (site_root / "core" / "project-overviews.html").read_text()
        syllabus_text = (site_root / "core" / "syllabus.html").read_text()
        marker = "Mini-Project 3 — Harness + Hooks (graded)"
        assert marker in syllabus_text
        assert marker not in project_overviews_text


class TestCSSCoverage:
    def test_every_html_class_is_defined_in_css(self, parsed_pages):
        """Every class="..." token used in markup must appear as a class
        selector somewhere in css/style.css.

        Regression guard for H1: markup was renamed to "notice notice-pending"
        but the CSS selector was never renamed to match, so it silently
        rendered unstyled. This is a superset check (any ".token" appearing
        anywhere in the CSS text counts as "defined"), which is deliberately
        permissive but still catches a used-but-never-defined class.
        """
        css_text = STYLE_CSS.read_text()
        defined = set(re.findall(r"\.([a-zA-Z][\w-]*)", css_text))

        used = {}
        for path, _, soup in parsed_pages:
            for tag in soup.find_all(class_=True):
                for cls in tag.get("class", []):
                    used.setdefault(cls, _rel(path))

        undefined = {cls: used[cls] for cls in used if cls not in defined}
        assert not undefined, f"Classes used in HTML but not styled in css/style.css: {undefined}"


class TestCSSDeadCode:
    def test_no_has_featured_image_block(self):
        """The unused hero-image duotone variant (.has-featured-image /
        .featured-media) must stay removed from css/style.css; the active
        .no-featured-image rules must remain untouched."""
        css_text = STYLE_CSS.read_text()
        assert "has-featured-image" not in css_text
        assert "featured-media" not in css_text
        assert "no-featured-image" in css_text


class TestAccessibility:
    def test_all_pages_have_skip_link_to_main(self, parsed_pages):
        """Every page must have a skip link as the first element in <body>
        pointing to an element with id="main"."""
        failures = []
        for path, _, soup in parsed_pages:
            body = soup.body
            first_tag = body.find(True) if body else None
            if not (
                first_tag
                and first_tag.name == "a"
                and "skip-link" in (first_tag.get("class") or [])
                and first_tag.get("href") == "#main"
            ):
                failures.append(_rel(path))
        assert not failures, f"Pages missing a leading .skip-link[href='#main']: {failures[:15]}"

    def test_all_pages_have_main_with_id(self, parsed_pages):
        """Every page's <main class="content-wrapper"> must carry id="main"
        so the skip link has a target."""
        failures = []
        for path, _, soup in parsed_pages:
            main = soup.select_one("main.content-wrapper")
            if not main or main.get("id") != "main":
                failures.append(_rel(path))
        assert not failures, f"Pages missing <main id='main'>: {failures[:15]}"

    def test_active_nav_link_has_aria_current(self, nav_pages, parsed_pages):
        """Every nav link with class="active" must also have aria-current="page".

        The current page's indicator lives in nav.main-nav for pages that
        nav item covers (Home/Syllabus/Schedule/Project Overviews), or in
        nav.footer-nav for pages reached only via the footer (About,
        Policies), so both navs are checked.
        """
        by_path = {p: (t, s) for p, t, s in parsed_pages}
        failures = []
        for path in nav_pages:
            _, soup = by_path[path]
            active_links = soup.select("nav.main-nav a.active, nav.footer-nav a.active")
            if not active_links:
                failures.append(f"{_rel(path)}: no active nav link found")
                continue
            for link in active_links:
                if link.get("aria-current") != "page":
                    failures.append(f"{_rel(path)}: active nav link missing aria-current='page'")
        assert not failures, f"aria-current issues: {failures[:15]}"

    def test_all_pages_have_meta_description(self, parsed_pages):
        """Every page must declare a non-empty <meta name="description">."""
        failures = []
        for path, _, soup in parsed_pages:
            meta = soup.find("meta", attrs={"name": "description"})
            if not meta or not (meta.get("content") or "").strip():
                failures.append(_rel(path))
        assert not failures, f"Pages missing meta description: {failures[:15]}"


class TestContentNotEmpty:
    def test_page_content_has_minimum_text(self, parsed_pages):
        """Every page's .page-content div must have at least 20 characters of stripped text."""
        failures = []
        for path, _, soup in parsed_pages:
            content_div = soup.select_one(".page-content")
            if not content_div:
                failures.append(f"{_rel(path)}: missing .page-content")
                continue
            text = content_div.get_text(strip=True)
            if len(text) < 20:
                failures.append(f"{_rel(path)}: only {len(text)} chars")
        assert not failures, f"Pages with near-empty .page-content: {failures[:15]}"
