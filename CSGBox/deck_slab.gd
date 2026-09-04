@tool
class_name DeckSlab
extends CSGBox3D

const FILL_MATERIAL := preload("res://CSGBox/deck_slab_material.tres")
const EDGE_MATERIAL := preload("res://CSGBox/deck_edge_material.tres")
const EDGE_COUNT := 4

@export_category("Deck Slab")
@export var slab_size: Vector2 = Vector2.ONE:
	set(value):
		slab_size = Vector2(maxf(value.x, 0.001), maxf(value.y, 0.001))
		_request_update()

@export_range(0.01, 1.0, 0.01) var slab_thickness := 0.12:
	set(value):
		slab_thickness = maxf(value, 0.01)
		_request_update()

@export_range(0.01, 0.5, 0.01) var edge_thickness := 0.09:
	set(value):
		edge_thickness = maxf(value, 0.01)
		_request_update()

var _edges_root: Node3D
var _edges: Array[MeshInstance3D] = []
var _update_pending := false


func _ready() -> void:
	use_collision = true
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_ensure_edges()
	_apply_properties()
	set_process(true)


func _process(_delta: float) -> void:
	var expected_size := Vector3(slab_size.x, slab_thickness, slab_size.y)
	if not size.is_equal_approx(expected_size):
		slab_size = Vector2(size.x, size.z)
		slab_thickness = size.y


func _request_update() -> void:
	if not is_inside_tree() or _update_pending:
		return
	_update_pending = true
	call_deferred("_apply_properties")


func _ensure_edges() -> void:
	_edges_root = get_node_or_null("PerimeterEdges") as Node3D
	if _edges_root == null:
		_edges_root = Node3D.new()
		_edges_root.name = "PerimeterEdges"
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
		edge.material_override = EDGE_MATERIAL
		_edges.append(edge)


func _apply_properties() -> void:
	_update_pending = false
	if not is_inside_tree():
		return

	_ensure_edges()
	size = Vector3(slab_size.x, slab_thickness, slab_size.y)
	material = FILL_MATERIAL

	var half_size := slab_size * 0.5
	var half_edge := edge_thickness * 0.5
	var edge_y := slab_thickness * 0.5
	var edge_sizes: Array[Vector3] = [
		Vector3(slab_size.x, edge_thickness, edge_thickness),
		Vector3(slab_size.x, edge_thickness, edge_thickness),
		Vector3(edge_thickness, edge_thickness, slab_size.y),
		Vector3(edge_thickness, edge_thickness, slab_size.y),
	]
	var edge_positions: Array[Vector3] = [
		Vector3(0.0, edge_y, half_size.y - half_edge),
		Vector3(0.0, edge_y, -half_size.y + half_edge),
		Vector3(half_size.x - half_edge, edge_y, 0.0),
		Vector3(-half_size.x + half_edge, edge_y, 0.0),
	]

	for index in EDGE_COUNT:
		(_edges[index].mesh as BoxMesh).size = edge_sizes[index]
		_edges[index].position = edge_positions[index]
