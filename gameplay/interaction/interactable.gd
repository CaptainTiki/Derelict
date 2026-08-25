extends Area3D
class_name Interactable


signal interacted(actor: Node)
signal focus_entered(actor: Node)
signal focus_exited(actor: Node)

@export var interaction_prompt: String = "Interact"
@export var interaction_enabled: bool = true

var is_focused: bool = false


func can_interact(_actor: Node) -> bool:
	return interaction_enabled and is_visible_in_tree()


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
