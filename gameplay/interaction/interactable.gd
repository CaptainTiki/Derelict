extends Area3D
class_name Interactable


signal interacted(actor: Node)
signal focus_entered(actor: Node)
signal focus_exited(actor: Node)

@export var interaction_prompt: String = "Interact"
@export var interaction_enabled: bool = true
@export_node_path("Node") var interaction_provider_path: NodePath

@onready var interaction_provider: Node = get_node_or_null(interaction_provider_path)

var is_focused: bool = false


func can_interact(actor: Node) -> bool:
	if not interaction_enabled or not is_visible_in_tree():
		return false
	if is_instance_valid(interaction_provider) and interaction_provider.has_method("can_interact"):
		return interaction_provider.can_interact(actor)
	return true


func get_interaction_prompt(actor: Node) -> String:
	if is_instance_valid(interaction_provider) and interaction_provider.has_method("get_interaction_prompt"):
		return interaction_provider.get_interaction_prompt(actor)
	return interaction_prompt


func interact(actor: Node) -> bool:
	if not can_interact(actor):
		return false
	interacted.emit(actor)
	return true


func set_focused(focused: bool, actor: Node) -> void:
	if is_focused == focused:
		return
	is_focused = focused
	if is_focused:
		focus_entered.emit(actor)
	else:
		focus_exited.emit(actor)
