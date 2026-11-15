
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = [a for a in eas.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh]
B = []
for a in acts:
    o, e = a.get_actor_bounds(False)
    B.append((a, o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y, o.z - e.z, o.z + e.z))
mn = [min(b[1] for b in B), min(b[3] for b in B), min(b[5] for b in B)]
mx = [max(b[2] for b in B), max(b[4] for b in B), max(b[6] for b in B)]
print('world bounds', [round(v) for v in mn], [round(v) for v in mx])
sel = [b for b in B if b[5] < mn[2] + ZBAND and SIDE(b, mn, mx)]
sel.sort(key=lambda b: (b[3], b[1]))
for b in sel:
    a = b[0]; sm = a.static_mesh_component.static_mesh
    print('%-34s %-40s x %6.0f..%6.0f y %6.0f..%6.0f z %5.0f..%5.0f' % (a.get_actor_label()[:34], sm.get_name()[:40], b[1], b[2], b[3], b[4], b[5], b[6]))
import collections
print('names L1/floor-ish:', collections.Counter(b[0].static_mesh_component.static_mesh.get_name() for b in B if any(k in b[0].static_mesh_component.static_mesh.get_name().lower() for k in ('floor','slab','int','ceil','plane','rect'))))
