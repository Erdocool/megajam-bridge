
# L_Town step 7: filler buildings along the cross street (west side + east side past the SFA)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in w.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
for lab in ('HERO_Studio_NYAF', 'HERO_MainApt_SFA'):
    o, e = acts[lab].get_actor_bounds(False); print(lab, 'bounds x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f' % (o.x-e.x, o.x+e.x, o.y-e.y, o.y+e.y, o.z-e.z, o.z+e.z))
if any(l.startswith('FILLX_') for l in acts):
    raise SystemExit('cross fillers already placed')
o, e = acts['Town_Ground'].get_actor_bounds(False); ZG = o.z + e.z
ar = unreal.AssetRegistryHelpers.get_asset_registry()
pk = {str(a.asset_name): str(a.package_name) for a in ar.get_assets_by_path('/Game/CitySampleBuildings', recursive=True) if str(a.asset_name).startswith('BPP_')}
n = 0
for side, names, y0, y1, yaw in (('W', ['BPP_NYAB_Ref_N1', 'BPP_CHB_Ref_A1_N1', 'BPP_NYAE_Ref_N1', 'BPP_SFJ_Ref_N1', 'BPP_NYAC_Ref_N1'], 1000, 16800, 90),
                                ('E', ['BPP_NYAE_Ref_N1'], 13200, 16800, -90)):
    cur = y0
    for name in names:
        a = eas.spawn_actor_from_class(unreal.load_asset(pk[name]).generated_class(), unreal.Vector(0, cur, 0), unreal.Rotator(0, 0, yaw))
        mn, mx = ism_bounds(a)
        L = mx[1] - mn[1]
        if cur + L > y1:
            eas.destroy_actor(a); continue
        p = a.get_actor_location()
        dx = (11050 - mx[0]) if side == 'W' else (12950 - mn[0])
        a.set_actor_location(unreal.Vector(p.x + dx, p.y + cur - mn[1], p.z + ZG - mn[2]), False, False)
        n += 1; a.set_actor_label('FILLX_%s_%02d_%s' % (side, n, name.replace('BPP_', '').replace('_N1', '')))
        print('FILLX', side, 'y %.0f..%.0f' % (cur, cur + L), name, 'depth %.0f H %.0f' % (mx[0] - mn[0], mx[2] - mn[2]))
        cur += L + 250
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
