import unreal
# NewMegaJam step 1d: open L_Town (Main is clean) and report state; no save
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if ues.get_editor_world().get_name() != 'L_Town':
    assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0, 'dirty map, not switching'
    les.load_level('/Game/DirectorsCut/Maps/L_Town')
w = ues.get_editor_world(); print('map', w.get_name())
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
need = ['HERO_Studio_NYAF', 'HERO_MainApt_SFA', 'INT_Studio', 'INT_Building', 'MJ_StudioExit_Trigger', 'MJ_SFA_Entrance', 'PlayerStart_Town', 'Key_Building_Front', 'Proxy_Key_Building_Front', 'MJ_KeyCrate', 'MJ_PPV_StudioInterior', 'MJ_PPV_BuildingInterior', 'MJ_Exposure_PPV', 'L_SkyAtmosphere']
print('missing', [n for n in need if n not in acts])
print('bounds', [l for l in acts if l.startswith('MJ_Bound_')], [acts[l].is_hidden_ed() or acts[l].get_editor_property('hidden') for l in acts if l.startswith('MJ_Bound_')])
for l in ('MJ_Exposure_PPV', 'MJ_PPV_BuildingInterior', 'MJ_PPV_StudioInterior'):
    if l in acts: s = acts[l].settings; print(l[3:], s.auto_exposure_method, round(s.auto_exposure_min_brightness, 2), round(s.auto_exposure_max_brightness, 2))
BD = unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Door.BP_Door_C')
print('door', [(bool(x.get_editor_property('bLocked')), str(x.get_editor_property('KeyID'))) for x in unreal.GameplayStatics.get_all_actors_of_class(w, BD) if x.get_actor_label() == 'Door_Street'])
if 'Key_Building_Front' in acts: print('keyid', acts['Key_Building_Front'].get_editor_property('KeyID'))
mov = st = 0
for li in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Light):
    if '_MJ' in li.get_path_name() and li.light_component and not isinstance(li, unreal.DirectionalLight):
        if li.light_component.mobility == unreal.ComponentMobility.MOVABLE: mov += 1
        else: st += 1
print('LI lights movable', mov, 'other', st)
for l, a in sorted(acts.items()):
    if l.startswith('FILL'):
        o, e = a.get_actor_bounds(False); print('F', l, int(o.x - e.x), int(o.x + e.x), int(o.y - e.y), int(o.y + e.y), int(o.z + e.z), a.is_hidden_ed())
