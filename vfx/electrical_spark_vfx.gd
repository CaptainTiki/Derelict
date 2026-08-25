extends Node3D
class_name ElectricalSparkVFX


signal burst_started()
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
@export_range(0.05, 60.0, 0.05, "or_greater") var interval_min: float = 0.8
@export_range(0.05, 60.0, 0.05, "or_greater") var interval_max: float = 3.0

@export_category("Burst")
@export_range(1, 128, 1, "or_greater") var spark_count_min: int = 10
@export_range(1, 128, 1, "or_greater") var spark_count_max: int = 22

@export_category("Audio")
@export var spark_sounds: Array[AudioStream] = []
@export_range(0.5, 2.0, 0.01) var pitch_min: float = 0.88
@export_range(0.5, 2.0, 0.01) var pitch_max: float = 1.12

@onready var particles: GPUParticles3D = $Sparks
@onready var flash_animation: AnimationPlayer = $FlashAnimation
@onready var audio_player: AudioStreamPlayer3D = $SparkAudio
@onready var interval_timer: Timer = $IntervalTimer

var _random := RandomNumberGenerator.new()


func _ready() -> void:
	_random.randomize()
	_apply_active_state()


func set_active(value: bool) -> void:
	active = value


func trigger_burst() -> void:
	if not is_inside_tree():
		return

	particles.amount = _random.randi_range(
		mini(spark_count_min, spark_count_max),
		maxi(spark_count_min, spark_count_max)
	)
	particles.restart()
	particles.emitting = true
	_play_spark_sound()
	flash_animation.stop()
	flash_animation.play(&"flash")
	burst_started.emit()


func _apply_active_state() -> void:
	interval_timer.stop()
	if active:
		_schedule_next_burst()
		return

	particles.emitting = false
	audio_player.stop()
	flash_animation.play(&"RESET")
	flash_animation.advance(0.0)
	flash_animation.stop()


func _schedule_next_burst() -> void:
	if not active:
		return
	interval_timer.start(_random.randf_range(
		minf(interval_min, interval_max),
		maxf(interval_min, interval_max)
	))


func _play_spark_sound() -> void:
	if not spark_sounds.is_empty():
		var selected_sound := spark_sounds[_random.randi_range(0, spark_sounds.size() - 1)]
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
	if not active:
		return
	trigger_burst()
	_schedule_next_burst()
