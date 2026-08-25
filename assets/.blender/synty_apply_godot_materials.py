"""Assign Derelict's shared Godot materials to every exported Synty GLB.

Run this after Godot has created the ``.glb.import`` sidecars. The material
labels embedded by ``synty_batch_export.py`` determine which shared resource
Godot should use, so re-exporting geometry never duplicates materials.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import struct


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GEOMETRY_ROOT = PROJECT_ROOT / "assets" / "geometry"

MATERIALS = {
    "M_SyntySpace_External": (
        "res://assets/materials/scifi_space_emission.tres",
        "uid://cnwjxwjexjsmp",
    ),
    "M_SyntySpace_Glass_External": (
        "res://assets/materials/scifi_space_glass.tres",
        "uid://c6v4d6t0f8q2m",
    ),
    "M_SyntySpace_Sign_External": (
        "res://assets/materials/scifi_space_sign.tres",
        "uid://b5q1k3w9m7x2h",
    ),
}


def glb_material_names(glb_path: Path) -> list[str]:
    data = glb_path.read_bytes()
    if data[:4] != b"glTF":
        raise RuntimeError(f"Not a GLB file: {glb_path}")

    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise RuntimeError(f"First GLB chunk is not JSON: {glb_path}")

    document = json.loads(data[20 : 20 + json_length].decode("utf-8"))
    return [material["name"] for material in document.get("materials", [])]


def material_block(material_names: list[str]) -> str:
    if not material_names:
        return "_subresources={}\n"

    entries = []
    for material_name in material_names:
        if material_name not in MATERIALS:
            raise RuntimeError(f"Unknown exported material: {material_name}")
        resource_path, resource_uid = MATERIALS[material_name]
        entries.append(
            f'"{material_name}": {{\n'
            '"use_external/enabled": true,\n'
            f'"use_external/fallback_path": "{resource_path}",\n'
            f'"use_external/path": "{resource_uid}"\n'
            "}"
        )

    return '_subresources={\n"materials": {\n' + ",\n".join(entries) + "\n}\n}\n"


def apply_mapping(glb_path: Path) -> bool:
    import_path = glb_path.with_suffix(glb_path.suffix + ".import")
    if not import_path.exists():
        raise RuntimeError(f"Godot import sidecar is missing: {import_path}")

    material_names = glb_material_names(glb_path)
    original = import_path.read_text(encoding="utf-8")
    updated, replacements = re.subn(
        r"(?ms)^_subresources=.*?(?=^gltf/)",
        material_block(material_names),
        original,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError(f"Could not find _subresources in {import_path}")

    if updated == original:
        return False
    import_path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    glb_paths = sorted(GEOMETRY_ROOT.rglob("*.glb"))
    changed = sum(apply_mapping(glb_path) for glb_path in glb_paths)
    materialless = sum(not glb_material_names(glb_path) for glb_path in glb_paths)
    print(
        f"Mapped {len(glb_paths)} GLBs; updated {changed} Godot import sidecars; "
        f"{materialless} source helpers contain no rendered material."
    )


if __name__ == "__main__":
    main()
