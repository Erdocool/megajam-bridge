import unreal, collections
# LI_Building_MJ: 4 missing keys, per-flat material variants for repeated props, a few unique adds, idle NPCs. Saves LI, reloads L_Town.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
V, R, LC = unreal.Vector, unreal.Rotator, unreal.LinearColor
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
D = '/Game/DirectorsCut/Materials/MJ_Vary'
def save(a): EAL.save_loaded_asset(a, False)
def mi(name, parent):
    p = D + '/' + name
    if EAL.does_asset_exist(p): return unreal.load_asset(p), False
    m = AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, parent); return m, True
# master: Albedo texture x Tint
MP = D + '/M_MJ_TintTex'
if EAL.does_asset_exist(MP): MT = unreal.load_asset(MP)
else:
    MT = AT.create_asset('M_MJ_TintTex', D, unreal.Material, unreal.MaterialFactoryNew())
    t = MEL.create_material_expression(MT, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
    t.set_editor_property('parameter_name', 'Albedo'); t.set_editor_property('texture', unreal.load_asset('/Engine/EngineResources/DefaultTexture'))
    c = MEL.create_material_expression(MT, unreal.MaterialExpressionVectorParameter, -700, 300)
    c.set_editor_property('parameter_name', 'Tint'); c.set_editor_property('default_value', LC(1, 1, 1, 1))
    mu = MEL.create_material_expression(MT, unreal.MaterialExpressionMultiply, -350, 100)
    MEL.connect_material_expressions(t, 'RGB', mu, 'A'); MEL.connect_material_expressions(c, '', mu, 'B')
    MEL.connect_material_property(mu, '', unreal.MaterialProperty.MP_BASE_COLOR)
    r = MEL.create_material_expression(MT, unreal.MaterialExpressionScalarParameter, -350, 350)
    r.set_editor_property('parameter_name', 'Rough'); r.set_editor_property('default_value', 0.6)
    MEL.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(MT); save(MT)
MC = unreal.load_asset('/Game/DirectorsCut/Materials/M_DC_Color')
TINT = {'F1': LC(0.55, 0.8, 0.95, 1), 'F2': LC(1.0, 0.72, 0.42, 1), 'F3': LC(0.6, 0.66, 0.58, 1), 'F4': LC(0.62, 0.3, 0.27, 1)}
CER = {'F1': LC(0.62, 0.8, 1.0, 1), 'F2': LC(1.0, 0.68, 0.74, 1), 'F3': LC(0.58, 0.68, 0.38, 1), 'F4': LC(0.16, 0.16, 0.18, 1)}
BAD = ('normal', 'rough', 'metal', 'ao', 'orm', 'mra', 'occlusion', 'mask', 'emis', 'height', '_n', 'spec')
GOOD = ('albedo', 'basecolor', 'base color', 'base_color', 'diffuse', 'color', 'col', '_d', '_bc', 'base')
def albedo(m):
    cands = []
    if isinstance(m, unreal.MaterialInstance):
        for n in MEL.get_texture_parameter_names(m):
            tx = MEL.get_material_instance_texture_parameter_value(m, n)
            if tx: cands.append((str(n).lower(), tx))
    else:
        cands = [(tx.get_name().lower(), tx) for tx in MEL.get_used_textures(m)]
    for key, tx in cands:
        if any(b in key for b in BAD) or not isinstance(tx, unreal.Texture2D) or not tx.get_editor_property('srgb'): continue
        if any(g in key for g in GOOD) or len(cands) == 1: return tx
    ok = [tx for key, tx in cands if isinstance(tx, unreal.Texture2D) and tx.get_editor_property('srgb') and not key.endswith('_n')]
    return ok[0] if ok else None
VAR = {}; stats = collections.Counter()
def variant(m, fl):
    k = (m.get_path_name(), fl)
    if k in VAR: return VAR[k]
    nm = 'MI_MJV_%s_%s' % (m.get_name()[:40], fl); tx = albedo(m)
    vparams = [str(n) for n in MEL.get_vector_parameter_names(m)] if not tx else []
    if tx:
        v, new = mi(nm, MT)
        if new: MEL.set_material_instance_texture_parameter_value(v, 'Albedo', tx); MEL.set_material_instance_vector_parameter_value(v, 'Tint', TINT[fl]); save(v)
        stats['tex'] += 1
    elif vparams:
        v, new = mi(nm, m)
        if new:
            for n in vparams:
                ln = n.lower()
                if any(b in ln for b in ('emis', 'display', 'screen', 'bulp', 'specular', 'ambient', 'soap')): continue
                col = CER[fl] if 'chrome' not in ln else LC(CER[fl].r * 0.5 + 0.4, CER[fl].g * 0.5 + 0.4, CER[fl].b * 0.5 + 0.4, 1)
                MEL.set_material_instance_vector_parameter_value(v, n, col)
            save(v)
        stats['par'] += 1
    else:
        v, new = mi(nm, MC)
        if new: MEL.set_material_instance_vector_parameter_value(v, 'Color', TINT[fl]); save(v)
        stats['col'] += 1
    VAR[k] = v; return v
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
FLOOR = lambda f: 'F0' if f.split('/')[-1] in ('Doorman', 'Floor0') else f.split('/')[-1].replace('Floor', 'F')
furn = [a for a in acts.values() if str(a.get_folder_path()).startswith('Furniture/') and isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh]
owner = {}
for a in sorted(furn, key=lambda a: FLOOR(str(a.get_folder_path()))):
    owner.setdefault(a.static_mesh_component.static_mesh.get_path_name(), FLOOR(str(a.get_folder_path())))
changed = collections.Counter()
for a in furn:
    sm = a.static_mesh_component.static_mesh; fl = FLOOR(str(a.get_folder_path()))
    if fl == owner[sm.get_path_name()] or '/Engine/BasicShapes' in sm.get_path_name() or sm.get_name() == 'SM_Curtain' or unreal.Name('MJ_Vary') in a.tags: continue
    c = a.static_mesh_component
    for i, m in enumerate(c.get_materials()):
        if m: c.set_material(i, variant(m, fl))
    a.tags = list(a.tags) + [unreal.Name('MJ_Vary')]; changed[fl] += 1
print('vary', dict(changed), dict(stats))
# unique adds
def put(label, mesh, x, y, ztop, yaw, folder):
    a = acts.get(label) or eas.spawn_actor_from_object(unreal.load_asset(mesh), V(x, y, ztop), R(0, 0, yaw))
    a.set_actor_label(label); a.set_actor_location(V(x, y, ztop), False, False); a.set_actor_rotation(R(0, 0, yaw), False)
    o, e = a.get_actor_bounds(False); a.set_actor_location(V(x, y, ztop + (ztop - (o.z - e.z))), False, False)
    a.set_folder_path(folder); a.tags = [unreal.Name('DC_Bldg'), unreal.Name('MJ_Add')]; return a
DO = '/Game/DetectiveOffice/StaticMeshes/'
put('Furn_F4_Study_Safe', DO + 'SM_safe', 955, 590, 1200, 180, 'Furniture/Floor4')
put('Furn_F4_Study_Phone', DO + 'SM_phone', 840, 615, 1283, 160, 'Furniture/Floor4')
put('Furn_F4_Study_Folder', DO + 'SM_folder_004', 830, 750, 1283, 10, 'Furniture/Floor4')
put('Furn_F2_Kit_Radio', DO + 'SM_radio', 165, 850, 683, 200, 'Furniture/Floor2')
put('Furn_F3_Study_Book', DO + 'SM_book_1', 815, 735, 983, 30, 'Furniture/Floor3')
put('Furn_F1_Salon_Clock', DO + 'SM_clock', 360, 450, 305, 45, 'Furniture/Floor1') if False else None
# keys (each reachable before its door): Flat1 key (lobby) -> Flat1 study: Key_Doorman -> doorman flat: Key_Boiler -> boiler: Key_Flat2 -> Flat2 salon: Key_Flat3 -> Flat3 study: Key_Manager -> manager corridor: HiddenRoom
KC = unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Key.BP_Key_C')
src = acts['Proxy_Key_Flat1_Pickup']; off = src.get_actor_location() - acts['Key_Flat1_Pickup'].get_actor_location()
KEYS = [('Key_Doorman', 830, 655, 387), ('Key_Flat2', 330, 1365, 5), ('Key_Flat3', 250, 345, 685), ('Key_Manager', 810, 650, 985)]
for kid, x, y, z in KEYS:
    lab = kid + '_Pickup'; k = acts.get(lab) or eas.spawn_actor_from_class(KC, V(x, y, z), R(0, 0, 0))
    k.set_actor_label(lab); k.set_actor_location(V(x, y, z), False, False); k.set_folder_path('Keys')
    k.set_editor_property('KeyID', type(k.get_editor_property('KeyID'))(kid)); k.tags = [unreal.Name('DC_Bldg'), unreal.Name('KeyID:' + kid)]
    p = acts.get('Proxy_' + lab) or eas.spawn_actor_from_object(src.static_mesh_component.static_mesh, V(x, y, z) + off, R(0, 0, 0))
    p.set_actor_label('Proxy_' + lab); p.set_actor_location(V(x, y, z) + off, False, False); p.set_actor_scale3d(src.get_actor_scale3d())
    p.static_mesh_component.set_material(0, src.static_mesh_component.get_material(0)); p.static_mesh_component.set_collision_profile_name('NoCollision')
    p.set_folder_path('Keys/Proxies'); p.tags = [unreal.Name('DC_Bldg'), unreal.Name('KeyProxy')]
    k.set_editor_property('MJ_Proxy', p)
print('keys', [k[0] for k in KEYS])
# idle NPCs (mannequins tinted by their clothing colour)
MM = unreal.load_asset('/Game/Characters/Mannequins/Materials/M_Mannequin')
IDLE = unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle')
SK = {'M': unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'), 'Q': unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple')}
NPC = [('NPC_Hasan_Demir', 'M', 330, 430, 0, 0, 1.0, LC(0.33, 0.2, 0.1, 1)),
       ('NPC_Sevgi_Aksoy', 'Q', 125, 690, 300, 90, 1.0, LC(0.2, 0.35, 0.8, 1)),
       ('NPC_Kemal_Aksoy', 'M', 380, 330, 300, 90, 1.0, LC(0.06, 0.09, 0.25, 1)),
       ('NPC_Elif_Aksoy', 'Q', 720, 390, 300, -90, 0.7, LC(0.95, 0.8, 0.15, 1)),
       ('NPC_Deniz_Aydin', 'M', 370, 200, 600, 90, 1.0, LC(0.12, 0.55, 0.2, 1)),
       ('NPC_Selim_Karaca', 'M', 730, 610, 1200, -90, 1.0, LC(0.12, 0.13, 0.15, 1))]
for lab, s, x, y, z, yaw, sc, col in NPC:
    a = acts.get(lab) or eas.spawn_actor_from_class(unreal.SkeletalMeshActor, V(x, y, z), R(0, 0, yaw))
    a.set_actor_label(lab); a.set_actor_location(V(x, y, z), False, False); a.set_actor_rotation(R(0, 0, yaw), False); a.set_actor_scale3d(V(sc, sc, sc))
    c = a.skeletal_mesh_component; c.set_skinned_asset_and_update(SK[s])
    m, new = mi('MI_MJ_' + lab, MM)
    if new: MEL.set_material_instance_vector_parameter_value(m, 'Paint Tint', col); save(m)
    for i in range(c.get_num_materials()): c.set_material(i, m)
    c.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    pd = unreal.SingleAnimationPlayData(); pd.set_editor_property('anim_to_play', IDLE); pd.set_editor_property('saved_looping', True); pd.set_editor_property('saved_playing', True)
    c.set_editor_property('animation_data', pd); c.set_collision_profile_name('NoCollision')
    a.set_folder_path('Characters'); a.tags = [unreal.Name('DC_Bldg'), unreal.Name('MJ_NPC')]
print('npc', len(NPC))
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
