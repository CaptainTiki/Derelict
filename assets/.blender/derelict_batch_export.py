"""Batch-export a modular Blender asset library to individual Godot GLBs.

Collection convention:

    EXPORT
    ├── geometry
    │   └── ceilings
    │       ├── Ceiling_A     -> assets/geometry/ceilings/Ceiling_A.glb
    │       └── Ceiling_B     -> assets/geometry/ceilings/Ceiling_B.glb
    └── props
        ├── Box               -> assets/props/Box.glb
        └── AirCylinder       -> assets/props/AirCylinder.glb

Every collection beneath EXPORT becomes an output folder. Every mesh object
inside those collections is exported as its own GLB, using the object name as
the filename.

The script assumes MeshLibrary.blend is stored in assets/.blender/. Output is
therefore written one directory above the .blend file, into assets/.
"""

from pathlib import Path
import bpy


EXPORT_ROOT_NAME = "EXPORT"
PLACEHOLDER_MATERIAL_NAME = "M_PixPal_External"

# MeshLibrary.blend lives in assets/.blender, so ".." resolves to assets.
OUTPUT_ROOT = Path(bpy.path.abspath("//.."))


def descendant_collections(collection):
    """Yield every collection beneath collection."""
    for child in collection.children:
        yield child
        yield from descendant_collections(child)


def collection_path_from_root(collection, root):
    """Return the collection-name path between root and collection."""
    path_parts = [collection.name]
    current = collection

    while current != root:
        parents = [candidate for candidate in bpy.data.collections
                   if current.name in candidate.children]

        if not parents:
            raise RuntimeError(
                f"Collection '{collection.name}' is not beneath '{root.name}'."
            )

        current = parents[0]
        if current != root:
            path_parts.append(current.name)

    return list(reversed(path_parts))


def export_object(obj, collection, root):
    relative_parts = collection_path_from_root(collection, root)
    output_directory = OUTPUT_ROOT.joinpath(*relative_parts)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_file = output_directory / f"{obj.name}.glb"

    bpy.ops.object.select_all(action="DESELECT")
    was_hidden = obj.hide_get()
    original_materials = list(obj.data.materials)

    placeholder = bpy.data.materials.get(PLACEHOLDER_MATERIAL_NAME)
    if placeholder is None:
        placeholder = bpy.data.materials.new(PLACEHOLDER_MATERIAL_NAME)
        placeholder.use_nodes = False

    try:
        obj.hide_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # A real, textureless material is required so Godot receives surface 0
        # and can remap it to the shared external M_PixPal material. Blender's
        # PLACEHOLDER mode omits the material slot entirely in current builds.
        obj.data.materials.clear()
        obj.data.materials.append(placeholder)

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
        obj.data.materials.clear()
        for material in original_materials:
            obj.data.materials.append(material)
        obj.hide_set(was_hidden)

    print(f"EXPORTED: {obj.name} -> {output_file}")
    return True


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Save the Blender file before exporting.")

    root = bpy.data.collections.get(EXPORT_ROOT_NAME)
    if root is None:
        raise RuntimeError(
            f"Create a collection named '{EXPORT_ROOT_NAME}' and place the "
            "export hierarchy inside it."
        )

    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    previously_selected = list(bpy.context.selected_objects)
    previously_active = bpy.context.view_layer.objects.active

    exported = 0
    try:
        already_exported = set()
        for collection in descendant_collections(root):
            for obj in collection.objects:
                if obj.type != "MESH" or obj.name in already_exported:
                    continue
                exported += int(export_object(obj, collection, root))
                already_exported.add(obj.name)
    finally:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in previously_selected:
            if obj.name in bpy.context.view_layer.objects:
                obj.select_set(True)
        if previously_active and previously_active.name in bpy.context.view_layer.objects:
            bpy.context.view_layer.objects.active = previously_active

    print(f"DONE: Exported {exported} asset(s) to {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
