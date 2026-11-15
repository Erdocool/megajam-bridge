
import collections, re
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = eas.get_all_level_actors()
print('actors', len(acts), collections.Counter(a.get_class().get_name() for a in acts).most_common(12))
pre = collections.Counter(re.split(r'[_ ]', a.get_actor_label())[0] for a in acts)
print('label prefixes', pre.most_common(30))
geo = []
for a in acts:
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        o, e = a.get_actor_bounds(False); geo.append((a.get_actor_label(), o, e))
big = [g for g in geo if g[2].x > 150 and g[2].y > 150 and g[2].z < 30]
zc = collections.Counter(round((g[1].z + g[2].z) / 10) * 10 for g in big)
print('slab tops (z: count)', sorted(zc.items())[:30])
core = [g for g in geo if abs(g[1].x) < 20000 and abs(g[1].y) < 20000 and g[1].z > -500]
print('core bounds x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f' % (min(g[1].x-g[2].x for g in core), max(g[1].x+g[2].x for g in core), min(g[1].y-g[2].y for g in core), max(g[1].y+g[2].y for g in core), min(g[1].z-g[2].z for g in core), max(g[1].z+g[2].z for g in core)))
for a in acts:
    l = a.get_actor_label(); cn = a.get_class().get_name()
    if any(k in l.lower() for k in ('stair', 'entr', 'lobby', 'main', 'street', 'front')) or cn in ('PlayerStart', 'DirectionalLight', 'SkyLight', 'PostProcessVolume'):
        p = a.get_actor_location(); print('  %-34s %-22s (%.0f, %.0f, %.0f)' % (l[:34], cn[:22], p.x, p.y, p.z))
