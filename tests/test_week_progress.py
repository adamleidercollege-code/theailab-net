"""Tests for the sitewide segmented week-progress bar reflecting
weeks/manifest.json state."""
import json


def test_week_progress_segment_counts_match_manifest(site_root, parsed_pages):
    """Every page's .week-progress segments must match the actual live/pending
    counts and per-week states in weeks/manifest.json, not a value hand-typed
    independently of it."""
    manifest = json.loads((site_root / "weeks" / "manifest.json").read_text())
    total = len(manifest)
    expected_states = [manifest[key]["state"] for key in sorted(manifest)]
    live = sum(1 for state in expected_states if state == "live")
    pending = total - live

    failures = []
    for path, _, soup in parsed_pages:
        track = soup.select_one(".week-progress .week-progress-track")
        if track is None:
            failures.append(f"{path.relative_to(site_root)}: missing .week-progress-track")
            continue

        segments = track.select(".week-progress-segment")
        if len(segments) != total:
            failures.append(
                f"{path.relative_to(site_root)}: expected {total} segments, found {len(segments)}"
            )
            continue

        actual_states = [
            "live" if "is-live" in seg.get("class", []) else "pending"
            for seg in segments
        ]
        if actual_states != expected_states:
            failures.append(
                f"{path.relative_to(site_root)}: segment states {actual_states} "
                f"!= manifest states {expected_states}"
            )

        label = soup.select_one(".week-progress .week-progress-label")
        if label is None:
            failures.append(f"{path.relative_to(site_root)}: missing .week-progress-label")
            continue
        label_text = label.get_text(" ", strip=True)
        if f"Week {live} of {total}" not in label_text:
            failures.append(f"{path.relative_to(site_root)}: label missing 'Week {live} of {total}': {label_text!r}")
        if f"{live} live" not in label_text:
            failures.append(f"{path.relative_to(site_root)}: label missing '{live} live': {label_text!r}")
        if f"{pending} pending" not in label_text:
            failures.append(f"{path.relative_to(site_root)}: label missing '{pending} pending': {label_text!r}")

    assert not failures, "\n".join(failures)


def test_week_progress_appears_on_all_pages(all_html_files, parsed_pages):
    """The segmented progress bar must appear on every page in the site
    (including 404.html), not just the homepage."""
    missing = [
        str(path.name) for path, _, soup in parsed_pages
        if soup.select_one(".week-progress") is None
    ]
    assert not missing, f"Pages missing .week-progress: {missing}"
    assert len(parsed_pages) == len(all_html_files)


def test_week_progress_positioned_between_header_and_main(parsed_pages):
    """The progress bar must sit directly below the site header and above
    the main page content, not nested inside either."""
    failures = []
    for path, _, soup in parsed_pages:
        bar = soup.select_one(".week-progress")
        header = soup.select_one("header.site-header")
        main = soup.select_one("main.content-wrapper")
        if bar is None or header is None or main is None:
            failures.append(str(path.name))
            continue
        if bar.find_parent("header") is not None:
            failures.append(f"{path.name}: nested inside header")
        if bar.find_parent("main") is not None:
            failures.append(f"{path.name}: nested inside main")
        # bar must appear after header and before main in document order
        siblings_after_header = list(header.find_next_siblings())
        if bar not in siblings_after_header:
            failures.append(f"{path.name}: not a sibling following header")
        elif main in siblings_after_header and siblings_after_header.index(bar) > siblings_after_header.index(main):
            failures.append(f"{path.name}: appears after main, not before it")
    assert not failures, f"Placement issues: {failures}"


def test_homepage_no_longer_has_old_single_bar_markup(site_root):
    """Regression guard: the previous homepage-only continuous progress bar
    (.progress-tracker/.progress-bar) must not reappear."""
    index_text = (site_root / "index.html").read_text()
    assert "progress-tracker" not in index_text
    assert "progress-bar-fill" not in index_text
