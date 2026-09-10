"""Tests for weeks/manifest.json structure."""
import json


class TestManifestSchema:
    def test_no_entry_has_by_or_published_at(self, site_root):
        """No manifest entry should carry the dead `by`/`published_at` keys.

        These fields were never read by any code in the repo and were never
        populated for live entries either (always null) — dropped entirely
        (M3, option b) until real publish automation exists to populate them.
        """
        manifest = json.loads((site_root / "weeks" / "manifest.json").read_text())
        offenders = {
            week: sorted(set(entry) & {"by", "published_at"})
            for week, entry in manifest.items()
            if set(entry) & {"by", "published_at"}
        }
        assert not offenders, f"Entries still carry dead by/published_at keys: {offenders}"

    def test_all_entries_have_state_and_source_sha_or_are_pending(self, site_root):
        """Every entry must have a `state`; live entries must also have `source_sha`."""
        manifest = json.loads((site_root / "weeks" / "manifest.json").read_text())
        failures = []
        for week, entry in manifest.items():
            if "state" not in entry:
                failures.append(f"{week}: missing state")
                continue
            if entry["state"] == "live" and "source_sha" not in entry:
                failures.append(f"{week}: live but missing source_sha")
        assert not failures, f"Manifest entry issues: {failures}"
