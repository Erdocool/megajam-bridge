
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
