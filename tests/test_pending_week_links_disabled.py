"""Tests that pending weeks (per weeks/manifest.json) are not click-through-able
from core/schedule.html, while live weeks remain fully functional links."""
import json
import re

import pytest
from bs4 import BeautifulSoup


@pytest.fixture(scope="module")
def manifest(site_root):
    return json.loads((site_root / "weeks" / "manifest.json").read_text())


@pytest.fixture(scope="module")
def schedule_soup(site_root):
    text = (site_root / "core" / "schedule.html").read_text(encoding="utf-8")
    return BeautifulSoup(text, "lxml")


def _link_for_week(soup, week):
    matches = [
        a for a in soup.select(".item-list a")
        if a.get("href", "").endswith(f"week-{week}.html")
    ]
    assert len(matches) == 1, f"expected exactly one schedule link for week-{week}.html, found {len(matches)}"
    return matches[0]


class TestPendingWeekLinksDisabled:
    def test_pending_week_links_are_marked_disabled(self, manifest, schedule_soup):
        """Every pending week's link on the schedule page must be visually and
        programmatically disabled: aria-disabled, unfocusable, and styled with
        the is-disabled class (not a bare, clickable anchor)."""
        failures = []
        for week, entry in manifest.items():
            if entry["state"] != "pending":
                continue
            link = _link_for_week(schedule_soup, week)
            if "is-disabled" not in (link.get("class") or []):
                failures.append(f"week-{week}: missing is-disabled class")
            if link.get("aria-disabled") != "true":
                failures.append(f"week-{week}: missing aria-disabled='true'")
            if link.get("tabindex") != "-1":
                failures.append(f"week-{week}: missing tabindex='-1'")
        assert not failures, f"Pending week links not properly disabled: {failures}"

    def test_live_week_links_remain_functional(self, manifest, schedule_soup):
        """Live weeks must NOT carry any of the disabled-link markers, so they
        stay clickable and focusable."""
        failures = []
        for week, entry in manifest.items():
            if entry["state"] != "live":
                continue
            link = _link_for_week(schedule_soup, week)
            if "is-disabled" in (link.get("class") or []):
                failures.append(f"week-{week}: unexpectedly has is-disabled class")
            if link.get("aria-disabled") is not None:
                failures.append(f"week-{week}: unexpectedly has aria-disabled")
            if link.get("tabindex") is not None:
                failures.append(f"week-{week}: unexpectedly has tabindex")
        assert not failures, f"Live week links incorrectly disabled: {failures}"

    def test_is_disabled_class_uses_muted_border_variables_and_blocks_clicks(self, site_root):
        """The .is-disabled rule must use the site's existing muted-text
        variable (not a new color) and must set pointer-events: none so the
        link cannot be clicked through, even though the <a href> remains in
        the DOM for direct navigation/testing purposes."""
        css_text = (site_root / "css" / "style.css").read_text()
        match = re.search(r"\.item-list\s+a\.is-disabled\s*\{([^}]*)\}", css_text)
        assert match, "expected a .item-list a.is-disabled rule in css/style.css"
        rule_body = match.group(1)
        assert "pointer-events" in rule_body and "none" in rule_body, (
            "is-disabled rule must set pointer-events: none"
        )
        assert "var(--text-lt)" in rule_body or "var(--border)" in rule_body, (
            "is-disabled rule must reuse an existing muted/border variable, not a new color"
        )
        # No brand-new color variable introduced for this feature.
        assert "--disabled" not in css_text and "--muted" not in css_text
