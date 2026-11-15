import unreal, math
# (dc_17) Child/study rooms per flat, built on the dc_15 helpers. Original header of dc_15:
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

retired = {}
def bb(a): o, e = a.get_actor_bounds(False); return (o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y, o.z - e.z, o.z + e.z)
def put(a, cx, cy, zb, yaw=None):  # move a prop so its footprint is centred on (cx,cy) and it stands on zb
    if a is None: return
    if yaw is not None: a.set_actor_rotation(R(0, 0, yaw), False)
    b = bb(a); p = a.get_actor_location()
    a.set_actor_location(V(p.x + cx - (b[0] + b[1]) / 2, p.y + cy - (b[2] + b[3]) / 2, p.z + zb - b[4]), False, False)
def tz(lab): return bb(acts[lab])[5]
def desk(P, fl, x0, x1, y0, y1, topm, legm, h=75):
    box(P + 'DeskTop', fl, x0, x1, y0, y1, Z + h - 4, Z + h, topm)
    for i, (lx, ly) in enumerate(((x0 + 2, y0 + 2), (x1 - 6, y0 + 2), (x0 + 2, y1 - 6), (x1 - 6, y1 - 6))): box(P + 'DeskLeg%d' % i, fl, lx, lx + 4, ly, ly + 4, Z, Z + h - 4, legm)
    return Z + h
def chair(P, fl, cx, cy, face, seatm, framem):
    box(P + 'ChairSeat', fl, cx - 21, cx + 21, cy - 21, cy + 21, Z + 42, Z + 47, seatm)
    for i, (lx, ly) in enumerate(((cx - 20, cy - 20), (cx + 17, cy - 20), (cx - 20, cy + 17), (cx + 17, cy + 17))): box(P + 'ChairLeg%d' % i, fl, lx, lx + 3, ly, ly + 3, Z, Z + 42, framem)
    bx = {'+x': (cx - 21, cx - 17, cy - 21, cy + 21), '-x': (cx + 17, cx + 21, cy - 21, cy + 21), '+y': (cx - 21, cx + 21, cy - 21, cy - 17), '-y': (cx - 21, cx + 21, cy + 17, cy + 21)}[face]
    box(P + 'ChairBack', fl, bx[0], bx[1], bx[2], bx[3], Z + 47, Z + 92, framem)
def shelf(P, fl, x0, x1, y0, y1, h, n, body, books):
    lx = (x1 - x0) >= (y1 - y0)
    if lx: box(P + 'ShelfSideA', fl, x0, x0 + 2.5, y0, y1, Z, Z + h, body); box(P + 'ShelfSideB', fl, x1 - 2.5, x1, y0, y1, Z, Z + h, body)
    else: box(P + 'ShelfSideA', fl, x0, x1, y0, y0 + 2.5, Z, Z + h, body); box(P + 'ShelfSideB', fl, x0, x1, y1 - 2.5, y1, Z, Z + h, body)
    box(P + 'ShelfBack', fl, *((x0, x1, y1 - 1.5, y1) if lx and y1 > 700 else (x0, x1, y0, y0 + 1.5) if lx else (x1 - 1.5, x1, y0, y1) if x1 > 900 else (x0, x0 + 1.5, y0, y1)), Z, Z + h, body)
    L = (x1 - x0) if lx else (y1 - y0)
    for i in range(n + 1):
        zz = Z + 2 + i * (h - 4) / n
        box(P + 'ShelfBoard%d' % i, fl, x0 + (2.5 if lx else 0), x1 - (2.5 if lx else 0), y0 + (0 if lx else 2.5), y1 - (0 if lx else 2.5), zz, zz + 2, body)
        if i == n: continue
        u = 6 + (i * 7) % 11
        for j in range(6):
            c, bw, bh = books[(i * 2 + j) % len(books)]
            if u + bw > L - 6 or bh > (h - 4) / n - 4: break
            if (i + j) % 4 == 3: u += 10; continue
            if lx: box(P + 'Book%d_%d' % (i, j), fl, x0 + u, x0 + u + bw, y0 + 4, y1 - 4, zz + 2, zz + 2 + bh, c)
            else: box(P + 'Book%d_%d' % (i, j), fl, x0 + 4, x1 - 4, y0 + u, y0 + u + bw, zz + 2, zz + 2 + bh, c)
            u += bw + 1
def mvkey(lab, x, y, z):
    k = acts.get(lab); px = acts.get('Proxy_' + lab)
    if not k: return
    off = (px.get_actor_location() - k.get_actor_location()) if px else V(0, 0, 25)
    k.set_actor_location(V(x, y, z), False, False)
    if px: px.set_actor_location(V(x, y, z) + off, False, False)
def npc(lab, x, y, z, yaw):
    if lab in acts: acts[lab].set_actor_location(V(x, y, z), False, False); acts[lab].set_actor_rotation(R(0, 0, yaw), False)
KEEP = ('Picture', 'Photo', 'Curtain', 'Store_Cupboard')
CARRY = ('TeddyBear', 'ToyBlocks', 'ToyCar', 'SewingMachine', 'Child_Lamp', 'Study_Lamp', 'Study_Book', 'Study_Folder', 'Study_Phone', 'Study_Safe')
for fl in (1, 2, 3, 4):
    for a in list(acts.values()):
        if not isinstance(a, unreal.StaticMeshActor) or unreal.Name('MJ_Retired') in a.tags: continue
        f = str(a.get_folder_path()); l = a.get_actor_label()
        if not f.startswith('Furniture/Floor%d' % fl) or f.endswith('/Rooms'): continue
        p = a.get_actor_location()
        if 674 < p.x < 976 and 354 < p.y < 780 and int(p.z // 300) == fl and not any(k in l for k in KEEP + CARRY): retire(a, fl)
B3 = lambda m: [(m[0], 4, 26), (m[1], 5, 22), (m[2], 3, 28), (m[0], 6, 20), (m[1], 4, 24)]
g = lambda l: acts.get(l)
# ---- Flat 1: kid room + father's study (white/oak/teal) ----
fl = 1; Z = 301.5; P = 'Furn_F1_Kid_'
W, OAK, TEAL, RED, YEL = col('KidWhite', (0.85, 0.85, 0.82), 0.5), col('F1_Oak', (0.55, 0.38, 0.22)), col('KidTeal', (0.1, 0.5, 0.5)), col('KidRed', (0.7, 0.12, 0.1)), col('KidYellow', (0.85, 0.65, 0.1))
box(P + 'Rug', fl, 690, 900, 470, 550, Z, Z + 1, col('KidRugBlue', (0.25, 0.45, 0.75), 0.9))
kit_bed(P, fl, 96, W, W, TEAL, W, 70, x1=975, yc=405, L=190, fh=28)
nz = kit_night(P + 'Night', fl, 458, 496, W, OAK, h=48)
kit_wardrobe(P, fl, W, OAK, h=170, x0=676, x1=752, y0=356, d=52)
dz = desk(P, fl, 775, 880, 512, 558, OAK, W, h=68); chair(P, fl, 828, 488, '+y', TEAL, W)
put(g('Furn_F1_Child_Lamp'), 954, 477, nz); put(g('Furn_F1_TeddyBear'), 940, 380, Z + 28 + 20)
put(g('Furn_F1_ToyBlocks'), 715, 525, Z + 1); put(g('Furn_F1_ToyCar'), 750, 535, Z + 1)
box(P + 'ToyBox', fl, 676, 706, 512, 556, Z, Z + 30, RED)
npc('NPC_Elif_Aksoy', 925, 527, Z, 180)
P = 'Furn_F1_Std_'
dz = desk(P, fl, 905, 973, 605, 745, OAK, OAK, h=76); chair(P, fl, 878, 675, '+x', col('F1_Leather', (0.3, 0.17, 0.08)), OAK)
shelf(P, fl, 760, 900, 746, 778, 190, 5, OAK, B3([TEAL, RED, W]))
box(P + 'Cupboard', fl, 760, 880, 576, 618, Z, Z + 90, W)
put(g('Furn_F1_Study_Lamp'), 950, 725, dz); mvkey('Key_Doorman_Pickup', 935, 640, dz + 1)
box(P + 'Rug', fl, 780, 890, 625, 725, Z, Z + 1, col('F1_RugStudy', (0.55, 0.5, 0.42), 0.9))
# ---- Flat 2: sewing room + study (black/walnut/mustard) ----
fl = 2; Z = 601.5; P = 'Furn_F2_Sew_'
BLK, WAL, MUS = col('F2_Black', (0.04, 0.04, 0.04), 0.4), col('F2_Walnut', (0.32, 0.2, 0.1)), col('F2_Mustard', (0.75, 0.55, 0.1))
dz = desk(P, fl, 905, 973, 395, 525, WAL, BLK, h=74); chair(P, fl, 878, 460, '+x', MUS, BLK)
put(g('Furn_F2_SewingMachine'), 940, 455, dz, ); put(g('Furn_F2_Child_Lamp'), 950, 505, dz)
box(P + 'FabricChest', fl, 760, 890, 356, 402, Z, Z + 95, WAL)
for i, c in enumerate(((0.6, 0.15, 0.2), (0.2, 0.35, 0.6), (0.85, 0.8, 0.7))): box(P + 'Fabric%d' % i, fl, 770 + i * 40, 805 + i * 40, 362, 396, Z + 95, Z + 95 + 6 + 3 * i, col('Fabric%d' % i, c, 0.95))
box(P + 'DayBed', fl, 770, 890, 488, 558, Z, Z + 40, BLK); box(P + 'DayBedPad', fl, 772, 888, 490, 556, Z + 40, Z + 52, MUS)
box(P + 'DressPole', fl, 718, 722, 530, 534, Z, Z + 120, BLK, CYL); box(P + 'DressForm', fl, 704, 736, 516, 548, Z + 120, Z + 175, col('F2_Linen', (0.8, 0.75, 0.62), 0.95), CYL)
box(P + 'Rug', fl, 730, 880, 410, 480, Z, Z + 1, col('F2_RugSew', (0.45, 0.12, 0.12), 0.9))
P = 'Furn_F2_Std_'
dz = desk(P, fl, 760, 900, 576, 636, BLK, BLK, h=76); chair(P, fl, 830, 662, '-y', BLK, WAL)
shelf(P, fl, 940, 974, 600, 760, 195, 5, WAL, B3([MUS, BLK, col('F2_Cream', (0.8, 0.75, 0.6))]))
box(P + 'FileCab', fl, 676, 724, 734, 778, Z, Z + 105, col('F2_Steel', (0.35, 0.36, 0.38), 0.35))
put(g('Furn_F2_Study_Lamp'), 880, 600, dz)
# ---- Flat 3: dusty store room + study (dark walnut, sheets) ----
fl = 3; Z = 901.5; P = 'Furn_F3_Store_'
DW, SHEET, CARD, MET = col('F3_DarkWalnut', (0.2, 0.12, 0.07)), col('F3_DustSheet', (0.7, 0.68, 0.62), 0.95), col('Cardboard', (0.55, 0.42, 0.26), 0.9), col('F3_Metal', (0.3, 0.3, 0.3), 0.5)
cb = bb(acts['Furn_F3_Store_Cupboard']) if 'Furn_F3_Store_Cupboard' in acts else (0, 0, 0, 0, 0, 0)
if cb[1] < 925 or cb[3] < 354 or cb[2] > 560:
    shelf(P, fl, 935, 974, 360, 556, 200, 4, MET, [(CARD, 30, 30), (CARD, 25, 35), (SHEET, 40, 25)])
else:
    shelf(P, fl, 760, 920, 356, 392, 200, 4, MET, [(CARD, 30, 30), (CARD, 25, 35), (SHEET, 40, 25)])
for i, (x0, y0, w, h) in enumerate(((800, 500, 50, 40), (805, 505, 40, 30), (860, 515, 40, 35))):
    zb = Z + (40 if i == 1 else 0); box(P + 'Box%d' % i, fl, x0, x0 + w, y0, y0 + 40 if i != 1 else y0 + 30, zb, zb + h, CARD)
box(P + 'SheetLump', fl, 700, 760, 520, 556, Z, Z + 70, SHEET)
P = 'Furn_F3_Std_'
dz = desk(P, fl, 905, 973, 610, 750, DW, DW, h=78); chair(P, fl, 878, 680, '+x', col('F3_Bordo', (0.35, 0.05, 0.07)), DW)
shelf(P, fl, 720, 900, 576, 606, 200, 5, DW, B3([col('F3_Bordo', (0.35, 0.05, 0.07)), col('F3_Olive', (0.3, 0.3, 0.12)), SHEET]))
put(g('Furn_F3_Study_Book'), 940, 640, dz); put(g('Furn_F3_Study_Lamp'), 950, 730, dz); mvkey('Key_Manager_Pickup', 930, 690, dz + 1)
box(P + 'SheetChair', fl, 700, 750, 740, 778, Z, Z + 85, SHEET)
# ---- Flat 4: guest room + study (mahogany/gold/navy) ----
fl = 4; Z = 1201.5; P = 'Furn_F4_Guest_'
MAH, GOLD, NAVY, CRM = col('F4_Mahogany', (0.3, 0.08, 0.05)), col('F4_Gold', (0.75, 0.55, 0.2), 0.3), col('F4_Navy', (0.05, 0.08, 0.25)), col('F4_Cream', (0.85, 0.8, 0.7))
kit_bed(P, fl, 120, MAH, CRM, NAVY, CRM, 100, x1=975, yc=417, L=200, fh=32)
nz = kit_night(P + 'Night', fl, 480, 520, MAH, GOLD, h=55)
box(P + 'Dresser', fl, 780, 900, 516, 558, Z, Z + 85, MAH)
for i in range(3): box(P + 'DresserKnob%d' % i, fl, 805 + i * 35, 810 + i * 35, 514, 516, Z + 60, Z + 64, GOLD)
box(P + 'Suitcase', fl, 735, 765, 365, 410, Z, Z + 60, col('F4_Tan', (0.5, 0.3, 0.15), 0.6))
box(P + 'Rug', fl, 700, 770, 425, 545, Z, Z + 1, NAVY)
put(g('Furn_F4_Child_Lamp'), 952, 500, nz)
P = 'Furn_F4_Std_'
dz = desk(P, fl, 770, 930, 712, 778, MAH, MAH, h=78); chair(P, fl, 850, 690, '+y', col('F4_Leather', (0.25, 0.05, 0.03)), MAH)
shelf(P, fl, 944, 974, 630, 770, 200, 5, MAH, B3([NAVY, GOLD, CRM]))
put(g('Furn_F4_Study_Safe'), 950, 600, Z); put(g('Furn_F4_Study_Folder'), 800, 745, dz); put(g('Furn_F4_Study_Phone'), 900, 745, dz); put(g('Furn_F4_Study_Lamp'), 870, 765, dz)
npc('NPC_Selim_Karaca', 735, 600, Z, 90)
# doorman bed lamp: nudge away from the bed by the overlap
la, be = g('Furn_DM_Bed_Lamp'), g('Furn_DM_Bed_Bed')
if la and be:
    a, b = bb(la), bb(be); ox = min(a[1], b[1]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[2], b[2])
    if ox > 0 and oy > 0:
        p = la.get_actor_location()
        if ox < oy: d = (ox + 2) * (1 if (a[0] + a[1]) > (b[0] + b[1]) else -1); la.set_actor_location(V(p.x + d, p.y, p.z), False, False)
        else: d = (oy + 2) * (1 if (a[2] + a[3]) > (b[2] + b[3]) else -1); la.set_actor_location(V(p.x, p.y + d, p.z), False, False)
        print('DMLAMP moved', round(d))
print('ROOMS2 new', stat, 'retired', retired)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
