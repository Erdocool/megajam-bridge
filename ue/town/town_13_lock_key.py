
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
    print('KEY', k.get_actor_label(), 'proxy', p.get_actor_label() if p else None, sm.static_mesh.get_path_name() if sm else None,
          [round(v, 2) for v in (p.get_actor_scale3d().x,)] if p else None, 'off', (p.get_actor_location() - k.get_actor_location()) if p else None)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town')
print('back', 'L_Town' in unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name())
