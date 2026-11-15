import unreal, math, time
# NewMegaJam step 3: Fab city (Main's static meshes) as a backdrop around L_Town. Main is only read; only L_Town is saved.
t0 = time.time()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
YAW, DX, DY = 270.0, -20000.0, 145000.0
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0, 'dirty map'
les.load_level('/Game/Main') if unreal.EditorAssetLibrary.does_asset_exist('/Game/Main') else None
if ues.get_editor_world().get_name() != 'Main':
    p = [a for a in unreal.EditorAssetLibrary.list_assets('/Game', True) if a.split('.')[-1] == 'Main']
    les.load_level(p[0].split('.')[0])
src = []
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and not str(a.get_folder_path()).startswith('Lighting'):
        c = a.static_mesh_component; sm = c.static_mesh
        if sm: src.append((a.get_actor_label(), sm, a.get_actor_transform(), list(c.get_editor_property('override_materials'))))
print('src', len(src), [s[0][:18] for s in src])
les.load_level('/Game/DirectorsCut/Maps/L_Town')
assert ues.get_editor_world().get_name() == 'L_Town'
cy, sy = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
def tw(x, y): return (cy * x - sy * y + DX, sy * x + cy * y + DY)
ZB = [(0, 5404, -2814, -926), (10500, 17500, 2150, 13734), (11000, 12950, 2950, 12934)]  # studio, SFA, bounds area
ZS = [(0, 20000, -900, 900), (11100, 12900, 900, 17000)]
inz = lambda x, y, Z: any(z[0] <= x <= z[1] and z[2] <= y <= z[3] for z in Z)
gmax = -1e9; gmin = 1e9; bz = 0; sp = -1e9; bcells = set()
for lab, sm, tr, _ in src:
    isb = 'Building' in lab
    for s in range(sm.get_num_sections(0)):
        for v in unreal.ProceduralMeshLibrary.get_section_from_static_mesh(sm, 0, s)[0]:
            p = tr.transform_location(v); x, y = tw(p.x, p.y)
            if x < -40000 or x > 60000 or y < -40000 or y > 60000: continue
            if isb:
                bcells.add((int(x // 1000), int(y // 1000), int(p.z // 1000)))
                if inz(x, y, ZB + ZS): bz += 1
            elif inz(x, y, ZB):
                gmax = max(gmax, p.z); gmin = min(gmin, p.z)
            elif inz(x, y, ZS): sp = max(sp, p.z)
DZ = -gmax - 5.0
print('ground in zones z', round(gmin), round(gmax), 'DZ', round(DZ), 'bldg verts in zones', bz, 'street poke cm', round(sp + DZ), round(time.time() - t0))
# hide (not delete) L_Town fillers that would intersect city buildings
def ism_bounds(actor):
    mn = [1e18] * 3; mx = [-1e18] * 3
    for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        if not sm: continue
        bb = sm.get_bounding_box(); lo, hi = bb.min, bb.max
        cs = [unreal.Vector(x, y, z) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        n = c.get_instance_count()
        for i in range(0, n, max(1, n // 300)):
            t = c.get_instance_transform(i, True)
            for q in cs:
                w = t.transform_location(q)
                for k, val in enumerate((w.x, w.y, w.z)): mn[k] = min(mn[k], val); mx[k] = max(mx[k], val)
    return mn, mx
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
hid = []
for l, a in acts.items():
    if not l.startswith('FILL'): continue
    mn, mx = ism_bounds(a)
    if mn[0] > 1e17: continue
    hit = any((cx, cy_, cz) in bcells for cx in range(int(mn[0] // 1000), int(mx[0] // 1000) + 1) for cy_ in range(int(mn[1] // 1000), int(mx[1] // 1000) + 1)
              for cz in range(int((mn[2] - DZ) // 1000), int((mx[2] - DZ) // 1000) + 1))
    if hit:
        a.set_is_temporarily_hidden_in_editor(False); a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
        for c in a.get_components_by_class(unreal.PrimitiveComponent): c.set_visibility(False)
        a.tags = list(a.tags) + [unreal.Name('MJ_HiddenForCity')]; hid.append(l[:12])
print('fillers hidden', hid)
n = 0
for lab, sm, tr, mats in src:
    l2 = 'CITY_' + lab
    a = acts.get(l2) or eas.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label(l2); a.set_folder_path('FabCity')
    loc = tr.translation; x, y = tw(loc.x, loc.y)
    r = tr.rotation.rotator()
    a.set_actor_location_and_rotation(unreal.Vector(x, y, loc.z + DZ), unreal.Rotator(roll=r.roll, pitch=r.pitch, yaw=r.yaw + YAW), False, False)
    a.set_actor_scale3d(tr.scale3d)
    c = a.static_mesh_component
    for i, m in enumerate(mats):
        if m: c.set_material(i, m)
    c.set_editor_property('cast_shadow', False); c.set_collision_profile_name('NoCollision'); n += 1
print('city actors', n, 'saved', les.save_current_level(), round(time.time() - t0))
