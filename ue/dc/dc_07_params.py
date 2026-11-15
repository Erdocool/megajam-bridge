import unreal
MEL = unreal.MaterialEditingLibrary
names = ['M_Classic_Cupboard','MI_Modern_Bed_Table','M_Toilet','M_CeramicWhite','MI_KitchenBase','MI_Fridge','M_Lamp','M_DarkWalnut','M_Chrome','MI_Rug','M_Classic_table','M_Classic_chair','M_TV','M_Bathtub','MI_KitchenUppers','T_Table_Lamp','MI_DeskLamp','M_Old_Chair','MI_Lampshade','M_DC_Color','M_DC_Emissive','M_DC_Albedo','MI_DC_MonitorGlow','MI_Manny_01','MI_Quinn_01','M_Mannequin']
ar = unreal.AssetRegistryHelpers.get_asset_registry()
idx = {}
for d in ar.get_assets_by_path('/Game', recursive=True):
    c = str(d.asset_class_path.asset_name)
    if c in ('Material', 'MaterialInstanceConstant') and str(d.asset_name) in names: idx.setdefault(str(d.asset_name), str(d.package_name))
for n in names:
    p = idx.get(n)
    if not p: print('X', n); continue
    m = unreal.load_asset(p)
    v = [str(x) for x in MEL.get_vector_parameter_names(m)]; s = [str(x) for x in MEL.get_scalar_parameter_names(m)]; t = [str(x) for x in MEL.get_texture_parameter_names(m)]
    par = m.get_editor_property('parent').get_name() if isinstance(m, unreal.MaterialInstance) else '-'
    print('P', n, p.split('/')[2], par, 'V', v[:5], 'T', t[:3], 'S', s[:3])
