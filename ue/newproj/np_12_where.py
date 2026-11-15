import unreal
# read-only: where do Center city verts poke into our street / INT_Building / studio?
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
Z = {'st': (0, 20000, -900, 900, 15), 'xst': (11100, 12900, 900, 17000, 15), 'intb': (13351, 14401, 6405, 7855, 0), 'stu': (1000, 4404, -2014, -926, 0)}
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if not l.startswith('CITY_') or 'Center' not in l: continue
    sm = a.static_mesh_component.static_mesh; tr = a.get_actor_transform(); r = {}
    for s in range(sm.get_num_sections(0)):
        for v in unreal.ProceduralMeshLibrary.get_section_from_static_mesh(sm, 0, s)[0]:
            p = tr.transform_location(v)
            for k, z in Z.items():
                if z[0] <= p.x <= z[1] and z[2] <= p.y <= z[3] and p.z > z[4]:
                    b = r.setdefault(k, [1e9, -1e9, 1e9, -1e9, -1e9, 0]); b[0] = min(b[0], p.x); b[1] = max(b[1], p.x); b[2] = min(b[2], p.y); b[3] = max(b[3], p.y); b[4] = max(b[4], p.z); b[5] += 1
    print(l[5:16], {k: [int(x) for x in v] for k, v in r.items()})
