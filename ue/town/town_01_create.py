# L_Town step 1: new level, daylight (same as L_Building), ground/road/sidewalks, candidate building catalog row.
# Only creates/saves /Game/DirectorsCut/Maps/L_Town. Refuses if any map is dirty.
import unreal
TOWN = '/Game/DirectorsCut/Maps/L_Town'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
dm = [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
if dm:
    raise RuntimeError('dirty maps, not switching: %s' % dm)
if unreal.EditorAssetLibrary.does_asset_exist(TOWN):
    raise RuntimeError('L_Town already exists - step 1 already done')
print('new_level', les.new_level(TOWN))
V, R = unreal.Vector, unreal.Rotator

def spawn(cls, loc, rot=R(0, 0, 0), label=None):
    a = eas.spawn_actor_from_class(cls, loc, rot)
    if label:
        a.set_actor_label(label)
    return a

sun = spawn(unreal.DirectionalLight, V(0, 0, 2000), R(pitch=-40, yaw=30, roll=0), 'L_Sun')
c = sun.get_component_by_class(unreal.DirectionalLightComponent)
c.set_editor_property('intensity', 2.5)
c.set_editor_property('atmosphere_sun_light', True)
sky = spawn(unreal.SkyLight, V(0, 0, 2000), label='L_SkyLight')
sc = sky.get_component_by_class(unreal.SkyLightComponent)
sc.set_editor_property('real_time_capture', True)
sc.set_editor_property('intensity', 1.0)
spawn(unreal.SkyAtmosphere, V(0, 0, 0), label='L_SkyAtmosphere')
spawn(unreal.ExponentialHeightFog, V(0, 0, 0), label='L_Fog')
ppv = spawn(unreal.PostProcessVolume, V(0, 0, 0), label='MJ_Exposure_PPV')
ppv.set_editor_property('unbound', True)
s = ppv.get_editor_property('settings')
for k, v in (('auto_exposure_method', unreal.AutoExposureMethod.AEM_HISTOGRAM), ('auto_exposure_min_brightness', -2.5),
             ('auto_exposure_max_brightness', 0.5), ('auto_exposure_bias', 0.0), ('auto_exposure_speed_up', 2.0), ('auto_exposure_speed_down', 1.0)):
    s.set_editor_property('override_' + k, True)
    s.set_editor_property(k, v)
ppv.set_editor_property('settings', s)
spawn(unreal.PlayerStart, V(1000, -700, 120), R(0, 0, 0), 'PlayerStart_Town')

cube = unreal.load_asset('/Engine/BasicShapes/Cube')
def mat(p):
    return unreal.load_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else None
M_ASPH = mat('/Game/DirectorsCut/Materials/Dusk/MI_Clip_M_Asphalt')
M_SIDE = mat('/Game/Uniblocks/Materials/Concrete/MI_UBT_concreteRaw_rough_tilesL_rnd') or mat('/Game/StarterContent/Materials/M_Concrete_Tiles')
M_GRND = mat('/Game/DirectorsCut/Materials/Dusk/MI_Clip_M_ConcreteDark')
M_LINE = mat('/Game/Uniblocks/Materials/Concrete/MI_UBT_concreteRaw_white_plain')

def box(label, cx, cy, top, sx, sy, sz, m):
    # cube is 100cm centered at pivot
    a = spawn(unreal.StaticMeshActor, V(cx, cy, top - sz / 2.0), label=label)
    smc = a.static_mesh_component
    smc.set_static_mesh(cube)
    a.set_actor_scale3d(V(sx / 100.0, sy / 100.0, sz / 100.0))
    if m:
        smc.set_material(0, m)
    return a

L = 20000.0  # street along +X, 0..L ; road Y -500..500
box('Town_Ground', L / 2, 0, -2, L + 6000, 12000, 20, M_GRND)
box('Town_Road', L / 2, 0, 0, L, 1000, 20, M_ASPH)
box('Town_Sidewalk_S', L / 2, -700, 15, L, 400, 35, M_SIDE)
box('Town_Sidewalk_N', L / 2, 700, 15, L, 400, 35, M_SIDE)
for i in range(int(L / 600)):
    box('Town_Lane_%02d' % i, 300 + i * 600, 0, 1, 300, 15, 2, M_LINE)

# candidate catalog row (away from the street, Y = -9000), measure bounds
ar = unreal.AssetRegistryHelpers.get_asset_registry()
names = ['BPP_Bldg_Hero_Low_SFD_Long_N1', 'BPP_Bldg_Hero_Mid_NYG_Modern_A01_N1', 'BPP_Bldg_Hero_Mid_CHG_Long_A01_N1',
         'BPP_Bldg_Hero_Mid_SFA_Triangle_N1', 'BPP_Bldg_Hero_Mid_NYG_Triangle_B01_N1', 'BPP_Bldg_Hero_Mid_SFE_C01_N1',
         'BPP_Bldg_Hero_Mid_SFC_Triangle_N1', 'BPP_Bldg_Hero_CHA_A01_N1', 'BPP_Bldg_Hero_CHH_N1', 'BPP_Bldg_Hero_SFB_N1',
         'BPP_Bldg_Hero_NYG_Modern_Square_A01_N1', 'BPP_Bldg_Hero_CHC_BlockThreeBuilding_A01_N1']
pk = {}
for a in ar.get_assets_by_path('/Game/CitySampleBuildings', recursive=True):
    if str(a.asset_name) in names:
        pk[str(a.asset_name)] = str(a.package_name)
x = 0.0
for n in names:
    if n not in pk:
        print('MISSING', n); continue
    bp = unreal.load_asset(pk[n])
    a = spawn(bp.generated_class(), V(x, -30000, 0), label='CAND_' + n.replace('BPP_Bldg_Hero_', '').replace('_N1', ''))
    o, e = a.get_actor_bounds(False)
    # put bounds min z on 0 and min x at cursor
    piv = a.get_actor_location()
    a.set_actor_location(V(piv.x + (x - (o.x - e.x)), piv.y + (-30000 - o.y), piv.z - (o.z - e.z)), False, False)
    o2, e2 = a.get_actor_bounds(False)
    print('CAND %s | W(X)=%.0f D(Y)=%.0f H=%.0f cm | pivot->center offset (%.0f,%.0f) | floors~%d' % (
        n, 2 * e.x, 2 * e.y, 2 * e.z, o.x - piv.x, o.y - piv.y, round(2 * e.z / 380)))
    x += 2 * e.x + 3000
print('saved', les.save_current_level())
