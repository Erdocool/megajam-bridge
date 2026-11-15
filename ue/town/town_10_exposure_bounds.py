
# L_Town step 10: outdoor exposure fix (our own PPV only), interior PPV boxes (copies of the interiors' settings, ours), play-area blockers in front of SFA
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in w.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
V, R = unreal.Vector, unreal.Rotator
allppv = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.PostProcessVolume)
src = {}
for a in allppv:
    pn = a.get_path_name()
    if 'LI_Studio_MJ' in pn or 'Studio_MJ' in pn: src['studio'] = a
    elif 'Building_MJ' in pn: src['bldg'] = a
out = acts['MJ_Exposure_PPV']; s = out.settings
s.set_editor_property('auto_exposure_min_brightness', OUT_MIN); s.set_editor_property('auto_exposure_max_brightness', OUT_MAX)
out.set_editor_property('settings', s)
print('outdoor EV100', OUT_MIN, OUT_MAX)
def box_ppv(lab, srcppv, center, ext, prio):
    a = acts.get(lab) or eas.spawn_actor_from_class(unreal.PostProcessVolume, center, R(0, 0, 0))
    a.set_actor_label(lab); a.set_actor_location(center, False, False)
    a.set_actor_scale3d(V(ext[0] / 100.0, ext[1] / 100.0, ext[2] / 100.0))
    a.set_editor_property('settings', srcppv.settings); a.set_editor_property('unbound', False)
    a.set_editor_property('priority', prio); a.set_editor_property('blend_radius', 50.0)
    o, e = a.get_actor_bounds(False); print(lab, 'ext', [round(v) for v in (e.x, e.y, e.z)])
box_ppv('MJ_PPV_StudioInterior', src['studio'], V(2350, -1450, 1085), (420, 330, 170), 20.0)
box_ppv('MJ_PPV_BuildingInterior', src['bldg'], V(13826, 7107, 760), (610, 800, 800), 20.0)
# play-area blockers (invisible in game, BlockAll) around the space in front of SFA: x 11050..12950, y 3000..12884
cube = unreal.load_asset('/Engine/BasicShapes/Cube')
H = 800.0
def wall(lab, x0, x1, y0, y1):
    a = acts.get(lab) or eas.spawn_actor_from_object(cube, V(0, 0, 0), R(0, 0, 0))
    a.set_actor_label(lab); a.set_actor_location(V((x0 + x1) / 2, (y0 + y1) / 2, H / 2), False, False)
    a.set_actor_scale3d(V((x1 - x0) / 100.0, (y1 - y0) / 100.0, H / 100.0))
    c = a.static_mesh_component
    c.set_collision_profile_name('BlockAll'); c.set_editor_property('hidden_in_game', True)
    c.set_editor_property('cast_shadow', False); a.tags = [unreal.Name('MJ_PlayBound')]
wall('MJ_Bound_South', 11000, 12950, 2950, 3000)
wall('MJ_Bound_North', 11000, 12950, 12884, 12934)
wall('MJ_Bound_West', 11000, 11050, 2950, 12934)
print('bounds placed')
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
