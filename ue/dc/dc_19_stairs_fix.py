import unreal
# Stairwell rebuild (V3) + door-path fixes found by dc_18_keytest. Nothing deleted: old pieces are "retired"
# (hidden, collision off, moved 5000 down, original spot in a tag, folder Furniture/_Retired or _RetiredStructure).
# Old stairs could not be walked: full ceiling/floor slabs over the stairwell, lane divider ran to the wall (no turn),
# mid landings 1.4 m over the floor landings. New: stacked U-stair per floor in x590..1000, y1110..1400:
# lane A (y1110..1240) rises east 9 steps to a mid landing (x860..1000, +150), lane B (y1270..1400) rises west to the next floor,
# divider wall between lanes, slab holes cut, guard rail on floor 4.
SL = unreal.SystemLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V, R = unreal.Vector, unreal.Rotator
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
nret = [0]; made = [0]
def retire(a, folder='_RetiredStructure'):
    if unreal.Name('MJ_Retired') in a.tags: return
    p = a.get_actor_location(); a.tags = list(a.tags) + [unreal.Name('MJ_Retired'), unreal.Name('MJ_Orig:%d,%d,%d' % (p.x, p.y, p.z))]
    a.set_actor_location(V(p.x, p.y, p.z - 5000), False, False); a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
    a.set_folder_path(folder); nret[0] += 1
def mk(lab, src, x0, x1, y0, y1, z0, z1):
    a = acts.get(lab)
    if a is None:
        a = eas.duplicate_actor(src, w, V(0, 0, 0)); a.set_actor_label(lab); acts[lab] = a
        a.tags = [t for t in src.tags if not str(t).startswith('MJ_')] + [unreal.Name('MJ_StairV3')]
        a.set_actor_hidden_in_game(False); a.set_actor_enable_collision(True); a.set_folder_path('Building/StairV3')
    a.set_actor_rotation(R(0, 0, 0), False); a.set_actor_scale3d(V(1, 1, 1)); a.set_actor_location(V(0, 0, 0), False, False)
    o, e = a.get_actor_bounds(False)
    s = V((x1 - x0) / (2 * e.x), (y1 - y0) / (2 * e.y), (z1 - z0) / (2 * e.z))
    a.set_actor_scale3d(s)
    a.set_actor_location(V((x0 + x1) / 2 - o.x * s.x, (y0 + y1) / 2 - o.y * s.y, (z0 + z1) / 2 - o.z * s.z), False, False)
    made[0] += 1; return a
S_STEP = acts['Stair_0_0_A_V2']; S_LAND = acts['LandingMid_0_V2']; S_DIV = acts['Rail_0_A_V2']
S_SLAB = acts['F1_SlabStair']; S_CEIL = acts['F0_Ceil']
X0, XL, XE = 590.0, 860.0, 1000.0
for k in range(4):
    b = 300.0 * k
    for i in range(9):
        t = b + 150.0 * (i + 1) / 9
        mk('StairV3_%d_A%d' % (k, i), S_STEP, X0 + 30 * i, X0 + 30 * i + 30, 1110, 1240, max(b, t - 20), t)
        t2 = b + 150 + 150.0 * (i + 1) / 9
        mk('StairV3_%d_B%d' % (k, i), S_STEP, XL - 30 * i - 30, XL - 30 * i, 1270, 1400, t2 - 20, t2)
    mk('LandingMidV3_%d' % k, S_LAND, XL, XE, 1110, 1400, b + 138, b + 150)
    mk('StairDivV3_%d' % k, S_DIV, X0, XL, 1240, 1270, b, b + 300)
mk('UnderStairV3_0', S_DIV, X0 + 30, XL, 1272, 1398, 0, 140)
mk('GuardV3_4A', S_DIV, X0 - 6, X0, 1110, 1240, 1200, 1300); mk('GuardV3_4Div', S_DIV, X0, XE, 1240, 1270, 1200, 1300)
for L in range(1, 5):
    z0, z1 = 300.0 * L - 20, 300.0 * L
    mk('SlabStairV3_%d_W' % L, S_SLAB, 0, X0, 1100, 1400, z0, z1); mk('SlabStairV3_%d_N' % L, S_SLAB, X0, XE, 1100, 1110, z0, z1)
    mk('CeilV3_%d_Flat' % L, S_CEIL, -25, 1025, -25, 1100, z0, z1); mk('CeilV3_%d_W' % L, S_CEIL, -25, X0, 1100, 1425, z0, z1)
    mk('CeilV3_%d_N' % L, S_CEIL, X0, 1025, 1100, 1110, z0, z1); mk('CeilV3_%d_S' % L, S_CEIL, X0, 1025, 1400, 1425, z0, z1); mk('CeilV3_%d_E' % L, S_CEIL, XE, 1025, 1110, 1400, z0, z1)
for l, a in list(acts.items()):
    if l.startswith(('Stair_', 'LandingMid_', 'Rail_')) or l in ['LandingFloor_%d' % i for i in range(1, 5)] + ['F%d_Ceil' % i for i in range(4)] + ['F%d_SlabStair' % i for i in range(1, 5)]:
        retire(a)
print('STAIRS made', made[0], 'retired', nret[0])
# path fixes ------------------------------------------------------------
STRUCT = ('Wall', 'Cor', 'Div', 'Floor', 'Slab', 'Ceil', 'Ext_', 'Over', 'Win', 'Balc', 'Stair', 'Landing', 'Rail', 'Guard')
def free(x0, x1, y0, y1, z0, z1, ign):
    ov = SL.box_overlap_actors(w, V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), V((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2), [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2], None, ign)
    if isinstance(ov, tuple): ov = ov[-1]
    return not [a for a in (ov or []) if not any(k in a.get_actor_label() for k in STRUCT)]
def put(a, cx, cy, zb, yaw=None):
    if yaw is not None: a.set_actor_rotation(R(0, 0, yaw), False)
    o, e = a.get_actor_bounds(False); p = a.get_actor_location()
    a.set_actor_location(V(p.x + cx - o.x, p.y + cy - o.y, p.z + zb - (o.z - e.z)), False, False)
mir = []
for fl in (1, 2, 3, 4):
    m = acts.get('Furn_F%d_Hall_Mirror' % fl)
    if not m: continue
    fz = 300 * fl; o, e = m.get_actor_bounds(False); zb = o.z - e.z
    for cy in (905, 1015, 930):
        if free(461, 470, cy - 30, cy + 30, zb, zb + 2 * e.z, [m]):
            put(m, 462, cy, zb, m.get_actor_rotation().yaw + 180); mir.append('%d@%d' % (fl, cy)); break
    else: mir.append('%d:nofree' % fl)
print('MIRRORS', mir)
la = acts.get('Furn_DM_Bed_Lamp'); lp = None
if la:
    o, e = la.get_actor_bounds(False)
    for cx, cy in ((425, 725), (470, 720), (85, 640), (470, 600), (100, 700)):
        if free(cx - e.x, cx + e.x, cy - e.y, cy + e.y, 8, 100, [la]): put(la, cx, cy, o.z - e.z); lp = (cx, cy); break
print('DMLAMP', lp)
bal = []
for l, a in acts.items():
    if l.startswith('Door_') and l.endswith('_Balcony'):
        kid = a.get_editor_property('KeyID'); a.set_editor_property('KeyID', type(kid)('Balcony_Stuck')); a.set_editor_property('bLocked', True); bal.append(l[5:-8])
print('BALCONY locked', bal)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
