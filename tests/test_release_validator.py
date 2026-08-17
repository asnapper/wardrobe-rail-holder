import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from scripts.validate_release import ValidationError, _validate_p1s_slice


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_release.py"
MODEL_FIXTURES = ROOT / "dist" / "models"
P1S_FIXTURE = (
    ROOT / "dist" / "wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf"
)
MODEL_FILENAMES = {
    "wardrobe_rail_bracket_main.stl",
    "wardrobe_rail_bracket_cap.stl",
    "wardrobe_rail_bracket_main.3mf",
    "wardrobe_rail_bracket_cap.3mf",
    "wardrobe_rail_bracket_complete.3mf",
}
P1S_REQUIRED_MEMBERS = {
    "3D/3dmodel.model",
    "Metadata/model_settings.config",
    "Metadata/project_settings.config",
    "Metadata/slice_info.config",
    "Metadata/plate_1.json",
    "Metadata/plate_1.gcode",
    "Metadata/plate_1.gcode.md5",
}


def rewrite_zip(path, *, replacements=None, omitted=(), additions=None):
    replacements = replacements or {}
    additions = additions or {}
    omitted = set(omitted)
    temporary = path.with_name(f".{path.name}.rewrite")
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED
    ) as destination:
        for name in source.namelist():
            if name not in omitted:
                destination.writestr(name, replacements.get(name, source.read(name)))
        for name, payload in additions.items():
            destination.writestr(name, payload)
    temporary.replace(path)


def translated_model(payload, *, z_delta):
    root = ET.fromstring(payload)
    namespace = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
    for vertex in root.findall(f".//{namespace}vertex"):
        vertex.set("z", str(float(vertex.attrib["z"]) + z_delta))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def one_volume_complete_model():
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
 xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <resources><object id="1" type="model"><mesh>
  <vertices>
   <vertex x="0" y="0" z="0"/><vertex x="133.5" y="0" z="0"/>
   <vertex x="0" y="75" z="0"/><vertex x="0" y="0" z="50"/>
  </vertices>
  <triangles>
   <triangle v1="0" v2="2" v3="1"/><triangle v1="0" v2="1" v3="3"/>
   <triangle v1="1" v2="2" v3="3"/><triangle v1="2" v2="0" v3="3"/>
  </triangles>
 </mesh></object></resources><build><item objectid="1"/></build>
</model>"""


def non_manifold_main_stl():
    header = b"non-manifold test fixture".ljust(80, b"\0")
    triangle = struct.pack(
        "<12fH",
        0,
        0,
        1,
        0,
        0,
        0,
        63.5,
        75,
        0,
        0,
        0,
        50,
        0,
    )
    return header + struct.pack("<I", 1) + triangle


class SharedReleaseValidatorTests(unittest.TestCase):
    def run_validator(self, *arguments):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *map(str, arguments)],
            text=True,
            capture_output=True,
        )

    def copy_models(self, destination):
        for filename in MODEL_FILENAMES:
            shutil.copy2(MODEL_FIXTURES / filename, destination / filename)

    def copy_p1s(self, destination):
        shutil.copy2(P1S_FIXTURE, destination)

    def assert_rejected(self, result, diagnostic):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(diagnostic.lower(), result.stderr.lower())

    def test_accepts_checked_in_release_artifacts(self):
        models = self.run_validator("models", MODEL_FIXTURES)
        p1s = self.run_validator("p1s", P1S_FIXTURE)

        self.assertEqual(models.returncode, 0, models.stderr)
        self.assertEqual(p1s.returncode, 0, p1s.stderr)

    def test_models_reject_missing_artifact_before_partial_set_can_pass(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            models = Path(temporary_directory)
            self.copy_models(models)
            (models / "wardrobe_rail_bracket_cap.stl").unlink()

            self.assert_rejected(self.run_validator("models", models), "missing")

    def test_models_reject_malformed_stl_and_3mf(self):
        cases = {
            "wardrobe_rail_bracket_main.stl": b"not an STL",
            "wardrobe_rail_bracket_main.3mf": b"not a ZIP archive",
        }
        for filename, payload in cases.items():
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                models = Path(temp)
                self.copy_models(models)
                (models / filename).write_bytes(payload)

                self.assert_rejected(
                    self.run_validator("models", models),
                    "STL" if filename.endswith(".stl") else "3MF",
                )

    def test_models_reject_missing_3mf_model_payload(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            models = Path(temporary_directory)
            self.copy_models(models)
            archive = models / "wardrobe_rail_bracket_main.3mf"
            rewrite_zip(archive, omitted={"3D/3dmodel.model"})

            self.assert_rejected(self.run_validator("models", models), "3D model")

    def test_models_reject_wrong_envelope_or_orientation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            models = Path(temporary_directory)
            self.copy_models(models)
            shutil.copy2(
                models / "wardrobe_rail_bracket_cap.stl",
                models / "wardrobe_rail_bracket_main.stl",
            )
            self.assert_rejected(self.run_validator("models", models), "envelope")

        with tempfile.TemporaryDirectory() as temporary_directory:
            models = Path(temporary_directory)
            self.copy_models(models)
            archive = models / "wardrobe_rail_bracket_main.3mf"
            with zipfile.ZipFile(archive) as source:
                model = translated_model(source.read("3D/3dmodel.model"), z_delta=-1)
            rewrite_zip(archive, replacements={"3D/3dmodel.model": model})
            self.assert_rejected(self.run_validator("models", models), "build plate")

    def test_models_reject_wrong_volume_count(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            models = Path(temporary_directory)
            self.copy_models(models)
            archive = models / "wardrobe_rail_bracket_complete.3mf"
            rewrite_zip(
                archive,
                replacements={"3D/3dmodel.model": one_volume_complete_model()},
            )

            self.assert_rejected(self.run_validator("models", models), "volume")

    def test_models_reject_non_manifold_stl(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            models = Path(temporary_directory)
            self.copy_models(models)
            (models / "wardrobe_rail_bracket_main.stl").write_bytes(
                non_manifold_main_stl()
            )

            self.assert_rejected(self.run_validator("models", models), "manifold")

    def test_models_reject_gcode_and_slicer_metadata_members(self):
        cases = {
            "Metadata/plate_1.gcode": b"G1 X0 Y0\n",
            "Metadata/project_settings.config": b"{}",
            "Metadata/slice_info.config": b"<config/>",
        }
        for member, payload in cases.items():
            with self.subTest(member=member), tempfile.TemporaryDirectory() as temp:
                models = Path(temp)
                self.copy_models(models)
                archive = models / "wardrobe_rail_bracket_main.3mf"
                rewrite_zip(archive, additions={member: payload})

                self.assert_rejected(self.run_validator("models", models), "neutral")

    def test_p1s_rejects_malformed_zip(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            archive.write_bytes(b"not a ZIP archive")
            self.assert_rejected(self.run_validator("p1s", archive), "ZIP")

    def test_p1s_rejects_each_missing_required_payload(self):
        for member in sorted(P1S_REQUIRED_MEMBERS):
            with self.subTest(member=member), tempfile.TemporaryDirectory() as temp:
                archive = Path(temp) / "release.gcode.3mf"
                self.copy_p1s(archive)
                rewrite_zip(archive, omitted={member})

                self.assert_rejected(self.run_validator("p1s", archive), "missing")

    def test_p1s_rejects_wrong_object_count(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            with zipfile.ZipFile(archive) as source:
                root = ET.fromstring(source.read("Metadata/model_settings.config"))
            root.remove(root.findall("object")[-1])
            plate = root.find("plate")
            plate.remove(plate.findall("model_instance")[-1])
            rewrite_zip(
                archive,
                replacements={
                    "Metadata/model_settings.config": ET.tostring(
                        root, encoding="utf-8", xml_declaration=True
                    )
                },
            )

            self.assert_rejected(self.run_validator("p1s", archive), "object")

    def test_p1s_rejects_wrong_package_object_count(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            member = "3D/3dmodel.model"
            with zipfile.ZipFile(archive) as source:
                root = ET.fromstring(source.read(member))
            namespace = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
            resources = root.find(f"./{namespace}resources")
            build = root.find(f"./{namespace}build")
            resources.remove(resources.findall(f"./{namespace}object")[-1])
            build.remove(build.findall(f"./{namespace}item")[-1])
            rewrite_zip(
                archive,
                replacements={
                    member: ET.tostring(root, encoding="utf-8", xml_declaration=True)
                },
            )

            self.assert_rejected(self.run_validator("p1s", archive), "object")

    def test_p1s_rejects_wrong_object_width(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            member = "3D/Objects/main_print.stl_1.model"
            with zipfile.ZipFile(archive) as source:
                root = ET.fromstring(source.read(member))
            namespace = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
            vertices = root.findall(f".//{namespace}vertex")
            rightmost = max(vertices, key=lambda vertex: float(vertex.attrib["x"]))
            rightmost.set("x", str(float(rightmost.attrib["x"]) + 1))
            rewrite_zip(
                archive,
                replacements={
                    member: ET.tostring(root, encoding="utf-8", xml_declaration=True)
                },
            )

            self.assert_rejected(self.run_validator("p1s", archive), "width")

    def test_p1s_rejects_main_meshes_substituted_for_cap_payloads(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            with zipfile.ZipFile(archive) as source:
                main_mesh = source.read("3D/Objects/main_print.stl_1.model")
            rewrite_zip(
                archive,
                replacements={
                    "3D/Objects/cap_print.stl_3.model": main_mesh,
                    "3D/Objects/cap_print.stl_4.model": main_mesh,
                },
            )

            self.assert_rejected(self.run_validator("p1s", archive), "cap")

    def test_p1s_rejects_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            rewrite_zip(
                archive,
                replacements={"Metadata/plate_1.gcode.md5": b"0" * 32},
            )

            self.assert_rejected(self.run_validator("p1s", archive), "checksum")

    def test_p1s_rejects_wrong_machine_material_bed_and_process_settings(self):
        cases = {
            "printer_model": "Different printer",
            "filament_type": ["PETG"],
            "curr_bed_type": "Cool Plate",
            "wall_loops": "2",
        }
        for key, value in cases.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp:
                archive = Path(temp) / "release.gcode.3mf"
                self.copy_p1s(archive)
                with zipfile.ZipFile(archive) as source:
                    settings = json.loads(
                        source.read("Metadata/project_settings.config")
                    )
                settings[key] = value
                rewrite_zip(
                    archive,
                    replacements={
                        "Metadata/project_settings.config": json.dumps(settings)
                    },
                )

                self.assert_rejected(self.run_validator("p1s", archive), key)

    def test_p1s_rejects_support_used_other_than_false(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            with zipfile.ZipFile(archive) as source:
                root = ET.fromstring(source.read("Metadata/slice_info.config"))
            support = root.find("./plate/metadata[@key='support_used']")
            support.set("value", "true")
            rewrite_zip(
                archive,
                replacements={
                    "Metadata/slice_info.config": ET.tostring(
                        root, encoding="utf-8", xml_declaration=True
                    )
                },
            )

            self.assert_rejected(self.run_validator("p1s", archive), "support_used")

    def test_p1s_rejects_implausible_weight_and_time_estimates(self):
        cases = {
            "weight": "168.9",
            "prediction": "22376",
        }
        for key, value in cases.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp:
                archive = Path(temp) / "release.gcode.3mf"
                self.copy_p1s(archive)
                with zipfile.ZipFile(archive) as source:
                    root = ET.fromstring(source.read("Metadata/slice_info.config"))
                root.find("./plate/metadata[@key='weight']").set("value", "169.15")
                root.find("./plate/metadata[@key='prediction']").set(
                    "value", "22314"
                )
                metadata = root.find(f"./plate/metadata[@key='{key}']")
                self.assertIsNotNone(metadata)
                metadata.set("value", value)
                rewrite_zip(
                    archive,
                    replacements={
                        "Metadata/slice_info.config": ET.tostring(
                            root, encoding="utf-8", xml_declaration=True
                        )
                    },
                )

                with zipfile.ZipFile(archive) as candidate:
                    with self.assertRaisesRegex(ValidationError, key):
                        _validate_p1s_slice(candidate)

    def test_p1s_rejects_support_toolpaths_even_with_matching_checksum(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            with zipfile.ZipFile(archive) as source:
                gcode = source.read("Metadata/plate_1.gcode") + b"\n; FEATURE: Support\n"
            rewrite_zip(
                archive,
                replacements={
                    "Metadata/plate_1.gcode": gcode,
                    "Metadata/plate_1.gcode.md5": hashlib.md5(gcode).hexdigest(),
                },
            )

            self.assert_rejected(self.run_validator("p1s", archive), "support toolpath")

    def test_p1s_rejects_checksum_updated_comment_only_gcode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive = Path(temporary_directory) / "release.gcode.3mf"
            self.copy_p1s(archive)
            gcode = b"; no printable toolpaths\n"
            rewrite_zip(
                archive,
                replacements={
                    "Metadata/plate_1.gcode": gcode,
                    "Metadata/plate_1.gcode.md5": hashlib.md5(gcode).hexdigest(),
                },
            )

            self.assert_rejected(self.run_validator("p1s", archive), "layer")


if __name__ == "__main__":
    unittest.main(verbosity=2)
