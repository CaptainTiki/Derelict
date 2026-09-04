extends Node3D

const WALK_SPEED := 2.0
const FAST_SPEED := 4.0
const MOUSE_SENSITIVITY := 0.0025
const MAX_PITCH := deg_to_rad(89.0)

@onready var _camera: Camera3D = $WalkthroughCamera
@onready var _start_marker: Marker3D = $"../Start_Hangar"
@onready var _readout: Label = $"../WalkthroughHUD/Panel/Readout"
@onready var _split_readout: Label = $"../WalkthroughHUD/Panel/SplitReadout"

var _elapsed := 0.0
var _distance := 0.0
var _timer_started := false
var _pitch := 0.0
var _fly_mode := true


func _ready() -> void:
	_camera.make_current()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_reset_walkthrough()


func _process(delta: float) -> void:
	var input_2d := Input.get_vector("strafe_left", "strafe_right", "forward", "backward")
	var camera_basis := _camera.global_transform.basis
	var right := camera_basis.x
	var forward := -camera_basis.z

	if not _fly_mode:
		right.y = 0.0
		forward.y = 0.0
		right = right.normalized()
		forward = forward.normalized()

	var direction := right * input_2d.x + forward * -input_2d.y
	if _fly_mode:
		if Input.is_action_pressed("jump"):
			direction += Vector3.UP
		if Input.is_key_pressed(KEY_CTRL) or Input.is_key_pressed(KEY_C):
			direction += Vector3.DOWN

	var speed := FAST_SPEED if Input.is_action_pressed("sprint") else WALK_SPEED
	if direction.length_squared() > 0.0:
		var movement := direction.normalized() * speed * delta
		global_position += movement
		_distance += movement.length()
		_timer_started = true

	if _timer_started:
		_elapsed += delta

	_update_hud(speed)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * MOUSE_SENSITIVITY)
		_pitch = clampf(_pitch - event.relative.y * MOUSE_SENSITIVITY, -MAX_PITCH, MAX_PITCH)
		_camera.rotation.x = _pitch
		get_viewport().set_input_as_handled()
		return

	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			get_viewport().set_input_as_handled()
		return

	if event is not InputEventKey or not event.pressed or event.echo:
		return

	match event.keycode:
		KEY_ESCAPE:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		KEY_R:
			_reset_walkthrough()
		KEY_T:
			_record_split()
		KEY_F:
			_fly_mode = not _fly_mode
			print("WALKTHROUGH MODE: %s" % ("FLY" if _fly_mode else "PLANAR"))
		_:
			return
	get_viewport().set_input_as_handled()


func _reset_walkthrough() -> void:
	global_transform = _start_marker.global_transform
	_pitch = 0.0
	_camera.rotation = Vector3.ZERO
	_elapsed = 0.0
	_distance = 0.0
	_timer_started = false
	_split_readout.text = ""
	_update_hud(WALK_SPEED)


func _record_split() -> void:
	var time_text := _format_time(_elapsed)
	var split_text := "SPLIT\nTime: %s\nDistance: %.1f m" % [time_text, _distance]
	_split_readout.text = split_text
	print("SPLIT | Time: %s | Distance: %.1f m" % [time_text, _distance])


func _update_hud(speed: float) -> void:
	var mode_text := "FLY" if _fly_mode else "PLANAR"
	_readout.text = (
		"WALKTHROUGH\n"
		+ "Mode: %s\n" % mode_text
		+ "Speed: %.1f m/s\n" % speed
		+ "Elapsed: %s\n" % _format_time(_elapsed)
		+ "Distance: %.1f m\n\n" % _distance
		+ "Position:\n"
		+ "X %.1f\nY %.1f\nZ %.1f" % [global_position.x, global_position.y, global_position.z]
	)


func _format_time(seconds: float) -> String:
	var total_tenths := int(floor(seconds * 10.0))
	var minutes := total_tenths / 600
	var whole_seconds := (total_tenths / 10) % 60
	var tenths := total_tenths % 10
	return "%02d:%02d.%d" % [minutes, whole_seconds, tenths]
