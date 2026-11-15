SKYF=4.0; SKY_INT=1.5; OUT_EV=0.3
KEY_MESH='/Engine/BasicShapes/Cube'; KEY_SCALE=0.1; KEY_OFF=unreal.Vector(0,0,0)

# ==== batch 16: bounds invisible + sky/exposure + lock street door + key ====

# step 14: MJ_PlayBound walls (user-aligned; transforms untouched) -> hidden in game, BlockAll, no shadow
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in w.get_path_name()
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('MJ_Bound_'):
        c = a.static_mesh_component
        c.set_editor_property('hidden_in_game', True); a.set_actor_hidden_in_game(True)
        c.set_collision_profile_name('BlockAll'); c.set_editor_property('cast_shadow', False)
        print(a.get_actor_label(), 'hig', c.get_editor_property('hidden_in_game'), c.get_collision_profile_name(), c.get_collision_enabled())
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())

# L_Town step 12: brighter day sky via our own SkyAtmosphere luminance factor + skylight, fixed outdoor EV; numeric capture stats (tiny output)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in w.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
atm = acts['L_SkyAtmosphere'].get_component_by_class(unreal.SkyAtmosphereComponent)
atm.set_editor_property('sky_luminance_factor', unreal.LinearColor(SKYF, SKYF, SKYF, 1))
sl = acts['L_SkyLight'].get_component_by_class(unreal.SkyLightComponent)
sl.set_editor_property('intensity', SKY_INT); sl.recapture_sky()
out = acts['MJ_Exposure_PPV']; s = out.settings
s.set_editor_property('auto_exposure_min_brightness', OUT_EV); s.set_editor_property('auto_exposure_max_brightness', OUT_EV)
out.set_editor_property('settings', s)

print('sky ok', SKYF, SKY_INT, OUT_EV)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

# step 13a: in the LI_Building_MJ copy lock Door_Street with KeyID; report a key proxy mesh to reuse
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if 'L_Town' in w.get_path_name(): les.save_current_level()
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
d = acts['Door_Street']
print('before', d.get_editor_property('bLocked'), d.get_editor_property('KeyID'))
d.set_editor_property('bLocked', True); d.set_editor_property('KeyID', type(d.get_editor_property('KeyID'))('Key_Building_Front'))
print('after', d.get_editor_property('bLocked'), d.get_editor_property('KeyID'))
keys = [a for a in acts.values() if a.get_class().get_name() == 'BP_Key_C']
for k in keys[:1]:
    p = k.get_editor_property('MJ_Proxy')
    sm = p.static_mesh_component if p else None
    KEY_MESH = sm.static_mesh.get_path_name(); KEY_SCALE = p.get_actor_scale3d().x; KEY_OFF = p.get_actor_location() - k.get_actor_location()
    print('KEY mesh', KEY_MESH.split('/')[-1], round(KEY_SCALE, 2))
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town')
print('back', 'L_Town' in unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name())

# step 15: BP_Key 'Key_Building_Front' on a crate on the west sidewalk across from the SFA door (inside the bounded area)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in w.get_path_name()
V, R = unreal.Vector, unreal.Rotator
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
KX, KY = 11300.0, 9800.0
crate = acts.get('MJ_KeyCrate') or eas.spawn_actor_from_object(unreal.load_asset('/Engine/BasicShapes/Cube'), V(KX, KY, 60), R(0, 0, 0))
crate.set_actor_label('MJ_KeyCrate'); crate.set_actor_scale3d(V(0.7, 0.7, 0.9))
k = acts.get('Key_Building_Front') or eas.spawn_actor_from_class(unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Key.BP_Key_C'), V(KX, KY, 110), R(0, 0, 0))
k.set_actor_label('Key_Building_Front')
k.set_editor_property('KeyID', type(k.get_editor_property('KeyID'))('Key_Building_Front'))
p = acts.get('Proxy_Key_Building_Front') or eas.spawn_actor_from_object(unreal.load_asset(KEY_MESH), V(KX, KY, 110) + KEY_OFF, R(0, 0, 0))
p.set_actor_label('Proxy_Key_Building_Front'); p.set_actor_scale3d(V(KEY_SCALE, KEY_SCALE, KEY_SCALE))
p.static_mesh_component.set_collision_profile_name('NoCollision')
k.set_editor_property('MJ_Proxy', p)
print('key', k.get_editor_property('KeyID'), 'at', KX, KY, 'proxy', p.get_actor_label())
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
