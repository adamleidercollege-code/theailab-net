"""Unit tests for the href-resolution helper used by link-checking tests.

Covers root-relative absolute hrefs (e.g. "/index.html"), which pages nested
under a subdirectory can use instead of "../"-style relative paths that
assume a fixed directory depth.
"""
from test_integration_links import _resolve_href, SITE_ROOT


def test_relative_href_resolves_against_page_directory():
    page = SITE_ROOT / "core" / "syllabus.html"
    target = _resolve_href("../index.html", page)
    assert target == (SITE_ROOT / "index.html").resolve()


def test_relative_href_within_same_directory():
    page = SITE_ROOT / "core" / "syllabus.html"
    target = _resolve_href("schedule.html", page)
    assert target == (SITE_ROOT / "core" / "schedule.html").resolve()


def test_root_relative_absolute_href_resolves_against_site_root_not_filesystem_root():
    page = SITE_ROOT / "core" / "about.html"
    target = _resolve_href("/index.html", page)
    assert target == (SITE_ROOT / "index.html").resolve()


def test_root_relative_absolute_href_into_subdirectory():
    page = SITE_ROOT / "core" / "about.html"
    target = _resolve_href("/core/syllabus.html", page)
    assert target == (SITE_ROOT / "core" / "syllabus.html").resolve()


def test_external_and_anchor_hrefs_still_return_none():
    page = SITE_ROOT / "index.html"
    assert _resolve_href("https://example.com", page) is None
    assert _resolve_href("#section", page) is None
    assert _resolve_href("mailto:a@b.com", page) is None
    assert _resolve_href("", page) is None
