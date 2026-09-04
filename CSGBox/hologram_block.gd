@tool
class_name HologramBlock
extends CSGBox3D

const FILL_SHADER := preload("res://CSGBox/hologram_fill.gdshader")
const EDGE_SHADER := preload("res://CSGBox/hologram_edge.gdshader")
const EDGE_COUNT := 12

@export_category("Hologram")
@export var box_size: Vector3 = Vector3.ONE:
	set(value):
		box_size = Vector3(
			maxf(value.x, 0.001),
			maxf(value.y, 0.001),
			maxf(value.z, 0.001)
		)
		if is_inside_tree():
			size = box_size
		_request_update()

@export var tint: Color = Color(0.1, 0.8, 1.0, 1.0):
	set(value):
		tint = value
		_request_update()

@export_range(0.0, 1.0, 0.001) var fill_alpha := 0.04:
	set(value):
		fill_alpha = clampf(value, 0.0, 1.0)
		_request_update()

@export_range(0.001, 1.0, 0.001, "or_greater") var edge_thickness := 0.12:
	set(value):
		edge_thickness = maxf(value, 0.001)
		_request_update()

@export_range(0.0, 1.0, 0.001) var edge_alpha := 0.9:
	set(value):
		edge_alpha = clampf(value, 0.0, 1.0)
		_request_update()

@export_range(0.0, 5.0, 0.01, "or_greater") var edge_emission := 1.5:
	set(value):
		edge_emission = maxf(value, 0.0)
		_request_update()

@export_range(0.0, 1.0, 0.001) var fresnel_strength := 0.08:
	set(value):
		fresnel_strength = clampf(value, 0.0, 1.0)
		_request_update()

var _edges_root: Node3D
var _edges: Array[MeshInstance3D] = []
var _fill_material: ShaderMaterial
var _edge_material: ShaderMaterial
var _update_pending := false


func _ready() -> void:
	use_collision = true
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_ensure_geometry()
	_apply_properties()
	set_process(true)


func _process(_delta: float) -> void:
	# The inherited CSG size is changed by the viewport resize handles. Polling it
	# keeps the exported hologram size and edge frame in sync without rebuilding.
	if not size.is_equal_approx(box_size):
		box_size = size


func _request_update() -> void:
	if not is_inside_tree() or _update_pending:
		return
	_update_pending = true
	call_deferred("_apply_properties")


func _ensure_geometry() -> void:
	if material is ShaderMaterial and (material as ShaderMaterial).shader == FILL_SHADER:
		_fill_material = material as ShaderMaterial
	else:
		_fill_material = ShaderMaterial.new()
		_fill_material.shader = FILL_SHADER
		_fill_material.render_priority = -1
		material = _fill_material

	_edges_root = get_node_or_null("Edges") as Node3D
	if _edges_root == null:
		_edges_root = Node3D.new()
		_edges_root.name = "Edges"
		add_child(_edges_root, false, Node.INTERNAL_MODE_BACK)

	_edges.clear()
	for index in EDGE_COUNT:
		var edge_name := "Edge%02d" % (index + 1)
		var edge := _edges_root.get_node_or_null(edge_name) as MeshInstance3D
		if edge == null:
			edge = MeshInstance3D.new()
			edge.name = edge_name
			edge.mesh = BoxMesh.new()
			edge.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_edges_root.add_child(edge, false, Node.INTERNAL_MODE_BACK)
		_edges.append(edge)

	if not _edges.is_empty() and _edges[0].material_override is ShaderMaterial:
		var existing_material := _edges[0].material_override as ShaderMaterial
		if existing_material.shader == EDGE_SHADER:
			_edge_material = existing_material

	if _edge_material == null:
		_edge_material = ShaderMaterial.new()
		_edge_material.shader = EDGE_SHADER
		_edge_material.render_priority = 1

	for edge in _edges:
		edge.material_override = _edge_material


func _apply_properties() -> void:
	_update_pending = false
	if not is_inside_tree():
		return

	_ensure_geometry()
	size = box_size
	_fill_material.set_shader_parameter("tint", tint)
	_fill_material.set_shader_parameter("fill_alpha", fill_alpha)
	_fill_material.set_shader_parameter("fresnel_strength", fresnel_strength)

	_edge_material.set_shader_parameter("tint", tint)
	_edge_material.set_shader_parameter("edge_alpha", edge_alpha)
	_edge_material.set_shader_parameter("emission_strength", edge_emission)

	var half_size := box_size * 0.5
	var thickness := edge_thickness
	var edge_sizes: Array[Vector3] = [
		Vector3(box_size.x, thickness, thickness),
		Vector3(box_size.x, thickness, thickness),
		Vector3(box_size.x, thickness, thickness),
		Vector3(box_size.x, thickness, thickness),
		Vector3(thickness, box_size.y, thickness),
		Vector3(thickness, box_size.y, thickness),
		Vector3(thickness, box_size.y, thickness),
		Vector3(thickness, box_size.y, thickness),
		Vector3(thickness, thickness, box_size.z),
		Vector3(thickness, thickness, box_size.z),
		Vector3(thickness, thickness, box_size.z),
		Vector3(thickness, thickness, box_size.z),
	]
	var edge_positions: Array[Vector3] = [
		Vector3(0.0, half_size.y, half_size.z),
		Vector3(0.0, half_size.y, -half_size.z),
		Vector3(0.0, -half_size.y, half_size.z),
		Vector3(0.0, -half_size.y, -half_size.z),
		Vector3(half_size.x, 0.0, half_size.z),
		Vector3(half_size.x, 0.0, -half_size.z),
		Vector3(-half_size.x, 0.0, half_size.z),
		Vector3(-half_size.x, 0.0, -half_size.z),
		Vector3(half_size.x, half_size.y, 0.0),
		Vector3(half_size.x, -half_size.y, 0.0),
		Vector3(-half_size.x, half_size.y, 0.0),
		Vector3(-half_size.x, -half_size.y, 0.0),
	]

	for index in EDGE_COUNT:
		(_edges[index].mesh as BoxMesh).size = edge_sizes[index]
		_edges[index].position = edge_positions[index]
