import unreal, json, os
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
def P(v): return [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
def gp(a, n):
    try: v = a.get_editor_property(n); return v if isinstance(v, (bool, int, float)) else str(v)
    except Exception: return None
out = {}
for lvl in ('/Game/DirectorsCut/Buildings/LI_Building_MJ', '/Game/DirectorsCut/Buildings/LI_Studio_MJ'):
    les.load_level(lvl); L = []
    for a in eas.get_all_level_actors():
        o, e = a.get_actor_bounds(False)
        d = {'l': a.get_actor_label(), 'c': a.get_class().get_name(), 'p': P(a.get_actor_location()), 'r': [round(a.get_actor_rotation().roll), round(a.get_actor_rotation().pitch), round(a.get_actor_rotation().yaw)], 's': P(a.get_actor_scale3d()), 'o': P(o), 'e': P(e), 'f': str(a.get_folder_path()), 'h': a.is_hidden_ed()}
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
            sm = a.static_mesh_component.static_mesh; bb = sm.get_bounding_box(); d['m'] = sm.get_path_name().split('.')[0]; d['bb'] = [P(bb.min), P(bb.max)]
            d['mob'] = str(a.static_mesh_component.get_editor_property('mobility'))
        if d['c'].startswith('BP_Door') or d['c'].startswith('BP_Key'):
            for n in ('bOpen', 'OpenAngle', 'bLocked', 'KeyID'): d[n] = gp(a, n)
            px = gp(a, 'MJ_Proxy'); d['px'] = px
            try: d['pxl'] = a.get_editor_property('MJ_Proxy').get_actor_label()
            except Exception: pass
        par = a.get_attach_parent_actor(); d['par'] = par.get_actor_label() if par else None
        L.append(d)
    out[lvl.split('/')[-1]] = L
les.load_level('/Game/DirectorsCut/Maps/L_Town')
p = os.path.join(unreal.Paths.project_saved_dir(), 'mj_doors.json'); json.dump(out, open(p, 'w')); print('DD', {k: len(v) for k, v in out.items()})
