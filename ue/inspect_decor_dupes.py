# READ-ONLY: repeated static meshes across floors F0-F4 in L_Building + recently added Fab/Megascans content.
import os, time, collections
import unreal
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
def floor(z):
    return 'F0' if z < 290 else 'F1' if z < 590 else 'F2' if z < 890 else 'F3' if z < 1190 else 'F4'
tab = collections.defaultdict(lambda: collections.Counter())
for a in acts:
    if a.get_class().get_name() != 'StaticMeshActor':
        continue
    lab = a.get_actor_label()
    if not lab.startswith('Furn_'):
        continue
    sm = a.get_component_by_class(unreal.StaticMeshComponent).get_editor_property('static_mesh')
    if not sm:
        continue
    tab[sm.get_name()][floor(a.get_actor_location().z)] += 1
print('mesh | F0 F1 F2 F3 F4 | floors')
rows = sorted(tab.items(), key=lambda kv: (-len(kv[1]), kv[0]))
for m, c in rows:
    if len(c) >= 2:
        print('%s | %s | %d' % (m, ' '.join(str(c.get(f, 0)) for f in ('F0', 'F1', 'F2', 'F3', 'F4')), len(c)))
print('unique-to-one-floor meshes:', sum(1 for m, c in rows if len(c) == 1))
root = unreal.Paths.project_content_dir()
now = time.time()
agg = collections.defaultdict(lambda: [0, 0, 0.0])
for top in ('Fab', 'Megascans', 'MSPresets'):
    base = os.path.join(root, top)
    if not os.path.isdir(base):
        continue
    for dp, dn, fn in os.walk(base):
        for f in fn:
            if not f.endswith('.uasset'):
                continue
            fp = os.path.join(dp, f)
            rel = os.path.relpath(fp, root).replace('\\', '/').split('/')
            key = '/'.join(rel[:2]) if len(rel) > 2 else rel[0]
            st = os.path.getmtime(fp)
            agg[key][0] += 1
            agg[key][2] = max(agg[key][2], st)
            if f.startswith('SM_') or 'mesh' in dp.lower():
                agg[key][1] += 1
print('\ncontent pack | assets | mesh-ish | newest (local)')
for k, (n, nm, st) in sorted(agg.items(), key=lambda kv: -kv[1][2]):
    print('%s | %d | %d | %s%s' % (k, n, nm, time.strftime('%H:%M %d.%m', time.localtime(st)), '  NEW' if now - st < 3 * 3600 else ''))
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for top in ('/Game/Fab', '/Game/Megascans'):
    sms = [x for x in ar.get_assets_by_path(top, recursive=True) if str(x.asset_class_path.asset_name) == 'StaticMesh']
    print('\nStaticMeshes under', top, len(sms))
    for x in sms[:80]:
        print('  ', str(x.package_name))
