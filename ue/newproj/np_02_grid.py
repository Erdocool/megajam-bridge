import unreal
# NewMegaJam step 1b: read-only. Downward traces over the city centre -> class grid + height grid (tiny text)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_name() == 'Main'
X0, Y0, STEP, N = -100000, -102000, 5000, 41
cls = {'SM_Building_Center': 'B', 'SM_RoadCenter': 'R', 'SM_Terrain_Center': 'T', 'SM_Water': 'W', 'SM_PlaneWater': 'w'}
rows, hrows, nhit = [], [], 0
for j in range(N):
    r = ''; h = ''
    for i in range(N):
        x, y = X0 + i * STEP, Y0 + j * STEP
        hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, 40000), unreal.Vector(x, y, -5000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else (False,)
        if t[0]:
            act = [v for v in t if isinstance(v, unreal.Actor)]
            loc = [v for v in t if isinstance(v, unreal.Vector)][0]
            lab = act[0].get_actor_label() if act else '?'
            r += cls.get(lab, '?'); nhit += 1
            h += '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'[max(0, min(61, int((loc.z - 3000) / 400)))]
        else:
            r += '.'; h += '.'
    rows.append(r); hrows.append(h)
print('hits', nhit)
print('C', '|'.join(rows))
print('H', '|'.join(hrows))
