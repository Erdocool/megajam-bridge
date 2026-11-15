import unreal
# step 18 (one batch): LI copies' lights -> Movable + intensity cap; fixed exposures; Door_Street lock; key. Walls untouched. Originals untouched.
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
V, R = unreal.Vector, unreal.Rotator
CAP = {unreal.LightUnits.CANDELAS: 8.0, unreal.LightUnits.LUMENS: 100.0, unreal.LightUnits.UNITLESS: 128.0, unreal.LightUnits.EV: 3.0}
EV_OUT, EV_BLDG = 0.5, 0.5
info = {}
def wname(): return ues.get_editor_world().get_path_name()
def fix_lights():
    n = 0; capped = 0
    for a in eas.get_all_level_actors():
        for c in a.get_components_by_class(unreal.LocalLightComponent):
            c.set_mobility(unreal.ComponentMobility.MOVABLE); n += 1
            u = c.get_editor_property('intensity_units'); i = c.get_editor_property('intensity'); m = CAP.get(u, 8.0)
            if i > m: c.set_editor_property('intensity', m); capped += 1
    return n, capped
assert 'L_Town' in wname(), 'not in L_Town'
les.save_current_level()  # keeps the user's current L_Town state (nothing discarded)
les.load_level('/Game/DirectorsCut/Buildings/LI_Studio_MJ')
print('studio lights movable/capped', fix_lights(), 'saved', les.save_current_level())
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
print('bldg lights movable/capped', fix_lights())
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
d = acts['Door_Street']; d.set_editor_property('bLocked', True)
d.set_editor_property('KeyID', type(d.get_editor_property('KeyID'))('Key_Building_Front'))
km = None
for k in acts.values():
    if k.get_class().get_name() == 'BP_Key_C' and k.get_editor_property('MJ_Proxy'):
        p = k.get_editor_property('MJ_Proxy'); km = (p.static_mesh_component.static_mesh.get_path_name(), p.get_actor_scale3d(), p.get_actor_location() - k.get_actor_location()); break
print('door', d.get_editor_property('bLocked'), d.get_editor_property('KeyID'), 'keymesh', km and km[0].split('.')[-1], 'saved', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town')
assert 'L_Town' in wname()
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
def fixed(a, ev):
    s = a.settings
    s.set_editor_property('override_auto_exposure_method', True); s.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_HISTOGRAM)
    for p in ('min', 'max'):
        s.set_editor_property('override_auto_exposure_%s_brightness' % p, True); s.set_editor_property('auto_exposure_%s_brightness' % p, ev)
    s.set_editor_property('override_auto_exposure_bias', True); s.set_editor_property('auto_exposure_bias', 0.0)
    a.set_editor_property('settings', s)
fixed(acts['MJ_Exposure_PPV'], EV_OUT); fixed(acts['MJ_PPV_BuildingInterior'], EV_BLDG)
st = acts['MJ_PPV_StudioInterior'].settings
print('studio ppv', st.auto_exposure_method, st.auto_exposure_bias, st.get_editor_property('auto_exposure_apply_physical_camera_exposure'))
if st.auto_exposure_method == unreal.AutoExposureMethod.AEM_MANUAL and st.get_editor_property('auto_exposure_apply_physical_camera_exposure'):
    pass  # original L_Apartment manual camera exposure kept as-is
elif st.auto_exposure_method != unreal.AutoExposureMethod.AEM_MANUAL:
    fixed(acts['MJ_PPV_StudioInterior'], EV_BLDG)
# key on a crate, west sidewalk across from the SFA door (inside the bounded area)
KX, KY = 11300.0, 9800.0
crate = acts.get('MJ_KeyCrate') or eas.spawn_actor_from_object(unreal.load_asset('/Engine/BasicShapes/Cube'), V(KX, KY, 60), R(0, 0, 0))
crate.set_actor_label('MJ_KeyCrate'); crate.set_actor_scale3d(V(0.7, 0.7, 0.9))
k = acts.get('Key_Building_Front') or eas.spawn_actor_from_class(unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Key.BP_Key_C'), V(KX, KY, 110), R(0, 0, 0))
k.set_actor_label('Key_Building_Front'); k.set_editor_property('KeyID', type(k.get_editor_property('KeyID'))('Key_Building_Front'))
mesh, sc, off = km if km else ('/Engine/BasicShapes/Cube', V(0.15, 0.05, 0.05), V(0, 0, 0))
p = acts.get('Proxy_Key_Building_Front') or eas.spawn_actor_from_object(unreal.load_asset(mesh), V(KX, KY, 110) + off, R(0, 0, 0))
p.set_actor_label('Proxy_Key_Building_Front'); p.set_actor_scale3d(sc); p.static_mesh_component.set_collision_profile_name('NoCollision')
k.set_editor_property('MJ_Proxy', p)
print('key ok', k.get_editor_property('KeyID'), 'saved', les.save_current_level())
