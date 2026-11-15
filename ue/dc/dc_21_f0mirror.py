import unreal
# Floor-0 hall mirror stood free in the walkway to the (new) stairs: move it onto the hall's north wall.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V, R = unreal.Vector, unreal.Rotator
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
m = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'Furn_F0_Hall_Mirror'][0]
o, e = m.get_actor_bounds(False); zb = o.z - e.z
m.set_actor_rotation(R(0, 0, m.get_actor_rotation().yaw - 90), False)
o, e = m.get_actor_bounds(False); p = m.get_actor_location()
m.set_actor_location(V(p.x + 400 - o.x, p.y + (1100 + e.y + 0.5) - o.y, p.z + zb - (o.z - e.z)), False, False)
o, e = m.get_actor_bounds(False); print('MIR', round(o.x - e.x), round(o.x + e.x), round(o.y - e.y), round(o.y + e.y))
print('saved LI', les.save_current_level()); les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
