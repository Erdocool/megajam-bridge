import unreal
# NewMegaJam step 1a: read-only. assets exist? Main's city meshes (path, bounds, nanite)
EAL = unreal.EditorAssetLibrary
miss = [p for p in ('/Game/DirectorsCut/Maps/L_Town', '/Game/DirectorsCut/Buildings/LI_Studio_MJ', '/Game/DirectorsCut/Buildings/LI_Building_MJ',
     '/Game/DirectorsCut/Buildings/LI_NYAF_MJ', '/Game/DirectorsCut/Buildings/LI_SFA_MJ', '/Game/DirectorsCut/Blueprints/BP_MJExitTrigger',
     '/Game/DirectorsCut/Blueprints/BP_Door', '/Game/DirectorsCut/Blueprints/BP_Key', '/Game/DirectorsCut/Blueprints/Components/BPC_MJExitTeleport') if not EAL.does_asset_exist(p)]
print('missing', miss)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print('map', w.get_name(), 'dirty', len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and str(a.get_folder_path()).startswith('Model'):
        sm = a.static_mesh_component.static_mesh
        o, e = a.get_actor_bounds(False)
        nan = sm.get_editor_property('nanite_settings').enabled if sm else None
        print('M', a.get_actor_label()[:28], sm.get_path_name().split('.')[0] if sm else None, [int(o.x), int(o.y), int(o.z)], [int(e.x), int(e.y), int(e.z)], 'N' if nan else 'n', [round(v, 2) for v in (a.get_actor_scale3d().x,)])
