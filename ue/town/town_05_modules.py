
import re, collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
for lab in TARGETS:
    a = acts['CAND_' + lab]
    mn, mx = ism_bounds(a)
    lv = collections.defaultdict(lambda: [1e9, -1e9, 0])
    ent = []
    for comp in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        sm = comp.get_editor_property('static_mesh')
        if not sm: continue
        nm = sm.get_name(); m = re.search(r'_(L\d+|RF\w*|Roof\w*)_', nm); key = m.group(1) if m else nm[:30]
        bb = sm.get_bounding_box()
        for i in range(comp.get_instance_count()):
            t = comp.get_instance_transform(i, True)
            cs = [t.transform_location(unreal.Vector(x, y, z)) for x in (bb.min.x, bb.max.x) for y in (bb.min.y, bb.max.y) for z in (bb.min.z, bb.max.z)]
            z0 = min(c.z for c in cs) - mn[2]; z1 = max(c.z for c in cs) - mn[2]
            L = lv[key]; L[0] = min(L[0], z0); L[1] = max(L[1], z1); L[2] += 1
            if any(k in nm.lower() for k in ENTKEYS):
                ent.append((nm, round(min(c.x for c in cs) - mn[0]), round(max(c.x for c in cs) - mn[0]), round(min(c.y for c in cs) - mn[1]), round(max(c.y for c in cs) - mn[1]), round(z0), round(z1)))
    print('==', lab, 'size', [round(mx[k] - mn[k]) for k in range(3)], 'pivot z rel', round(a.get_actor_location().z - mn[2]))
    for k, v in sorted(lv.items(), key=lambda kv: kv[1][0]):
        print('  level %-10s z %6.0f..%6.0f  n=%d' % (k, v[0], v[1], v[2]))
    for e in ent[:30]:
        print('  ENT %-40s x %d..%d y %d..%d z %d..%d' % e)
