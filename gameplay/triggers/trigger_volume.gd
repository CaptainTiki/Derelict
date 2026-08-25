extends Area3D
class_name TriggerVolume


signal triggered(body: Node3D)
signal entered(body: Node3D)
signal exited(body: Node3D)

@export var trigger_enabled: bool = true
@export var one_shot: bool = false
@export var required_group: StringName = &"player"

var has_triggered: bool = false


func _on_body_entered(body: Node3D) -> void:
	if not _accepts(body):
		return
	entered.emit(body)
	if one_shot and has_triggered:
		return
	has_triggered = true
	triggered.emit(body)


func _on_body_exited(body: Node3D) -> void:
	if _matches_required_group(body):
		exited.emit(body)


func reset() -> void:
	has_triggered = false


func _accepts(body: Node3D) -> bool:
	return trigger_enabled and _matches_required_group(body)


func _matches_required_group(body: Node3D) -> bool:
	return required_group.is_empty() or body.is_in_group(required_group)
