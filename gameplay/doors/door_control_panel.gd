extends Node3D
class_name DoorControlPanel


signal operation_requested(actor: Node)

@export_node_path("Node3D") var target_door_path: NodePath

@onready var target_door: Node = get_node_or_null(target_door_path)


func can_interact(_actor: Node) -> bool:
	return is_instance_valid(target_door) and target_door.has_method("request_toggle") and not target_door.locked


func get_interaction_prompt(_actor: Node) -> String:
	if not is_instance_valid(target_door) or not target_door.has_method("request_toggle"):
		return "Unavailable"
	if target_door.locked:
		return "Locked"
	if target_door.state == 1 or target_door.state == 2:
		return "Close Door"
	return "Open Door"


func _on_interacted(actor: Node) -> void:
	operation_requested.emit(actor)
	if not is_instance_valid(target_door):
		push_warning("DoorControlPanel has no valid target door.")
		return
	if not target_door.has_method("request_toggle"):
		push_warning("DoorControlPanel target does not implement request_toggle().")
		return
	target_door.request_toggle(actor)
