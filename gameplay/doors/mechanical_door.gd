extends Node3D
class_name MechanicalDoor


const TriggerVolumeComponent = preload("res://gameplay/triggers/trigger_volume.gd")

enum DoorState {
	CLOSED,
	OPENING,
	OPEN,
	CLOSING,
}

signal state_changed(previous_state: DoorState, current_state: DoorState)
signal opening_started(source: Node)
signal opened()
signal closing_started(source: Node)
signal closed()
signal access_denied(source: Node)

@export var proximity_enabled: bool = false:
	set(value):
		proximity_enabled = value
		if is_node_ready():
			_apply_proximity_setting()
@export var starts_open: bool = false
@export var locked: bool = false
@export var auto_close_enabled: bool = false
@export_range(0.1, 30.0, 0.1) var auto_close_delay: float = 2.0
@export_range(0.1, 4.0, 0.1) var animation_speed: float = 1.0

@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var auto_close_timer: Timer = $AutoCloseTimer
@onready var proximity_trigger: TriggerVolumeComponent = $ProximityTrigger

var state: DoorState = DoorState.CLOSED


func _ready() -> void:
	animation_player.speed_scale = animation_speed
	auto_close_timer.wait_time = auto_close_delay
	_apply_proximity_setting()
	_apply_starting_state()


func request_open(source: Node = null) -> bool:
	if locked:
		access_denied.emit(source)
		return false
	if state == DoorState.OPEN or state == DoorState.OPENING:
		return false

	auto_close_timer.stop()
	var resume_position := -1.0
	if state == DoorState.CLOSING:
		resume_position = animation_player.current_animation_position
	_set_state(DoorState.OPENING)
	opening_started.emit(source)
	animation_player.play(&"open")
	if resume_position >= 0.0:
		animation_player.seek(resume_position, true)
	return true


func request_close(source: Node = null) -> bool:
	if state == DoorState.CLOSED or state == DoorState.CLOSING:
		return false

	auto_close_timer.stop()
	var resume_position := -1.0
	if state == DoorState.OPENING:
		resume_position = animation_player.current_animation_position
	_set_state(DoorState.CLOSING)
	closing_started.emit(source)
	animation_player.play_backwards(&"open")
	if resume_position >= 0.0:
		animation_player.seek(resume_position, true)
	return true


func request_toggle(source: Node = null) -> bool:
	if state == DoorState.CLOSED or state == DoorState.CLOSING:
		return request_open(source)
	return request_close(source)


func set_locked(value: bool) -> void:
	locked = value


func _apply_starting_state() -> void:
	animation_player.play(&"RESET")
	animation_player.advance(0.0)
	animation_player.stop()
	if starts_open:
		animation_player.play(&"open")
		animation_player.seek(animation_player.current_animation_length, true)
		animation_player.pause()
		state = DoorState.OPEN
	else:
		state = DoorState.CLOSED


func _apply_proximity_setting() -> void:
	proximity_trigger.trigger_enabled = proximity_enabled
	proximity_trigger.monitoring = proximity_enabled


func _set_state(next_state: DoorState) -> void:
	if state == next_state:
		return
	var previous_state := state
	state = next_state
	state_changed.emit(previous_state, state)


func _on_animation_finished(animation_name: StringName) -> void:
	if animation_name != &"open":
		return
	if state == DoorState.OPENING:
		_set_state(DoorState.OPEN)
		opened.emit()
		_schedule_auto_close_if_clear()
	elif state == DoorState.CLOSING:
		_set_state(DoorState.CLOSED)
		closed.emit()


func _on_proximity_triggered(body: Node3D) -> void:
	if proximity_enabled:
		request_open(body)


func _on_proximity_exited(_body: Node3D) -> void:
	if proximity_enabled and auto_close_enabled and state == DoorState.OPEN:
		auto_close_timer.start(auto_close_delay)


func _on_auto_close_timeout() -> void:
	if proximity_enabled and proximity_trigger.has_overlapping_bodies():
		return
	request_close(self)


func _schedule_auto_close_if_clear() -> void:
	if not auto_close_enabled:
		return
	if proximity_enabled and proximity_trigger.has_overlapping_bodies():
		return
	auto_close_timer.start(auto_close_delay)
