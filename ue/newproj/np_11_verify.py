import unreal, math
# read-only: per city actor, z stats (world, L_Town) of vertices inside our zones
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
Z = {'stu': (0, 5404, -2814, -926), 'sfa': (12950, 16700, 3000, 12900), 'bnd': (11000, 12950, 2950, 12934), 'st': (0, 20000, -900, 900)}
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if not l.startswith('CITY_') or 'Center' not in l: continue
    sm = a.static_mesh_component.static_mesh; tr = a.get_actor_transform(); zs = {k: [] for k in Z}
    for s in range(sm.get_num_sections(0)):
        for v in unreal.ProceduralMeshLibrary.get_section_from_static_mesh(sm, 0, s)[0]:
            p = tr.transform_location(v)
            for k, z in Z.items():
                if z[0] <= p.x <= z[1] and z[2] <= p.y <= z[3]: zs[k].append(p.z)
    out = []
    for k, L in zs.items():
        if L: L.sort(); out.append('%s n%d %d/%d/%d' % (k, len(L), L[0], L[len(L) // 2], L[-1]))
    print(l[5:20], ' '.join(out))
