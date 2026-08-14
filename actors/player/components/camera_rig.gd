extends Node3D


@export_range(0.01, 1.0, 0.01) var mouse_sensitivity: float = 0.1
@export_range(-89.0, 0.0, 1.0) var minimum_pitch_degrees: float = -80.0
@export_range(0.0, 89.0, 1.0) var maximum_pitch_degrees: float = 80.0
@export var capture_mouse_on_ready: bool = true

@onready var player: Node3D = get_parent()


func _ready() -> void:
	if capture_mouse_on_ready:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_rotate_from_mouse(event.relative)
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif event is InputEventMouseButton and event.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _rotate_from_mouse(mouse_delta: Vector2) -> void:
	player.rotate_y(deg_to_rad(-mouse_delta.x * mouse_sensitivity))

	var pitch_delta := deg_to_rad(-mouse_delta.y * mouse_sensitivity)
	rotation.x = clampf(
		rotation.x + pitch_delta,
		deg_to_rad(minimum_pitch_degrees),
		deg_to_rad(maximum_pitch_degrees)
	)
