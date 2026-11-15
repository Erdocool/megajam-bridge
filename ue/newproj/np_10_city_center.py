import unreal, math, time
# step 3b: light backdrop = only the *_Center city meshes; hide (not delete) Surrounding/water; search a placement where
# SFA+bounds+studio sit on open, fairly flat city ground; move the Center actors; no shadows; re-check fillers; save L_Town
t0 = time.time(); C = 2000.0
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name() == 'L_Town'
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
city = {l: a for l, a in acts.items() if l.startswith('CITY_')}
use = {l: a for l, a in city.items() if 'Center' in l}
for l, a in city.items():
    if l not in use:
        a.set_actor_hidden_in_game(True); a.static_mesh_component.set_visibility(False)
B = set(); GX = {}; GN = {}; BM = {}; BN = {}
for l, a in use.items():
    sm = a.static_mesh_component.static_mesh; tr = a.get_actor_transform(); isb = 'Building' in l
    for s in range(sm.get_num_sections(0)):
        for v in unreal.ProceduralMeshLibrary.get_section_from_static_mesh(sm, 0, s)[0]:
            p = tr.transform_location(v); k = (int(p.x // C), int(p.y // C))
            if isb:
                if p.z > BM.get(k, -1e9): BM[k] = p.z
                if p.z < BN.get(k, 1e9): BN[k] = p.z
            else:
                if p.z > GX.get(k, -1e9): GX[k] = p.z
                if p.z < GN.get(k, 1e9): GN[k] = p.z
for k, zt in BM.items():
    base = GN.get(k, BN[k])
    if zt - base > 300: B.add(k)
print('cells', len(BM), 'tall', len(B), 'ground', len(GX))
def pts(x0, x1, y0, y1, s=C):
    out = []; x = x0
    while x <= x1:
        y = y0
        while y <= y1: out.append((x, y)); y += s
        x += s
    return out
KEEP = pts(10900, 16700, 2900, 12950) + pts(800, 4600, -2100, -900)
STREET = pts(0, 20000, -900, 900) + pts(11100, 12900, 900, 17000)
RING = pts(-15000, 35000, -15000, 30000, 4000)
gx = [k[0] for k in GX]; gy = [k[1] for k in GX]
best = None
for yaw in (0, 90, 180, 270):
    c, s = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    rot = lambda P: [(int((c * x - s * y) // C), int((s * x + c * y) // C)) for x, y in P]
    K, S_, Rg = rot(KEEP), rot(STREET), rot(RING)
    ki = [k[0] for k in K]; kj = [k[1] for k in K]
    for tx in range(min(ki) - max(gx), max(ki) - min(gx) + 1):
        for ty in range(min(kj) - max(gy), max(kj) - min(gy) + 1):
            nb = 0; zs = []
            for (i, j) in K:
                k = (i - tx, j - ty)
                if k in B:
                    nb += 1
                    if nb > 8: break
                if k in GX: zs.append(GX[k]); zs.append(GN[k])
            if nb > 8 or len(zs) < len(K) // 3 or max(zs) - min(zs) > 800: continue
            sb = sum(1 for (i, j) in S_ if (i - tx, j - ty) in B)
            ring = sum(1 for (i, j) in Rg if (i - tx, j - ty) in B)
            sc = ring - 15 * sb - 40 * nb - (max(zs) - min(zs)) / 50.0
            if not best or sc > best[0]: best = (sc, yaw, tx, ty, max(zs), max(zs) - min(zs), sb, nb, ring)
print('best', best and [round(v) if isinstance(v, float) else v for v in best], round(time.time() - t0))
if best:
    sc, yaw, tx, ty, zmax, zr, sb, nb, ring = best
    # our point z maps to city-cur point R(-yaw) z - t' ; so new city transform: p_new = R(yaw)(p_cur + t'), t' = (tx,ty)*C ; then dz
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    dz = -zmax - 5.0
    for l, a in use.items():
        p = a.get_actor_location(); r = a.get_actor_rotation()
        x, y = p.x + tx * C, p.y + ty * C
        a.set_actor_location_and_rotation(unreal.Vector(c * x - s * y, s * x + c * y, p.z + dz), unreal.Rotator(roll=r.roll, pitch=r.pitch, yaw=r.yaw + yaw), False, False)
        cm = a.static_mesh_component; cm.set_editor_property('cast_shadow', False); cm.set_collision_profile_name('NoCollision')
    # fillers: re-check against the moved centre buildings (unhide earlier ones that are clear now)
    def ism_bounds(actor):
        mn = [1e18] * 3; mx = [-1e18] * 3
        for cc in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            sm = cc.get_editor_property('static_mesh')
            if not sm: continue
            bb = sm.get_bounding_box(); lo, hi = bb.min, bb.max
            cs = [unreal.Vector(X, Y, Z) for X in (lo.x, hi.x) for Y in (lo.y, hi.y) for Z in (lo.z, hi.z)]
            n = cc.get_instance_count()
            for i in range(0, n, max(1, n // 200)):
                t = cc.get_instance_transform(i, True)
                for q in cs:
                    w = t.transform_location(q)
                    for k, val in enumerate((w.x, w.y, w.z)): mn[k] = min(mn[k], val); mx[k] = max(mx[k], val)
        return mn, mx
    cn, sn = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    hid = []
    for l, a in acts.items():
        if not l.startswith('FILL'): continue
        mn, mx = ism_bounds(a)
        if mn[0] > 1e17: continue
        clash = False
        for X in range(int(mn[0]), int(mx[0]) + 1, 1000):
            for Y in range(int(mn[1]), int(mx[1]) + 1, 1000):
                k = (int((cn * X - sn * Y) // C) - tx, int((sn * X + cn * Y) // C) - ty)
                if k in B: clash = True; break
            if clash: break
        tagged = unreal.Name('MJ_HiddenForCity') in a.tags
        if clash:
            a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
            for p_ in a.get_components_by_class(unreal.PrimitiveComponent): p_.set_visibility(False)
            if not tagged: a.tags = list(a.tags) + [unreal.Name('MJ_HiddenForCity')]
            hid.append(l[:12])
        elif tagged:
            a.set_actor_hidden_in_game(False); a.set_actor_enable_collision(True)
            for p_ in a.get_components_by_class(unreal.PrimitiveComponent): p_.set_visibility(True)
            a.tags = [t for t in a.tags if t != unreal.Name('MJ_HiddenForCity')]
    print('dz', round(dz), 'fillers hidden', hid)
    print('saved', les.save_current_level(), round(time.time() - t0))
