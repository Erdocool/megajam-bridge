import unreal
# attach each group's actors to its building (KEEP_WORLD); verify world transforms; save L_Town
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name() == 'L_Town'
print('dirty before', len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()))
acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
P = {'MJ_Grup_Studyo': acts['HERO_Studio_NYAF'], 'MJ_Grup_SFA': acts['HERO_MainApt_SFA']}
KW = unreal.AttachmentRule.KEEP_WORLD
ok = []; bad = []
for l, a in acts.items():
    f = str(a.get_folder_path())
    if f not in P or a == P[f]: continue
    par = P[f]; t0 = a.get_actor_transform()
    a.attach_to_actor(par, '', KW, KW, KW, False)
    t1 = a.get_actor_transform()
    d = (t1.translation - t0.translation).length(); dr = abs((t1.rotation.rotator().yaw - t0.rotation.rotator().yaw + 180) % 360 - 180); ds = (t1.scale3d - t0.scale3d).length()
    att = a.get_attach_parent_actor() == par
    (ok if att and d < 0.5 and dr < 0.05 and ds < 1e-3 else bad).append('%s%s' % (l[:20], '' if att else '(no)'))
    if d >= 0.5 or ds >= 1e-3: a.set_actor_transform(t0, False, False)
print('attached', len(ok), ok)
print('problems', bad)
tp = [a for a in eas.get_all_level_actors() if unreal.Name('MJ_SFA_Entrance') in a.tags]
print('teleport targets', [a.get_actor_label() for a in tp], 'parents', [str(acts['HERO_Studio_NYAF'].static_mesh_component.mobility) if hasattr(acts['HERO_Studio_NYAF'], 'static_mesh_component') else acts['HERO_Studio_NYAF'].root_component.mobility, acts['HERO_MainApt_SFA'].root_component.mobility])
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
