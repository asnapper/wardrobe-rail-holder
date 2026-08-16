#!/usr/bin/env python3
"""Validate generated release artifacts before they are published."""

import argparse
import hashlib
import json
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


CORE_NAMESPACE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
MODEL_CONTRACTS = {
    "wardrobe_rail_bracket_main.stl": ((63.5, 75.0, 30.0), 1),
    "wardrobe_rail_bracket_cap.stl": ((63.5, 24.0, 15.7), 1),
    "wardrobe_rail_bracket_main.3mf": ((63.5, 75.0, 30.0), 1),
    "wardrobe_rail_bracket_cap.3mf": ((63.5, 24.0, 15.7), 1),
    "wardrobe_rail_bracket_complete.3mf": ((133.5, 75.0, 30.0), 2),
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
P1S_EXPECTED_SETTINGS = {
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
    "outer_wall_speed": "120",
    "inner_wall_speed": "200",
    "sparse_infill_speed": "200",
    "filament_type": ["PLA"],
    "filament_vendor": ["Bambu Lab"],
    "filament_density": ["1.26"],
}
SUPPORT_TOOLPATH = re.compile(
    r"^\s*;\s*(?:FEATURE|TYPE)\s*:\s*SUPPORT(?:\s+INTERFACE)?\b",
    re.IGNORECASE | re.MULTILINE,
)


class ValidationError(Exception):
    """A generated artifact does not satisfy its release contract."""


def _read_binary_stl(path):
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise ValidationError(f"unable to read STL {path.name}: {error}") from error
    if len(payload) < 84:
        raise ValidationError(f"malformed STL {path.name}: file is too small")
    triangle_count = struct.unpack_from("<I", payload, 80)[0]
    expected_size = 84 + triangle_count * 50
    if triangle_count == 0 or len(payload) != expected_size:
        raise ValidationError(
            f"malformed STL {path.name}: triangle table does not match file size"
        )

    triangles = []
    for triangle_index in range(triangle_count):
        offset = 84 + triangle_index * 50 + 12
        triangle = tuple(
            struct.unpack_from("<fff", payload, offset + vertex_index * 12)
            for vertex_index in range(3)
        )
        if not all(math.isfinite(value) for vertex in triangle for value in vertex):
            raise ValidationError(f"malformed STL {path.name}: non-finite vertex")
        triangles.append(triangle)
    return triangles


def _checked_archive(path, artifact_label):
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValidationError(f"malformed {artifact_label} ZIP archive: {path}")
    try:
        archive = zipfile.ZipFile(path)
        duplicate = next(
            (name for name, count in Counter(archive.namelist()).items() if count > 1),
            None,
        )
        if duplicate is not None:
            archive.close()
            raise ValidationError(
                f"malformed {artifact_label} ZIP archive: duplicate member {duplicate}"
            )
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            archive.close()
            raise ValidationError(
                f"malformed {artifact_label} ZIP archive: corrupt member {corrupt_member}"
            )
        return archive
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        raise ValidationError(
            f"malformed {artifact_label} ZIP archive {path}: {error}"
        ) from error


def _xml_root(payload, member):
    if not payload:
        raise ValidationError(f"required payload is empty: {member}")
    try:
        return ET.fromstring(payload)
    except ET.ParseError as error:
        raise ValidationError(f"malformed XML payload {member}: {error}") from error


def _triangles_from_model(payload, member):
    root = _xml_root(payload, member)
    triangles = []
    for mesh in root.findall(f".//{CORE_NAMESPACE}mesh"):
        vertices = []
        for vertex in mesh.findall(f"./{CORE_NAMESPACE}vertices/{CORE_NAMESPACE}vertex"):
            try:
                coordinates = tuple(float(vertex.attrib[axis]) for axis in ("x", "y", "z"))
            except (KeyError, ValueError) as error:
                raise ValidationError(f"malformed 3MF model payload {member}: vertex") from error
            if not all(math.isfinite(value) for value in coordinates):
                raise ValidationError(
                    f"malformed 3MF model payload {member}: non-finite vertex"
                )
            vertices.append(coordinates)
        for triangle in mesh.findall(
            f"./{CORE_NAMESPACE}triangles/{CORE_NAMESPACE}triangle"
        ):
            try:
                indices = tuple(int(triangle.attrib[key]) for key in ("v1", "v2", "v3"))
                triangles.append(tuple(vertices[index] for index in indices))
            except (IndexError, KeyError, ValueError) as error:
                raise ValidationError(
                    f"malformed 3MF model payload {member}: triangle"
                ) from error
    if not triangles:
        raise ValidationError(f"3MF model payload has no mesh triangles: {member}")
    return triangles


def _mesh_envelope(triangles):
    coordinates = tuple(
        zip(*(vertex for triangle in triangles for vertex in triangle))
    )
    lower = tuple(min(axis) for axis in coordinates)
    upper = tuple(max(axis) for axis in coordinates)
    return tuple(high - low for low, high in zip(lower, upper)), lower


def _volume_count(triangles):
    edge_triangles = defaultdict(list)
    for triangle_index, triangle in enumerate(triangles):
        for start, end in ((0, 1), (1, 2), (2, 0)):
            edge_triangles[tuple(sorted((triangle[start], triangle[end])))].append(
                triangle_index
            )

    neighbours = defaultdict(set)
    for adjacent in edge_triangles.values():
        for triangle_index in adjacent:
            neighbours[triangle_index].update(
                other for other in adjacent if other != triangle_index
            )
    unseen = set(range(len(triangles)))
    volumes = 0
    while unseen:
        volumes += 1
        pending = [unseen.pop()]
        while pending:
            adjacent = neighbours[pending.pop()] & unseen
            unseen.difference_update(adjacent)
            pending.extend(adjacent)
    return volumes, edge_triangles


def _validate_neutral_mesh(filename, triangles, expected_size, expected_volumes):
    size, lower = _mesh_envelope(triangles)
    if any(abs(actual - expected) > 0.06 for actual, expected in zip(size, expected_size)):
        formatted = tuple(round(value, 3) for value in size)
        raise ValidationError(
            f"incorrect M6 envelope for {filename}: {formatted}, expected {expected_size}"
        )
    if abs(lower[2]) > 0.01:
        raise ValidationError(
            f"incorrect print orientation for {filename}: mesh does not rest on build plate"
        )
    volume_count, edges = _volume_count(triangles)
    if volume_count != expected_volumes:
        raise ValidationError(
            f"incorrect printable volume count for {filename}: "
            f"{volume_count}, expected {expected_volumes}"
        )
    if any(len(set(triangle)) != 3 for triangle in triangles) or any(
        len(adjacent) != 2 for adjacent in edges.values()
    ):
        raise ValidationError(f"non-manifold mesh in {filename}")


def validate_models(output_directory):
    output_directory = Path(output_directory)
    missing = sorted(
        filename
        for filename in MODEL_CONTRACTS
        if not (output_directory / filename).is_file()
    )
    if missing:
        raise ValidationError(f"missing neutral model artifact(s): {', '.join(missing)}")

    for filename, (expected_size, expected_volumes) in MODEL_CONTRACTS.items():
        path = output_directory / filename
        if path.suffix == ".stl":
            triangles = _read_binary_stl(path)
        else:
            with _checked_archive(path, "3MF") as archive:
                names = set(archive.namelist())
                prohibited = sorted(
                    name
                    for name in names
                    if ".gcode" in Path(name).name.lower()
                    or name.lower()
                    in {
                        "metadata/project_settings.config",
                        "metadata/model_settings.config",
                        "metadata/slice_info.config",
                    }
                    or (
                        name.lower().startswith("metadata/plate_")
                        and name.lower().endswith(".json")
                    )
                )
                if prohibited:
                    raise ValidationError(
                        f"neutral 3MF contains G-code or slicer metadata: {prohibited[0]}"
                    )
                model_member = "3D/3dmodel.model"
                if model_member not in names:
                    raise ValidationError(
                        f"neutral 3MF is missing required 3D model payload: {filename}"
                    )
                triangles = _triangles_from_model(
                    archive.read(model_member), model_member
                )
        _validate_neutral_mesh(
            filename, triangles, expected_size, expected_volumes
        )


def _required_archive_payload(archive, member):
    try:
        payload = archive.read(member)
    except KeyError as error:
        raise ValidationError(f"P1S archive is missing required payload: {member}") from error
    if not payload:
        raise ValidationError(f"required P1S payload is empty: {member}")
    return payload


def _validate_p1s_objects(archive):
    model_settings = _xml_root(
        _required_archive_payload(archive, "Metadata/model_settings.config"),
        "Metadata/model_settings.config",
    )
    objects = model_settings.findall("./object")
    instances = model_settings.findall("./plate/model_instance")
    names = []
    for object_element in objects:
        metadata = object_element.find("./metadata[@key='name']")
        if metadata is None or "value" not in metadata.attrib:
            raise ValidationError("P1S object is missing its model name")
        names.append(metadata.attrib["value"])
    expected_names = Counter({"main_print.stl": 2, "cap_print.stl": 2})
    if len(objects) != 4 or len(instances) != 4 or Counter(names) != expected_names:
        raise ValidationError(
            "incorrect P1S object count: expected two main and two cap objects"
        )

    object_members = sorted(
        name
        for name in archive.namelist()
        if name.startswith("3D/Objects/") and name.endswith(".model")
    )
    if len(object_members) != 4:
        raise ValidationError(
            f"incorrect P1S object model count: {len(object_members)}, expected 4"
        )
    for member in object_members:
        triangles = _triangles_from_model(_required_archive_payload(archive, member), member)
        size, _ = _mesh_envelope(triangles)
        if abs(size[0] - 63.5) > 0.06:
            raise ValidationError(
                f"incorrect P1S object width for {member}: {size[0]:.3f}, expected 63.5"
            )


def _validate_p1s_settings(archive):
    member = "Metadata/project_settings.config"
    try:
        settings = json.loads(_required_archive_payload(archive, member))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValidationError(f"malformed JSON payload {member}: {error}") from error
    if not isinstance(settings, dict):
        raise ValidationError(f"malformed JSON payload {member}: expected object")
    for key, expected in P1S_EXPECTED_SETTINGS.items():
        actual = settings.get(key)
        if actual != expected:
            raise ValidationError(
                f"incorrect P1S setting {key}: {actual!r}, expected {expected!r}"
            )


def _validate_p1s_slice(archive):
    member = "Metadata/slice_info.config"
    slice_info = _xml_root(_required_archive_payload(archive, member), member)
    support = slice_info.find("./plate/metadata[@key='support_used']")
    actual = None if support is None else support.attrib.get("value")
    if actual != "false":
        raise ValidationError(
            f"incorrect P1S support_used metadata: {actual!r}, expected 'false'"
        )

    gcode = _required_archive_payload(archive, "Metadata/plate_1.gcode")
    checksum_payload = _required_archive_payload(
        archive, "Metadata/plate_1.gcode.md5"
    )
    try:
        expected_checksum = checksum_payload.decode("ascii").strip().lower()
    except UnicodeDecodeError as error:
        raise ValidationError("malformed embedded G-code checksum") from error
    actual_checksum = hashlib.md5(gcode).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{32}", expected_checksum) or (
        actual_checksum != expected_checksum
    ):
        raise ValidationError(
            "embedded G-code checksum mismatch: "
            f"{actual_checksum}, expected {expected_checksum!r}"
        )
    gcode_text = gcode.decode("utf-8", errors="replace")
    if SUPPORT_TOOLPATH.search(gcode_text):
        raise ValidationError("embedded G-code contains a support toolpath feature")


def validate_p1s(archive_path):
    archive_path = Path(archive_path)
    with _checked_archive(archive_path, "P1S") as archive:
        names = set(archive.namelist())
        missing = sorted(P1S_REQUIRED_MEMBERS - names)
        if missing:
            raise ValidationError(
                f"P1S archive is missing required payload(s): {', '.join(missing)}"
            )
        for member in P1S_REQUIRED_MEMBERS:
            _required_archive_payload(archive, member)
        package_model = _xml_root(
            _required_archive_payload(archive, "3D/3dmodel.model"),
            "3D/3dmodel.model",
        )
        package_objects = package_model.findall(
            f"./{CORE_NAMESPACE}resources/{CORE_NAMESPACE}object"
        )
        package_items = package_model.findall(
            f"./{CORE_NAMESPACE}build/{CORE_NAMESPACE}item"
        )
        if len(package_objects) != 4 or len(package_items) != 4:
            raise ValidationError(
                "incorrect P1S package object count: expected 4 objects and 4 build items"
            )
        try:
            json.loads(_required_archive_payload(archive, "Metadata/plate_1.json"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValidationError(
                f"malformed JSON payload Metadata/plate_1.json: {error}"
            ) from error
        _validate_p1s_objects(archive)
        _validate_p1s_settings(archive)
        _validate_p1s_slice(archive)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    models_parser = subparsers.add_parser("models", help="validate neutral models")
    models_parser.add_argument("output_directory", type=Path)
    p1s_parser = subparsers.add_parser("p1s", help="validate one P1S archive")
    p1s_parser.add_argument("archive", type=Path)
    arguments = parser.parse_args(argv)

    try:
        if arguments.mode == "models":
            validate_models(arguments.output_directory)
        else:
            validate_p1s(arguments.archive)
    except ValidationError as error:
        parser.exit(1, f"release validation failed: {error}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
