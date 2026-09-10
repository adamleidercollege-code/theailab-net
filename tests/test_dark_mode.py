"""Dark mode: data-theme toggle, its CSS tokens, and its persisted state."""
import re
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent
STYLE_CSS = SITE_ROOT / "css" / "style.css"
THEME_JS = SITE_ROOT / "js" / "theme-toggle.js"


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


class TestToggleControlPresent:
    def test_every_page_has_a_theme_toggle_button_in_the_header(self, parsed_pages):
        """Every page must expose #theme-toggle inside header.site-header so it's
        visible on every page, not just some."""
        failures = []
        for path, _, soup in parsed_pages:
            header = soup.select_one("header.site-header")
            toggle = header.select_one("#theme-toggle") if header else None
            if not toggle:
                failures.append(_rel(path))
        assert not failures, f"Pages missing #theme-toggle in the header: {failures[:15]}"

    def test_toggle_is_a_real_button_with_accessible_state(self, parsed_pages):
        """The toggle must be a <button> (keyboard/AT operable) that exposes its
        on/off state via aria-pressed, plus a label describing its action."""
        failures = []
        for path, _, soup in parsed_pages:
            toggle = soup.select_one("#theme-toggle")
            if not toggle:
                continue
            if toggle.name != "button":
                failures.append(f"{_rel(path)}: not a <button>")
                continue
            if toggle.get("aria-pressed") not in ("true", "false"):
                failures.append(f"{_rel(path)}: missing/invalid aria-pressed")
            if not (toggle.get("aria-label") or "").strip():
                failures.append(f"{_rel(path)}: missing aria-label")
        assert not failures, f"Toggle accessibility issues: {failures[:15]}"

    def test_toggle_ids_are_unique_per_page(self, parsed_pages):
        """Exactly one #theme-toggle per page (ids must be unique in a document)."""
        failures = [
            f"{_rel(path)}: {len(soup.select('#theme-toggle'))}"
            for path, _, soup in parsed_pages
            if len(soup.select("#theme-toggle")) != 1
        ]
        assert not failures, f"Pages without exactly one #theme-toggle: {failures[:15]}"


class TestThemeInitScript:
    def test_every_page_has_early_inline_theme_init_script(self, parsed_pages):
        """A blocking inline <script> in <head> must read localStorage and set
        data-theme before first paint, so returning dark-mode users don't see a
        flash of the light theme."""
        failures = []
        for path, _, soup in parsed_pages:
            head = soup.head
            scripts = head.find_all("script", src=False) if head else []
            hit = any(
                "localStorage" in (s.string or "") and "data-theme" in (s.string or "")
                for s in scripts
            )
            if not hit:
                failures.append(_rel(path))
        assert not failures, f"Pages missing an early inline theme-init script: {failures[:15]}"

    def test_every_page_loads_the_shared_theme_toggle_script(self, parsed_pages):
        """Every page must load js/theme-toggle.js and it must resolve to a real file."""
        failures = []
        for path, _, soup in parsed_pages:
            scripts = [
                s.get("src") for s in soup.find_all("script", src=True)
                if "theme-toggle.js" in s.get("src", "")
            ]
            if not scripts:
                failures.append(f"{_rel(path)}: no theme-toggle.js script tag")
                continue
            target = (path.parent / scripts[0]).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: src '{scripts[0]}' does not resolve")
        assert not failures, f"theme-toggle.js script issues: {failures[:15]}"


class TestThemeToggleScriptBehavior:
    def test_theme_toggle_js_exists(self):
        assert THEME_JS.exists(), "js/theme-toggle.js is missing"

    def test_theme_toggle_js_persists_choice_to_local_storage(self):
        js = THEME_JS.read_text(encoding="utf-8")
        assert "localStorage.setItem" in js
        assert "data-theme" in js

    def test_theme_toggle_js_binds_to_the_toggle_button(self):
        js = THEME_JS.read_text(encoding="utf-8")
        assert "theme-toggle" in js
        assert "addEventListener" in js


class TestDarkModeCSSTokens:
    def test_dark_theme_selector_exists(self):
        css_text = STYLE_CSS.read_text()
        assert re.search(r':root\[data-theme=["\']dark["\']\]\s*{', css_text), (
            "css/style.css has no :root[data-theme=\"dark\"] rule"
        )

    # Non-color tokens (fonts, widths, offsets) are shared across themes by
    # design and must NOT be overridden here.
    NON_COLOR_TOKENS = {"fh", "fb", "mw", "mww", "col-left"}

    def test_dark_theme_redefines_the_core_color_tokens(self):
        """The dark block must override every color token the light :root
        defines, not just a couple, so nothing silently stays light-mode-colored."""
        css_text = STYLE_CSS.read_text()
        root_match = re.search(r":root\s*{([^}]*)}", css_text)
        dark_match = re.search(r':root\[data-theme=["\']dark["\']\]\s*{([^}]*)}', css_text)
        assert root_match and dark_match
        light_tokens = set(re.findall(r"--([\w-]+)\s*:", root_match.group(1)))
        dark_tokens = set(re.findall(r"--([\w-]+)\s*:", dark_match.group(1)))
        missing = (light_tokens - self.NON_COLOR_TOKENS) - dark_tokens
        assert not missing, f"Color tokens not overridden in dark mode: {sorted(missing)}"

    def test_toggle_classes_are_styled(self):
        css_text = STYLE_CSS.read_text()
        for cls in (".theme-toggle", ".theme-toggle-track", ".theme-toggle-thumb"):
            assert re.search(re.escape(cls) + r"[\s,{.:\[]", css_text), (
                f"{cls} is used in markup but has no rule in css/style.css"
            )
