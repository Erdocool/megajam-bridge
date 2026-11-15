
# L_Town step 9: place interior copies as level instances, move exit trigger + PlayerStart, interior-friendly light levels (as L_Building)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if 'L_Town' not in w.get_path_name():
    assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    les.load_level('/Game/DirectorsCut/Maps/L_Town')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
V, R = unreal.Vector, unreal.Rotator
o, e = acts['Town_Sidewalk_N'].get_actor_bounds(False); ZS = o.z + e.z
print('ZS', ZS)
def li(lab, path, loc, yaw=0):
    if lab in acts:
        a = acts[lab]; a.set_actor_location(loc, False, False); a.set_actor_rotation(R(0, 0, yaw), False); return a
    a = eas.spawn_actor_from_object(unreal.load_asset(path), loc, R(0, 0, yaw)); a.set_actor_label(lab); acts[lab] = a; return a
SZ = ZS + 930          # NYAF floor 3 level
li('INT_Studio', '/Game/DirectorsCut/Buildings/LI_Studio_MJ', V(2000, -1450, SZ))
li('INT_Building', '/Game/DirectorsCut/Buildings/LI_Building_MJ', V(13376, 6430, ZS))
t = acts['MJ_StudioExit_Trigger']; t.set_actor_location(V(2150, -1650, SZ + 90), False, False)
ps = acts['PlayerStart_Town']; ps.set_actor_location(V(2420, -1450, SZ + 100), False, False); ps.set_actor_rotation(R(0, 90, 0), False)
# light levels back to the L_Building calibration so the interiors' own lights read correctly
acts['L_Sun'].light_component.set_intensity(2.5); acts['L_SkyLight'].light_component.set_intensity(1.0)
ppv = acts['MJ_Exposure_PPV']; s = ppv.settings
s.set_editor_property('auto_exposure_min_brightness', -2.5); s.set_editor_property('auto_exposure_max_brightness', 0.5); ppv.set_editor_property('settings', s)
for lab in ('INT_Studio', 'INT_Building'):
    o, e = acts[lab].get_actor_bounds(False); print(lab, acts[lab].get_class().get_name(), 'x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f' % (o.x-e.x, o.x+e.x, o.y-e.y, o.y+e.y, o.z-e.z, o.z+e.z))
print('saved', les.save_current_level())
