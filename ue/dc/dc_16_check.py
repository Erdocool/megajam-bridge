import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
B = []
for a in eas.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor) or unreal.Name('MJ_Retired') in a.tags: continue
    f = str(a.get_folder_path())
    if not f.startswith('Furniture/'): continue
    l = a.get_actor_label()
    if any(k in l for k in ('Rug', 'Curtain', 'Photo', 'Picture', 'Mirror', 'Towel', 'Lamp_Wall', 'Hook', 'Peg', 'Knob', 'Seam', 'Books', 'Shelf', 'Screen', 'TVStand', 'TVNeck', 'Pillow', 'Duvet', 'Mattress', 'Cushion', 'Top', 'Head')): continue
    o, e = a.get_actor_bounds(False); B.append((l, o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y, o.z - e.z, o.z + e.z))
bad = []
for i in range(len(B)):
    for j in range(i + 1, len(B)):
        a, b = B[i], B[j]
        ox = min(a[2], b[2]) - max(a[1], b[1]); oy = min(a[4], b[4]) - max(a[3], b[3]); oz = min(a[6], b[6]) - max(a[5], b[5])
        if ox > 4 and oy > 4 and oz > 4 and abs(a[5] - b[6]) > 3 and abs(b[5] - a[6]) > 3: bad.append((round(min(ox, oy)), a[0][5:], b[0][5:]))
bad.sort(reverse=True)
mine = [x for x in bad if any(k in x[1] + x[2] for k in ('Salon_', 'Master_', 'DM_', 'Hall_'))]
print('OVL', len(bad), 'mine', len(mine)); [print('O', *x) for x in mine[:12]]
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back')
