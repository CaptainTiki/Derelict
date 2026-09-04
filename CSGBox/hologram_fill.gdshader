shader_type spatial;

render_mode blend_mix, depth_draw_never, cull_back, unshaded;

uniform vec4 tint : source_color = vec4(0.1, 0.8, 1.0, 1.0);
uniform float fill_alpha : hint_range(0.0, 1.0) = 0.04;
uniform float fresnel_strength : hint_range(0.0, 1.0) = 0.08;

void fragment() {
	float fresnel = pow(
		1.0 - abs(dot(normalize(NORMAL), normalize(VIEW))),
		3.0
	);

	ALBEDO = tint.rgb;
	EMISSION = tint.rgb * (0.08 + fresnel * 0.25);
	ALPHA = clamp(fill_alpha + fresnel * fresnel_strength, 0.0, 1.0);
}
