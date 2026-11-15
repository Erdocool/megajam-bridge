import time
import unreal

BP_DOOR = '/Game/DirectorsCut/Blueprints/BP_Door'
BP_KEY = '/Game/DirectorsCut/Blueprints/BP_Key'
LEAF_MODE = 'auto'          # 'auto' | 'component:<VarName>' | 'attached'
DOOR_DIST = 200.0           # cm, pawn -> door leaf centre
KEY_DIST = 170.0
DOOR_FACING = 0.5           # dot(camera forward, dir to target)
KEY_FACING = 0.3
SWING_SPEED = 6.0
DRY_RUN = False

BEL = unreal.BlueprintEditorLibrary
BGE = unreal.BlueprintGraphEditor
KML = '/Script/Engine.KismetMathLibrary.'
KSL = '/Script/Engine.KismetSystemLibrary.'
KSTR = '/Script/Engine.KismetStringLibrary.'
GPS = '/Script/Engine.GameplayStatics.'
ACT = '/Script/Engine.Actor.'
LOG = []
FAIL = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


class G(object):
    """Tiny helper around BlueprintGraphEditor for one graph."""

    def __init__(self, bp, graph):
        self.bp = bp
        self.ed = BGE.get_graph_editor(graph)
        self.x = 400
        self.y = 600

    def _pos(self, node, dx=260):
        try:
            node.set_node_pos(unreal.IntPoint(self.x, self.y))
        except Exception:
            pass
        self.x += dx

    def pin_in(self, node, name):
        pin = node.find_input_pin(name)
        if not pin.is_valid():
            FAIL.append('no input pin %s on %s' % (name, node.get_node_title()))
        return pin

    def pin_out(self, node, name=None):
        pin = node.find_output_pin(name) if name else node.find_result_pin()
        if not pin.is_valid():
            FAIL.append('no output pin %s on %s' % (name, node.get_node_title()))
        return pin

    def connect(self, out_pin, in_pin, what=''):
        ok = False
        try:
            ok = out_pin.try_create_connection(in_pin)
        except Exception as e:
            FAIL.append('connect %s: %s' % (what, e))
            return False
        if not ok:
            FAIL.append('connect failed %s (%s -> %s)' % (what, out_pin.get_pin_name(), in_pin.get_pin_name()))
        return ok

    def feed(self, node, pins):
        for name, v in pins.items():
            ip = self.pin_in(node, name)
            if not ip.is_valid():
                continue
            if isinstance(v, unreal.BlueprintGraphPin):
                self.connect(v, ip, name)
            elif isinstance(v, tuple):
                self.connect(self.pin_out(v[0], v[1]), ip, name)
            elif isinstance(v, unreal.K2Node):
                self.connect(self.pin_out(v), ip, name)
            else:
                if not ip.set_pin_value(str(v)):
                    FAIL.append('set %s=%s failed on %s' % (name, v, node.get_node_title()))

    def fn(_g, path, **pins):
        node = _g.ed.add_call_function_node(path)
        if node is None:
            FAIL.append('missing function ' + path)
            raise RuntimeError('missing function ' + path)
        _g._pos(node, 0)
        _g.y += 40
        _g.feed(node, pins)
        return node

    def get(self, var, cls='', target=None):
        node = self.ed.add_get_member_variable_node(var, cls)
        if node is None:
            raise RuntimeError('no getter for %s %s' % (var, cls))
        self._pos(node, 0)
        self.y += 40
        if target is not None:
            self.feed(node, {'self': target})
        return node

    def setv(self, var, value, cls='', target=None):
        node = self.ed.add_set_member_variable_node(var, cls)
        if node is None:
            raise RuntimeError('no setter for ' + var)
        self._pos(node)
        self.y = 600
        ip = None
        for pin in node.list_input_pins():
            if str(pin.get_pin_name()) == var:
                ip = pin
        if ip is None:
            FAIL.append('setter pin %s missing' % var)
        else:
            if isinstance(value, (unreal.K2Node, tuple, unreal.BlueprintGraphPin)):
                src = value if isinstance(value, unreal.BlueprintGraphPin) else (
                    self.pin_out(value[0], value[1]) if isinstance(value, tuple) else self.pin_out(value))
                self.connect(src, ip, 'set ' + var)
            else:
                ip.set_pin_value(str(value))
        if target is not None:
            self.feed(node, {'self': target})
        return node

    def branch(self, cond):
        node = self.ed.add_branch_node()
        self._pos(node)
        self.y = 600
        src = cond if isinstance(cond, unreal.BlueprintGraphPin) else self.pin_out(cond)
        self.connect(src, node.find_condition_pin(), 'branch')
        return node

    def by_menu(self, candidates, keywords, context=None):
        loc = unreal.Vector2D(self.x, self.y)
        for c in candidates:
            try:
                n = self.ed.create_node_from_name(c, loc, context or [])
                if n:
                    return n
            except Exception:
                pass
        names = list(self.ed.list_available_nodes(context or []))
        hits = [n for n in names if all(k.lower() in n.lower() for k in keywords)]
        hits.sort(key=len)
        say('   menu search', keywords, '->', hits[:6])
        for h in hits:
            try:
                n = self.ed.create_node_from_name(h, loc, context or [])
                if n:
                    return n
            except Exception:
                pass
        raise RuntimeError('menu node not found: %s' % (keywords,))

    @staticmethod
    def then(node):
        return node.find_then_pin()

    def chain(self, out_exec, node):
        self.connect(out_exec, node.find_execute_pin(), 'exec->' + str(node.get_node_title()))
        return node


def is_impure(node):
    try:
        return node.find_execute_pin().is_valid()
    except Exception:
        return False


def ensure_var(bp, g, name, type_name, default, editable=False):
    if name in list(BEL.list_member_variable_names(bp, True)):
        return
    pt = BEL.get_basic_type_by_name(type_name) if isinstance(type_name, str) else type_name
    ok = g.ed.add_member_variable(name, pt, str(default))
    BEL.set_blueprint_variable_category(bp, name, unreal.Text('MJ'))
    if editable:
        BEL.set_blueprint_variable_instance_editable(bp, name, True)
    say('  + var', name, ok)


def hook_event(bp, g, event_name, pos):
    """Return an exec output pin that fires on the event, keeping existing logic.
    An old 'Execute Python Script' successor is disconnected (node kept)."""
    ev = BEL.add_event_override(bp, event_name, unreal.IntPoint(pos[0], pos[1]))
    if ev is None:
        raise RuntimeError('cannot add event ' + event_name)
    then = ev.find_then_pin()
    linked = list(then.list_connected_pins())
    keep = []
    for lp in linked:
        owner = lp.get_owning_node()
        if owner and 'ExecutePythonScript' in owner.get_class().get_name():
            then.break_single_pin_link(lp)
            say('  disconnected old python hook from', event_name, '(node kept)')
        else:
            keep.append(lp)
    if not keep:
        return then
    seq = g.by_menu(['Utilities|FlowControl|Sequence'], ['FlowControl', 'Sequence'])
    then.break_pin_links()
    g.connect(then, seq.find_execute_pin(), 'seq in')
    for lp in keep:
        g.connect(seq.find_output_pin_by_index(0), lp, 'seq old')
    say('  inserted Sequence after', event_name, 'to keep existing logic')
    return seq.find_output_pin_by_index(1)


def leaf_component_var(bp):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    comps = []
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d = lib.get_data(h)
        obj = lib.get_object(d)
        if isinstance(obj, unreal.SceneComponent):
            comps.append((str(lib.get_variable_name(d)), obj))
    say('  components:', [(n, o.get_class().get_name()) for n, o in comps])
    for keys in (('hinge', 'pivot'), ('leaf', 'panel', 'kanat')):
        for n, o in comps:
            if any(k in n.lower() for k in keys):
                return n
    for n, o in comps:
        if isinstance(o, unreal.StaticMeshComponent) and 'frame' not in n.lower() and 'trigger' not in n.lower():
            return n
    return None


def near_and_facing(g, target_loc_pin, dist, facing):
    pc_mgr = g.fn(GPS + 'GetPlayerCameraManager', PlayerIndex='0')
    cam_loc = g.fn('/Script/Engine.PlayerCameraManager.GetCameraLocation', self=pc_mgr)
    cam_rot = g.fn('/Script/Engine.PlayerCameraManager.GetCameraRotation', self=pc_mgr)
    fwd = g.fn(KML + 'GetForwardVector', InRot=cam_rot)
    diff = g.fn(KML + 'Subtract_VectorVector', A=target_loc_pin, B=cam_loc)
    nrm = g.fn(KML + 'Normal', A=diff)
    dot = g.fn(KML + 'Dot_VectorVector', A=fwd, B=nrm)
    look = g.fn(KML + 'Greater_DoubleDouble', A=dot, B=str(facing))
    pawn = g.fn(GPS + 'GetPlayerPawn', PlayerIndex='0')
    ploc = g.fn(ACT + 'K2_GetActorLocation', self=pawn)
    d = g.fn(KML + 'Vector_Distance', V1=ploc, V2=target_loc_pin)
    close = g.fn(KML + 'Less_DoubleDouble', A=d, B=str(dist))
    pc = g.fn(GPS + 'GetPlayerController', PlayerIndex='0')
    pressed = g.fn('/Script/Engine.PlayerController.WasInputKeyJustPressed', self=pc, Key='E')
    a1 = g.fn(KML + 'BooleanAND', A=look, B=close)
    a2 = g.fn(KML + 'BooleanAND', A=a1, B=pressed)
    return a2, pawn


def key_tag_name(g, key_getter):
    """Name 'HasKey:<KeyID>' from a KeyID getter (Name or String)."""
    out = g.pin_out(key_getter)
    tdisp = str(out.get_pin_type_display_string()).lower()
    if 'name' in tdisp:
        s = g.fn(KSTR + 'Conv_NameToString', InName=out)
        s_pin = g.pin_out(s)
    else:
        s_pin = out
    cat = g.fn(KSTR + 'Concat_StrStr', A='HasKey:', B=s_pin)
    return g.fn(KSTR + 'Conv_StringToName', InString=cat)


def print_msg(g, text, r, gr, b):
    return g.fn(KSL + 'PrintString', InString=text, Duration='2.0',
                TextColor='(R=%s,G=%s,B=%s,A=1.000000)' % (r, gr, b))


def pkg_dirty(path):
    names = [x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    return path in names


def link_proxies():
    """Editor data only: point each door/key at its Proxy_<label> mesh actor and make that mesh
    Movable so it can swing at runtime. Nothing is moved."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = eas.get_all_level_actors()
    by_label = dict((a.get_actor_label(), a) for a in acts)
    n = 0
    miss = []
    for a in acts:
        cn = a.get_class().get_name()
        if not (cn.startswith('BP_Door') or cn.startswith('BP_Key')):
            continue
        prox = by_label.get('Proxy_' + a.get_actor_label())
        if prox is None:
            miss.append(a.get_actor_label())
            continue
        a.set_editor_property('MJ_Proxy', prox)
        rc = prox.get_editor_property('root_component')
        if rc and cn.startswith('BP_Door'):
            rc.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
        n += 1
    say('linked proxies', n, 'missing', miss)
    return n


def backup(path):
    """Copy the on-disk .uasset (pristine, saved version) to <Project>/Saved/MJBackups/<time>/."""
    import os, shutil
    rel = path.replace('/Game/', '', 1) + '.uasset'
    src = os.path.join(unreal.Paths.project_content_dir(), rel)
    dst_dir = os.path.join(unreal.Paths.project_saved_dir(), 'MJBackups', time.strftime('%Y%m%d_%H%M%S'))
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(rel))
    shutil.copy2(src, dst)
    say('backup', os.path.abspath(dst))
    return os.path.isfile(dst)


def finish(bp, path):
    ok = BEL.compile_blueprint(bp)
    errs = []
    for gr in BEL.list_graphs(bp):
        for n in BGE.get_graph_editor(gr).list_nodes_with_errors():
            errs.append('%s: %s' % (n.get_node_title(), n.get_editor_property('error_msg')))
    say('compile', path, ok, 'errors:', errs[:10])
    if FAIL:
        say('wiring problems:', FAIL[:25])
    if ok and not errs and not FAIL and not DRY_RUN:
        unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        say('SAVED', path)
        return True
    pkg = bp.get_outermost()
    unreal.EditorLoadingAndSavingUtils.reload_packages([pkg])
    say('DISCARDED (reloaded from disk)', path)
    return False

def fresh_component_bp(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path) or unreal.find_object(None, path + '.' + path.split('/')[-1]):
        c = unreal.load_object(None, path + '.' + path.split('/')[-1])
    else:
        c = BEL.create_blueprint_asset_with_parent(path, unreal.ActorComponent)
    eg = BEL.find_event_graph(c)
    ed = BGE.get_graph_editor(eg)
    old = [n for n in ed.list_all_nodes()]
    if old:
        ed.remove_nodes(old)   # our own generated component graph only
    return c, G(c, eg)


def ensure_proxy_var(bp):
    if 'MJ_Proxy' not in list(BEL.list_member_variable_names(bp, True)):
        ok = BEL.add_member_variable(bp, 'MJ_Proxy', BEL.get_object_reference_type(unreal.Actor))
        BEL.set_blueprint_variable_instance_editable(bp, 'MJ_Proxy', True)
        BEL.set_blueprint_variable_category(bp, 'MJ_Proxy', unreal.Text('MJ'))
        say('  + BP var MJ_Proxy', ok)


def ensure_component(bp, comp_bp):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    gc = comp_bp.generated_class()
    for h in handles:
        o = lib.get_associated_object(lib.get_data(h)) if hasattr(lib, 'get_associated_object') else lib.get_object(lib.get_data(h))
        if o is not None and o.get_class() == gc:
            say('  component already on', bp.get_name())
            return True
    params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=gc, blueprint_context=bp)
    res = sub.add_new_subobject(params)
    say('  add component ->', res)
    return True


def owner_cast(g, cast_name, var):
    """BeginPlay: cast GetOwner to the BP and store it in var. Returns exec-out pin of the setter."""
    own = g.fn(ACT.replace('Actor.', 'ActorComponent.') + 'GetOwner')
    cast = g.by_menu([cast_name], [cast_name.split('|')[-1]])
    g.connect(g.pin_out(own), cast.find_input_pin('Object'), 'owner->cast')
    return cast

