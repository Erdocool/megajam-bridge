import unreal
# Per-flat distinct hall furniture (coat + shoe storage) kit-built from engine shapes, against the corridor walls,
# clear of the entry-door swing (hinge x610,y1093; leaf sweeps x<=610,y>=993). Old repeated SM_CoatRack/SM_ShoeRack in F1-F4
# are retired (hidden, no collision, moved 5000 down, tag keeps the original spot) - nothing deleted.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
V, R, LC = unreal.Vector, unreal.Rotator, unreal.LinearColor
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
CUBE = unreal.load_asset('/Engine/BasicShapes/Cube'); CYL = unreal.load_asset('/Engine/BasicShapes/Cylinder')
D = '/Game/DirectorsCut/Materials/MJ_Vary'; MC = unreal.load_asset('/Game/DirectorsCut/Materials/M_DC_Color')
def col(name, c, rough=0.6):
    p = D + '/MI_MJ_Hall_' + name
    if EAL.does_asset_exist(p): return unreal.load_asset(p)
    m = AT.create_asset('MI_MJ_Hall_' + name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, MC); MEL.set_material_instance_vector_parameter_value(m, 'Color', LC(*c))
    MEL.set_material_instance_scalar_parameter_value(m, 'Roughness', rough); EAL.save_loaded_asset(m, False); return m
les.load_level('/Game/DirectorsCut/Buildings/LI_Building_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
n = 0
def box(lab, fl, x0, x1, y0, y1, z0, z1, mat, mesh=None):
    global n
    a = acts.get(lab) or eas.spawn_actor_from_object(mesh or CUBE, V(0, 0, 0), R(0, 0, 0))
    a.set_actor_label(lab); a.set_actor_rotation(R(0, 0, 0), False)
    a.set_actor_scale3d(V((x1 - x0) / 100.0, (y1 - y0) / 100.0, (z1 - z0) / 100.0))
    a.set_actor_location(V((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0), False, False)
    a.static_mesh_component.set_material(0, mat); a.set_folder_path('Furniture/Floor%d/Hall' % fl)
    a.tags = [unreal.Name('DC_Bldg'), unreal.Name('MJ_Hall')]; n += 1; return a
def hook(lab, fl, x0, y, z, mat, out=+1):  # small peg sticking out of the wall
    return box(lab, fl, x0, x0 + 9 * out, y - 1.5, y + 1.5, z - 1.5, z + 1.5, mat, CYL) if out > 0 else box(lab, fl, x0 - 9, x0, y - 1.5, y + 1.5, z - 1.5, z + 1.5, mat, CYL)
WL, WR = 460.0, 660.0  # corridor inner wall faces
for fl in (1, 2, 3, 4):
    z = 300.0 * fl; P = 'Furn_F%d_Hall_' % fl
    if fl == 1:   # family: light-wood hook rail with low hooks for Elif + open 3-shelf shoe rack
        w = col('LightOak', (0.62, 0.45, 0.28)); m = col('BrassHook', (0.75, 0.6, 0.25), 0.3); s = col('WhiteShelf', (0.85, 0.85, 0.82))
        box(P + 'HookRail', fl, WL, WL + 2.5, 950, 1070, z + 160, z + 172, w)
        for i, y in enumerate((962, 986, 1010, 1034, 1058)): hook(P + 'Hook%d' % i, fl, WL + 2.5, y, z + 166, m)
        box(P + 'KidRail', fl, WL, WL + 2.5, 990, 1050, z + 100, z + 108, w); hook(P + 'KidHook', fl, WL + 2.5, 1020, z + 104, m)
        for i, h in enumerate((2, 30, 58)): box(P + 'ShoeShelf%d' % i, fl, WR - 32, WR, 995, 1085, z + h, z + h + 2.5, s)
        box(P + 'ShoeSideA', fl, WR - 32, WR, 995, 997.5, z, z + 62, s); box(P + 'ShoeSideB', fl, WR - 32, WR, 1082.5, 1085, z, z + 62, s)
    elif fl == 2:  # Deniz: black metal standing rack (pole + base + arms) + grey closed shoe cabinet
        b = col('BlackMetal', (0.03, 0.03, 0.035), 0.35); g = col('ConcreteGrey', (0.45, 0.46, 0.47)); hnd = col('Steel', (0.7, 0.7, 0.72), 0.25)
        box(P + 'RackBase', fl, WL + 5, WL + 45, 990, 1030, z, z + 3, b, CYL); box(P + 'RackPole', fl, WL + 22.5, WL + 27.5, 1007.5, 1012.5, z + 3, z + 178, b, CYL)
        box(P + 'RackArmX', fl, WL + 10, WL + 40, 1008.5, 1011.5, z + 165, z + 168, b); box(P + 'RackArmY', fl, WL + 23.5, WL + 26.5, 995, 1025, z + 160, z + 163, b)
        box(P + 'ShoeCab', fl, WR - 34, WR, 995, 1085, z, z + 95, g)
        box(P + 'ShoeCabSeam', fl, WR - 34.5, WR - 34, 1039.5, 1040.5, z + 3, z + 92, b)
        box(P + 'ShoeCabHandleA', fl, WR - 36, WR - 34, 1030, 1034, z + 70, z + 85, hnd); box(P + 'ShoeCabHandleB', fl, WR - 36, WR - 34, 1046, 1050, z + 70, z + 85, hnd)
    elif fl == 3:  # Aylin: dark walnut wall panel with 4 pegs + upholstered shoe bench
        d = col('Walnut', (0.22, 0.12, 0.07)); c = col('CreamCushion', (0.85, 0.78, 0.62), 0.9); m = col('SilverHook', (0.8, 0.8, 0.82), 0.25)
        box(P + 'CoatPanel', fl, WL, WL + 2, 960, 1060, z + 120, z + 200, d)
        for i, y in enumerate((972, 997, 1022, 1047)): hook(P + 'Peg%d' % i, fl, WL + 2, y, z + 180, m)
        box(P + 'BenchBody', fl, WR - 36, WR, 995, 1085, z, z + 40, d); box(P + 'BenchCushion', fl, WR - 35, WR - 1, 996, 1084, z + 40, z + 47, c)
        box(P + 'BenchShelf', fl, WR - 35.5, WR - 0.5, 997, 1083, z + 12, z + 14, c)
    else:          # Selim (manager): tall closed hall wardrobe + umbrella stand
        k = col('Mahogany', (0.3, 0.09, 0.07), 0.45); hnd = col('Gold', (0.8, 0.62, 0.2), 0.2); u = col('UmbrellaStand', (0.1, 0.12, 0.2))
        box(P + 'Wardrobe', fl, WR - 42, WR, 995, 1085, z, z + 205, k)
        box(P + 'WardrobeSeam', fl, WR - 42.5, WR - 42, 1039.5, 1040.5, z + 5, z + 200, hnd)
        box(P + 'WardrobeKnobA', fl, WR - 44, WR - 42, 1033, 1036, z + 100, z + 112, hnd); box(P + 'WardrobeKnobB', fl, WR - 44, WR - 42, 1044, 1047, z + 100, z + 112, hnd)
        box(P + 'Umbrella', fl, WL + 4, WL + 28, 1050, 1074, z, z + 55, u, CYL)
ret = []
for a in list(acts.values()):
    sm = a.static_mesh_component.static_mesh if isinstance(a, unreal.StaticMeshActor) else None
    lab = a.get_actor_label()
    if sm and sm.get_name() in ('SM_CoatRack', 'SM_ShoeRack') and lab.startswith(('Furn_F1', 'Furn_F2', 'Furn_F3', 'Furn_F4')) and unreal.Name('MJ_Retired') not in a.tags:
        p = a.get_actor_location()
        a.tags = list(a.tags) + [unreal.Name('MJ_Retired'), unreal.Name('MJ_Orig:%d,%d,%d' % (p.x, p.y, p.z))]
        a.set_actor_location(V(p.x, p.y, p.z - 5000), False, False); a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
        a.set_folder_path('Furniture/_Retired'); ret.append(lab)
print('HALL parts', n, 'retired', ret)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
