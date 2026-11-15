# dc_25: Mixamo import (Picking Up = Y Bot mesh+skeleton, + 3 anim-only FBX) -> IK rig + retargeter -> Manny anims + montages.
# Built from bridge steps q33..q38 (2026-11-15 ~23:30 TSI). No Blueprint graph edits. Source: C:/MegaJam/Imports/MJ_Mixamo_Anims/

# ---- step q33 ----
import unreal
SRC = 'C:/MegaJam/Imports/MJ_Mixamo_Anims/'; DST = '/Game/DirectorsCut/Mixamo'
AT = unreal.AssetToolsHelpers.get_asset_tools()
def imp(fn, skel=None):
    t = unreal.AssetImportTask(); t.filename = SRC + fn; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    o = unreal.FbxImportUI(); o.import_mesh = skel is None; o.import_animations = True; o.import_as_skeletal = True
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH; o.import_materials = False; o.import_textures = False
    if skel: o.skeleton = skel
    o.anim_sequence_import_data.set_editor_property('import_bone_tracks', True)
    t.options = o; AT.import_asset_tasks([t]); return list(t.imported_object_paths)
p1 = imp('Picking Up.fbx'); print('I1', [x.split('/')[-1] for x in p1])
sk = None
for x in p1:
    a = unreal.load_asset(x)
    if isinstance(a, unreal.Skeleton): sk = a
    elif isinstance(a, unreal.SkeletalMesh) and sk is None: sk = a.skeleton
print('SKEL', sk.get_path_name() if sk else None)
if sk:
    p2 = imp('Reaching Out.fbx', sk); print('I2', [x.split('/')[-1] for x in p2])

# ---- step q34 ----
import unreal
SRC = 'C:/MegaJam/Imports/MJ_Mixamo_Anims/'; DST = '/Game/DirectorsCut/Mixamo'
AT = unreal.AssetToolsHelpers.get_asset_tools()
sk = unreal.load_asset(DST + '/Picking_Up_Skeleton')
for fn in ['Reaching Out.fbx']:
    t = unreal.AssetImportTask(); t.filename = SRC + fn; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    o = unreal.FbxImportUI(); o.import_mesh = False; o.import_animations = True; o.import_as_skeletal = True; o.import_materials = False; o.import_textures = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION; o.original_import_type = unreal.FBXImportType.FBXIT_ANIMATION; o.skeleton = sk
    t.options = o; AT.import_asset_tasks([t]); print('I', fn, [x.split('/')[-1] for x in t.imported_object_paths])
print('L', [a.split('/')[-1] for a in unreal.EditorAssetLibrary.list_assets(DST, True, False)])

# ---- step q35 ----
import unreal
SRC = 'C:/MegaJam/Imports/MJ_Mixamo_Anims/'; DST = '/Game/DirectorsCut/Mixamo'
AT = unreal.AssetToolsHelpers.get_asset_tools()
sk = unreal.load_asset(DST + '/Picking_Up_Skeleton')
for fn in ['Opening Door Inwards.fbx', 'Button Pushing.fbx']:
    t = unreal.AssetImportTask(); t.filename = SRC + fn; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = True
    o = unreal.FbxImportUI(); o.import_mesh = False; o.import_animations = True; o.import_as_skeletal = True; o.import_materials = False; o.import_textures = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION; o.original_import_type = unreal.FBXImportType.FBXIT_ANIMATION; o.skeleton = sk
    t.options = o; AT.import_asset_tasks([t]); print('I', fn, len(t.imported_object_paths))
AR = unreal.AssetRegistryHelpers.get_asset_registry()
for c in ['IKRigDefinition', 'IKRetargeter']:
    print('A', c, [str(a.package_name) for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/IKRig', c))][:8])
print('M1', [m for m in dir(unreal.IKRigController) if not m.startswith('_')][:200])
print('M2', [m for m in dir(unreal.IKRetargeterController) if not m.startswith('_')][:200])
print('M3', [m for m in dir(unreal.IKRetargetBatchOperation) if not m.startswith('_') and 'retarget' in m.lower()])

# ---- step q36 ----
import unreal
D = '/Game/DirectorsCut/Mixamo'; AT = unreal.AssetToolsHelpers.get_asset_tools(); E = unreal.EditorAssetLibrary
S = unreal.RetargetSourceOrTarget.SOURCE; T = unreal.RetargetSourceOrTarget.TARGET
mix = unreal.load_asset(D + '/Picking_Up'); manny = unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple')
ikm = unreal.load_asset('/Game/ControlRig/Characters/Mannequins/Rigs/IK_Mannequin')
rig = unreal.load_asset(D + '/IK_MixamoYBot') or AT.create_asset('IK_MixamoYBot', D, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
rc = unreal.IKRigController.get_controller(rig); rc.set_skeletal_mesh(mix)
ok = rc.apply_auto_generated_retarget_definition()
print('R1', ok, rc.get_retarget_root(), len(rc.get_retarget_chains()))
rtg = unreal.load_asset(D + '/RTG_Mixamo_to_Manny') or AT.create_asset('RTG_Mixamo_to_Manny', D, unreal.IKRetargeter, unreal.IKRetargetFactory())
c = unreal.IKRetargeterController.get_controller(rtg)
c.set_ik_rig(S, rig); c.set_ik_rig(T, ikm)
try: c.remove_all_ops()
except Exception as e: print('W ops', e)
c.add_default_ops(); c.assign_ik_rig_to_all_ops(S, rig); c.assign_ik_rig_to_all_ops(T, ikm)
c.set_preview_mesh(S, mix); c.set_preview_mesh(T, manny)
c.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
try:
    c.create_retarget_pose('MJ_Align', T); c.auto_align_all_bones(T)
except Exception as e: print('W align', e)
print('R2 ops', c.get_num_retarget_ops())
for a in (rig, rtg): E.save_loaded_asset(a, False)
anims = [unreal.load_asset(D + '/' + n) for n in ['Reaching_Out', 'Picking_Up_Anim', 'Opening_Door_Inwards', 'Button_Pushing']]
anims = [a for a in anims if a]
out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(anims, mix, manny, rtg, '', '', 'MJ_', '', D + '/Manny', False, False, True)
print('R3', [str(x.asset_name) for x in out])
for x in out: E.save_asset(str(x.package_name), False)

# ---- step q37 ----
import unreal
D = '/Game/DirectorsCut/Mixamo'; E = unreal.EditorAssetLibrary
mix = unreal.load_asset(D + '/Picking_Up'); manny = unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple')
rtg = unreal.load_asset(D + '/RTG_Mixamo_to_Manny')
ad = [E.find_asset_data(D + '/' + n) for n in ['Reaching_Out', 'Picking_Up_Anim', 'Opening_Door_Inwards', 'Button_Pushing']]
ad = [a for a in ad if a.is_valid()]
out = unreal.IKRetargetBatchOperation.duplicate_and_retarget(ad, mix, manny, rtg, '', '', 'MJ_', '', D + '/Manny', False, False, True)
print('R3', [str(x.asset_name) for x in out])
for x in out: E.save_asset(str(x.package_name), False)
a = unreal.load_asset(D + '/Manny/MJ_Reaching_Out')
if a: print('R4', a.skeleton.get_name(), round(a.sequence_length, 2))

# ---- step q38 ----
import unreal
D = '/Game/DirectorsCut/Mixamo/Manny'; E = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
for n in ['MJ_Reaching_Out', 'MJ_Picking_Up_Anim', 'MJ_Opening_Door_Inwards', 'MJ_Button_Pushing']:
    a = unreal.load_asset(D + '/' + n)
    m = unreal.load_asset(D + '/AM_' + n[3:])
    if not m:
        f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', a)
        m = AT.create_asset('AM_' + n[3:], D, unreal.AnimMontage, f)
    if m: E.save_loaded_asset(m, False)
    print('M', n, a.get_editor_property('skeleton').get_name(), round(a.get_editor_property('sequence_length'), 2), m.get_name() if m else None)
for p in ['/Game/FirstPerson/Anims/ABP_FP_Copy', '/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed']:
    pass
AR = unreal.AssetRegistryHelpers.get_asset_registry()
for n in ['ABP_FP_Copy', 'ABP_Unarmed']:
    r = [str(x.package_name) for x in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'AnimBlueprint')) if str(x.asset_name) == n]
    if r:
        bp = unreal.load_asset(r[0]); s = []
        for g in unreal.BlueprintEditorLibrary.get_graphs(bp) if hasattr(unreal.BlueprintEditorLibrary, 'get_graphs') else []: s.append(g.get_name())
        print('G', n, r[0])
