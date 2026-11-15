import unreal
EAL = unreal.EditorAssetLibrary
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print('proj', unreal.Paths.get_project_file_path()[-40:], 'map', w.get_name(), 'dirty', len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()))
P = ['/Game/DirectorsCut/Maps/L_Town', '/Game/DirectorsCut/Maps/L_Building', '/Game/DirectorsCut/Maps/L_Apartment', '/Game/DirectorsCut/Blueprints/BP_Door', '/Game/DirectorsCut/Blueprints/BP_Key',
     '/Game/DirectorsCut/Blueprints/Components/BPC_MJDoor', '/Game/DirectorsCut/Blueprints/Components/BPC_MJKey', '/Game/DirectorsCut/Blueprints/Components/BPC_MJExitTeleport', '/Game/DirectorsCut/Blueprints/BP_MJExitTrigger']
print('missing', [p.split('/')[-1] for p in P if not EAL.does_asset_exist(p)])
print('bp', sorted(a.split('.')[-1] for a in EAL.list_assets('/Game/DirectorsCut/Blueprints', True) )[:60])
print('maps', sorted(a.split('.')[-1] for a in EAL.list_assets('/Game/DirectorsCut/Maps', False)))
