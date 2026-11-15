
import re, collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
B = []
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.is_visible():
        o, e = a.get_actor_bounds(False); B.append((a.static_mesh_component.static_mesh.get_name(), o.x-e.x, o.x+e.x, o.y-e.y, o.y+e.y, o.z-e.z, o.z+e.z))
mn = [min(b[1] for b in B), min(b[3] for b in B), min(b[5] for b in B)]
mx = [max(b[2] for b in B), max(b[4] for b in B), max(b[6] for b in B)]
print('outer', [round(v) for v in mn], [round(v) for v in mx])
lv = collections.defaultdict(list)
for b in B:
    m = re.search(r'_(L\d+)_', b[0])
    if m: lv[m.group(1)].append(b)
for k in sorted(lv, key=lambda k: int(k[1:])):
    bs = lv[k]
    z0 = min(b[5] for b in bs); z1 = max(b[6] for b in bs)
    walls = [b for b in bs if 'Wall' in b[0]]
    def med(v): v = sorted(v); return v[len(v)//2] if v else float('nan')
    ix0 = med([b[2] for b in walls if b[1] < mn[0] + 500]); ix1 = med([b[1] for b in walls if b[2] > mx[0] - 500])
    iy0 = med([b[4] for b in walls if b[3] < mn[1] + 500]); iy1 = med([b[3] for b in walls if b[4] > mx[1] - 500])
    print('%-3s z %6.0f..%6.0f (h %4.0f) inner x %6.0f..%6.0f y %6.0f..%6.0f -> %4.0f x %4.0f cm' % (k, z0, z1, z1-z0, ix0, ix1, iy0, iy1, ix1-ix0, iy1-iy0))
