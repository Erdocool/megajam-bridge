
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
