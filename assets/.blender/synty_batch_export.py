"""Export allowlisted objects from synty_space_library.blend as Godot GLBs.

Every mesh linked beneath EXPORT is written as an individual GLB under
``assets/geometry/<collection path>``. Canonical Blender preview
materials are temporarily replaced with textureless placeholder materials so
Godot can remap every imported surface to shared external material resources.
"""

from pathlib import Path
import bpy


EXPORT_ROOT_NAME = "EXPORT"
OUTPUT_ROOT = Path(bpy.path.abspath("//../geometry"))

MATERIAL_PLACEHOLDERS = {
    "M_SyntySpace_Opaque_A": "M_SyntySpace_External",
    "M_SyntySpace_Glass": "M_SyntySpace_Glass_External",
    "M_SyntySpace_Sign_B": "M_SyntySpace_Sign_External",
}


def descendant_collections(collection):
    for child in collection.children:
        yield child
        yield from descendant_collections(child)


def collection_path_from_root(collection, root):
    path_parts = [collection.name]
    current = collection
    while current != root:
        parents = [candidate for candidate in bpy.data.collections if current.name in candidate.children]
        if not parents:
            raise RuntimeError(f"Collection '{collection.name}' is not beneath '{root.name}'.")
        current = parents[0]
        if current != root:
            path_parts.append(current.name)
    return list(reversed(path_parts))


def placeholder_for(material):
    placeholder_name = MATERIAL_PLACEHOLDERS.get(material.name)
    if placeholder_name is None:
        raise RuntimeError(f"No Godot placeholder mapping for material '{material.name}'.")
    placeholder = bpy.data.materials.get(placeholder_name)
    if placeholder is None:
        placeholder = bpy.data.materials.new(placeholder_name)
        placeholder.use_nodes = False
    return placeholder


def export_object(obj, collection, root):
    output_directory = OUTPUT_ROOT.joinpath(*collection_path_from_root(collection, root))
    output_directory.mkdir(parents=True, exist_ok=True)
    output_file = output_directory / f"{obj.name}.glb"

    original_materials = list(obj.data.materials)
    original_scene_name = bpy.context.scene.name
    if not original_materials:
        raise RuntimeError(f"Export mesh '{obj.name}' has no material slots.")

    bpy.ops.object.select_all(action="DESELECT")
    was_hidden = obj.hide_get()
    try:
        # Godot uses the glTF scene name as the instantiated PackedScene root.
        # Give every exported file its asset name instead of inheriting the
        # master Blender library's scene name.
        bpy.context.scene.name = obj.name
        obj.hide_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.data.materials.clear()
        for material in original_materials:
            obj.data.materials.append(placeholder_for(material))

        bpy.ops.export_scene.gltf(
            filepath=str(output_file),
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_texcoords=True,
            export_normals=True,
            export_tangents=False,
            export_materials="EXPORT",
            export_cameras=False,
            export_lights=False,
            export_animations=False,
            export_extras=False,
            export_yup=True,
        )
    finally:
        bpy.context.scene.name = original_scene_name
        obj.data.materials.clear()
        for material in original_materials:
            obj.data.materials.append(material)
        obj.hide_set(was_hidden)

    print(f"EXPORTED: {obj.name} -> {output_file}")


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Save the Blender library before exporting.")
    root = bpy.data.collections.get(EXPORT_ROOT_NAME)
    if root is None:
        raise RuntimeError(f"Collection '{EXPORT_ROOT_NAME}' does not exist.")

    exported = set()
    for collection in descendant_collections(root):
        for obj in collection.objects:
            if obj.type != "MESH" or obj.name in exported:
                continue
            export_object(obj, collection, root)
            exported.add(obj.name)
    print(f"DONE: Exported {len(exported)} GLB(s) to {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
