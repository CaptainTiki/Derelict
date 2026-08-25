extends Node3D
class_name PlayerInteraction


const InteractableComponent = preload("res://gameplay/interaction/interactable.gd")

signal focus_changed(interactable: InteractableComponent, actor: Node)
signal interaction_performed(interactable: InteractableComponent, actor: Node)
signal interaction_rejected(interactable: InteractableComponent, actor: Node)

@export var actor_path: NodePath
@export var interaction_action: StringName = &"interact"

@onready var interaction_ray: RayCast3D = $InteractionRay
@onready var actor: Node = get_node(actor_path)

var focused_interactable: InteractableComponent


func _physics_process(_delta: float) -> void:
	_update_focus()


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed(interaction_action, false):
		return
	if not is_instance_valid(focused_interactable):
		return
	if focused_interactable.interact(actor):
		interaction_performed.emit(focused_interactable, actor)
	else:
		interaction_rejected.emit(focused_interactable, actor)
	get_viewport().set_input_as_handled()


func _update_focus() -> void:
	var next_interactable := _get_raycast_interactable()
	if next_interactable == focused_interactable:
		return

	if is_instance_valid(focused_interactable):
		focused_interactable.set_focused(false, actor)

	focused_interactable = next_interactable

	if is_instance_valid(focused_interactable):
		focused_interactable.set_focused(true, actor)

	focus_changed.emit(focused_interactable, actor)


func _get_raycast_interactable() -> InteractableComponent:
	if not interaction_ray.is_colliding():
		return null
	var collider := interaction_ray.get_collider()
	if collider is InteractableComponent:
		return collider as InteractableComponent
	return null
