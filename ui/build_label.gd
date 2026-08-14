extends Label


func _ready() -> void:
	var version := str(ProjectSettings.get_setting("application/config/version", "dev"))
	text = "Build: %s" % version
