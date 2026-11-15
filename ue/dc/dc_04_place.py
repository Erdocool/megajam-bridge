import unreal
# L_Town: markers for HUD logic + GameMode override (level setting only); save
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = ues.get_editor_world(); assert w.get_name() == 'L_Town'
print('dirty before', len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()))
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
M = {'MJ_EditDesk': (2285, -1246, 1020), 'MJ_BlueEnvelope': (2228, -1272, 1022), 'MJ_TimerStart': (13750, 7680, 115), 'MJ_DayStart_1': (2420, -1450, 1045)}
for l, p in M.items():
    a = acts.get(l) or eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(*p), unreal.Rotator(0, 0, 0))
    a.set_actor_label(l); a.set_actor_location(unreal.Vector(*p), False, False); a.tags = [unreal.Name(l)]; a.set_folder_path('MJ_Gameplay')
ws = w.get_world_settings()
ws.set_editor_property('default_game_mode', unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_MJGameMode.BP_MJGameMode_C'))
print('gm', ws.get_editor_property('default_game_mode').get_name())
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
