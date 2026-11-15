
import collections
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
for lab in TARGETS:
    a = acts['CAND_' + lab]
    cls = a.get_class()
    chain = []; c = cls
    for _ in range(6):
        try:
            chain.append(c.get_name()); c = unreal.SystemLibrary.get_super_class(c) if hasattr(unreal.SystemLibrary,'get_super_class') else None
            if c is None: break
        except Exception: break
    print('==', lab, 'class', cls.get_name(), 'isPLA', isinstance(a, unreal.PackedLevelActor), 'isLI', isinstance(a, unreal.LevelInstance))
    for prop in ('world_asset',):
        try: print('  ', prop, a.get_editor_property(prop))
        except Exception as ex: print('  ', prop, 'n/a')
    mn, mx = ism_bounds(a)
    print('  bounds min', [round(v) for v in mn], 'max', [round(v) for v in mx], 'actor loc', a.get_actor_location(), 'rot', a.get_actor_rotation().yaw)
    rows = []
    for comp in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        sm = comp.get_editor_property('static_mesh')
        if not sm: continue
        n = comp.get_instance_count()
        zs = []; xs = []; ys = []
        for i in range(n):
            t = comp.get_instance_transform(i, True).translation
            xs.append(t.x - mn[0]); ys.append(t.y - mn[1]); zs.append(t.z - mn[2])
        rows.append((sm.get_name(), n, min(zs), max(zs), min(xs), max(xs), min(ys), max(ys), sorted(set(round(z) for z in zs))[:14]))
    rows.sort(key=lambda r: r[2])
    zl = sorted(set(round(r[2]) for r in rows)); print('  module z levels', zl)
    for r in rows:
        if r[2] > zl[0] + 50 and not any(k in r[0].lower() for k in ('entr','door','store')): continue
        print('  %-48s n=%4d z %5.0f..%5.0f x %5.0f..%5.0f y %5.0f..%5.0f zs %s' % r)
