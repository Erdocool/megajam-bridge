
# L_Town step 3: filler buildings along both sides (2 slots left empty + marked), parked cars. Idempotent (re-run replaces FILL_/CAR_/SLOT_).
import random
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert 'L_Town' in world.get_path_name(), world.get_path_name()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
for lab, a in list(acts.items()):
    if lab.startswith(('FILL_', 'CAR_', 'SLOT_')):
        eas.destroy_actor(a)
def top(lab):
    o, e = acts[lab].get_actor_bounds(False); return o.z + e.z
Z_GROUND, Z_ROAD = top('Town_Ground'), top('Town_Road')
print('ground top %.1f road top %.1f' % (Z_GROUND, Z_ROAD))
ar = unreal.AssetRegistryHelpers.get_asset_registry()
pk = {str(a.asset_name): str(a.package_name) for a in ar.get_assets_by_path('/Game/CitySampleBuildings', recursive=True) if str(a.asset_name).startswith('BPP_')}
FILL = ['BPP_CHB_Ref_A1_N1', 'BPP_NYAB_Ref_N1', 'BPP_SFJ_Ref_N1', 'BPP_CHF_Ref_A1_N1', 'BPP_NYAD_Ref_N1', 'BPP_CHC_Ref_A1_N1',
        'BPP_NYAC_Ref_N1', 'BPP_SFE_Ref_N1', 'BPP_NYAE_Ref_N1', 'BPP_CHA_Ref_N1', 'BPP_Bldg_Hero_Mid_NYG_Triangle_B01_N1', 'BPP_SFC_Ref_N1', 'BPP_CHE_Ref_A1_N1']
FILL = [f for f in FILL if f in pk]
WIDTH = {}
GAP, CURB = 250.0, 950.0
SEGS = [('N', 0, 7000), ('N', 15000, 20000), ('S', 0, 1500), ('S', 8500, 20000)]
fi = 0; n = 0
for side, x0, x1 in SEGS:
    cur = x0
    tries = 0
    while tries < len(FILL):
        name = FILL[fi % len(FILL)]
        w = WIDTH.get(name)
        if w is not None and cur + w > x1:
            fi += 1; tries += 1; continue
        yaw = 0.0 if side == 'N' else 180.0
        a = eas.spawn_actor_from_class(unreal.load_asset(pk[name]).generated_class(), unreal.Vector(cur, 0, 0), unreal.Rotator(0, 0, yaw))
        mn, mx = ism_bounds(a)
        w = mx[0] - mn[0]; WIDTH[name] = w
        if cur + w > x1:
            eas.destroy_actor(a); fi += 1; tries += 1; continue
        p = a.get_actor_location()
        dy = (CURB - mn[1]) if side == 'N' else (-CURB - mx[1])
        a.set_actor_location(unreal.Vector(p.x + cur - mn[0], p.y + dy, p.z + Z_GROUND - mn[2]), False, False)
        n += 1
        a.set_actor_label('FILL_%s_%02d_%s' % (side, n, name.replace('BPP_', '').replace('_N1', '')))
        print('FILL %s x %.0f..%.0f %s (D %.0f H %.0f)' % (side, cur, cur + w, name, mx[1] - mn[1], mx[2] - mn[2]))
        cur += w + GAP; fi += 1; tries = 0
# slot markers (thin coloured pads on the ground + text label)
cube = unreal.load_asset('/Engine/BasicShapes/Cube')
for lab, side, x0, x1 in (('SLOT_A_PlayerStudio', 'S', 1500, 8500), ('SLOT_B_MainApartment', 'N', 7000, 15000)):
    d = 3000.0
    yc = (CURB + d / 2) * (1 if side == 'N' else -1)
    s = eas.spawn_actor_from_object(cube, unreal.Vector((x0 + x1) / 2, yc, Z_GROUND + 1), unreal.Rotator(0, 0, 0))
    s.set_actor_scale3d(unreal.Vector((x1 - x0 - 200) / 100.0, d / 100.0, 0.02)); s.set_actor_label(lab)
    t = eas.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector((x0 + x1) / 2, yc, Z_GROUND + 400), unreal.Rotator(0, 90 if side == 'S' else -90, 0))
    t.text_render.set_editor_property('text', lab); t.text_render.set_editor_property('world_size', 250.0)
    t.text_render.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)
    t.set_actor_label(lab + '_Label')
# parked cars: whole-car _LOD static meshes, along both curbs
cars = sorted(str(a.package_name) for a in ar.get_assets_by_path('/Game/CitySampleVehicles', recursive=True)
              if str(a.asset_class_path.asset_name) == 'StaticMesh' and str(a.asset_name).endswith('_LOD')
              and ('vehCar' in str(a.asset_name) or 'vehVan' in str(a.asset_name)))
print('car meshes', [c.split('/')[-1] for c in cars])
rnd = random.Random(7)
nc = 0
for side in ('S', 'N'):
    x = 600.0 + rnd.uniform(0, 400)
    while x < 19300:
        if rnd.random() < 0.35:
            x += rnd.uniform(500, 1400); continue
        sm = unreal.load_asset(rnd.choice(cars))
        bb = sm.get_bounding_box(); L = bb.max.x - bb.min.x; Wc = bb.max.y - bb.min.y
        if x + L > 19500: break
        yaw = 0.0 if side == 'S' else 180.0
        y = (-500 + Wc / 2 + 40) if side == 'S' else (500 - Wc / 2 - 40)
        cx = x + L / 2
        a = eas.spawn_actor_from_object(sm, unreal.Vector(cx - ((bb.max.x + bb.min.x) / 2) * (1 if yaw == 0 else -1), y, Z_ROAD - bb.min.z), unreal.Rotator(0, 0, yaw))
        a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
        nc += 1; a.set_actor_label('CAR_%s_%02d_%s' % (side, nc, sm.get_name().replace('SM_', '').replace('_LOD', '')))
        x += L + rnd.uniform(150, 450)
print('fillers', n, 'cars', nc)
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
