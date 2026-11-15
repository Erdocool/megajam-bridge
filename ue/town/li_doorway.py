
# open a doorway in the duplicated level-instance world: hide one wall module (kept, not deleted), add a lintel above the door height
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert '/Game/DirectorsCut/Buildings/' in w.get_path_name(), w.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
a = acts[MODULE]
o, e = a.get_actor_bounds(False)
smc = a.static_mesh_component
mat = smc.get_material(0)
smc.set_visibility(False, True); smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
a.tags = list(a.tags) + ['MJ_DoorwayHidden']
zb = o.z - e.z; zt = o.z + e.z
if 'MJ_Lintel' not in acts and zt - zb > DOOR_H + 20:
    cube = unreal.load_asset('/Engine/BasicShapes/Cube')
    h = zt - (zb + DOOR_H)
    l = eas.spawn_actor_from_object(cube, unreal.Vector(o.x, o.y, zb + DOOR_H + h / 2), unreal.Rotator(0, 0, 0))
    l.set_actor_scale3d(unreal.Vector(2 * e.x / 100.0, 2 * e.y / 100.0, h / 100.0)); l.set_actor_label('MJ_Lintel')
    if mat: l.static_mesh_component.set_material(0, mat)
# threshold/sill marker for the door BP later
if 'MJ_DoorSpot' not in acts:
    t = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(o.x, o.y, zb), unreal.Rotator(0, 0, 0)); t.set_actor_label('MJ_DoorSpot')
print('opening', MODULE, 'x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f door_h %d mat %s' % (o.x-e.x, o.x+e.x, o.y-e.y, o.y+e.y, zb, zt, DOOR_H, mat.get_name() if mat else None))
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
