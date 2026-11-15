import unreal
# re-point flat-colour fallback variants to the textured tint master (FFP albedo textures end in _A/_a)
MEL = unreal.MaterialEditingLibrary; EAL = unreal.EditorAssetLibrary; LC = unreal.LinearColor
ar = unreal.AssetRegistryHelpers.get_asset_registry()
MT = unreal.load_asset('/Game/DirectorsCut/Materials/MJ_Vary/M_MJ_TintTex')
TINT = {'F1': LC(0.55, 0.8, 0.95, 1), 'F2': LC(1.0, 0.72, 0.42, 1), 'F3': LC(0.6, 0.66, 0.58, 1), 'F4': LC(0.62, 0.3, 0.27, 1)}
src = {str(d.asset_name): str(d.package_name) for d in ar.get_assets_by_path('/Game/FreeFurniturePack', recursive=True) if str(d.asset_class_path.asset_name) == 'Material'}
n = 0; miss = []
for d in ar.get_assets_by_path('/Game/DirectorsCut/Materials/MJ_Vary'):
    v = unreal.load_asset(str(d.package_name))
    if not isinstance(v, unreal.MaterialInstance) or v.get_editor_property('parent').get_name() != 'M_DC_Color': continue
    nm = str(d.asset_name); fl = nm[-2:]; orig = nm[7:-3]
    m = unreal.load_asset(src[orig]) if orig in src else None
    tx = [t for t in (MEL.get_used_textures(m) if m else []) if isinstance(t, unreal.Texture2D) and t.get_editor_property('srgb') and not t.get_name().lower().endswith('_n')]
    if not tx: miss.append(orig); continue
    MEL.set_material_instance_parent(v, MT); MEL.set_material_instance_texture_parameter_value(v, 'Albedo', tx[0]); MEL.set_material_instance_vector_parameter_value(v, 'Tint', TINT[fl])
    EAL.save_loaded_asset(v, False); n += 1
print('FIX', n, 'miss', sorted(set(miss)))
