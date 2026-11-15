import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
for n in ('Door_Flat1_Salon', 'Door_Flat1_Entry'):
    d = acts[n]
    for c in d.get_components_by_class(unreal.SceneComponent):
        l = c.get_world_location(); rl = c.get_editor_property('relative_location'); rr = c.get_editor_property('relative_rotation')
        m = c.static_mesh.get_name() if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh else ''
        ex = ''
        if isinstance(c, unreal.PrimitiveComponent):
            o, e, r = unreal.SystemLibrary.get_component_bounds(c); ex = [round(o.x), round(o.y), round(o.z), round(e.x), round(e.y), round(e.z)]
        print('C', n[5:], c.get_name()[:18], c.get_class().get_name()[:14], m[:16], [round(v) for v in (rl.x, rl.y, rl.z)], round(rr.yaw), ex, [round(s, 2) for s in (c.get_editor_property('relative_scale3d').x, c.get_editor_property('relative_scale3d').y, c.get_editor_property('relative_scale3d').z)])
    px = [p for p in ('LeafPath', 'Leaf', 'MJ_Leaf', 'Proxy', 'MJ_Proxy') if True]
    for p in ('MJ_Proxy', 'Leaf', 'MJ_Leaf'):
        try: v = d.get_editor_property(p); print('P', p, v.get_actor_label() if hasattr(v, 'get_actor_label') else v)
        except Exception: pass
pr = [a for a in acts.values() if str(a.get_folder_path()) == 'Doors/Proxies'][:2]
for a in pr:
    o, e = a.get_actor_bounds(False); print('PX', a.get_actor_label(), a.static_mesh_component.static_mesh.get_name(), [round(v) for v in (o.x, o.y, o.z, e.x, e.y, e.z)], round(a.get_actor_rotation().yaw), a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None)
les.load_level('/Game/DirectorsCut/Maps/L_Town')
