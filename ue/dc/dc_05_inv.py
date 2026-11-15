import unreal, json, os
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
out = {}
def assets(path, cls=None):
    r = []
    for d in ar.get_assets_by_path(path, recursive=True):
        c = str(d.asset_class_path.asset_name)
        if cls is None or c in cls: r.append((str(d.package_name), c))
    return r
out['worlds'] = [p for p, c in assets('/Game', ['World'])]
out['skel'] = [p for p, c in assets('/Game', ['SkeletalMesh', 'Blueprint']) if any(k in p.lower() for k in ('metahuman', 'manny', 'quinn', 'mannequin', '/bp_', 'character', 'npc'))][:80]
out['anims'] = [p for p, c in assets('/Game', ['AnimSequence']) if 'idle' in p.lower()][:30]
out['media'] = [p + ':' + c for p, c in assets('/Game', ['MediaPlayer', 'MediaTexture', 'FileMediaSource', 'Material']) if any(k in p.lower() for k in ('media', 'screen', 'emis', 'monitor', 'tv'))][:40]
def dump(level):
    les.load_level(level); L = []
    for a in eas.get_all_level_actors():
        p = a.get_actor_location(); r = a.get_actor_rotation(); o, e = a.get_actor_bounds(False)
        d = {'l': a.get_actor_label(), 'c': a.get_class().get_name(), 'p': [round(p.x), round(p.y), round(p.z)], 'yaw': round(r.yaw), 'e': [round(e.x), round(e.y), round(e.z)], 'f': str(a.get_folder_path()), 't': [str(t) for t in a.tags], 'h': a.is_hidden_ed()}
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
            d['m'] = a.static_mesh_component.static_mesh.get_path_name().split('.')[0]
            d['mat'] = [m.get_name() if m else None for m in a.static_mesh_component.get_materials()][:3]
        for comp in a.get_components_by_class(unreal.ActorComponent):
            cn = comp.get_class().get_name()
            if 'MJDoor' in cn or 'MJKey' in cn:
                for k in ('KeyID', 'Key ID', 'KeyId'):
                    try: d['key'] = cn[:9] + ':' + str(comp.get_editor_property(k)); break
                    except Exception: pass
        L.append(d)
    return L
out['bld'] = dump('/Game/DirectorsCut/Buildings/LI_Building_MJ') if unreal.EditorAssetLibrary.does_asset_exist('/Game/DirectorsCut/Buildings/LI_Building_MJ') else 'missing'
les.load_level('/Game/DirectorsCut/Maps/L_Town')
out['town_bld'] = [ (a.get_actor_label(), a.get_class().get_name(), [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)], round(a.get_actor_rotation().yaw)) for a in eas.get_all_level_actors() if 'Building' in a.get_actor_label() or 'LevelInstance' in a.get_class().get_name()]
p = os.path.join(unreal.Paths.project_saved_dir(), 'mj_inv.json'); json.dump(out, open(p, 'w')); print('INV', p.replace('\\', '/'), len(out['bld']))
