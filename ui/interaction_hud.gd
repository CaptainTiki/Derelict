extends Control
class_name InteractionHUD


const InteractableComponent = preload("res://gameplay/interaction/interactable.gd")
const AVAILABLE_COLOR := Color(0.35, 0.85, 1.0, 1.0)
const UNAVAILABLE_COLOR := Color(1.0, 0.42, 0.18, 1.0)

@onready var idle_dot: ColorRect = $Center/IdleDot
@onready var interaction_ring: Control = $Center/InteractionRing
@onready var prompt_label: Label = $Center/InteractionPrompt
@onready var feedback_animation: AnimationPlayer = $FeedbackAnimation

var focused_interactable: InteractableComponent
var focused_actor: Node


func _ready() -> void:
	_refresh_display()


func _on_focus_changed(interactable: InteractableComponent, actor: Node) -> void:
	focused_interactable = interactable
	focused_actor = actor
	_refresh_display()


func _on_interaction_performed(interactable: InteractableComponent, actor: Node) -> void:
	focused_interactable = interactable
	focused_actor = actor
	_refresh_display()
	_play_feedback(&"accepted")


func _on_interaction_rejected(interactable: InteractableComponent, actor: Node) -> void:
	focused_interactable = interactable
	focused_actor = actor
	_refresh_display()
	_play_feedback(&"rejected")


func _refresh_display() -> void:
	var has_focus := is_instance_valid(focused_interactable)
	idle_dot.visible = not has_focus
	interaction_ring.visible = has_focus
	prompt_label.visible = has_focus
	if not has_focus:
		return

	var is_available := focused_interactable.can_interact(focused_actor)
	var feedback_color := AVAILABLE_COLOR if is_available else UNAVAILABLE_COLOR
	interaction_ring.modulate = feedback_color
	prompt_label.add_theme_color_override("font_color", feedback_color)
	var prompt := focused_interactable.get_interaction_prompt(focused_actor)
	prompt_label.text = "[E] %s" % prompt if is_available else prompt


func _play_feedback(animation_name: StringName) -> void:
	feedback_animation.stop()
	feedback_animation.play(animation_name)
