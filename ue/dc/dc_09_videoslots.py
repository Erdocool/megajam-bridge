import unreal
# LI_Studio_MJ: media-ready placeholder on the two editing-desk screens (clue clips play here). Saves LI, reloads L_Town.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools(); LC = unreal.LinearColor
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
D = '/Game/DirectorsCut/Media'
def get(name, cls, fac):
    p = D + '/' + name
    return unreal.load_asset(p) if EAL.does_asset_exist(p) else AT.create_asset(name, D, cls, fac)
les.load_level('/Game/DirectorsCut/Buildings/LI_Studio_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
glow = LC(0.35, 0.45, 0.6, 1); strength = 2.0
s0 = acts['Screen_Monitor_L'].static_mesh_component.get_material(0)
try:
    glow = MEL.get_material_instance_vector_parameter_value(s0, 'Color'); strength = MEL.get_material_instance_scalar_parameter_value(s0, 'Strength')
except Exception: pass
print('old', s0.get_name(), [round(glow.r, 2), round(glow.g, 2), round(glow.b, 2)], strength)
MT = {}
for side in 'LR':
    mp = get('MP_MJClue_' + side, unreal.MediaPlayer, unreal.MediaPlayerFactoryNew())
    mp.set_editor_property('loop', True); EAL.save_loaded_asset(mp, False)
    mt = get('MT_MJClue_' + side, unreal.MediaTexture, unreal.MediaTextureFactoryNew())
    mt.set_editor_property('media_player', mp); mt.set_editor_property('clear_color', glow); mt.set_editor_property('auto_clear', True)
    EAL.save_loaded_asset(mt, False); MT[side] = mt
MP = D + '/M_MJ_ClueScreen'
if EAL.does_asset_exist(MP): M = unreal.load_asset(MP)
else:
    M = AT.create_asset('M_MJ_ClueScreen', D, unreal.Material, unreal.MaterialFactoryNew())
    M.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    t = MEL.create_material_expression(M, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
    t.set_editor_property('parameter_name', 'Video'); t.set_editor_property('texture', MT['L']); t.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_EXTERNAL)
    s = MEL.create_material_expression(M, unreal.MaterialExpressionScalarParameter, -700, 300)
    s.set_editor_property('parameter_name', 'Strength'); s.set_editor_property('default_value', strength)
    mu = MEL.create_material_expression(M, unreal.MaterialExpressionMultiply, -350, 100)
    MEL.connect_material_expressions(t, 'RGB', mu, 'A'); MEL.connect_material_expressions(s, '', mu, 'B')
    MEL.connect_material_property(mu, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(M); EAL.save_loaded_asset(M, False)
for side in 'LR':
    p = D + '/MI_MJ_ClueScreen_' + side
    mi = unreal.load_asset(p) if EAL.does_asset_exist(p) else AT.create_asset('MI_MJ_ClueScreen_' + side, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, M); MEL.set_material_instance_texture_parameter_value(mi, 'Video', MT[side]); EAL.save_loaded_asset(mi, False)
    a = acts['Screen_Monitor_' + side]; a.static_mesh_component.set_material(0, mi)
    a.tags = [t for t in a.tags if not str(t).startswith('MJ_VideoSlot')] + [unreal.Name('MJ_VideoSlot'), unreal.Name('MJ_VideoSlot:' + side)]
print('stats', M.get_editor_property('blend_mode'), 'ok')
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
