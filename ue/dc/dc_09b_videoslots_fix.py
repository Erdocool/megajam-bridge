import unreal
# media textures can't be material parameters: one material per screen with a fixed TextureSample of its MediaTexture
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
D = '/Game/DirectorsCut/Media'
def build(name, mt):
    p = D + '/' + name
    M = unreal.load_asset(p) if EAL.does_asset_exist(p) else AT.create_asset(name, D, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(M)
    M.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    t = MEL.create_material_expression(M, unreal.MaterialExpressionTextureSample, -700, 0)
    t.set_editor_property('texture', mt); t.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    s = MEL.create_material_expression(M, unreal.MaterialExpressionScalarParameter, -700, 300)
    s.set_editor_property('parameter_name', 'Strength'); s.set_editor_property('default_value', 2.0)
    mu = MEL.create_material_expression(M, unreal.MaterialExpressionMultiply, -350, 100)
    MEL.connect_material_expressions(t, 'RGB', mu, 'A'); MEL.connect_material_expressions(s, '', mu, 'B')
    MEL.connect_material_property(mu, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(M); EAL.save_loaded_asset(M, False)
    st = MEL.get_statistics(M); return M, st.num_pixel_shader_instructions
les.load_level('/Game/DirectorsCut/Buildings/LI_Studio_MJ')
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
for side, name in (('L', 'M_MJ_ClueScreen'), ('R', 'M_MJ_ClueScreen_R')):
    M, ins = build(name, unreal.load_asset(D + '/MT_MJClue_' + side))
    acts['Screen_Monitor_' + side].static_mesh_component.set_material(0, M); print('mat', side, name, 'ps', ins)
print('saved LI', les.save_current_level())
les.load_level('/Game/DirectorsCut/Maps/L_Town'); print('back town')
