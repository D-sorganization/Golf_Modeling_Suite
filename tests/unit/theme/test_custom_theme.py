"""Targeted unit tests for custom theme save/load/delete + validation.

Closes #5487. PR #5406 (#5395) added ``save_custom_theme``,
``delete_custom_theme``, ``_load_custom_themes``, ``_persist_custom_themes``
and ``_validate_custom_theme_colors`` to
``src/shared/python/theme/theme_manager.py`` without targeted tests. These
exercises pin the behaviour we care about:

* Round trip: save -> reload (new instance) -> delete.
* Validation: malformed hex strings raise ``ValueError``.
* Persistence file format: schema is a flat ``{name: {color_key: "#rrggbb"}}``
  JSON object so future format changes are intentional.
* Name conflict with a built-in theme raises ``ValueError`` (the documented
  behaviour of the public API).

The tests use the ``isolated_qsettings`` fixture from this directory's
``conftest.py`` to ensure neither the developer's real Qt config nor a
sibling test can be observed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.shared.python.theme.colors import BUILTIN_THEMES, THEME_COLOR_KEYS
from src.shared.python.theme.theme_manager import ThemeManager


# ---------------------------------------------------------------------------
# Helpers (DRY)
# ---------------------------------------------------------------------------


def make_theme_dict(name: str = "MyTheme") -> dict[str, str]:
    """Return a fully populated, valid custom-theme colour dict.

    Centralised so individual tests do not duplicate the THEME_COLOR_KEYS
    enumeration. ``name`` is unused for the colour payload itself — the
    ``name`` argument exists so call sites read declaratively at the
    test site.
    """
    del name  # name is documentary; ThemeManager stores the name separately.
    palette = [
        "#101820",  # bg
        "#1f2933",  # group_bg
        "#3e4c59",  # border
        "#e4e7eb",  # text
        "#cbd2d9",  # text_secondary
        "#9aa5b1",  # label
        "#52606d",  # focus
        "#0b0e13",  # input_bg
        "#f0b429",  # accent
        "#2d3742",  # title_bg
        "#f0b429",  # title_border
        "#1f2933",  # table_header
        "#323f4b",  # table_alt
        "#f7c948",  # button_hover
    ]
    assert len(palette) == len(THEME_COLOR_KEYS), (
        "make_theme_dict palette must match THEME_COLOR_KEYS length"
    )
    return dict(zip(THEME_COLOR_KEYS, palette, strict=True))


def _fresh_manager() -> ThemeManager:
    """Return a freshly built ``ThemeManager``, bypassing the singleton.

    Each call gives a separate instance so we can simulate a relaunch.
    """
    ThemeManager.reset_instance()
    return ThemeManager()


# ---------------------------------------------------------------------------
# Save -> reload -> delete round trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_save_then_reload_in_new_instance(self, isolated_qsettings: Path) -> None:
        del isolated_qsettings  # used for its side-effect of isolation
        manager = _fresh_manager()
        manager.save_custom_theme("MyTheme", make_theme_dict("MyTheme"))

        assert "MyTheme" in manager.get_custom_theme_names()

        # A new ``ThemeManager`` should pick the theme up from disk.
        reloaded = _fresh_manager()
        assert "MyTheme" in reloaded.get_custom_theme_names()
        assert reloaded.get_theme_colors("MyTheme") == make_theme_dict("MyTheme")

    def test_delete_removes_theme_from_reloaded_instance(
        self, isolated_qsettings: Path
    ) -> None:
        del isolated_qsettings
        manager = _fresh_manager()
        manager.save_custom_theme("DeletableTheme", make_theme_dict("DeletableTheme"))

        deleted = manager.delete_custom_theme("DeletableTheme")
        assert deleted is True
        assert "DeletableTheme" not in manager.get_custom_theme_names()

        reloaded = _fresh_manager()
        assert "DeletableTheme" not in reloaded.get_custom_theme_names()

    def test_delete_returns_false_for_missing_theme(
        self, isolated_qsettings: Path
    ) -> None:
        del isolated_qsettings
        manager = _fresh_manager()
        assert manager.delete_custom_theme("never-existed") is False


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    @pytest.mark.parametrize(
        "bad_hex",
        [
            "#XX",  # non-hex digits
            "not-a-color",  # nothing hex about it
            "#12",  # too short (1-2 digits)
            "12345",  # missing leading ``#`` AND wrong length
            "",  # empty
        ],
    )
    def test_rejects_malformed_hex(
        self, isolated_qsettings: Path, bad_hex: str
    ) -> None:
        del isolated_qsettings
        manager = _fresh_manager()
        colors = make_theme_dict("Bad")
        colors["bg"] = bad_hex

        with pytest.raises(ValueError):
            manager.save_custom_theme("BadHex", colors)

        # Failed save must NOT leak the partially-validated theme.
        assert "BadHex" not in manager.get_custom_theme_names()

    def test_rejects_missing_required_keys(self, isolated_qsettings: Path) -> None:
        del isolated_qsettings
        manager = _fresh_manager()
        colors = make_theme_dict("Partial")
        del colors["bg"]
        del colors["text"]

        with pytest.raises(ValueError, match="Missing colour values"):
            manager.save_custom_theme("Partial", colors)

    def test_rejects_empty_name(self, isolated_qsettings: Path) -> None:
        del isolated_qsettings
        manager = _fresh_manager()
        with pytest.raises(ValueError, match="cannot be empty"):
            manager.save_custom_theme("   ", make_theme_dict("blank"))

    def test_accepts_short_hex_and_normalises(self, isolated_qsettings: Path) -> None:
        """3-digit hex like ``#f00`` is valid and should be normalised."""
        del isolated_qsettings
        manager = _fresh_manager()
        colors = make_theme_dict("Short")
        colors["accent"] = "#f00"  # 3-digit shorthand
        manager.save_custom_theme("ShortHex", colors)

        stored = manager.get_theme_colors("ShortHex")
        assert stored is not None
        assert stored["accent"] == "#ff0000"


# ---------------------------------------------------------------------------
# Conflict handling
# ---------------------------------------------------------------------------


class TestNameConflict:
    """Saving a theme whose name matches a built-in must be rejected.

    The public API raises ``ValueError`` so the caller can show a UI
    error rather than silently overwriting a built-in. The built-in
    theme must remain unchanged on disk and in memory.
    """

    def test_rejects_builtin_name(self, isolated_qsettings: Path) -> None:
        del isolated_qsettings
        manager = _fresh_manager()
        original_light = dict(BUILTIN_THEMES["Light"])

        with pytest.raises(ValueError, match="conflicts with a built-in"):
            manager.save_custom_theme("Light", make_theme_dict("Light"))

        # Built-in must be untouched.
        assert BUILTIN_THEMES["Light"] == original_light
        assert "Light" not in manager.get_custom_theme_names()

    def test_two_saves_same_name_overwrite_custom(
        self, isolated_qsettings: Path
    ) -> None:
        """Saving a custom theme name twice overwrites in-place.

        Built-in conflict is rejected (above) but custom <-> custom
        collision is a legitimate "edit my theme" workflow.
        """
        del isolated_qsettings
        manager = _fresh_manager()
        first = make_theme_dict("V1")
        manager.save_custom_theme("Editable", first)

        second = make_theme_dict("V2")
        second["accent"] = "#abcdef"
        manager.save_custom_theme("Editable", second)

        stored = manager.get_theme_colors("Editable")
        assert stored is not None
        assert stored["accent"] == "#abcdef"
        # Only one custom entry — overwrite, not duplicate.
        assert manager.get_custom_theme_names().count("Editable") == 1


# ---------------------------------------------------------------------------
# Persistence file format (snapshot pin)
# ---------------------------------------------------------------------------


class TestPersistenceSchema:
    """Pin the on-disk JSON schema so future format changes are intentional."""

    def test_persistence_file_is_flat_name_to_colors_mapping(
        self, isolated_qsettings: Path
    ) -> None:
        del isolated_qsettings
        manager = _fresh_manager()
        manager.save_custom_theme("SnapshotTheme", make_theme_dict("Snap"))

        # We deliberately use the protected helper here once -- the test
        # is intentionally about the on-disk schema, which is part of
        # the contract this issue asks us to pin. Public API does not
        # expose the path.
        persistence_path = manager._get_custom_theme_path()  # noqa: SLF001
        assert persistence_path.exists()

        with open(persistence_path, encoding="utf-8") as f:
            raw = json.load(f)

        # Top level: dict of theme-name -> colour map.
        assert isinstance(raw, dict)
        assert "SnapshotTheme" in raw

        entry = raw["SnapshotTheme"]
        assert isinstance(entry, dict)

        # Every required colour key is present and the value is a
        # normalised ``#rrggbb`` string.
        for key in THEME_COLOR_KEYS:
            assert key in entry, f"missing key {key!r}"
            value = entry[key]
            assert isinstance(value, str)
            assert value.startswith("#") and len(value) == 7, (
                f"value for {key!r} is not normalised #rrggbb: {value!r}"
            )

        # No extra unknown keys leak in (THEME_COLOR_KEYS is the schema).
        assert set(entry) == set(THEME_COLOR_KEYS)

    def test_corrupt_json_is_tolerated(self, isolated_qsettings: Path) -> None:
        """A corrupt user_themes.json must not crash ThemeManager startup."""
        del isolated_qsettings
        manager = _fresh_manager()
        path = manager._get_custom_theme_path()  # noqa: SLF001
        path.write_text("{not valid json", encoding="utf-8")

        # Fresh manager should load an empty custom-theme set, not crash.
        recovered = _fresh_manager()
        assert recovered.get_custom_theme_names() == []
