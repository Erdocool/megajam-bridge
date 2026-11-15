import unreal
# Floor 3->4 flight moved to the west half (the hidden room sits over the east half of the stairwell on floor 4).
# Floor 4 east part floored again (landing to the Manager door + the hidden-room door), floor 3 east lane A guarded.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V, R = unreal.Vector, unreal.Rotator
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
nret = [0]; made = [0]
def retire(a):
    if unreal.Name('MJ_Retired') in a.tags: return
    p = a.get_actor_location(); a.tags = list(a.tags) + [unreal.Name('MJ_Retired'), unreal.Name('MJ_Orig:%d,%d,%d' % (p.x, p.y, p.z))]
    a.set_actor_location(V(p.x, p.y, p.z - 5000), False, False); a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
    a.set_folder_path('_RetiredStructure'); nret[0] += 1
def mk(lab, src, x0, x1, y0, y1, z0, z1):
    a = acts.get(lab)
    if a is None:
        a = eas.duplicate_actor(src, w, V(0, 0, 0)); a.set_actor_label(lab); acts[lab] = a
        a.tags = [t for t in src.tags if not str(t).startswith('MJ_Retired') and not str(t).startswith('MJ_Orig')]
        a.set_actor_hidden_in_game(False); a.set_actor_enable_collision(True); a.set_folder_path('Building/StairV3')
    a.set_actor_rotation(R(0, 0, 0), False); a.set_actor_scale3d(V(1, 1, 1)); a.set_actor_location(V(0, 0, 0), False, False)
    o, e = a.get_actor_bounds(False); s = V((x1 - x0) / (2 * e.x), (y1 - y0) / (2 * e.y), (z1 - z0) / (2 * e.z)); a.set_actor_scale3d(s)
    a.set_actor_location(V((x0 + x1) / 2 - o.x * s.x, (y0 + y1) / 2 - o.y * s.y, (z0 + z1) / 2 - o.z * s.z), False, False); made[0] += 1; return a
S_STEP = acts['StairV3_0_A0']; S_LAND = acts['LandingMidV3_0']; S_DIV = acts['StairDivV3_0']; S_SLAB = acts['SlabStairV3_3_W']; S_CEIL = acts['CeilV3_3_W']
for i in range(9): retire(acts['StairV3_3_A%d' % i]); retire(acts['StairV3_3_B%d' % i])
for l in ('LandingMidV3_3', 'GuardV3_4A', 'GuardV3_4Div', 'SlabStairV3_4_Aext', 'CeilV3_4_Aext', 'SlabStairV3_4_W', 'CeilV3_4_W'): retire(acts[l])
b = 900.0
for i in range(9):
    t = b + 150.0 * (i + 1) / 9; mk('StairV3w_3_A%d' % i, S_STEP, 500 - 30 * (i + 1), 500 - 30 * i, 1110, 1240, max(b, t - 20), t)
    t2 = b + 150 + 150.0 * (i + 1) / 9; mk('StairV3w_3_B%d' % i, S_STEP, 230 + 30 * i, 260 + 30 * i, 1270, 1400, t2 - 20, t2)
mk('LandingMidV3w_3', S_LAND, 90, 230, 1110, 1400, 1038, 1050)
mk('StairDivV3w_3', S_DIV, 230, 500, 1240, 1270, 900, 1200)
mk('UnderStairV3w_3', S_DIV, 232, 498, 1272, 1398, 900, 1040)
# floor 3: landing strip over east lane A + guard
mk('SlabStairV3_3_Aext', S_SLAB, 590, 640, 1110, 1240, 880, 900); mk('CeilV3_3_Aext', S_CEIL, 590, 640, 1110, 1240, 880, 900)
mk('GuardV3_3A', S_DIV, 640, 646, 1110, 1240, 900, 1000)
# floor 4: hole now x90..500; east part floored; guards round the west hole
z0, z1 = 1180.0, 1200.0
mk('SlabStairV3_4_W0', S_SLAB, 0, 90, 1100, 1400, z0, z1); mk('SlabStairV3_4_W1', S_SLAB, 500, 590, 1100, 1400, z0, z1); mk('SlabStairV3_4_W2', S_SLAB, 90, 500, 1100, 1110, z0, z1)
mk('SlabStairV3_4_E', S_SLAB, 590, 1000, 1110, 1400, z0, z1)
mk('CeilV3_4_W0', S_CEIL, -25, 90, 1100, 1425, z0, z1); mk('CeilV3_4_W1', S_CEIL, 500, 590, 1100, 1425, z0, z1); mk('CeilV3_4_W2', S_CEIL, 90, 500, 1100, 1110, z0, z1)
mk('CeilV3_4_W3', S_CEIL, 90, 500, 1400, 1425, z0, z1); mk('CeilV3_4_Ea', S_CEIL, 590, 1000, 1110, 1400, z0, z1)
mk('GuardV3w_4A', S_DIV, 494, 500, 1110, 1240, 1200, 1300); mk('GuardV3w_4Div', S_DIV, 230, 500, 1240, 1270, 1200, 1300)  # not over the mid landing (head room)
print('F3STAIR made', made[0], 'retired', nret[0])
print('saved LI', les.save_current_level()); les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
