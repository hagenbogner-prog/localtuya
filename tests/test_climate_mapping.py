"""Tests for custom LocalTuya climate mappings."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "localtuya"
    / "climate_mapping.py"
)


def load_builder():
    """Load the pure mapping helper without importing Home Assistant."""
    if not MODULE_PATH.exists():
        raise AssertionError(f"Missing mapping helper: {MODULE_PATH}")
    spec = spec_from_file_location("localtuya_climate_mapping", MODULE_PATH)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.build_custom_mapping


class BuildCustomMappingTests(unittest.TestCase):
    """Verify custom raw Tuya values are normalized safely."""

    def test_ignores_missing_and_blank_values(self):
        build_custom_mapping = load_builder()
        config = {"cool": "cool", "heat": "", "dry": "   "}
        fields = {"COOL": "cool", "HEAT": "heat", "DRY": "dry", "FAN": "fan"}

        self.assertEqual({"COOL": "cool"}, build_custom_mapping(config, fields))

    def test_strips_surrounding_whitespace(self):
        build_custom_mapping = load_builder()
        config = {"medium": "  mid  "}
        fields = {"MEDIUM": "medium"}

        self.assertEqual({"MEDIUM": "mid"}, build_custom_mapping(config, fields))

    def test_preserves_supported_hvac_raw_values(self):
        build_custom_mapping = load_builder()
        config = {
            "auto": "auto",
            "cool": "cool",
            "dry": "dry",
            "fan_only": "fan",
        }
        fields = {
            "AUTO": "auto",
            "COOL": "cool",
            "DRY": "dry",
            "FAN_ONLY": "fan_only",
        }

        self.assertEqual(
            {"AUTO": "auto", "COOL": "cool", "DRY": "dry", "FAN_ONLY": "fan"},
            build_custom_mapping(config, fields),
        )

    def test_preserves_supported_fan_raw_values(self):
        build_custom_mapping = load_builder()
        config = {"low": "low", "medium": "mid", "high": "high"}
        fields = {"LOW": "low", "MEDIUM": "medium", "HIGH": "high"}

        self.assertEqual(
            {"LOW": "low", "MEDIUM": "mid", "HIGH": "high"},
            build_custom_mapping(config, fields),
        )

    def test_ignores_non_string_values(self):
        build_custom_mapping = load_builder()
        config = {"cool": 1, "dry": None, "fan": False}
        fields = {"COOL": "cool", "DRY": "dry", "FAN": "fan"}

        self.assertEqual({}, build_custom_mapping(config, fields))


if __name__ == "__main__":
    unittest.main()
