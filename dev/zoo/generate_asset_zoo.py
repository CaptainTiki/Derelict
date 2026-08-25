from __future__ import annotations

import json
import math
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
ZOO_DIR = ROOT / "dev" / "zoo"
BIOME_DIR = ZOO_DIR / "biomes"


def res_path(path: Path) -> str:
    return "res://" + path.relative_to(ROOT).as_posix()


def clean_node_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    if not cleaned or cleaned[0].isdigit():
        cleaned = "N_" + cleaned
    return cleaned[:90]


def vector3(x: float, y: float, z: float) -> str:
    return f"Vector3({x:.3f}, {y:.3f}, {z:.3f})".replace(".000", "")


def color(r: float, g: float, b: float, a: float = 1.0) -> str:
    return f"Color({r:.3f}, {g:.3f}, {b:.3f}, {a:.3f})".replace(".000", "")


def all_glbs() -> list[Path]:
    return sorted((ROOT / "assets" / "geometry").rglob("*.glb"), key=lambda p: p.as_posix().lower())


def classify_asset(path: Path) -> tuple[str | None, str]:
    rel = path.relative_to(ROOT).as_posix()
    parts = rel.split("/")
    top = parts[2] if len(parts) > 2 else ""
    sub = parts[3] if len(parts) > 4 else ""
    name = path.stem
    low = name.lower()

    if top in {"ships", "environment"}:
        return None, "excluded_space_or_environment"
    if top == "vehicles":
        return None, "ambiguous_vehicle_or_exterior"
    if top == "character_parts":
        return None, "ambiguous_character_asset"
    if top == "fx":
        return None, "ambiguous_fx_or_non_catalog_mesh"
    if top == "buildings" and sub in {"hangarexteriorship", "landing"}:
        return None, "excluded_exterior_building"
    if "exterior" in low or "roof_exterior" in low:
        return None, "excluded_exterior_named"
    if sub in {"satellite", "solar", "spacewalk", "missile", "mine"}:
        return None, "ambiguous_space_or_weapon_prop"
    if top == "signs" and any(token in low for token in ["planet", "rocket", "ship"]):
        return None, "excluded_space_icon_sign"

    if top == "floors":
        if "hand_rail" in low:
            return "Structural/Railings", "included"
        if "walkway" in low:
            return "Structural/Walkways", "included"
        if "hatch" in low:
            return "Doors", "included"
        return "Floors", "included"
    if top == "walls":
        if "glass" in low or "window" in low:
            return "Windows", "included"
        if any(token in low for token in ["mechanical", "tube", "pods"]):
            return "Mechanical", "included"
        return "Walls", "included"
    if top == "ceilings":
        if "pipe" in low:
            return "Mechanical", "included"
        return "Ceilings", "included"
    if top == "pillars":
        return "Structural/Pillars", "included"
    if top == "corridor":
        return "Structural/CorridorArches", "included"
    if top == "doors":
        return "Doors", "included"
    if top == "controls" or top == "hud":
        return "ScreensAndControls", "included"
    if top == "lights":
        return "Lights", "included"
    if top == "signs":
        return "Signs", "included"
    if top == "damage":
        return "Mechanical", "included"
    if top == "vents":
        return "Mechanical", "included"
    if top == "weapons":
        return "HeroSpecialized/Security", "included"
    if top == "buildings":
        if sub == "hangar":
            if "door" in low:
                return "Doors", "included"
            if "ceiling" in low:
                return "Ceilings", "included"
            if "floor" in low:
                return "Floors", "included"
            if "glass" in low:
                return "Windows", "included"
            return "HeroSpecialized/Hangar", "included"
        if sub == "hangarplatform":
            return "Structural/Platforms", "included"
        if sub == "house":
            return "Floors", "included"
        if sub == "hydroponics":
            if "walkway" in low:
                return "Structural/Walkways", "included"
            if "ladder" in low:
                return "Structural/Stairs", "included"
            return "HeroSpecialized/Hydroponics", "included"
        if sub == "lift":
            if "door" in low:
                return "Doors", "included"
            if "wall" in low:
                return "Walls", "included"
            return "HeroSpecialized/Lift", "included"
        if sub == "bridge":
            return "HeroSpecialized/Bridge", "included"
        if sub == "crew":
            return "HeroSpecialized/Crew", "included"
    if top == "props":
        if sub in {"stairs"}:
            return "Structural/Stairs", "included"
        if sub in {"stairsplatform"}:
            return "Structural/Platforms", "included"
        if sub in {"ladder"}:
            return "Structural/Stairs", "included"
        if sub in {"detail", "greeble", "hose", "oxygen", "panel", "pillar", "wall", "wires", "engine"}:
            if "light" in low:
                return "Lights", "included"
            return "Mechanical", "included"
        if sub in {"escapepod"}:
            return "Doors", "included"
        if sub == "turret":
            return "HeroSpecialized/Security", "included"
        if sub in {"centertube", "cryobed", "decontamination", "medical", "medicalarms", "test", "testtubes"}:
            return "HeroSpecialized/MedicalResearch", "included"
        if sub in {"chr", "deadzub"}:
            return None, "ambiguous_character_prop"
        return "Props", "included"

    return None, "ambiguous_unclassified"


def collect_catalog() -> tuple[dict[str, list[Path]], dict[str, list[str]]]:
    categories: dict[str, list[Path]] = {}
    excluded: dict[str, list[str]] = {}
    for path in all_glbs():
        category, reason = classify_asset(path)
        if category is None:
            excluded.setdefault(reason, []).append(res_path(path))
            continue
        categories.setdefault(category, []).append(path)
    for paths in categories.values():
        paths.sort(key=lambda p: p.stem.lower())
    return categories, excluded


class SceneBuilder:
    def __init__(self, root_name: str):
        self.root_name = root_name
        self.ext_resources: dict[str, str] = {}
        self.lines: list[str] = []
        self.node_counts: dict[tuple[str, str], int] = {}

    def ext(self, path: str, kind: str = "PackedScene") -> str:
        if path not in self.ext_resources:
            self.ext_resources[path] = f"{kind.lower()}_{len(self.ext_resources) + 1}"
        return self.ext_resources[path]

    def node(self, name: str, node_type: str | None, parent: str | None = None, instance: str | None = None, props: dict[str, str] | None = None) -> None:
        raw_parent = parent or ""
        key = (raw_parent, name)
        self.node_counts[key] = self.node_counts.get(key, 0) + 1
        if self.node_counts[key] > 1:
            name = f"{name}_{self.node_counts[key]:02d}"
        attrs = [f'name="{name}"']
        if node_type:
            attrs.append(f'type="{node_type}"')
        if parent:
            if parent == self.root_name:
                parent = "."
            elif parent.startswith(self.root_name + "/"):
                parent = parent[len(self.root_name) + 1 :]
            attrs.append(f'parent="{parent}"')
        if instance:
            attrs.append(f'instance=ExtResource("{instance}")')
        self.lines.append("\n[node " + " ".join(attrs) + "]")
        for key, value in (props or {}).items():
            self.lines.append(f"{key} = {value}")

    def label(self, name: str, parent: str, text: str, position: tuple[float, float, float], size: int = 48) -> None:
        self.node(
            clean_node_name(name),
            "Label3D",
            parent,
            props={
                "position": vector3(*position),
                "billboard": "1",
                "font_size": str(size),
                "pixel_size": "0.018",
                "modulate": color(0.92, 0.96, 1.0),
                "outline_size": "8",
                "text": json.dumps(text),
            },
        )

    def asset(self, parent: str, path: Path, position: tuple[float, float, float], rotation_y: float | None = None) -> None:
        rid = self.ext(res_path(path))
        props = {"position": vector3(*position)}
        if rotation_y is not None:
            props["rotation"] = vector3(0.0, rotation_y, 0.0)
        self.node(clean_node_name(path.stem), None, parent, rid, props)

    def finish(self) -> str:
        header = [f"[gd_scene load_steps={len(self.ext_resources) + 6} format=3]"]
        for path, rid in self.ext_resources.items():
            header.append(f'[ext_resource type="PackedScene" path="{path}" id="{rid}"]')
        header.extend(
            [
                "",
                '[sub_resource type="StandardMaterial3D" id="GroundMat"]',
                f"albedo_color = {color(0.24, 0.25, 0.27)}",
                'roughness = 0.9',
                "",
                '[sub_resource type="StandardMaterial3D" id="ReferenceMat"]',
                f"albedo_color = {color(0.18, 0.22, 0.26)}",
                "",
                '[sub_resource type="ProceduralSkyMaterial" id="SkyMat"]',
                f"sky_horizon_color = {color(0.48, 0.51, 0.56)}",
                f"ground_horizon_color = {color(0.24, 0.25, 0.27)}",
                "energy_multiplier = 0.65",
                "",
                '[sub_resource type="Sky" id="Sky"]',
                'sky_material = SubResource("SkyMat")',
                "",
                '[sub_resource type="Environment" id="ZooEnvironment"]',
                "background_mode = 2",
                'sky = SubResource("Sky")',
                "ambient_light_source = 2",
                f"ambient_light_color = {color(0.62, 0.68, 0.76)}",
                "ambient_light_energy = 0.75",
                "tonemap_mode = 2",
                "ssao_enabled = true",
            ]
        )
        return "\n".join(header + self.lines) + "\n"


def add_common_roots(scene: SceneBuilder, root_name: str, player_position: tuple[float, float, float], floor_size: tuple[float, float, float]) -> None:
    player_id = scene.ext("res://player.tscn")
    scene.node(root_name, "Node3D")
    scene.node("WorldEnvironment", "WorldEnvironment", root_name, props={"environment": 'SubResource("ZooEnvironment")'})
    scene.node(
        "InspectionFloor",
        "CSGBox3D",
        root_name,
        props={
            "position": vector3(35, -0.08, floor_size[2] / 2 - 20),
            "size": vector3(*floor_size),
            "use_collision": "true",
            "material": 'SubResource("GroundMat")',
        },
    )
    scene.node("Lighting", "Node3D", root_name)
    scene.node(
        "SunKey",
        "DirectionalLight3D",
        f"{root_name}/Lighting",
        props={
            "rotation": vector3(-0.85, 0.55, 0.0),
            "light_energy": "1.35",
            "shadow_enabled": "true",
        },
    )
    scene.node(
        "FillLight",
        "OmniLight3D",
        f"{root_name}/Lighting",
        props={
            "position": vector3(22, 8, 20),
            "light_energy": "3.0",
            "omni_range": "38.0",
        },
    )
    scene.node("PlayerStart", "Marker3D", root_name, props={"position": vector3(*player_position)})
    scene.node("Player", None, root_name, player_id, {"position": vector3(*player_position)})


def add_catalog_section(scene: SceneBuilder, scene_root: str, parent_path: str, label: str, paths: list[Path], z_offset: float) -> float:
    section_name = clean_node_name(label.replace("/", "_"))
    section_parent = parent_path
    if "/" in label:
        parts = label.split("/")
        section_name = clean_node_name(parts[-1])
        section_parent = parent_path + "/" + "/".join(clean_node_name(p) for p in parts[:-1])
    node_path = f"{section_parent}/{section_name}"
    scene.node(section_name, "Node3D", section_parent, props={"position": vector3(0, 0, z_offset)})
    scene.label(f"Label_{section_name}", node_path, label, (-4.5, 3.0, -3.8), 72)
    columns = 4 if label.startswith("HeroSpecialized") else 6
    spacing_x = 14.0 if label.startswith("HeroSpecialized") else 9.0
    spacing_z = 12.0 if label.startswith("HeroSpecialized") else 9.0
    for index, path in enumerate(paths):
        row = index // columns
        col = index % columns
        x = col * spacing_x
        z = row * spacing_z
        scene.asset(node_path, path, (x, 0, z))
        scene.label(f"Label_{path.stem}", node_path, path.stem, (x, 2.35, z + 3.1), 36)
    rows = max(1, math.ceil(len(paths) / columns))
    return rows * spacing_z + 13.0


def full_zoo(categories: dict[str, list[Path]]) -> str:
    scene = SceneBuilder("FullZoo")
    major_order = [
        "Floors",
        "Walls",
        "Ceilings",
        "Structural/Pillars",
        "Structural/CorridorArches",
        "Structural/Platforms",
        "Structural/Walkways",
        "Structural/Railings",
        "Structural/Stairs",
        "Doors",
        "Windows",
        "Mechanical",
        "Props",
        "Lights",
        "ScreensAndControls",
        "Signs",
        "HeroSpecialized/Bridge",
        "HeroSpecialized/Crew",
        "HeroSpecialized/Hangar",
        "HeroSpecialized/Hydroponics",
        "HeroSpecialized/Lift",
        "HeroSpecialized/MedicalResearch",
        "HeroSpecialized/Security",
    ]
    total_depth = 60 + sum(max(22, math.ceil(len(categories.get(cat, [])) / (4 if cat.startswith("HeroSpecialized") else 6)) * (12 if cat.startswith("HeroSpecialized") else 9) + 13) for cat in major_order)
    add_common_roots(scene, "FullZoo", (-8, 1.05, -10), (92, 0.12, total_depth))
    scene.node("Catalog", "Node3D", "FullZoo")
    scene.node("Structural", "Node3D", "FullZoo/Catalog")
    scene.node("HeroSpecialized", "Node3D", "FullZoo/Catalog")
    scene.node("ReferenceArea", "Node3D", "FullZoo", props={"position": vector3(72, 0, 2)})
    scene.label("ReferenceArea_Label", "FullZoo/ReferenceArea", "ReferenceArea: 5m module checks", (0, 3.3, -4), 64)

    z = 0.0
    for category in major_order:
        paths = categories.get(category, [])
        if not paths:
            continue
        z += add_catalog_section(scene, "FullZoo", "FullZoo/Catalog", category, paths, z)

    def p(name: str) -> Path:
        matches = [path for paths in categories.values() for path in paths if path.stem == name]
        return matches[0]

    refs = [
        ("RefFloor5m", "SM_Bld_Floor_011", (0, 0, 0), None),
        ("RefWall5m", "SM_Bld_Wall_01_Alt", (0, 0, 0), None),
        ("RefCeiling5m", "SM_Bld_Ceiling_03", (0, 3.8, 0), None),
        ("RefSingleArch", "SM_Bld_Corridor_Single_Arch_01", (8, 0, 0), None),
        ("RefDoubleArch", "SM_Bld_Corridor_Double_Arch_01", (18, 0, 0), None),
    ]
    for _, asset_name, pos, rot in refs:
        try:
            scene.asset("FullZoo/ReferenceArea", p(asset_name), pos, rot)
        except IndexError:
            pass
    scene.node(
        "HumanScaleCapsule",
        "CSGCylinder3D",
        "FullZoo/ReferenceArea",
        props={
            "position": vector3(30, 0.9, 0),
            "height": "1.8",
            "radius": "0.28",
            "material": 'SubResource("ReferenceMat")',
        },
    )
    scene.label("HumanScaleLabel", "FullZoo/ReferenceArea", "1.8m scale", (30, 2.15, 1.8), 36)
    return scene.finish()


def ops_candidates(categories: dict[str, list[Path]]) -> dict[str, list[Path]]:
    all_paths = [path for paths in categories.values() for path in paths]

    def by_names(names: list[str]) -> list[Path]:
        wanted = set(names)
        return [p for p in all_paths if p.stem in wanted]

    return {
        "Floors": by_names([f"SM_Bld_Floor_{n:02d}" for n in range(1, 10)] + ["SM_Bld_Floor_010", "SM_Bld_Floor_011"]),
        "Walls": by_names(["SM_Bld_Wall_01", "SM_Bld_Wall_01_Alt", "SM_Bld_Wall_02", "SM_Bld_Wall_03", "SM_Bld_Wall_04", "SM_Bld_Wall_04_Alt", "SM_Bld_Wall_05", "SM_Bld_Wall_06"]),
        "Ceilings": by_names(["SM_Bld_Ceiling_01", "SM_Bld_Ceiling_02", "SM_Bld_Ceiling_03"]),
        "Structural": by_names([
            "SM_Bld_Corridor_Single_Arch_01", "SM_Bld_Corridor_Single_Arch_02", "SM_Bld_Corridor_Single_Arch_03",
            "SM_Bld_Corridor_Double_Arch_01", "SM_Bld_Corridor_Double_Arch_02",
            "SM_Bld_Wall_Pillar_01", "SM_Bld_Wall_Pillar_02", "SM_Bld_Wall_Pillar_03", "SM_Bld_Wall_Pillar_04",
            "SM_Bld_Wall_Corner_Pillar_01", "SM_Bld_Wall_Corner_Pillar_02", "SM_Bld_Wall_Corner_Pillar_Wide_01", "SM_Bld_Wall_Corner_Pillar_Wide_02",
        ]),
        "Doors": by_names([
            "SM_Bld_Wall_Door_01", "SM_Bld_Wall_Door_02", "SM_Bld_Wall_Door_06",
            "SM_Bld_Wall_Doorframe_01", "SM_Bld_Wall_Doorframe_02", "SM_Bld_Wall_Doorframe_03",
            "SM_Bld_Wall_Doorframe_04", "SM_Bld_Wall_Doorframe_05", "SM_Bld_Wall_Doorframe_06",
            "SM_Bld_Wall_Doorframe_Outer_01", "SM_Bld_Wall_Doorframe_Outer_02",
        ]),
        "Lights": by_names([f"SM_Prop_Light_Panel_{n:02d}" for n in range(1, 6)] + [f"SM_Prop_Light_Small_{n:02d}" for n in range(1, 9)]),
        "Props": by_names([
            "SM_Prop_ControllPanel_01", "SM_Prop_ControllPanel_02", "SM_Prop_ControllPanel_03", "SM_Prop_ControllPanel_04",
            "SM_Prop_MapTable_01", "SM_Prop_Radar_Panel_01", "SM_Prop_Radar_Panel_02",
            "SM_Prop_Screen_01", "SM_Prop_Screen_02", "SM_Prop_Screen_06", "SM_Prop_Screen_08",
            "SM_Prop_AirVent_Large_01", "SM_Prop_AirVent_Small_01", "SM_Prop_Detail_Airvent_01",
            "SM_Sign_Bridge_01", "SM_Sign_Exit_02", "SM_SignBorder_Communication_01", "SM_SignBorder_Warning_01",
            "SM_Prop_Crate_01", "SM_Prop_Crate_02",
        ]),
    }


def add_ops_diorama(scene: SceneBuilder, root: str, name: str, origin: tuple[float, float, float], wide: bool = False, room: bool = False) -> None:
    parent = f"{root}/Dioramas/{name}"
    scene.node(name, "Node3D", f"{root}/Dioramas", props={"position": vector3(*origin)})
    scene.label(f"{name}_Label", parent, name, (-2, 3.6, -4), 66)
    for child in ["Architecture", "Props", "PoweredLighting", "EmergencyLighting", "FX"]:
        props = {"visible": "false"} if child == "EmergencyLighting" else None
        scene.node(child, "Node3D", parent, props=props)

    def asset(parent_suffix: str, asset_path: str, pos: tuple[float, float, float], rot: float | None = None) -> None:
        scene.asset(f"{parent}/{parent_suffix}", ROOT / asset_path, pos, rot)

    floor = "assets/geometry/floors/SM_Bld_Floor_011.glb"
    wall = "assets/geometry/walls/SM_Bld_Wall_01_Alt.glb"
    wall_detail = "assets/geometry/walls/SM_Bld_Wall_02.glb"
    ceiling = "assets/geometry/ceilings/SM_Bld_Ceiling_03.glb"
    light_panel = "assets/geometry/lights/SM_Prop_Light_Panel_01.glb"

    width_tiles = 2 if wide or room else 1
    length_tiles = 2 if room else 3
    for x in range(width_tiles):
        for z in range(length_tiles):
            asset("Architecture", floor, (x * 5, 0, z * 5))
            asset("Architecture", ceiling, (x * 5, 3.8, z * 5))

    if room:
        for x in range(2):
            asset("Architecture", wall, (x * 5, 0, 0), 0)
            asset("Architecture", wall_detail, (x * 5 + 5, 0, 10), math.pi)
        for z in range(2):
            asset("Architecture", wall_detail, (0, 0, z * 5 + 5), math.pi / 2)
            asset("Architecture", wall, (10, 0, z * 5), -math.pi / 2)
        asset("Architecture", "assets/geometry/doors/SM_Bld_Wall_Doorframe_02.glb", (5, 0, 0))
        for pos in [(2.5, 3.25, 2.5), (7.5, 3.25, 7.5)]:
            asset("PoweredLighting", light_panel, pos)
        asset("Props", "assets/geometry/controls/SM_Prop_ControllPanel_01.glb", (2.5, 0, 8.2), math.pi)
        asset("Props", "assets/geometry/controls/SM_Prop_MapTable_01.glb", (6.8, 0, 5.2))
        asset("Props", "assets/geometry/signs/SM_Sign_Bridge_01.glb", (8.8, 1.6, 0.2))
    else:
        for z in range(length_tiles):
            asset("Architecture", wall if z % 2 == 0 else wall_detail, (0, 0, z * 5 + 5), math.pi / 2)
            asset("Architecture", wall_detail if z % 2 == 0 else wall, (width_tiles * 5, 0, z * 5), -math.pi / 2)
            if wide:
                asset("Architecture", "assets/geometry/corridor/SM_Bld_Corridor_Double_Arch_01.glb", (0, 0, z * 5))
            else:
                asset("Architecture", "assets/geometry/corridor/SM_Bld_Corridor_Single_Arch_01.glb", (0, 0, z * 5))
            asset("PoweredLighting", light_panel, (2.5 if not wide else 5, 3.2, z * 5 + 2.5))
        asset("Props", "assets/geometry/vents/SM_Prop_AirVent_Large_01.glb", (width_tiles * 5 - 0.25, 1.6, 6.5), -math.pi / 2)
        asset("Props", "assets/geometry/signs/SM_Sign_Exit_02.glb", (0.2, 1.8, 11.2), math.pi / 2)
    scene.node("PoweredFill", "OmniLight3D", f"{parent}/PoweredLighting", props={"position": vector3(5 if wide or room else 2.5, 3.0, 7.5), "light_color": color(0.58, 0.78, 1.0), "light_energy": "2.2", "omni_range": "9.0", "shadow_enabled": "true"})
    scene.node("EmergencyRed", "OmniLight3D", f"{parent}/EmergencyLighting", props={"position": vector3(5 if wide or room else 2.5, 2.8, 7.5), "light_color": color(1.0, 0.18, 0.10), "light_energy": "1.3", "omni_range": "8.0"})


def ops_zoo(categories: dict[str, list[Path]]) -> str:
    scene = SceneBuilder("OpsZoo")
    add_common_roots(scene, "OpsZoo", (-8, 1.05, -10), (150, 0.12, 135))
    scene.node("Candidates", "Node3D", "OpsZoo")
    scene.node("Dioramas", "Node3D", "OpsZoo")
    scene.node("StateTesting", "Node3D", "OpsZoo", props={"position": vector3(0, 0, 92)})
    scene.label("StateTestingLabel", "OpsZoo/StateTesting", "StateTesting scaffold: Powered / Emergency / Unpowered", (0, 3, 0), 54)

    z = 0.0
    for category, paths in ops_candidates(categories).items():
        z += add_catalog_section(scene, "OpsZoo", "OpsZoo/Candidates", category, paths, z)

    add_ops_diorama(scene, "OpsZoo", "StandardCorridor", (80, 0, 0), wide=False, room=False)
    add_ops_diorama(scene, "OpsZoo", "MainCorridor", (80, 0, 32), wide=True, room=False)
    add_ops_diorama(scene, "OpsZoo", "StandardRoom", (80, 0, 68), wide=False, room=True)
    return scene.finish()


def write_outputs() -> None:
    categories, excluded = collect_catalog()
    ZOO_DIR.mkdir(parents=True, exist_ok=True)
    BIOME_DIR.mkdir(parents=True, exist_ok=True)
    (ZOO_DIR / "full_zoo.tscn").write_text(full_zoo(categories), encoding="utf-8")
    (BIOME_DIR / "ops_zoo.tscn").write_text(ops_zoo(categories), encoding="utf-8")
    shutil.copy2(Path(__file__), ZOO_DIR / "generate_asset_zoo.py")

    major_counts: dict[str, int] = {}
    for category, paths in categories.items():
        major = category.split("/", 1)[0]
        major_counts[major] = major_counts.get(major, 0) + len(paths)
    manifest = {
        "source_asset_root": "res://assets/geometry/",
        "source_blend": "res://assets/.blender/synty_space_library.blend",
        "included_total": sum(len(paths) for paths in categories.values()),
        "major_counts": dict(sorted(major_counts.items())),
        "categories": {cat: [res_path(p) for p in paths] for cat, paths in sorted(categories.items())},
        "ops_candidates": {cat: [res_path(p) for p in paths] for cat, paths in ops_candidates(categories).items()},
        "excluded_or_manual_review": excluded,
    }
    (ZOO_DIR / "asset_zoo_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"included_total": manifest["included_total"], "major_counts": manifest["major_counts"], "excluded_groups": {k: len(v) for k, v in excluded.items()}}, indent=2))


if __name__ == "__main__":
    write_outputs()
