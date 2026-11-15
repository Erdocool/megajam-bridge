import unreal, math
# Living room + master bedroom per flat (F1-F4): old repeated pieces retired (hidden, moved 5000 down, original spot in a tag; nothing deleted),
# new set per flat placed against walls: library seating oriented by its backrest (vertex analysis), kit-built case goods/beds/TVs (exact).
# Doorman flat: duplicate coffee table + shoe rack retired, its own set re-arranged. Keys/NPCs in those rooms moved to free spots.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
V, R, LC = unreal.Vector, unreal.Rotator, unreal.LinearColor
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
CUBE = unreal.load_asset('/Engine/BasicShapes/Cube'); CYL = unreal.load_asset('/Engine/BasicShapes/Cylinder')
D = '/Game/DirectorsCut/Materials/MJ_Vary'; MC = unreal.load_asset('/Game/DirectorsCut/Materials/M_DC_Color')
MATS = {}
def col(name, c, rough=0.6):
    if name in MATS: return MATS[name]
    p = D + '/MI_MJ_Room_' + name
    if EAL.does_asset_exist(p): m = unreal.load_asset(p)
    else:
        m = AT.create_asset('MI_MJ_Room_' + name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(m, MC); MEL.set_material_instance_vector_parameter_value(m, 'Color', LC(c[0], c[1], c[2], 1))
        MEL.set_material_instance_scalar_parameter_value(m, 'Roughness', rough); EAL.save_loaded_asset(m, False)
    MATS[name] = m; return m
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
TAGS = lambda: [unreal.Name('DC_Bldg'), unreal.Name('MJ_Room')]
stat = {}
def bump(fl): stat[fl] = stat.get(fl, 0) + 1
def box(lab, fl, x0, x1, y0, y1, z0, z1, mat, mesh=None):
    a = acts.get(lab) or eas.spawn_actor_from_object(mesh or CUBE, V(0, 0, 0), R(0, 0, 0)); acts[lab] = a
    a.set_actor_label(lab); a.set_actor_rotation(R(0, 0, 0), False)
    a.set_actor_scale3d(V(max(0.01, (x1 - x0) / 100.0), max(0.01, (y1 - y0) / 100.0), max(0.01, (z1 - z0) / 100.0)))
    a.set_actor_location(V((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0), False, False)
    a.static_mesh_component.set_material(0, mat); a.set_folder_path('Furniture/Floor%d/Rooms' % fl); a.tags = TAGS(); bump(fl); return a
def facing(sm):  # local back direction of a seat/bed: where the tall central part (backrest) sits
    md = sm.get_static_mesh_description(0); n = md.get_vertex_count(); st = max(1, n // 2500)
    pts = [md.get_vertex_position(unreal.VertexID(i)) for i in range(0, n, st)]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    x0, x1, y0, y1, z0, z1 = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; dx, dy = x1 - x0, y1 - y0; ax = 'x' if dx < dy else 'y'
    def off(lo, hi):
        s = [p for p in pts if z0 + lo * (z1 - z0) < p.z <= z0 + hi * (z1 - z0) and (abs(p.y - cy) < 0.3 * dy if ax == 'x' else abs(p.x - cx) < 0.3 * dx)]
        if not s: return 0
        return (sum(p.x for p in s) / len(s) - cx) / dx if ax == 'x' else (sum(p.y for p in s) / len(s) - cy) / dy
    o = off(0.62, 1.01)
    if abs(o) < 0.08: o = off(0.42, 0.62)
    return (1 if o > 0 else -1, 0) if ax == 'x' else (0, 1 if o > 0 else -1)
WALLDIR = {'N': (0, -1), 'S': (0, 1), 'W': (-1, 0), 'E': (1, 0)}
def rot(v, deg):
    c, s = round(math.cos(math.radians(deg))), round(math.sin(math.radians(deg))); return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)
def lib(lab, fl, path, rect, wall, along, width, z, kind='seat', maxd=999, gap=2, a=None):
    """seat: backrest to `wall`; sym: long side along the wall. width = target size along the wall (uniform scale 0.5-2.2)."""
    sm = unreal.load_asset(path)
    if a is None:
        a = acts.get(lab) or eas.spawn_actor_from_object(sm, V(0, 0, z), R(0, 0, 0)); acts[lab] = a; a.set_actor_label(lab)
    want = WALLDIR[wall]
    if kind == 'seat':
        b = facing(sm); yaw = [d for d in (0, 90, 180, 270) if rot(b, d) == want][0]
    else:
        bb = sm.get_bounding_box(); lx = (bb.max.x - bb.min.x) >= (bb.max.y - bb.min.y)
        yaw = (0 if lx else 90) if wall in ('N', 'S') else (90 if lx else 0)
    a.set_actor_scale3d(V(1, 1, 1)); a.set_actor_rotation(R(0, 0, yaw), False); a.set_actor_location(V(0, 0, z), False, False)
    o, e = a.get_actor_bounds(False)
    al, dp = (e.x * 2, e.y * 2) if wall in ('N', 'S') else (e.y * 2, e.x * 2)
    s = max(0.5, min(2.2, width / al, maxd / dp)); a.set_actor_scale3d(V(s, s, s))
    o, e = a.get_actor_bounds(False); loc = a.get_actor_location()
    x0, x1, y0, y1 = rect
    if wall == 'N': tx, ty = along, y0 + gap + e.y
    elif wall == 'S': tx, ty = along, y1 - gap - e.y
    elif wall == 'W': tx, ty = x0 + gap + e.x, along
    else: tx, ty = x1 - gap - e.x, along
    a.set_actor_location(V(loc.x + tx - o.x, loc.y + ty - o.y, loc.z + z - (o.z - e.z)), False, False)
    a.set_folder_path('Furniture/Floor%d/Rooms' % fl); a.tags = TAGS(); bump(fl); return a
def center(lab, fl, path, x, y, z, width, a=None):
    sm = unreal.load_asset(path)
    if a is None:
        a = acts.get(lab) or eas.spawn_actor_from_object(sm, V(x, y, z), R(0, 0, 0)); acts[lab] = a; a.set_actor_label(lab)
    bb = sm.get_bounding_box(); yaw = 0 if (bb.max.x - bb.min.x) >= (bb.max.y - bb.min.y) else 90
    a.set_actor_scale3d(V(1, 1, 1)); a.set_actor_rotation(R(0, 0, yaw), False); a.set_actor_location(V(0, 0, 0), False, False)
    o, e = a.get_actor_bounds(False); s = max(0.5, min(2.2, width / (e.x * 2))); a.set_actor_scale3d(V(s, s, s))
    o, e = a.get_actor_bounds(False); loc = a.get_actor_location()
    a.set_actor_location(V(loc.x + x - o.x, loc.y + y - o.y, loc.z + z - (o.z - e.z)), False, False)
    a.set_folder_path('Furniture/Floor%d/Rooms' % fl); a.tags = TAGS(); bump(fl); return a
def top(a): o, e = a.get_actor_bounds(False); return o.z + e.z
retired = {}
def retire(a, fl):
    if unreal.Name('MJ_Retired') in a.tags: return
    p = a.get_actor_location(); a.tags = list(a.tags) + [unreal.Name('MJ_Retired'), unreal.Name('MJ_Orig:%d,%d,%d' % (p.x, p.y, p.z))]
    a.set_actor_location(V(p.x, p.y, p.z - 5000), False, False); a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
    a.set_folder_path('Furniture/_Retired'); retired[fl] = retired.get(fl, 0) + 1
def kit_tvunit(P, fl, xc, w, d, h, body, topm, knob, y1=580):
    box(P + 'TVUnit', fl, xc - w / 2, xc + w / 2, y1 - 2 - d, y1 - 2, Z, Z + h, body)
    box(P + 'TVUnitTop', fl, xc - w / 2 - 1, xc + w / 2 + 1, y1 - 3 - d, y1 - 2, Z + h, Z + h + 2.5, topm)
    box(P + 'TVUnitSeam', fl, xc - 0.5, xc + 0.5, y1 - 2.5 - d, y1 - 2 - d, Z + 4, Z + h - 3, knob)
    box(P + 'TVUnitKnobA', fl, xc - 8, xc - 4, y1 - 4 - d, y1 - 2 - d, Z + h * 0.6, Z + h * 0.6 + 3, knob)
    box(P + 'TVUnitKnobB', fl, xc + 4, xc + 8, y1 - 4 - d, y1 - 2 - d, Z + h * 0.6, Z + h * 0.6 + 3, knob)
    return Z + h + 2.5
def kit_tv(P, fl, xc, w, zt, y1=580, crt=False):
    blk = col('TVBlack', (0.02, 0.02, 0.025), 0.3); scr = col('TVScreen', (0.03, 0.05, 0.08), 0.1)
    if crt:
        box(P + 'TV', fl, xc - w / 2, xc + w / 2, y1 - 48, y1 - 8, zt, zt + w * 0.75, col('CRTBeige', (0.55, 0.5, 0.42)))
        box(P + 'TVScreen', fl, xc - w * 0.4, xc + w * 0.4, y1 - 49, y1 - 48, zt + w * 0.1, zt + w * 0.62, scr); return
    box(P + 'TVStand', fl, xc - 12, xc + 12, y1 - 30, y1 - 14, zt, zt + 2, blk); box(P + 'TVNeck', fl, xc - 3, xc + 3, y1 - 20, y1 - 16, zt, zt + 12, blk)
    box(P + 'TV', fl, xc - w / 2, xc + w / 2, y1 - 22, y1 - 17, zt + 10, zt + 10 + w * 0.58, blk)
    box(P + 'TVScreen', fl, xc - w / 2 + 2, xc + w / 2 - 2, y1 - 22.5, y1 - 22, zt + 12, zt + 8 + w * 0.58, scr)
def kit_shelf(P, fl, y0, y1, depth, h, n, body, books, x0=14):
    box(P + 'ShelfSideA', fl, x0 + 2, x0 + 2 + depth, y0, y0 + 2.5, Z, Z + h, body); box(P + 'ShelfSideB', fl, x0 + 2, x0 + 2 + depth, y1 - 2.5, y1, Z, Z + h, body)
    for i in range(n + 1):
        zz = Z + 2 + i * (h - 4) / n; box(P + 'ShelfBoard%d' % i, fl, x0 + 2, x0 + 2 + depth, y0 + 2.5, y1 - 2.5, zz, zz + 2, body)
        if 0 < i < n or i == 0:
            if i < n:
                for j, (c, bw, bh) in enumerate(books[(i * 3) % len(books):] [:3]):
                    yy = y0 + 8 + j * 26; box(P + 'Books%d_%d' % (i, j), fl, x0 + 6, x0 + depth - 2, yy, yy + bw, zz + 2, zz + 2 + bh, c)
def kit_bed(P, fl, w, frame, sheet, duvet, pillow, head_h, x1=975, yc=210, L=200, fh=32):
    y0, y1 = yc - w / 2, yc + w / 2; x0 = x1 - 2 - L
    box(P + 'BedFrame', fl, x0, x1 - 2, y0, y1, Z, Z + fh, frame)
    box(P + 'BedHead', fl, x1 - 8, x1 - 2, y0 - 2, y1 + 2, Z, Z + head_h, frame)
    box(P + 'BedMattress', fl, x0 + 2, x1 - 9, y0 + 2, y1 - 2, Z + fh, Z + fh + 20, sheet)
    box(P + 'BedDuvet', fl, x0 + 1, x1 - 60, y0 + 1, y1 - 1, Z + fh + 12, Z + fh + 25, duvet)
    for i, (a, b) in enumerate(((y0 + 8, yc - 4), (yc + 4, y1 - 8)) if w >= 140 else ((y0 + 10, y1 - 10),)):
        box(P + 'BedPillow%d' % i, fl, x1 - 52, x1 - 12, a, b, Z + fh + 20, Z + fh + 32, pillow)
    return y0, y1
def kit_night(P, fl, y0, y1, body, knob, h=50, x1=975, d=40):
    if y1 - y0 < 28: return None
    box(P + 'Body', fl, x1 - 2 - d, x1 - 2, y0, y1, Z, Z + h, body)
    box(P + 'Knob', fl, x1 - 4 - d, x1 - 2 - d, (y0 + y1) / 2 - 2, (y0 + y1) / 2 + 2, Z + h * 0.65, Z + h * 0.65 + 3, knob); return Z + h
def kit_wardrobe(P, fl, body, knob, h=200, x0=676, x1=764, y0=82, d=58):
    box(P + 'Wardrobe', fl, x0, x1, y0, y0 + d, Z, Z + h, body)
    box(P + 'WardrobeSeam', fl, (x0 + x1) / 2 - 0.5, (x0 + x1) / 2 + 0.5, y0 + d, y0 + d + 0.5, Z + 4, Z + h - 4, knob)
    for i, xx in enumerate(((x0 + x1) / 2 - 6, (x0 + x1) / 2 + 3)): box(P + 'WardrobeKnob%d' % i, fl, xx, xx + 3, y0 + d, y0 + d + 2, Z + h * 0.5, Z + h * 0.5 + 10, knob)
DO = '/Game/DetectiveOffice/StaticMeshes/'; FF = '/Game/FreeFurniturePack/Meshes/'; LU = '/Game/LucapyAssets/OldLivingRoom/StaticMeshes/Props/'
FLATS = {
 1: dict(sofa=('/Game/Fab/Leather_Sofa_3D_Model/leather-sofa-fbx', 200), arm=(FF + 'SM_Modern_Armchair', 85), coffee=('/Game/DirectorsCut/Props/CoffeeTable/SM_CoffeeTable', 95), lamp=(DO + 'SM_lamp_1', 61), blamp=(FF + 'SM_Bed_lamp_3', 30),
         body=(0.9, 0.9, 0.88), top=(0.62, 0.45, 0.28), knob=(0.75, 0.6, 0.25), rug=(0.2, 0.5, 0.55), bed=(160, (0.62, 0.45, 0.28), (0.95, 0.95, 0.95), (0.25, 0.6, 0.65), (0.95, 0.95, 0.9), 100), tvw=110, unit=(160, 42, 50), shelf=(30, 175, 4), crt=False),
 2: dict(sofa=(FF + 'SM_Modern_Sofa_2', 210), arm=(FF + 'SM_Elegant_chair', 80), coffee=(LU + 'SM_Table_Center_A0', 100), lamp=('/Game/DirectorsCut/Props/FloorLamp/SM_FloorLamp', 30), blamp=(DO + 'SM_lamp_2', 30),
         body=(0.04, 0.04, 0.045), top=(0.55, 0.35, 0.18), knob=(0.7, 0.7, 0.72), rug=(0.75, 0.55, 0.15), bed=(140, (0.2, 0.2, 0.22), (0.9, 0.9, 0.88), (0.85, 0.6, 0.1), (0.3, 0.3, 0.32), 70), tvw=120, unit=(180, 38, 42), shelf=(35, 120, 2), crt=False),
 3: dict(sofa=(DO + 'SM_sofa1', 190), arm=(DO + 'SM_armchair1', 85), coffee=(DO + 'SM_coffee_table', 100), lamp=None, blamp=(DO + 'SM_lamp_001', 35),
         body=(0.22, 0.12, 0.07), top=(0.18, 0.1, 0.06), knob=(0.8, 0.8, 0.82), rug=(0.38, 0.06, 0.08), bed=(160, (0.22, 0.12, 0.07), (0.85, 0.8, 0.7), (0.85, 0.8, 0.68), (0.9, 0.88, 0.8), 110), tvw=0, unit=(150, 45, 75), shelf=(32, 190, 5), crt=False),
 4: dict(sofa=(FF + 'SM_Classic_Leather_Sofa', 220), arm=(FF + 'SM_Classic_Leather_Armchair', 90), coffee=(FF + 'SM_Coffee_Table', 90), lamp=None, blamp=(DO + 'SM_lamp_001', 35),
         body=(0.3, 0.09, 0.07), top=(0.25, 0.07, 0.05), knob=(0.8, 0.62, 0.2), rug=(0.08, 0.1, 0.25), bed=(180, (0.3, 0.09, 0.07), (0.92, 0.92, 0.9), (0.08, 0.1, 0.28), (0.92, 0.92, 0.9), 130), tvw=100, unit=(170, 45, 55), shelf=(35, 200, 5), crt=False),
}
BOOKS = [((0.6, 0.1, 0.1), 18, 24), ((0.1, 0.25, 0.5), 22, 28), ((0.8, 0.7, 0.3), 16, 22), ((0.15, 0.4, 0.2), 20, 26), ((0.85, 0.85, 0.8), 14, 20)]
SAL = (30, 446, 80, 580); MAS = (674, 975, 80, 340)
inside = lambda p, r, m=5: r[0] - m <= p.x <= r[1] + m and r[2] - m <= p.y <= r[3] + m
for fl, F in FLATS.items():
    Z = 300.0 * fl + 1.5; P = 'Furn_F%d_' % fl
    for a in list(acts.values()):
        if not isinstance(a, unreal.StaticMeshActor) or not str(a.get_folder_path()).startswith('Furniture/Floor%d' % fl): continue
        if unreal.Name('MJ_Room') in a.tags or unreal.Name('MJ_Hall') in a.tags: continue
        p = a.get_actor_location(); l = a.get_actor_label()
        if not (Z - 20 < p.z < Z + 260): continue
        if (inside(p, SAL) or inside(p, MAS)) and not any(k in l for k in ('Curtain', 'Photo', 'Picture')): retire(a, fl)
        elif 'Photo' in l and inside(p, SAL):
            o, e = a.get_actor_bounds(False)
            if e.y < e.x: a.set_actor_location(V(380, 580 - 1 - e.y, Z + 150), False, False)
            else: a.set_actor_location(V(14 + 1 + e.x, 450, Z + 150), False, False)
    mb, mt, mk = col('Body%d' % fl, F['body']), col('Top%d' % fl, F['top'], 0.45), col('Knob%d' % fl, F['knob'], 0.3)
    box(P + 'Salon_Rug', fl, 120, 340, 150, 345, Z, Z + 1, col('Rug%d' % fl, F['rug'], 0.95))
    lib(P + 'Salon_Sofa', fl, F['sofa'][0], SAL, 'N', 230, F['sofa'][1], Z, maxd=110)
    ct = center(P + 'Salon_Coffee', fl, F['coffee'][0], 230, 250, Z + 1, F['coffee'][1])
    lib(P + 'Salon_Armchair', fl, F['arm'][0], SAL, 'E', 165, F['arm'][1], Z, maxd=100)
    uw, ud, uh = F['unit']; zt = kit_tvunit(P + 'Salon_', fl, 230, uw, ud, uh, mb, mt, mk)
    if F['tvw']: kit_tv(P + 'Salon_', fl, 230, F['tvw'], zt, crt=F['crt'])
    sd, sh, sn = F['shelf']; kit_shelf(P + 'Salon_', fl, 395, 495, sd, sh, sn, mt if fl in (3, 4) else mb, [(col('Book%d' % i, c), w, h) for i, (c, w, h) in enumerate(BOOKS)])
    if F['lamp']: lib(P + 'Salon_FloorLamp', fl, F['lamp'][0], SAL, 'N', 60, F['lamp'][1], Z, kind='sym')
    bw, fr, sh_, du, pi, hh = F['bed']
    by0, by1 = kit_bed(P + 'Master_', fl, bw, col('Frame%d' % fl, fr, 0.5), col('Sheet%d' % fl, sh_, 0.9), col('Duvet%d' % fl, du, 0.9), col('Pillow%d' % fl, pi, 0.9), hh)
    box(P + 'Master_Rug', fl, 715, 905, 105, 315, Z, Z + 1, col('MRug%d' % fl, (F['rug'][0] * 0.8 + 0.1, F['rug'][1] * 0.8 + 0.1, F['rug'][2] * 0.8 + 0.1), 0.95))
    t1 = kit_night(P + 'Master_NightN', fl, 82, by0 - 3, mb, mk); kit_night(P + 'Master_NightS', fl, by1 + 3, 338, mb, mk)
    if t1 and F['blamp']: center(P + 'Master_BedLamp', fl, F['blamp'][0], 955, (82 + by0 - 3) / 2, t1, min(F['blamp'][1], by0 - 3 - 82 - 4))
    kit_wardrobe(P + 'Master_', fl, mt if fl in (3, 4) else mb, mk)
    if fl == 2 and 'Key_Flat3_Pickup' in acts:  # key that sat on the old salon table -> new coffee table
        k = acts['Key_Flat3_Pickup']; px = acts.get('Proxy_Key_Flat3_Pickup'); kz = top(ct) + 1
        off = (px.get_actor_location() - k.get_actor_location()) if px else V(0, 0, 25)
        k.set_actor_location(V(215, 245, kz), False, False)
        if px: px.set_actor_location(V(215, 245, kz) + off, False, False)
for lab, (x, y, z, yaw) in {'NPC_Kemal_Aksoy': (395, 470, 301.5, 90), 'NPC_Deniz_Aydin': (395, 470, 601.5, 90)}.items():
    if lab in acts: acts[lab].set_actor_location(V(x, y, z), False, False); acts[lab].set_actor_rotation(R(0, 0, yaw), False)
# doorman living (x50..520, y50..560): retire the duplicate coffee table + shoe rack, re-arrange his own set
DL = (50, 520, 50, 560); Z = 1.5
for l in ('Furn_F0_Living_Coffee', 'Furn_F0_Living_ShoeRack'):
    if l in acts: retire(acts[l], 0)
g = lambda l: acts.get(l)
if g('Furn_DM_Living_Couch'): lib('Furn_DM_Living_Couch', 0, g('Furn_DM_Living_Couch').static_mesh_component.static_mesh.get_path_name().split('.')[0], DL, 'N', 310, 270, Z, maxd=95, a=g('Furn_DM_Living_Couch'))
t = g('Furn_DM_Living_Table')
if t:
    old = t.get_actor_location(); carry = [(c, c.get_actor_location() - old) for c in (g('Furn_DM_Living_Jar'), g('Furn_DM_Living_Dish')) if c]
    center('Furn_DM_Living_Table', 0, t.static_mesh_component.static_mesh.get_path_name().split('.')[0], 390, 400, Z, 150, a=t)
    for c, d in carry: c.set_actor_location(t.get_actor_location() + d, False, False)
    if g('Furn_F0_Living_Plant'): g('Furn_F0_Living_Plant').set_actor_location(V(440, 390, top(t) + 0.5), False, False)
    if g('Furn_DM_Living_Lamp'): lp = g('Furn_DM_Living_Lamp'); lp.set_actor_location(V(335, 385, top(t) + 0.5), False, False)
if g('Furn_DM_Living_Chair'):
    ch = g('Furn_DM_Living_Chair'); sm = ch.static_mesh_component.static_mesh; b = facing(sm)
    yaw = [d for d in (0, 90, 180, 270) if rot(b, d) == (0, 1)][0]; ch.set_actor_rotation(R(0, 0, yaw), False); ch.set_actor_location(V(390, 470, Z), False, False)
    o, e = ch.get_actor_bounds(False); ch.set_actor_location(ch.get_actor_location() + V(390 - o.x, 478 - o.y, Z - (o.z - e.z)), False, False)
if g('Furn_DM_Living_Rug'): g('Furn_DM_Living_Rug').set_actor_location(V(300, 250, 2), False, False)
if g('Furn_DM_Living_Photo'):
    ph = g('Furn_DM_Living_Photo'); o, e = ph.get_actor_bounds(False)
    ph.set_actor_location(V(310, 50 + 1 + e.y, 160), False, False) if e.y < e.x else ph.set_actor_location(V(50 + 1 + e.x, 300, 160), False, False)
if 'NPC_Hasan_Demir' in acts: acts['NPC_Hasan_Demir'].set_actor_location(V(250, 330, 1.5), False, False); acts['NPC_Hasan_Demir'].set_actor_rotation(R(0, 0, 180), False)
print('ROOMS new', stat, 'retired', retired)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
