
# L_Town step 11: daytime sky (SkyAtmosphere + real-time SkyLight), L_Town's own lights only
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in w.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
print('have', [l for l, a in acts.items() if isinstance(a, (unreal.SkyAtmosphere, unreal.ExponentialHeightFog, unreal.SkyLight, unreal.DirectionalLight))])
sky = [a for a in acts.values() if isinstance(a, unreal.SkyAtmosphere)]
if not sky:
    a = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); a.set_actor_label('L_SkyAtmosphere')
sun = acts['L_Sun'].get_component_by_class(unreal.DirectionalLightComponent)
sun.set_editor_property('atmosphere_sun_light', True); sun.set_editor_property('intensity', SUN_LUX)
sl = acts['L_SkyLight'].get_component_by_class(unreal.SkyLightComponent)
sl.set_editor_property('source_type', unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
sl.set_editor_property('real_time_capture', True); sl.set_editor_property('intensity', SKY_INT)
sl.recapture_sky()
print('sun', SUN_LUX, 'sky', SKY_INT)
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
