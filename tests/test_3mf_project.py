import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "dist" / "wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf"


class BambuProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROJECT.is_file():
            raise AssertionError(f"sliced Bambu project is missing: {PROJECT}")

        cls.archive = zipfile.ZipFile(PROJECT)
        cls.addClassCleanup(cls.archive.close)
        cls.names = set(cls.archive.namelist())
        cls.settings = json.loads(
            cls.archive.read("Metadata/project_settings.config")
        )

    def test_contains_models_toolpaths_and_preview(self):
        required = {
            "3D/3dmodel.model",
            "Metadata/model_settings.config",
            "Metadata/project_settings.config",
            "Metadata/slice_info.config",
            "Metadata/plate_1.json",
            "Metadata/plate_1.gcode",
            "Metadata/plate_1.gcode.md5",
            "Metadata/plate_1.png",
            "Metadata/plate_1_small.png",
        }
        self.assertTrue(required <= self.names, required - self.names)
        self.assertGreater(
            self.archive.getinfo("Metadata/plate_1.gcode").file_size,
            1_000_000,
        )

    def test_embedded_gcode_checksum_matches(self):
        gcode = self.archive.read("Metadata/plate_1.gcode")
        expected = (
            self.archive.read("Metadata/plate_1.gcode.md5")
            .decode()
            .strip()
            .lower()
        )
        self.assertEqual(hashlib.md5(gcode).hexdigest(), expected)

    def test_uses_agreed_p1s_pla_strength_settings(self):
        expected = {
            "printer_model": "Bambu Lab P1S",
            "printer_variant": "0.4",
            "curr_bed_type": "Textured PEI Plate",
            "layer_height": "0.2",
            "wall_loops": "5",
            "top_shell_layers": "6",
            "bottom_shell_layers": "6",
            "sparse_infill_density": "40%",
            "sparse_infill_pattern": "gyroid",
            "enable_support": "0",
            "brim_type": "outer_only",
            "brim_width": "5",
            "brim_object_gap": "0.1",
            "print_sequence": "by layer",
        }
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertEqual(self.settings[key], value)

        self.assertEqual(self.settings["filament_type"], ["PLA"])
        self.assertEqual(self.settings["filament_vendor"], ["Bambu Lab"])
        self.assertEqual(self.settings["filament_density"], ["1.26"])
        self.assertEqual(self.settings["outer_wall_speed"], ["120"])
        self.assertEqual(self.settings["inner_wall_speed"], ["200"])
        self.assertEqual(self.settings["sparse_infill_speed"], ["200"])

    def test_plate_contains_two_complete_brackets(self):
        root = ET.fromstring(self.archive.read("Metadata/model_settings.config"))
        names = []
        for object_element in root.findall("object"):
            name = object_element.find("metadata[@key='name']")
            self.assertIsNotNone(name)
            names.append(name.attrib["value"])

        self.assertEqual(
            Counter(names),
            Counter({"main_print.stl": 2, "cap_print.stl": 2}),
        )
        self.assertEqual(len(root.findall("./plate/model_instance")), 4)

    def test_slice_is_support_free_and_has_plausible_estimates(self):
        root = ET.fromstring(self.archive.read("Metadata/slice_info.config"))
        plate = root.find("plate")
        self.assertIsNotNone(plate)
        metadata = {
            item.attrib["key"]: item.attrib["value"]
            for item in plate.findall("metadata")
        }
        self.assertEqual(metadata["support_used"], "false")
        self.assertEqual(metadata["outside"], "false")
        self.assertGreater(float(metadata["weight"]), 110)
        self.assertLess(float(metadata["weight"]), 120)
        self.assertGreater(float(metadata["prediction"]), 18_000)
        self.assertLess(float(metadata["prediction"]), 18_500)

        gcode = self.archive.read("Metadata/plate_1.gcode").decode(
            "utf-8", errors="replace"
        )
        self.assertIn("; total layer number: 150", gcode)
        self.assertNotIn("; FEATURE: Support", gcode)

    def test_only_known_slicer_advisory_is_present_and_documented(self):
        root = ET.fromstring(self.archive.read("Metadata/slice_info.config"))
        warnings = [warning.attrib["msg"] for warning in root.findall("./plate/warning")]
        self.assertEqual(warnings, ["bed_temperature_too_high_than_filament"])

        readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("front door", readme)
        self.assertIn("upper glass", readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
