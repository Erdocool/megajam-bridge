# READ-ONLY inspection for the door/key mechanic (MegaJam DirectorsCut, UE 5.8).
# Changes nothing, saves nothing, loads no level. Run through the bridge:  !py + this file.
import os
import unreal

BP_DOOR = '/Game/DirectorsCut/Blueprints/BP_Door'
BP_KEY = '/Game/DirectorsCut/Blueprints/BP_Key'
LEVEL = '/Game/DirectorsCut/Maps/L_Building'
BEL = unreal.BlueprintEditorLibrary


def p(*a):
    print(' '.join(str(x) for x in a))


def safe(fn, default='?'):
    try:
        return fn()
    except Exception as e:  # noqa
        return '%s(ERR %s)' % (default, e)


p('== ENGINE', unreal.SystemLibrary.get_engine_version())
for n in ('BlueprintGraphEditor', 'BlueprintGraphPin', 'BlueprintEditorLibrary', 'SubobjectDataSubsystem', 'K2Node_ExecutePythonScript'):
    p('api', n, hasattr(unreal, n))

world = safe(lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), None)
level_path = safe(lambda: world.get_path_name().split('.')[0], '?')
p('== CURRENT LEVEL', level_path)
p('dirty packages (map/content):',
  safe(lambda: [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]),
  safe(lambda: [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]))


def var_type(bp, name):
    try:
        pt = BEL.get_member_variable_type(bp, name)
        if pt is None:
            return '?'
        try:
            return BEL.pin_type_to_json_schema(pt, None)[:120]
        except Exception:
            return str(pt)[:120]
    except Exception as e:
        return 'ERR %s' % e


def pin_desc(pin):
    try:
        name = str(pin.get_pin_name())
        d = 'in' if pin.get_pin_direction() == unreal.EdGraphPinDirection.EGPD_INPUT else 'out'
        t = str(pin.get_pin_type_display_string())
        v = pin.get_pin_value()
        links = []
        for o in pin.list_connected_pins():
            on = o.get_owning_node()
            links.append('%s.%s' % (on.get_name() if on else '?', o.get_pin_name()))
        s = '%s %s:%s' % (d, name, t)
        if v:
            s += '=' + v[:40]
        if links:
            s += ' -> ' + ','.join(links)
        return s
    except Exception as e:
        return 'pin ERR %s' % e


def dump_bp(path):
    p('\n== BLUEPRINT', path)
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        p('  MISSING')
        return None
    bp = unreal.EditorAssetLibrary.load_asset(path)
    p('  class', bp.get_class().get_name(), '| parent', safe(lambda: BEL.get_blueprint_parent_class(bp).get_name()))
    p('  saved_by', safe(lambda: BEL.get_saved_by_engine_version(bp)))
    names = safe(lambda: list(BEL.list_member_variable_names(bp, False)), [])
    p('  variables(own):', names)
    if isinstance(names, list):
        for n in names:
            p('    var', n, var_type(bp, n))
    # components (SCS)
    try:
        sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = sub.k2_gather_subobject_data_for_blueprint(bp)
        lib = unreal.SubobjectDataBlueprintFunctionLibrary
        for h in handles:
            d = lib.get_data(h)
            obj = lib.get_object(d)
            extra = ''
            if isinstance(obj, unreal.SceneComponent):
                extra = ' relLoc=%s relRot=%s' % (obj.get_editor_property('relative_location'), obj.get_editor_property('relative_rotation'))
            if isinstance(obj, unreal.StaticMeshComponent):
                sm = obj.get_editor_property('static_mesh')
                extra += ' mesh=%s' % (sm.get_path_name() if sm else None)
            p('    comp', lib.get_variable_name(d), '|', obj.get_class().get_name() if obj else None, extra)
    except Exception as e:
        p('  components ERR', e)
    # graphs and nodes
    try:
        for g in BEL.list_graphs(bp):
            ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
            nodes = ed.list_all_nodes()
            p('  graph', g.get_name(), 'nodes=%d' % len(nodes))
            for nd in nodes[:60]:
                p('    node', nd.get_name(), '|', nd.get_class().get_name(), '|', safe(lambda: nd.get_node_title()))
                for pin in safe(lambda: list(nd.list_all_pins()), [])[:14]:
                    p('       ', pin_desc(pin))
    except Exception as e:
        p('  graphs ERR', e)
    return bp


door_bp = dump_bp(BP_DOOR)
key_bp = dump_bp(BP_KEY)

# Python hook files
proj = unreal.Paths.project_dir()
for rel in ('Content/Python/init_unreal.py', 'Content/Python/dc_building_interact.py'):
    fp = os.path.join(proj, rel)
    if os.path.isfile(fp):
        txt = open(fp, 'r', encoding='utf-8', errors='replace').read()
        p('\n== FILE', rel, len(txt), 'bytes; HasKey' in txt, 'HasKey:' in txt)
        for line in txt.splitlines():
            ls = line.strip()
            if any(k in ls for k in ('HasKey', 'def ', 'KeyID', 'bLocked', 'OpenAngle', 'tag', 'Tag', 'rotation', 'attach')):
                p('   |', ls[:160])
    else:
        p('\n== FILE', rel, 'missing')

# Level instances (only if L_Building is the open level; nothing is loaded)
if level_path.endswith('L_Building'):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    p('\n== L_Building actors total', len(actors))
    doors = [a for a in actors if 'BP_Door' in a.get_class().get_name()]
    keys = [a for a in actors if 'BP_Key' in a.get_class().get_name()]
    p('doors', len(doors), 'keys', len(keys))
    for a in doors + keys:
        vals = []
        for v in ('bLocked', 'KeyID', 'bOpen', 'OpenAngle'):
            try:
                vals.append('%s=%s' % (v, a.get_editor_property(v)))
            except Exception:
                pass
        att = []
        try:
            for c in a.get_attached_actors():
                rc = c.root_component
                att.append('%s[%s rel=%s]' % (c.get_actor_label(), c.get_class().get_name(), rc.get_editor_property('relative_rotation') if rc else None))
        except Exception as e:
            att.append('ERR %s' % e)
        comps = []
        try:
            for c in a.get_components_by_class(unreal.SceneComponent):
                comps.append(c.get_name())
        except Exception:
            pass
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        p('  %s | loc=(%.0f,%.0f,%.0f) yaw=%.0f | %s | tags=%s | attached=%s | comps=%s' % (
            a.get_actor_label(), loc.x, loc.y, loc.z, rot.yaw, ' '.join(vals),
            [str(t) for t in a.tags], att, comps[:8]))
    ws = world.get_world_settings()
    gm = safe(lambda: ws.get_editor_property('default_game_mode'))
    p('\n== world GameMode override', gm)
    try:
        gmc = gm if gm else None
        if gmc:
            cdo = unreal.get_default_object(gmc)
            p('   default pawn', cdo.get_editor_property('default_pawn_class'))
    except Exception as e:
        p('   pawn ERR', e)
    p('player starts', len([a for a in actors if a.get_class().get_name() == 'PlayerStart']))
else:
    p('\n(L_Building is not the open level; instance dump skipped. Nothing was loaded.)')

p('\n== DONE (read-only, nothing saved)')
