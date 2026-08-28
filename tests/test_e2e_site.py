"""End-to-end tests: site completeness, page counts, and reachability."""
import pytest
from urllib.parse import unquote
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent

EXPECTED_TOTAL_PAGES = 22
EXPECTED_CORE_FILES = {
    "about.html", "assignments.html", "policies.html", "schedule.html", "syllabus.html",
}
EXPECTED_WEEK_FILES = {f"week-{n:02d}.html" for n in range(1, 16)}


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


class TestRequiredFiles:
    @pytest.mark.parametrize("filename", ["index.html", "404.html", "css/style.css"])
    def test_required_root_files_exist(self, site_root, filename):
        assert (site_root / filename).exists(), f"Missing required file: {filename}"

    @pytest.mark.parametrize("dirname", ["core", "weeks", "tests", "css"])
    def test_required_directories_exist(self, site_root, dirname):
        assert (site_root / dirname).is_dir(), f"Missing required directory: {dirname}"


class TestPageCount:
    def test_exact_total_page_count(self, all_html_files):
        """Site must have exactly 22 HTML pages (index, 404, 5 core, 15 weeks)."""
        count = len(all_html_files)
        files = [str(f.relative_to(SITE_ROOT)) for f in all_html_files]
        assert count == EXPECTED_TOTAL_PAGES, (
            f"Expected {EXPECTED_TOTAL_PAGES} HTML files, found {count}. Files: {files}"
        )


class TestCoreDirectoryContents:
    def test_core_has_exactly_expected_files(self, site_root):
        """core/ must contain exactly the 5 expected page files."""
        actual = {f.name for f in (site_root / "core").glob("*.html")}
        missing = EXPECTED_CORE_FILES - actual
        extra = actual - EXPECTED_CORE_FILES
        assert not missing and not extra, (
            f"core/ mismatch. Missing: {sorted(missing)}. Extra: {sorted(extra)}"
        )


class TestWeeksDirectoryContents:
    def test_weeks_has_exactly_15_zero_padded_files(self, site_root):
        """weeks/ must contain exactly week-01.html through week-15.html, no gaps or extras."""
        actual = {f.name for f in (site_root / "weeks").glob("*.html")}
        missing = EXPECTED_WEEK_FILES - actual
        extra = actual - EXPECTED_WEEK_FILES
        assert not missing and not extra, (
            f"weeks/ mismatch. Missing: {sorted(missing)}. Extra: {sorted(extra)}"
        )


class TestReachability:
    def test_all_pages_except_404_reachable_from_index(self, site_root, all_html_files):
        """BFS from index.html over local <a href> links must reach every page except 404.html."""
        index = site_root / "index.html"
        visited = set()
        queue = [index.resolve()]

        while queue:
            current = queue.pop()
            if current in visited or not current.exists():
                continue
            visited.add(current)
            text = current.read_text(encoding="utf-8", errors="replace")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if not href or href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                    continue
                href = href.split("#")[0]
                if not href:
                    continue
                target = (current.parent / unquote(href)).resolve()
                if target.exists() and target not in visited:
                    queue.append(target)

        expected_reachable = {f.resolve() for f in all_html_files if f.name != "404.html"}
        unreached = expected_reachable - visited
        unreached_rel = sorted(_rel(f) for f in unreached)
        assert not unreached_rel, (
            f"Pages not reachable from index.html via links: {unreached_rel}"
        )
