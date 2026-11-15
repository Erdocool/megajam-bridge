import unreal
# hide all old L_Town ground/road/sidewalk pieces (tag MJ_HiddenForCity); add invisible walk floor MJ_WalkFloor over the bounded area (top z=15)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name() == 'L_Town'
T = unreal.Name('MJ_HiddenForCity'); n = 0; acts = {}
for a in eas.get_all_level_actors():
    l = a.get_actor_label(); acts[l] = a
    if l.startswith('Town_'):
        a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
        for c in a.get_components_by_class(unreal.PrimitiveComponent): c.set_visibility(False)
        if T not in a.tags: a.tags = list(a.tags) + [T]
        n += 1
f = acts.get('MJ_WalkFloor') or eas.spawn_actor_from_object(unreal.load_asset('/Engine/BasicShapes/Cube'), unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
f.set_actor_label('MJ_WalkFloor'); f.set_actor_location(unreal.Vector(11975, 7942, -35), False, False); f.set_actor_scale3d(unreal.Vector(19.5, 99.9, 1.0))
c = f.static_mesh_component; c.set_collision_profile_name('BlockAll'); c.set_editor_property('hidden_in_game', True); c.set_editor_property('cast_shadow', False)
f.set_actor_hidden_in_game(True); f.tags = [unreal.Name('MJ_WalkFloor')]
print('hidden Town_', n, 'walkfloor ok saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
