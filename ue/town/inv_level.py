
import collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = eas.get_all_level_actors()
print('actors', len(acts), collections.Counter(a.get_class().get_name() for a in acts).most_common(25))
geo = [a for a in acts if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh]
xs=[];ys=[];zs=[]
for a in geo:
    o, e = a.get_actor_bounds(False)
    if e.x > 20000 or e.y > 20000: continue
    xs += [o.x-e.x, o.x+e.x]; ys += [o.y-e.y, o.y+e.y]; zs += [o.z-e.z, o.z+e.z]
print('geo bounds x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f' % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
for a in acts:
    cn = a.get_class().get_name(); l = a.get_actor_label()
    if any(k in cn for k in ('Light', 'Sky', 'Fog', 'PostProcess', 'PlayerStart', 'Atmosphere', 'BP_Door', 'BP_Key', 'Volume', 'Cloud')) or any(k in l.lower() for k in KEYS):
        p = a.get_actor_location(); print('  %-30s %-28s (%.0f, %.0f, %.0f)' % (l[:30], cn[:28], p.x, p.y, p.z))
