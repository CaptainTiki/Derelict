"""Render the interior-facing side of all 5x5 ceiling candidates."""

import math

import bpy


OUTPUT = r"C:\Users\John\.codex\visualizations\2026\08\23\01a03082-bfae-7041-81f2-e4e6af7361e1\ceiling_audition.png"
CEILINGS = [
    "SM_Bld_Ceiling_01",
    "SM_Bld_Ceiling_02",
    "SM_Bld_Ceiling_03",
    "SM_Bld_Roof_Exterior_01",
    "SM_Bld_Roof_Exterior_02",
    "SM_Bld_Roof_Exterior_03",
]

scene = bpy.context.scene
for obj in bpy.data.objects:
    obj.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUTPUT

world = bpy.data.worlds.new("Ceiling Audition World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.color = (0.025, 0.025, 0.025)

# The assets' room-facing surfaces sit at Z=4. Look upward from inside the room.
camera_data = bpy.data.cameras.new("Ceiling Audition Camera")
camera = bpy.data.objects.new("Ceiling Audition Camera", camera_data)
scene.collection.objects.link(camera)
camera.hide_render = False
camera.location = (9.5, -6.0, -10.0)
camera.rotation_euler.x = math.pi
camera_data.type = "ORTHO"
camera_data.ortho_scale = 16.0
scene.camera = camera

light_data = bpy.data.lights.new("Ceiling Audition Light", "AREA")
light_data.energy = 4500.0
light_data.shape = "RECTANGLE"
light_data.size = 24.0
light_data.size_y = 18.0
light = bpy.data.objects.new("Ceiling Audition Light", light_data)
scene.collection.objects.link(light)
light.hide_render = False
light.location = (9.5, -6.0, 1.5)
light.rotation_euler.x = math.pi

label_material = bpy.data.materials.new("Ceiling Label")
label_material.use_nodes = True
label_shader = label_material.node_tree.nodes.get("Principled BSDF")
label_shader.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
label_shader.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
label_shader.inputs["Emission Strength"].default_value = 2.0

for index, name in enumerate(CEILINGS):
    column = index % 3
    row = index // 3
    offset_x = column * 7.0
    offset_y = -row * 7.0

    source = bpy.data.objects[name]
    copy = source.copy()
    copy.data = source.data
    copy.hide_render = False
    scene.collection.objects.link(copy)
    copy.location.x += offset_x
    copy.location.y += offset_y

    curve = bpy.data.curves.new(f"Label {name}", "FONT")
    curve.body = name.replace("SM_Bld_Roof_Exterior_", "Roof ").replace("SM_Bld_Ceiling_", "Ceiling ")
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 0.48
    curve.materials.append(label_material)
    label = bpy.data.objects.new(f"Label {name}", curve)
    scene.collection.objects.link(label)
    label.hide_render = False
    label.location = (offset_x + 2.5, offset_y - 4.35, 3.65)
    label.rotation_euler.x = math.pi

bpy.ops.render.render(write_still=True)
print(f"RENDERED: {OUTPUT}")
