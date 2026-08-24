"""Render all full-size floor variants in a labeled comparison grid."""

import bpy


OUTPUT = r"C:\Users\John\.codex\visualizations\2026\08\23\01a03082-bfae-7041-81f2-e4e6af7361e1\floor_audition.png"
FLOORS = [
    "SM_Bld_Floor_01", "SM_Bld_Floor_02", "SM_Bld_Floor_03",
    "SM_Bld_Floor_04", "SM_Bld_Floor_05", "SM_Bld_Floor_06",
    "SM_Bld_Floor_07", "SM_Bld_Floor_08", "SM_Bld_Floor_09",
    "SM_Bld_Floor_010", "SM_Bld_Floor_011",
]

scene = bpy.context.scene
for obj in bpy.data.objects:
    obj.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUTPUT

world = bpy.data.worlds.new("Floor Audition World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.color = (0.025, 0.025, 0.025)

camera_data = bpy.data.cameras.new("Floor Audition Camera")
camera = bpy.data.objects.new("Floor Audition Camera", camera_data)
scene.collection.objects.link(camera)
camera.hide_render = False
camera.location = (12.5, -9.5, 40.0)
camera_data.type = "ORTHO"
camera_data.ortho_scale = 23.0
scene.camera = camera

light_data = bpy.data.lights.new("Floor Audition Light", "AREA")
light_data.energy = 5000.0
light_data.shape = "RECTANGLE"
light_data.size = 35.0
light_data.size_y = 25.0
light = bpy.data.objects.new("Floor Audition Light", light_data)
scene.collection.objects.link(light)
light.hide_render = False
light.location = (12.5, -9.5, 20.0)

label_material = bpy.data.materials.new("Floor Label")
label_material.use_nodes = True
label_shader = label_material.node_tree.nodes.get("Principled BSDF")
label_shader.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
label_shader.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
label_shader.inputs["Emission Strength"].default_value = 2.0

for index, name in enumerate(FLOORS):
    column = index % 4
    row = index // 4
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
    curve.body = name.replace("SM_Bld_Floor_", "")
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 0.7
    curve.materials.append(label_material)
    label = bpy.data.objects.new(f"Label {name}", curve)
    scene.collection.objects.link(label)
    label.hide_render = False
    label.location = (offset_x + 2.5, offset_y + 0.8, 0.3)

bpy.ops.render.render(write_still=True)
print(f"RENDERED: {OUTPUT}")
