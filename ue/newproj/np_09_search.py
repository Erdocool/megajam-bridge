import unreal, math, time
# read-only: search a relative (yaw, shift) for the CITY_ actors so our zones sit on flat open city ground (20 m cells)
t0 = time.time(); C = 2000.0
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
B = set(); GX = {}; GN = {}
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if not l.startswith('CITY_') or 'Plane' in l: continue
    sm = a.static_mesh_component.static_mesh; tr = a.get_actor_transform(); isb = 'Building' in l
    for s in range(sm.get_num_sections(0)):
        for v in unreal.ProceduralMeshLibrary.get_section_from_static_mesh(sm, 0, s)[0]:
            p = tr.transform_location(v); k = (int(p.x // C), int(p.y // C))
            if isb: B.add(k)
            else:
                if p.z > GX.get(k, -1e9): GX[k] = p.z
                if p.z < GN.get(k, 1e9): GN[k] = p.z
print('cells B', len(B), 'G', len(GX), round(time.time() - t0))
def pts(x0, x1, y0, y1, s=C):
    out = []; x = x0
    while x <= x1:
        y = y0
        while y <= y1: out.append((x, y)); y += s
        x += s
    return out
KEEP = pts(10900, 16700, 2900, 12950) + pts(0, 4500, -2100, -900)   # SFA+bounds, studio
STREET = pts(0, 20000, -900, 900) + pts(11100, 12900, 900, 17000)
RING = pts(-15000, 35000, -15000, 30000, 4000)
gx = [k[0] for k in GX]; gy = [k[1] for k in GX]
res = []
for yaw in (0, 90, 180, 270):
    c, s = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    rot = lambda P: [(int((c * x - s * y) // C), int((s * x + c * y) // C)) for x, y in P]
    K, S_, Rg = rot(KEEP), rot(STREET), rot(RING)
    for tx in range(min(gx), max(gx) + 1, 2):
        for ty in range(min(gy), max(gy) + 1, 2):
            ok = True; zs = []
            for (i, j) in K:
                k = (i - tx, j - ty)
                if k in B or k not in GX: ok = False; break
                zs.append(GX[k]); zs.append(GN[k])
            if not ok or max(zs) - min(zs) > 250: continue
            sb = sum(1 for (i, j) in S_ if (i - tx, j - ty) in B)
            if sb > 4: continue
            ring = sum(1 for (i, j) in Rg if (i - tx, j - ty) in B)
            res.append((ring - 20 * sb, yaw, tx, ty, int(max(zs)), int(max(zs) - min(zs)), sb))
res.sort(key=lambda r: -r[0])
print('n', len(res), round(time.time() - t0))
for r in res[:6]: print('R', r)
