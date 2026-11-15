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
SAL = (30, 446, 80, 580)
Z = 301.5
lib('Furn_F1_Salon_Sofa', 1, '/Game/DirectorsCut/Props/Sofa/SM_Sofa', SAL, 'N', 230, 200, Z, maxd=105, a=acts['Furn_F1_Salon_Sofa'])
acts['Furn_F1_Salon_Sofa'].static_mesh_component.set_static_mesh(unreal.load_asset('/Game/DirectorsCut/Props/Sofa/SM_Sofa'))
lib('Furn_F1_Salon_Sofa', 1, '/Game/DirectorsCut/Props/Sofa/SM_Sofa', SAL, 'N', 230, 200, Z, maxd=105, a=acts['Furn_F1_Salon_Sofa'])
lib('Furn_F1_Salon_Armchair', 1, '/Game/FreeFurniturePack/Meshes/SM_Modern_Armchair', SAL, 'E', 165, 110, Z, maxd=100, a=acts['Furn_F1_Salon_Armchair'])
t = acts['Furn_DM_Living_Table']; j = acts.get('Furn_DM_Living_Jar')
if j: j.set_actor_location(V(355, 420, top(t) + 0.5), False, False)
for l in ('Furn_F1_Salon_Sofa', 'Furn_F1_Salon_Armchair'):
    o, e = acts[l].get_actor_bounds(False); print('B', l[5:], 'x%d..%d y%d..%d h%d' % (o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y, 2 * e.z))
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
