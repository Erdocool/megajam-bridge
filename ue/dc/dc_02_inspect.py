import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gm = unreal.get_default_object(unreal.load_class(None, '/Script/EngineSettings.GameMapsSettings')) if False else None
s = unreal.GameMapsSettings.get_game_maps_settings() if hasattr(unreal.GameMapsSettings, 'get_game_maps_settings') else unreal.get_default_object(unreal.GameMapsSettings)
print('defaultGM', s.get_editor_property('global_default_game_mode'), 'map', s.get_editor_property('game_default_map'))
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
les.load_level('/Game/DirectorsCut/Buildings/LI_Studio_MJ')
hits = []
for a in eas.get_all_level_actors():
    l = a.get_actor_label(); ll = l.lower()
    if a.is_hidden_ed() or unreal.Name('MJ_HiddenForLI') in a.tags: continue
    if any(k in ll for k in ('desk', 'envelope', 'zarf', 'monitor', 'screen', 'pc', 'masa', 'hdd', 'disk', 'card', 'kart', 'box', 'kutu', 'package')):
        p = a.get_actor_location(); hits.append('%s@%d,%d,%d' % (l[:26], p.x, p.y, p.z))
print('studio', hits[:30])
les.load_level('/Game/DirectorsCut/Maps/L_Town')
w = ues.get_editor_world(); print('town GM override', w.get_world_settings().get_editor_property('default_game_mode'))
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
for l in ('INT_Studio', 'HERO_Studio_NYAF', 'HERO_MainApt_SFA', 'MJ_SFA_Entrance', 'PlayerStart_Town'):
    a = acts.get(l); print(l, a and [int(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z, a.get_actor_rotation().yaw)])
