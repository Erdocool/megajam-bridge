import unreal
# put studio / SFA related actors into Outliner folders (no transforms changed); report leftovers; save L_Town
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name() == 'L_Town'
ST = ('HERO_Studio_NYAF', 'INT_Studio', 'PlayerStart_Town', 'MJ_StudioExit_Trigger', 'MJ_PPV_StudioInterior')
SF = ('HERO_MainApt_SFA', 'INT_Building', 'MJ_SFA_Entrance', 'MJ_KeyCrate', 'Key_Building_Front', 'Proxy_Key_Building_Front', 'MJ_PPV_BuildingInterior', 'MJ_WalkFloor')
g = {'MJ_Grup_Studyo': [], 'MJ_Grup_SFA': []}; left = []
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if l in ST: f = 'MJ_Grup_Studyo'
    elif l in SF or l.startswith('MJ_Bound_'): f = 'MJ_Grup_SFA'
    else:
        if not l.startswith('CITY_') and unreal.Name('MJ_HiddenForCity') not in a.tags and not a.is_hidden_ed() and not l.startswith(('CAND_', 'SLOT_')):
            left.append(l[:22])
        continue
    a.set_folder_path(f); g[f].append(l)
for k, v in g.items(): print(k, len(v), v)
print('left', left)
p = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'MJ_Exposure_PPV'][0]
print('MJ_Exposure_PPV unbound', p.get_editor_property('unbound'))
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
