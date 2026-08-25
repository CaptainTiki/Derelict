"""Build the complete static POLYGON Sci-Fi Space Blender source library.

Run with Blender in background mode. The script discovers every static FBX in
the pack's FBX directory, organizes the assets by family, normalizes transforms
and materials, retains the first Derelict test-zone audition layout, and saves
``synty_space_library.blend`` beside this script.
"""

from collections import defaultdict
from pathlib import Path
import math
import re

import bpy


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ASSETS = SCRIPT_DIR.parent
PACK_ROOT = Path(r"D:\Godot\REPOs\POLYGON\Space")
FBX_ROOT = PACK_ROOT / "FBX"
TEXTURE_ROOT = PROJECT_ASSETS / "textures"
OUTPUT_BLEND = SCRIPT_DIR / "synty_space_library.blend"

ALBEDO_PATH = TEXTURE_ROOT / "PolygonSciFiSpace_Texture_01_A.png"
EMISSION_PATH = TEXTURE_ROOT / "PolygonSciFiSpace_Emissive_01.png"
SIGN_PATH = TEXTURE_ROOT / "PolygonSciFiSpace_Signs_Texture_01_B.png"
SIGN_EMISSION_PATH = TEXTURE_ROOT / "PolygonSciFiSpace_Signs_Texture_Emissive_01.png"

OPAQUE_MATERIAL = "M_SyntySpace_Opaque_A"
GLASS_MATERIAL = "M_SyntySpace_Glass"
SIGN_MATERIAL = "M_SyntySpace_Sign_B"

# The first production test group remains as a compact audition layout inside
# the complete source library.
AUDITION_ASSETS = {
    "floors": [
        "SM_Bld_Floor_01",
        "SM_Bld_Floor_02",
        "SM_Bld_Floor_03",
        "SM_Bld_Floor_04",
        "SM_Bld_Floor_05",
        "SM_Bld_Floor_06",
        "SM_Bld_Floor_07",
        "SM_Bld_Floor_08",
        "SM_Bld_Floor_09",
        "SM_Bld_Floor_010",
        "SM_Bld_Floor_011",
    ],
    "walls": [
        "SM_Bld_Wall_01",
        "SM_Bld_Wall_02",
        "SM_Bld_Wall_Mechanical_01",
    ],
    "ceilings": [
        "SM_Bld_Ceiling_01",
        "SM_Bld_Ceiling_02",
        "SM_Bld_Ceiling_03",
        "SM_Bld_Roof_Exterior_01",
        "SM_Bld_Roof_Exterior_02",
        "SM_Bld_Roof_Exterior_03",
    ],
    "corridor": [
        "SM_Bld_Corridor_Single_Arch_01",
    ],
    "doors": [
        "SM_Bld_Wall_Doorframe_01",
        # A powered-airlock candidate with independent left/right door leaves.
        "SM_Bld_Wall_Doorframe_05",
    ],
    "pillars": [
        "SM_Bld_Wall_Pillar_01",
        "SM_Bld_Wall_Corner_Pillar_01",
    ],
    "lights": [
        "SM_Prop_Light_Panel_01",
    ],
    "controls": [
        "SM_Prop_Detail_Button_01",
        "SM_Prop_Detail_Keypad_01",
    ],
    "damage": [
        "SM_Prop_Detail_Panel_Broken_01",
    ],
    "vents": [
        "SM_Prop_Detail_Airvent_01",
        "SM_Prop_Detail_Pipe_Broken_01",
    ],
}


def asset_category(asset_name: str) -> str:
    """Return a stable Godot geometry folder for a Synty asset name."""
    if asset_name.startswith(("SM_Bld_Ceiling", "SM_Bld_Roof")):
        return "ceilings"
    if asset_name.startswith("SM_Bld_Floor"):
        return "floors"
    if asset_name.startswith("SM_Bld_Corridor"):
        return "corridor"
    if asset_name.startswith(("SM_Bld_Wall_Door", "SM_Bld_Wall_EscPod_Hatch")):
        return "doors"
    if asset_name.startswith(("SM_Bld_Wall_Pillar", "SM_Bld_Wall_Corner_Pillar")):
        return "pillars"
    if asset_name.startswith("SM_Bld_Wall"):
        return "walls"

    if asset_name.startswith("SM_Prop_Light"):
        return "lights"
    if asset_name.startswith((
        "SM_Prop_Detail_Button",
        "SM_Prop_Detail_Keypad",
        "SM_Prop_Buttons",
        "SM_Prop_ControlPanel",
        "SM_Prop_HandScanner",
        "SM_Prop_Joystick",
        "SM_Prop_MapTable",
        "SM_Prop_Radar",
        "SM_Prop_Screen",
    )):
        return "controls"
    if asset_name.startswith("SM_Prop_Detail_Panel_Broken"):
        return "damage"
    if asset_name.startswith((
        "SM_Prop_Detail_Airvent",
        "SM_Prop_Detail_Pipe_Broken",
        "SM_Prop_AirVent",
    )):
        return "vents"

    parts = asset_name.split("_")
    family = parts[1].lower() if len(parts) > 1 else "misc"
    subfamily = parts[2].lower() if len(parts) > 2 else "misc"
    if family == "bld":
        return f"buildings/{subfamily}"
    if family == "prop":
        return f"props/{subfamily}"
    if family == "env":
        return "environment"
    if family == "veh":
        return "vehicles"
    if family == "ship":
        return "ships"
    if family in ("sign", "signborder"):
        return "signs"
    if family == "hud":
        return "hud"
    if family == "wep":
        return "weapons"
    if family == "chr":
        return "character_parts"
    if family == "fx":
        return "fx"
    return f"misc/{family}"


def discover_assets():
    """Discover the static FBX library and reject ambiguous duplicate names."""
    by_name = {}
    for fbx_path in sorted(FBX_ROOT.rglob("*.fbx")):
        asset_name = fbx_path.stem
        if asset_name in by_name:
            raise RuntimeError(
                f"Duplicate static asset name '{asset_name}': "
                f"{by_name[asset_name]} and {fbx_path}"
            )
        by_name[asset_name] = fbx_path
    return by_name


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)


def make_collection(name: str, parent=None):
    collection = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(collection)
    else:
        parent.children.link(collection)
    return collection


def make_collection_path(path: str, parent, prefix: str = ""):
    current = parent
    for part in path.split("/"):
        collection_name = f"{prefix}{part}"
        existing = next(
            (child for child in current.children if child.name == collection_name),
            None,
        )
        current = existing or make_collection(collection_name, current)
    return current


def load_image(path: Path):
    require_file(path)
    image = bpy.data.images.load(str(path), check_existing=True)
    image.filepath = bpy.path.relpath(str(path), start=str(OUTPUT_BLEND.parent))
    return image


def principled_input(shader, *names):
    for name in names:
        socket = shader.inputs.get(name)
        if socket is not None:
            return socket
    raise KeyError(f"None of the Principled inputs exist: {names}")


def make_opaque_material():
    material = bpy.data.materials.new(OPAQUE_MATERIAL)
    material.use_nodes = True
    material.use_fake_user = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (620, 40)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (260, 40)
    principled_input(shader, "Metallic").default_value = 0.0
    principled_input(shader, "Roughness").default_value = 0.68

    albedo = nodes.new("ShaderNodeTexImage")
    albedo.name = "Synty Albedo Atlas"
    albedo.label = "Synty Albedo Atlas"
    albedo.location = (-300, 180)
    albedo.image = load_image(ALBEDO_PATH)
    albedo.interpolation = "Linear"

    emission = nodes.new("ShaderNodeTexImage")
    emission.name = "Synty Emission Atlas"
    emission.label = "Synty Emission Atlas"
    emission.location = (-300, -160)
    emission.image = load_image(EMISSION_PATH)
    emission.interpolation = "Linear"

    links.new(albedo.outputs["Color"], principled_input(shader, "Base Color"))
    links.new(emission.outputs["Color"], principled_input(shader, "Emission Color", "Emission"))
    principled_input(shader, "Emission Strength").default_value = 1.0
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_glass_material():
    material = bpy.data.materials.new(GLASS_MATERIAL)
    material.use_nodes = True
    material.use_fake_user = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    principled_input(shader, "Base Color").default_value = (0.08, 0.32, 0.38, 1.0)
    principled_input(shader, "Roughness").default_value = 0.12
    principled_input(shader, "Metallic").default_value = 0.0
    principled_input(shader, "Alpha").default_value = 0.28
    transmission = shader.inputs.get("Transmission Weight") or shader.inputs.get("Transmission")
    if transmission is not None:
        transmission.default_value = 0.35
    return material


def make_sign_material():
    material = bpy.data.materials.new(SIGN_MATERIAL)
    material.use_nodes = True
    material.use_fake_user = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    albedo = nodes.new("ShaderNodeTexImage")
    emission = nodes.new("ShaderNodeTexImage")
    albedo.image = load_image(SIGN_PATH)
    emission.image = load_image(SIGN_EMISSION_PATH)
    links.new(albedo.outputs["Color"], principled_input(shader, "Base Color"))
    links.new(emission.outputs["Color"], principled_input(shader, "Emission Color", "Emission"))
    principled_input(shader, "Emission Strength").default_value = 1.0
    principled_input(shader, "Roughness").default_value = 0.65
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def unlink_object_everywhere(obj) -> None:
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)


def normalize_mesh(obj, asset_name, materials) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    if obj.name.upper().startswith("UCX_"):
        obj.hide_render = True
        obj.display_type = "WIRE"
        obj["derelict_collision_source"] = True
        return

    if "glass" in obj.name.lower() or "glass" in asset_name.lower() or "clear" in asset_name.lower():
        canonical = materials[GLASS_MATERIAL]
    elif asset_name.startswith("SM_Sign_"):
        canonical = materials[SIGN_MATERIAL]
    else:
        canonical = materials[OPAQUE_MATERIAL]

    obj.data.materials.clear()
    obj.data.materials.append(canonical)
    obj["derelict_source_material"] = canonical.name
    obj["derelict_export_ready"] = True

    try:
        obj.asset_mark()
        obj.asset_data.description = "POLYGON Sci-Fi Space source mesh normalized for Derelict"
    except (AttributeError, RuntimeError):
        pass


def import_asset(asset_name, fbx_path, category, source_category, export_category, materials):
    require_file(fbx_path)

    before = set(bpy.data.objects)
    preexisting_names = {obj.name for obj in before}
    result = bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    if "FINISHED" not in result:
        raise RuntimeError(f"Could not import {fbx_path}")
    imported = [obj for obj in bpy.data.objects if obj not in before]
    if not imported:
        raise RuntimeError(f"Import created no objects: {fbx_path}")

    # FBXs sometimes parent movable pieces to their surrounding static mesh.
    # Detach them while preserving world transforms so every exported object
    # keeps its authored pivot but can be normalized and exported independently.
    world_matrices = {obj: obj.matrix_world.copy() for obj in imported}
    for obj in imported:
        obj.parent = None
        obj.matrix_world = world_matrices[obj]

        # Some Synty FBXs reuse generic child names such as
        # SM_Bld_Wall_Door_01. Give only colliding children an asset-qualified
        # name so individual GLB filenames stay stable and descriptive.
        base_name = re.sub(r"\.\d{3}$", "", obj.name)
        if base_name in preexisting_names:
            obj.name = f"{asset_name}__{base_name}"

    asset_collection = make_collection(asset_name, source_category)
    visual_meshes = []
    for obj in imported:
        unlink_object_everywhere(obj)
        asset_collection.objects.link(obj)
        obj["derelict_source_fbx"] = str(fbx_path)
        obj["derelict_asset_group"] = asset_name
        if obj.type == "MESH":
            normalize_mesh(obj, asset_name, materials)
            if not obj.name.upper().startswith("UCX_"):
                export_category.objects.link(obj)
                visual_meshes.append(obj)

    print(f"IMPORTED: {asset_name} ({category}) -> {len(visual_meshes)} export mesh(es)")
    return visual_meshes


def add_audition_copy(source_obj, collection, offset, asset_name):
    copy = source_obj.copy()
    copy.data = source_obj.data
    copy.animation_data_clear()
    copy.name = f"AUD_{source_obj.name}"
    collection.objects.link(copy)
    copy.location.x += offset[0]
    copy.location.y += offset[1]
    copy.location.z += offset[2]
    copy["derelict_audition_source"] = asset_name
    copy.pop("derelict_export_ready", None)
    return copy


def build_audition_layout(imported_by_asset, audition_root):
    # Rows are separated enough for the native five-metre modules. Objects from
    # a compound FBX share an offset so doors remain aligned with their frames.
    row_spacing = 9.0
    item_spacing = 7.0
    for row, (category, names) in enumerate(AUDITION_ASSETS.items()):
        row_collection = make_collection(f"TEST_{category}", audition_root)
        for column, asset_name in enumerate(names):
            offset = (column * item_spacing, row * row_spacing, 0.0)
            for obj in imported_by_asset[asset_name]:
                add_audition_copy(obj, row_collection, offset, asset_name)


def main():
    for path in (ALBEDO_PATH, EMISSION_PATH, SIGN_PATH, SIGN_EMISSION_PATH):
        require_file(path)
    for names in AUDITION_ASSETS.values():
        for asset_name in names:
            require_file(FBX_ROOT / f"{asset_name}.fbx")

    discovered_assets = discover_assets()
    assets_by_category = defaultdict(list)
    for asset_name, fbx_path in discovered_assets.items():
        category = "fx" if fbx_path.parent != FBX_ROOT else asset_category(asset_name)
        assets_by_category[category].append(asset_name)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.name = "Synty Space Library"
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "METERS"
    bpy.context.scene.unit_settings.scale_length = 1.0
    # This file is generated reproducibly; retaining stale .blend1 snapshots can
    # make it too easy to open a previous automated build by mistake.
    bpy.context.preferences.filepaths.save_version = 0

    source_root = make_collection("SOURCE")
    export_root = make_collection("EXPORT")
    audition_root = make_collection("TEST_ZONE")

    materials = {
        OPAQUE_MATERIAL: make_opaque_material(),
        GLASS_MATERIAL: make_glass_material(),
        SIGN_MATERIAL: make_sign_material(),
    }

    imported_by_asset = {}
    skipped_assets = []
    for category in sorted(assets_by_category):
        source_category = make_collection_path(category, source_root, "SOURCE_")
        export_category = make_collection_path(category, export_root)
        for asset_name in sorted(assets_by_category[category]):
            try:
                imported_by_asset[asset_name] = import_asset(
                    asset_name,
                    discovered_assets[asset_name],
                    category,
                    source_category,
                    export_category,
                    materials,
                )
            except RuntimeError as error:
                if "ASCII FBX files are not supported" not in str(error):
                    raise
                imported_by_asset[asset_name] = []
                skipped_assets.append(asset_name)
                print(f"SKIPPED ASCII FBX: {asset_name} -> {discovered_assets[asset_name]}")

    build_audition_layout(imported_by_asset, audition_root)

    source_root.hide_render = True
    export_root.hide_render = True
    export_root.hide_viewport = True

    # Imported FBXs create duplicate materials and stale image datablocks. Once
    # every mesh points to a canonical material they can be removed safely.
    bpy.ops.outliner.orphans_purge(do_recursive=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND), check_existing=False)
    print(f"SAVED: {OUTPUT_BLEND}")
    print(f"ASSETS: {len(discovered_assets) - len(skipped_assets)} imported")
    print(f"SKIPPED: {skipped_assets}")
    print(f"CATEGORIES: {len(assets_by_category)}")
    print(f"MATERIALS: {[material.name for material in bpy.data.materials]}")


if __name__ == "__main__":
    main()
