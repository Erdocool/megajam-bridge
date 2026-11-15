import unreal
# Door instance tags 'Locked:x' / 'KeyID:x' are read at runtime by the door Blueprint; make them match the real
# bLocked / KeyID properties (Street door had Locked:0 + KeyID:Key_Street -> opened without its key).
# Also fixes the stair guard on floor 4 (was 6 cm into the Manager entry path): landing extended to x640, guard moved.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V, R = unreal.Vector, unreal.Rotator
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
ch = []
for l, a in acts.items():
    if not a.get_class().get_name().startswith('BP_Door'): continue
    lk = bool(a.get_editor_property('bLocked')); kid = str(a.get_editor_property('KeyID')); kid = '' if kid == 'None' else kid
    old = [str(t) for t in a.tags]
    new = [t for t in old if not t.startswith(('Locked:', 'KeyID:'))] + ['KeyID:' + kid, 'Locked:%d' % lk]
    if new != old: a.tags = [unreal.Name(t) for t in new]; ch.append(l[5:])
print('TAGS fixed', ch)
def mk(lab, src, x0, x1, y0, y1, z0, z1):
    a = acts.get(lab)
    if a is None:
        a = eas.duplicate_actor(src, w, V(0, 0, 0)); a.set_actor_label(lab); acts[lab] = a; a.set_folder_path('Building/StairV3')
    a.set_actor_rotation(R(0, 0, 0), False); a.set_actor_scale3d(V(1, 1, 1)); a.set_actor_location(V(0, 0, 0), False, False)
    o, e = a.get_actor_bounds(False); s = V((x1 - x0) / (2 * e.x), (y1 - y0) / (2 * e.y), (z1 - z0) / (2 * e.z)); a.set_actor_scale3d(s)
    a.set_actor_location(V((x0 + x1) / 2 - o.x * s.x, (y0 + y1) / 2 - o.y * s.y, (z0 + z1) / 2 - o.z * s.z), False, False); return a
mk('SlabStairV3_4_Aext', acts['SlabStairV3_4_W'], 590, 640, 1110, 1240, 1180, 1200)
mk('CeilV3_4_Aext', acts['CeilV3_4_W'], 590, 640, 1110, 1240, 1180, 1200)
mk('GuardV3_4A', acts['GuardV3_4A'], 640, 646, 1110, 1240, 1200, 1300)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
