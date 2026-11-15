import unreal
# NewMegaJam step 2: LI copies -> lights Movable + cap (town_18 logic), Door_Street locked; save only LI copies; back to L_Town
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
CAP = {unreal.LightUnits.CANDELAS: 8.0, unreal.LightUnits.LUMENS: 100.0, unreal.LightUnits.UNITLESS: 128.0, unreal.LightUnits.EV: 3.0}
assert ues.get_editor_world().get_name() == 'L_Town' and len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0, 'L_Town dirty'
for path in ('/Game/DirectorsCut/Buildings/LI_Studio_MJ', '/Game/DirectorsCut/Buildings/LI_Building_MJ'):
    les.load_level(path)
    n = mv = cp = 0; ch = False
    for a in eas.get_all_level_actors():
        for c in a.get_components_by_class(unreal.LocalLightComponent):
            n += 1
            if c.mobility != unreal.ComponentMobility.MOVABLE: c.set_mobility(unreal.ComponentMobility.MOVABLE); mv += 1; ch = True
            m = CAP.get(c.get_editor_property('intensity_units'), 8.0)
            if c.get_editor_property('intensity') > m: c.set_editor_property('intensity', m); cp += 1; ch = True
    msg = ''
    if path.endswith('Building_MJ'):
        d = [a for a in eas.get_all_level_actors() if a.get_actor_label() == 'Door_Street'][0]
        msg = 'door was %s %s' % (d.get_editor_property('bLocked'), d.get_editor_property('KeyID'))
        if not d.get_editor_property('bLocked') or str(d.get_editor_property('KeyID')) != 'Key_Building_Front':
            d.set_editor_property('bLocked', True); d.set_editor_property('KeyID', type(d.get_editor_property('KeyID'))('Key_Building_Front')); ch = True
    print(path.split('/')[-1], 'lights', n, 'set movable', mv, 'capped', cp, msg, 'saved' if ch and les.save_current_level() else 'unchanged')
les.load_level('/Game/DirectorsCut/Maps/L_Town')
w = ues.get_editor_world()
lis = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.LevelInstance)
print('L_Town', w.get_name(), 'LIs', len(lis), 'BP_Door seen', len(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Door.BP_Door_C'))))
