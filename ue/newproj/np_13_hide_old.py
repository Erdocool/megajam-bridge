import unreal
# hide (not delete) old City Sample fillers/candidates and old street pieces outside the bounded area; tag MJ_HiddenForCity; save L_Town
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name() == 'L_Town'
KEEP = ('HERO_Studio_NYAF', 'HERO_MainApt_SFA', 'INT_Studio', 'INT_Building')
T = unreal.Name('MJ_HiddenForCity'); hid = []; kept = []
def hide(a):
    a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
    for c in a.get_components_by_class(unreal.PrimitiveComponent): c.set_visibility(False)
    if T not in a.tags: a.tags = list(a.tags) + [T]
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if l in KEEP: continue
    if l.startswith(('FILL', 'CAND_', 'SLOT_', 'CAT_Ground')) or (isinstance(a, unreal.LevelInstance) and not l.startswith(('HERO_', 'INT_'))):
        hide(a); hid.append(l[:10]); continue
    if l.startswith('Town_'):
        o, e = a.get_actor_bounds(False)
        if o.x + e.x > 11000 and o.x - e.x < 12950 and o.y + e.y > 2950 and o.y - e.y < 12934: kept.append(l)
        else: hide(a); hid.append(l)
print('hidden', len(hid), sorted(set(h for h in hid if h.startswith('Town_'))))
print('kept street', kept)
print('saved', unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
