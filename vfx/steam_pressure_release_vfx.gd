extends Node3D
class_name SteamPressureReleaseVFX


signal release_started(duration: float)
signal release_finished()
signal active_changed(is_active: bool)

@export_category("Scheduling")
@export var active: bool = true:
	set(value):
		if active == value:
			return
		active = value
		if is_node_ready():
			_apply_active_state()
		active_changed.emit(active)
@export_range(0.05, 120.0, 0.05, "or_greater") var interval_min: float = 3.0
@export_range(0.05, 120.0, 0.05, "or_greater") var interval_max: float = 8.0
@export_range(0.05, 60.0, 0.05, "or_greater") var duration_min: float = 1.2
@export_range(0.05, 60.0, 0.05, "or_greater") var duration_max: float = 3.5

@export_category("Steam")
@export_range(1, 512, 1, "or_greater") var steam_amount: int = 48:
	set(value):
		steam_amount = value
		if is_node_ready():
			particles.amount = steam_amount

@export_category("Audio")
@export var release_sounds: Array[AudioStream] = []
@export_range(0.5, 2.0, 0.01) var pitch_min: float = 0.92
@export_range(0.5, 2.0, 0.01) var pitch_max: float = 1.08

@onready var particles: GPUParticles3D = $Steam
@onready var audio_player: AudioStreamPlayer3D = $ReleaseAudio
@onready var interval_timer: Timer = $IntervalTimer
@onready var duration_timer: Timer = $DurationTimer

var is_releasing: bool = false
var _random := RandomNumberGenerator.new()


func _ready() -> void:
	_random.randomize()
	particles.amount = steam_amount
	_apply_active_state()


func set_active(value: bool) -> void:
	active = value


func start_release(duration: float = -1.0) -> void:
	if not is_inside_tree():
		return

	interval_timer.stop()
	var release_duration := duration
	if release_duration <= 0.0:
		release_duration = _random.randf_range(
			minf(duration_min, duration_max),
			maxf(duration_min, duration_max)
		)

	is_releasing = true
	particles.amount = steam_amount
	particles.restart()
	particles.emitting = true
	duration_timer.start(release_duration)
	_play_release_sound()
	release_started.emit(release_duration)


func stop_release(schedule_next: bool = true) -> void:
	duration_timer.stop()
	particles.emitting = false
	audio_player.stop()

	var was_releasing := is_releasing
	is_releasing = false
	if was_releasing:
		release_finished.emit()
	if schedule_next and active:
		_schedule_next_release()


func _apply_active_state() -> void:
	interval_timer.stop()
	duration_timer.stop()
	if active:
		_schedule_next_release()
	else:
		stop_release(false)


func _schedule_next_release() -> void:
	if not active or is_releasing:
		return
	interval_timer.start(_random.randf_range(
		minf(interval_min, interval_max),
		maxf(interval_min, interval_max)
	))


func _play_release_sound() -> void:
	if not release_sounds.is_empty():
		var selected_sound := release_sounds[_random.randi_range(0, release_sounds.size() - 1)]
		if is_instance_valid(selected_sound):
			audio_player.stream = selected_sound
	if audio_player.stream == null:
		return

	audio_player.pitch_scale = _random.randf_range(
		minf(pitch_min, pitch_max),
		maxf(pitch_min, pitch_max)
	)
	audio_player.stop()
	audio_player.play()


func _on_interval_timer_timeout() -> void:
	if active:
		start_release()


func _on_duration_timer_timeout() -> void:
	stop_release(true)


func _on_release_audio_finished() -> void:
	if is_releasing and audio_player.stream != null:
		audio_player.play()
