
# step 17: read-only verify (no save)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
print('map', w.get_name(), 'dirty', unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() and len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()))
d = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Door.BP_Door_C')) if a.get_actor_label() == 'Door_Street']
print('door', [(x.get_editor_property('bLocked'), str(x.get_editor_property('KeyID'))) for x in d])
k = acts.get('Key_Building_Front'); print('key', bool(k), k and str(k.get_editor_property('KeyID')), k and k.get_editor_property('MJ_Proxy') is not None)
s = acts['MJ_Exposure_PPV'].settings; print('EV', s.auto_exposure_min_brightness, s.auto_exposure_max_brightness)
print('skyf', acts['L_SkyAtmosphere'].get_component_by_class(unreal.SkyAtmosphereComponent).get_editor_property('sky_luminance_factor').r)
