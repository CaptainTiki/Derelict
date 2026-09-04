shader_type spatial;

render_mode blend_mix, depth_draw_never, cull_disabled, unshaded;

uniform vec4 tint : source_color = vec4(0.1, 0.8, 1.0, 1.0);
uniform float edge_alpha : hint_range(0.0, 1.0) = 0.9;
uniform float emission_strength : hint_range(0.0, 5.0) = 1.5;

void fragment() {
	ALBEDO = tint.rgb;
	EMISSION = tint.rgb * emission_strength;
	ALPHA = edge_alpha;
}
