import unreal, json, os
ar = unreal.AssetRegistryHelpers.get_asset_registry(); out = {}
for root in ('/Game/DirectorsCut', '/Game/FreeFurniturePack', '/Game/LucapyAssets', '/Game/DetectiveOffice', '/Game/JapaneseStyleRoom', '/Game/StarterContent/Props', '/Game/Characters', '/Game/MetaHumans', '/Game/Fab'):
    out[root] = sorted('%s|%s' % (str(d.package_name), str(d.asset_class_path.asset_name)) for d in ar.get_assets_by_path(root, recursive=True) if str(d.asset_class_path.asset_name) in ('StaticMesh', 'Material', 'MaterialInstanceConstant', 'SkeletalMesh', 'Blueprint', 'AnimSequence', 'AnimBlueprint'))
out['top'] = sorted(set(str(p) for p in ar.get_sub_paths('/Game', False)))
m = unreal.load_asset('/Game/DirectorsCut/Materials/M_Decor_F1_MustardRug') if unreal.EditorAssetLibrary.does_asset_exist('/Game/DirectorsCut/Materials/M_Decor_F1_MustardRug') else None
out['decor'] = [m.get_class().get_name(), str(m.get_editor_property('parent')) if isinstance(m, unreal.MaterialInstance) else '', [str(n) for n in unreal.MaterialEditingLibrary.get_vector_parameter_names(m)]] if m else None
p = os.path.join(unreal.Paths.project_saved_dir(), 'mj_assets.json'); json.dump(out, open(p, 'w')); print('AS', sum(len(v) for v in out.values() if isinstance(v, list)))
