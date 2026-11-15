
# L_Town step 6: daylight, L-shaped layout (cross street), studio NYAF + main SFA as editable level instances, fewer cars, cross-street fillers
import math
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if 'L_Town' not in w.get_path_name():
    dm = [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    assert not dm, dm
    les.load_level('/Game/DirectorsCut/Maps/L_Town')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
V, R = unreal.Vector, unreal.Rotator
def top(lab):
    o, e = acts[lab].get_actor_bounds(False); return o.z + e.z
# --- daylight (only our own L_Town lights) ---
sun = acts['L_Sun']; sun.light_component.set_intensity(SUN); sun.set_actor_rotation(R(pitch=-48, yaw=35, roll=0), False)
ppv = acts['MJ_Exposure_PPV']; s = ppv.settings
d = math.log2(SUN / 2.5)
s.set_editor_property('auto_exposure_min_brightness', -2.5 + d); s.set_editor_property('auto_exposure_max_brightness', 0.5 + d)
ppv.set_editor_property('settings', s)
print('sun', SUN, 'ppv EV', -2.5 + d, 0.5 + d)
# --- cross street (N-S) at X 11500..12500 from the main street north ---
cube = unreal.load_asset('/Engine/BasicShapes/Cube')
def mat(lab): return acts[lab].static_mesh_component.get_material(0)
def box(lab, src, cx, cy, top_z, sx, sy, sz):
    if lab in acts: return acts[lab]
    a = eas.spawn_actor_from_object(cube, V(cx, cy, top_z - sz / 2), R(0, 0, 0))
    a.set_actor_scale3d(V(sx / 100.0, sy / 100.0, sz / 100.0)); a.set_actor_label(lab)
    a.static_mesh_component.set_material(0, mat(src)); acts[lab] = a; return a
ZG, ZR, ZS = top('Town_Ground'), top('Town_Road'), top('Town_Sidewalk_N')
Y1 = 17000.0
box('Town_Ground_N', 'Town_Ground', 10000, (6000 + Y1 + 2000) / 2, ZG, 26000, Y1 + 2000 - 6000, 20)
box('Town_Road_X', 'Town_Road', 12000, (500 + Y1) / 2, ZR, 1000, Y1 - 500, 20)
box('Town_Sidewalk_XW', 'Town_Sidewalk_N', 11300, (900 + Y1) / 2, ZS, 400, Y1 - 900, 35)
box('Town_Sidewalk_XE', 'Town_Sidewalk_N', 12700, (900 + Y1) / 2, ZS, 400, Y1 - 900, 35)
for i in range(int((Y1 - 1200) / 600)):
    box('Town_LaneX_%02d' % i, 'Town_Lane_00', 12000, 1500 + i * 600, top('Town_Lane_00'), 15, 300, 2)
# --- hero buildings as editable level instances of our duplicates ---
def hero(lab, path, loc, yaw):
    if lab in acts: return acts[lab]
    a = eas.spawn_actor_from_object(unreal.load_asset(path), loc, R(0, 0, yaw))
    a.set_actor_label(lab); acts[lab] = a
    print('hero', lab, a.get_class().get_name()); return a
# NYAF (studio): south side of main street, front (-Y local) turned to face the street (yaw 180), x 1000..4404
hero('HERO_Studio_NYAF', '/Game/DirectorsCut/Buildings/LI_NYAF_MJ', V(2702, -950 - 532, ZS), 180)
# SFA (main apartment): east side of the cross street, door facade (-X local) facing the street, x 12950.., y 3000..12884
hero('HERO_MainApt_SFA', '/Game/DirectorsCut/Buildings/LI_SFA_MJ', V(12950 + 1543, 3000 + 4942, ZS - 1275), 0)
# slot markers no longer needed: hide (kept)
for lab in ('SLOT_A_PlayerStudio', 'SLOT_A_PlayerStudio_Label', 'SLOT_B_MainApartment', 'SLOT_B_MainApartment_Label'):
    if lab in acts:
        acts[lab].set_actor_hidden_in_game(True); acts[lab].set_is_temporarily_hidden_in_editor(True)
        for c in acts[lab].get_components_by_class(unreal.PrimitiveComponent): c.set_visibility(False, True); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
# candidate catalog: hide in game (kept for reference, far away)
for lab, a in acts.items():
    if lab.startswith(('CAND_', 'CAT_')): a.set_actor_hidden_in_game(True)
# --- parked cars: keep ~10 on the main street, clear the junction ---
cars = sorted([a for l, a in acts.items() if l.startswith('CAR_')], key=lambda a: a.get_actor_label())
keep, gone = [], 0
for i, a in enumerate(cars):
    x = a.get_actor_location().x
    if (10600 < x < 13400) or (i % 3 != 0) or len(keep) >= 10:
        eas.destroy_actor(a); gone += 1
    else:
        keep.append(a.get_actor_label())
print('cars kept', len(keep), 'removed (our own duplicates)', gone)
# --- PlayerStart: on the sidewalk in front of the studio door ---
ps = acts['PlayerStart_Town']; ps.set_actor_location(V(4090, -720, ZS + 100), False, False); ps.set_actor_rotation(R(0, 90, 0), False)
print('saved', les.save_current_level())
