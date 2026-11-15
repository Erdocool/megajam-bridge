
# In a COPY level (under /Game/DirectorsCut/Buildings/): hide + disable everything outside the kept box, and the
# global environment actors (sun, sky, fog, atmosphere, clouds). Nothing deleted. Tags 'MJ_HiddenForLI'.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert '/Game/DirectorsCut/Buildings/LI_' in w.get_path_name(), w.get_path_name()
ENV = ('DirectionalLight', 'SkyLight', 'SkyAtmosphere', 'ExponentialHeightFog', 'VolumetricCloud')
def hide(a):
    a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        c.set_visibility(False, True); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for c in a.get_components_by_class(unreal.LightComponentBase):
        c.set_visibility(False, True)
    a.tags = list(a.tags) + ['MJ_HiddenForLI']
nh = 0; kept = 0
for a in eas.get_all_level_actors():
    cn = a.get_class().get_name()
    if 'MJ_HiddenForLI' in [str(t) for t in a.tags]: continue
    if cn in ENV or cn == 'PlayerStart':
        hide(a); nh += 1; continue
    if cn == 'PostProcessVolume':
        if a.get_editor_property('unbound'):
            a.set_editor_property('unbound', False); print('PPV bound now', a.get_actor_label())
        continue
    p = a.get_actor_location()
    if not (KEEP[0] <= p.x <= KEEP[1] and KEEP[2] <= p.y <= KEEP[3] and KEEP[4] <= p.z <= KEEP[5]):
        hide(a); nh += 1
    else:
        kept += 1
print('hidden', nh, 'kept', kept)
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
