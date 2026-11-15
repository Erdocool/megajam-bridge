# MegaJam DirectorsCut (UE 5.8): author NATIVE Blueprint logic for BP_Door / BP_Key with the
# UE 5.8 BlueprintGraphEditor Python API (no C++, no compile toolchain, works in packaged builds).
#
#  - E near a door (distance + looking at it) toggles it; the leaf swings on its hinge (FInterpTo on Tick).
#  - bLocked doors open only if the player pawn has the tag "HasKey:<KeyID>" (same scheme as the old
#    Python hook); then bLocked=false. Otherwise PrintString "Kilitli".
#  - E near a BP_Key adds "HasKey:<KeyID>" to the pawn tags, PrintString "Anahtar alindi", hides the key.
#  - The old Tick -> "Execute Python Script" link is only disconnected (node kept, nothing deleted).
#  - A pristine backup copy of each Blueprint is saved first (BP_Door_MJBackup_<time>).
#  - If compile fails, the in-memory Blueprint is reloaded from disk (changes discarded), nothing saved.
#  - No level actor is moved or edited; L_Apartment untouched; no project/engine settings changed.
#
# Run only after confirmation:  !pyurl <raw url of this file>   (or !py + contents)
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
DRY_RUN = True              # True = build + compile, then discard (reload) without saving

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

    def fn(self, path, **pins):
        node = self.ed.add_call_function_node(path)
        if node is None:
            FAIL.append('missing function ' + path)
            raise RuntimeError('missing function ' + path)
        self._pos(node, 0)
        self.y += 40
        self.feed(node, pins)
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

    def setv(self, var, value):
        node = self.ed.add_set_member_variable_node(var, '')
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
    seq = g.by_menu(['Utilities|Flow Control|Sequence', 'Utilities|FlowControl|Sequence'], ['Sequence'])
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


def backup(path):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    dst = '%s_MJBackup_%s' % (path, stamp)
    ok = unreal.EditorAssetLibrary.duplicate_asset(path, dst)
    if ok:
        unreal.EditorAssetLibrary.save_asset(dst, only_if_is_dirty=False)
    say('backup', dst, bool(ok))
    return bool(ok)


def finish(bp, path):
    ok = BEL.compile_blueprint(bp)
    errs = []
    for gr in BEL.list_graphs(bp):
        for n in BGE.get_graph_editor(gr).list_nodes_with_errors():
            errs.append('%s: %s' % (n.get_node_title(), n.get_editor_property('error_msg')))
    say('compile', path, ok, 'errors:', errs[:10])
    if ok and not errs and not DRY_RUN:
        unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        say('SAVED', path)
        return True
    pkg = bp.get_outermost()
    unreal.EditorLoadingAndSavingUtils.reload_packages([pkg])
    say('DISCARDED (reloaded from disk)', path)
    return False


def build_door():
    say('\n== BP_Door')
    bp = unreal.EditorAssetLibrary.load_asset(BP_DOOR)
    eg = BEL.find_event_graph(bp)
    g = G(bp, eg)
    own = list(BEL.list_member_variable_names(bp, True))
    for need in ('bLocked', 'KeyID', 'bOpen', 'OpenAngle'):
        if need not in own:
            raise RuntimeError('BP_Door missing variable %s (inspect first)' % need)
    scene_ref = BEL.get_object_reference_type(unreal.SceneComponent)
    ensure_var(bp, g, 'MJ_Leaf', scene_ref, '')
    ensure_var(bp, g, 'MJ_BaseYaw', 'real', 0)
    ensure_var(bp, g, 'MJ_CurrentYaw', 'real', 0)

    mode = LEAF_MODE
    comp = None
    if mode.startswith('component:'):
        comp = mode.split(':', 1)[1]
    elif mode == 'auto':
        comp = leaf_component_var(bp)
    say('  leaf source:', ('component ' + comp) if comp else 'first attached actor root')

    # ---- BeginPlay: cache leaf + base yaw
    g.x, g.y = 400, 200
    cur = hook_event(bp, g, 'ReceiveBeginPlay', (0, 200))
    if comp:
        leaf_src = g.get(comp)
    else:
        att = g.fn(ACT + 'GetAttachedActors')
        if is_impure(att):
            g.chain(cur, att)
            cur = g.then(att)
        arr_get = g.by_menu(['Utilities|Array|Get (a copy)', 'Utilities|Array|Get'], ['Array', 'Get'])
        g.connect(att.find_output_pin('OutActors'), arr_get.find_input_pin_by_index(0), 'array get')
        idx = arr_get.find_input_pin_by_index(1)
        if idx.is_valid():
            idx.set_pin_value('0')
        leaf_src = g.fn(ACT + 'K2_GetRootComponent', self=arr_get.find_output_pin_by_index(0))
    s1 = g.chain(cur, g.setv('MJ_Leaf', leaf_src))
    leaf = g.get('MJ_Leaf')
    rr = g.get('RelativeRotation', '/Script/Engine.SceneComponent', target=g.pin_out(leaf))
    brk = g.fn(KML + 'BreakRotator', InRot=rr)
    start = g.fn(KML + 'SelectFloat', A=g.get('OpenAngle'), B='0', bPickA=g.get('bOpen'))
    base = g.fn(KML + 'Subtract_DoubleDouble', A=(brk, 'Yaw'), B=start)
    s2 = g.chain(g.then(s1), g.setv('MJ_BaseYaw', base))
    g.chain(g.then(s2), g.setv('MJ_CurrentYaw', start))

    # ---- Tick: swing + interact
    g.x, g.y = 400, 900
    tick_out = hook_event(bp, g, 'ReceiveTick', (0, 900))
    tick_node = g.ed.find_event_node('ReceiveTick')
    dt = tick_node.find_output_pin('DeltaSeconds')
    tgt = g.fn(KML + 'SelectFloat', A=g.get('OpenAngle'), B='0', bPickA=g.get('bOpen'))
    interp = g.fn(KML + 'FInterpTo', Current=g.get('MJ_CurrentYaw'), Target=tgt, DeltaTime=dt, InterpSpeed=str(SWING_SPEED))
    s3 = g.chain(tick_out, g.setv('MJ_CurrentYaw', interp))
    leaf2 = g.get('MJ_Leaf')
    valid = g.fn(KSL + 'IsValid', Object=leaf2)
    b_valid = g.chain(g.then(s3), g.branch(valid))
    rr2 = g.get('RelativeRotation', '/Script/Engine.SceneComponent', target=g.pin_out(leaf2))
    brk2 = g.fn(KML + 'BreakRotator', InRot=rr2)
    yaw = g.fn(KML + 'Add_DoubleDouble', A=g.get('MJ_BaseYaw'), B=g.get('MJ_CurrentYaw'))
    mk = g.fn(KML + 'MakeRotator', Roll=(brk2, 'Roll'), Pitch=(brk2, 'Pitch'), Yaw=yaw)
    setrot = g.fn('/Script/Engine.SceneComponent.K2_SetRelativeRotation', self=g.pin_out(leaf2), NewRotation=mk)
    g.chain(g.then(b_valid), setrot)

    bounds = g.fn(KSL + 'GetComponentBounds', Component=g.pin_out(leaf2))
    want, pawn = near_and_facing(g, bounds.find_output_pin('Origin'), DOOR_DIST, DOOR_FACING)
    b_int = g.chain(g.then(setrot), g.branch(want))
    b_lock = g.chain(g.then(b_int), g.branch(g.get('bLocked')))
    tag = key_tag_name(g, g.get('KeyID'))
    has = g.fn(ACT + 'ActorHasTag', self=pawn, Tag=tag)
    b_key = g.chain(g.then(b_lock), g.branch(has))
    # locked + no key
    g.chain(b_key.find_else_pin(), print_msg(g, 'Kilitli', 1, 0.25, 0.2))
    # locked + key -> unlock -> message -> toggle
    unl = g.chain(g.then(b_key), g.setv('bLocked', 'false'))
    msg = g.chain(g.then(unl), print_msg(g, 'Kilit acildi', 0.4, 1, 0.4))
    notb = g.fn(KML + 'Not_PreBool', A=g.get('bOpen'))
    tog = g.setv('bOpen', notb)
    g.chain(g.then(msg), tog)
    g.chain(b_lock.find_else_pin(), tog)          # unlocked -> toggle
    return finish(bp, BP_DOOR)


def build_key():
    say('\n== BP_Key')
    bp = unreal.EditorAssetLibrary.load_asset(BP_KEY)
    eg = BEL.find_event_graph(bp)
    g = G(bp, eg)
    if 'KeyID' not in list(BEL.list_member_variable_names(bp, True)):
        raise RuntimeError('BP_Key missing KeyID (inspect first)')
    ensure_var(bp, g, 'MJ_Taken', 'bool', 'false')
    g.x, g.y = 400, 900
    tick_out = hook_event(bp, g, 'ReceiveTick', (0, 900))
    loc = g.fn(ACT + 'K2_GetActorLocation')
    want, pawn = near_and_facing(g, g.pin_out(loc), KEY_DIST, KEY_FACING)
    nt = g.fn(KML + 'Not_PreBool', A=g.get('MJ_Taken'))
    cond = g.fn(KML + 'BooleanAND', A=want, B=nt)
    b = g.chain(tick_out, g.branch(cond))
    tags = g.get('Tags', '/Script/Engine.Actor', target=g.pin_out(pawn))
    add = g.by_menu(['Utilities|Array|Add'], ['Array', 'Add'])
    g.connect(g.pin_out(tags), add.find_input_pin_by_index(1) if not add.find_input_pin('TargetArray').is_valid() else add.find_input_pin('TargetArray'), 'tags->add')
    tag = key_tag_name(g, g.get('KeyID'))
    item = add.find_input_pin('NewItem')
    g.connect(g.pin_out(tag), item, 'tag->add')
    g.chain(g.then(b), add)
    s = g.chain(g.then(add), g.setv('MJ_Taken', 'true'))
    m = g.chain(g.then(s), print_msg(g, 'Anahtar alindi', 1, 0.85, 0.2))
    h = g.chain(g.then(m), g.fn(ACT + 'SetActorHiddenInGame', bNewHidden='true'))
    g.chain(g.then(h), g.fn(ACT + 'SetActorEnableCollision', bNewActorEnableCollision='false'))
    return finish(bp, BP_KEY)


if not hasattr(unreal, 'BlueprintGraphEditor'):
    raise RuntimeError('BlueprintGraphEditor API not available in this editor - nothing changed.')
results = {}
for path, fn in ((BP_DOOR, build_door), (BP_KEY, build_key)):
    FAIL[:] = []
    if not DRY_RUN and not backup(path):
        say('backup failed, skipping', path)
        results[path] = False
        continue
    try:
        results[path] = fn()
    except Exception as e:
        say('ERROR', path, e)
        try:
            unreal.EditorLoadingAndSavingUtils.reload_packages([unreal.EditorAssetLibrary.load_asset(path).get_outermost()])
            say('DISCARDED (reloaded from disk)', path)
        except Exception as e2:
            say('reload failed', e2)
        results[path] = False
    if FAIL:
        say('wiring problems:', FAIL[:25])
say('\nRESULT', results, '| DRY_RUN', DRY_RUN)
