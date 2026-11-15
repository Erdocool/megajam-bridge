import unreal
# Snap each BP_Door proxy leaf (SM_Door: width local Y -90..0, hinge at Y=0, thick X +-9.2, h 200) into its wall gap, closed.
# Gaps computed from the wall cubes (dc_11 dump). Door actor (interaction point) -> gap centre. Locks/KeyIDs untouched.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V, R = unreal.Vector, unreal.Rotator
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
T = [
('Door_DM_Bath', 1, 676, 764, 527.0, 14, 0, 210, 280),
('Door_Flat1_Entry', 0, 510, 610, 1093.0, 14, 300, 510, 1480),
('Door_Flat1_Salon', 1, 250, 350, 453.0, 14, 300, 510, 1480),
('Door_Flat1_Kitchen', 1, 770, 870, 453.0, 14, 300, 510, 1480),
('Door_Flat1_Master', 1, 152, 248, 667.0, 14, 300, 510, 1480),
('Door_Flat1_Child', 1, 412, 508, 667.0, 14, 300, 510, 1480),
('Door_Street', 1, 1200, 1300, -12.0, 24, 0, 210, 1520),
('Door_Doorman', 0, 230, 330, 1093.0, 14, 0, 210, 280),
('Door_Flat1_Study', 1, 632, 728, 667.0, 14, 300, 510, 1480),
('Door_Flat1_Bath', 1, 892, 988, 667.0, 14, 300, 510, 1480),
('Door_Flat1_Balcony', 1, 240, 310, -2.5, 14, 300, 510, 1480),
('Door_Flat2_Entry', 0, 510, 610, 1093.0, 14, 600, 810, 1480),
('Door_Flat2_Salon', 1, 250, 350, 453.0, 14, 600, 810, 1480),
('Door_Flat2_Kitchen', 1, 770, 870, 453.0, 14, 600, 810, 1480),
('Door_Flat2_Master', 1, 152, 248, 667.0, 14, 600, 810, 1480),
('Door_Flat2_Child', 1, 412, 508, 667.0, 14, 600, 810, 1480),
('Door_Flat2_Study', 1, 632, 728, 667.0, 14, 600, 810, 1480),
('Door_Flat2_Bath', 1, 892, 988, 667.0, 14, 600, 810, 1480),
('Door_Boiler', 0, 230, 330, 1327.0, 14, 0, 210, 280),
('Door_Flat2_Balcony', 1, 240, 310, -2.5, 14, 600, 810, 1480),
('Door_Flat3_Entry', 0, 510, 610, 1093.0, 14, 900, 1110, 1480),
('Door_Flat3_Salon', 1, 250, 350, 453.0, 14, 900, 1110, 1480),
('Door_Flat3_Kitchen', 1, 770, 870, 453.0, 14, 900, 1110, 1480),
('Door_Flat3_Master', 1, 152, 248, 667.0, 14, 900, 1110, 1480),
('Door_Flat3_Child', 1, 412, 508, 667.0, 14, 900, 1110, 1480),
('Door_Flat3_Study', 1, 632, 728, 667.0, 14, 900, 1110, 1480),
('Door_Flat3_Bath', 1, 892, 988, 667.0, 14, 900, 1110, 1480),
('Door_Flat3_Balcony', 1, 240, 310, -2.5, 14, 900, 1110, 1480),
('Door_Manager_Entry', 0, 510, 610, 1093.0, 14, 1200, 1410, 1480),
('Door_DM_Bed', 0, 154, 244, 567.0, 14, 0, 210, 280),
('Door_Manager_Salon', 1, 250, 350, 453.0, 14, 1200, 1410, 1480),
('Door_Manager_Kitchen', 1, 770, 870, 453.0, 14, 1200, 1410, 1480),
('Door_Manager_Master', 1, 152, 248, 667.0, 14, 1200, 1410, 1480),
('Door_Manager_Child', 1, 412, 508, 667.0, 14, 1200, 1410, 1480),
('Door_Manager_Study', 1, 632, 728, 667.0, 14, 1200, 1410, 1480),
('Door_Manager_Bath', 1, 892, 988, 667.0, 14, 1200, 1410, 1480),
('Door_Manager_Balcony', 1, 240, 310, -2.5, 14, 1200, 1410, 1480),
('Door_HiddenRoom', 1, 1204, 1296, 787.0, 14, 1200, 1410, 1480)]
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
ok = 0; miss = []; chk = []
for lab, ax, l, r, plane, thick, z, lb, top in T:
    d = acts.get(lab); p = acts.get('Proxy_' + lab)
    if not d or not p: miss.append(lab); continue
    w = r - l; h = (lb - z) if lb else 210.0; mid = (l + r) / 2.0
    sx = min(1.0, max(0.4, (thick - 2.0) / 18.4))
    p.set_actor_scale3d(V(sx, w / 90.0, h / 200.0))
    if ax == 1: p.set_actor_rotation(R(0, 0, 0), False); p.set_actor_location(V(plane, r, z), False, False); d.set_actor_location(V(plane, mid, z), False, False)
    else: p.set_actor_rotation(R(0, 0, -90), False); p.set_actor_location(V(r, plane, z), False, False); d.set_actor_location(V(mid, plane, z), False, False)
    o, e = p.get_actor_bounds(False)
    cx, cy = (plane, mid) if ax == 1 else (mid, plane)
    chk.append(round(abs(o.x - cx) + abs(o.y - cy) + abs(o.z - (z + h / 2.0)), 1)); ok += 1
others = [a.get_actor_label() for a in eas.get_all_level_actors() if a.get_class().get_name().startswith('BP_Door') and a.get_actor_label() not in [t[0] for t in T]]
print('DOORS fixed', ok, 'miss', miss, 'other', others, 'maxerr', max(chk) if chk else None)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Buildings/LI_Studio_MJ')
sd = [a.get_actor_label() for a in eas.get_all_level_actors() if a.get_class().get_name().startswith('BP_Door') or 'MJDoor' in a.get_class().get_name()]
print('studio BP doors', sd)
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
