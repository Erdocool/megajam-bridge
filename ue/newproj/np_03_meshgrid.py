import unreal, time
# NewMegaJam step 1c: read-only. Vertex-based occupancy/height grids of the Fab city meshes (no collision on them)
t0 = time.time()
STEP = 2500.0; X0, Y0, N = -100000.0, -102500.0, 81
out = {}
for key, path in (('B', '/Game/DynamicMeshCreator/Mesh/SM_Building_Center'), ('R', '/Game/DynamicMeshCreator/Mesh/SM_Road_Center'), ('T', '/Game/DynamicMeshCreator/Mesh/SM_Terrain_Center')):
    sm = unreal.load_asset(path)
    g = {}
    ns = sm.get_num_sections(0)
    nv = 0
    for s in range(ns):
        res = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(sm, 0, s)
        verts = res[0]; nv += len(verts)
        for v in verts:
            i = int((v.x - X0) // STEP); j = int((v.y - Y0) // STEP)
            if 0 <= i < N and 0 <= j < N:
                k = j * N + i
                if key == 'B':
                    if v.z > g.get(k, -1e9): g[k] = v.z
                else:
                    if v.z < g.get(k, 1e9): g[k] = v.z
    out[key] = g
    print(key, 'sections', ns, 'verts', nv, 'cells', len(g), round(time.time() - t0, 1))
A = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
def enc(g, base, div):
    rows = []
    for j in range(N):
        rows.append(''.join(A[max(0, min(61, int((g[j * N + i] - base) / div)))] if (j * N + i) in g else '.' for i in range(N)))
    return '|'.join(rows)
print('GB', enc(out['B'], 4000, 500))
print('GR', enc(out['R'], 4000, 200))
print('GT', enc(out['T'], 4000, 200))
