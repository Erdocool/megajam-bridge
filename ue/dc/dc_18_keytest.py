import unreal, ctypes, math, time
# Automated key-chain test in PIE (nothing is saved): for the 8 keys in order -> each locked door refuses E with no/wrong keys,
# key pickup via E adds HasKey tag and +Bonus once, then the door unlocks/opens with E, the leaf swings ~90 deg, the open leaf
# overlaps nothing, and a player-sized capsule passes through the gap. Unlocked doors are opened too. E is a synthetic key press,
# sent only while the Unreal window is in front. Results -> Saved/mj_keytest.txt
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
GS, SL, ML = unreal.GameplayStatics, unreal.SystemLibrary, unreal.MathLibrary
V, R = unreal.Vector, unreal.Rotator
OUT = unreal.Paths.project_saved_dir() + 'mj_keytest.txt'
KEYS = ['Key_Building_Front', 'Key_Doorman', 'Key_Boiler', 'Key_Manager', 'Key_Flat1', 'Key_Flat2', 'Key_Flat3', 'HiddenRoom']
STRUCT = ('Wall', 'Floor', 'Ceil', 'Div', 'CorBack', 'LeftEnd', 'Over', 'Frame', 'Jamb', 'Stair', 'Landing', 'Rail', 'Roof', 'Lintel')
u32 = ctypes.windll.user32
LOG = []
def say(*a): LOG.append(' '.join(str(x) for x in a)); open(OUT, 'w').write('\n'.join(LOG) + '\n')
def fg():
    b = ctypes.create_unicode_buffer(256); u32.GetWindowTextW(u32.GetForegroundWindow(), b, 256); return b.value
def act_of(hr):
    if hr is None: return None
    try:
        for x in hr.to_tuple():
            if isinstance(x, unreal.Actor): return x
            if isinstance(x, unreal.PrimitiveComponent): return x.get_owner()
    except Exception: pass
    return 'hit'
def lab(a): return a if isinstance(a, str) else a.get_actor_label()
def run():
    while ues.get_game_world() is None or GS.get_player_pawn(ues.get_game_world(), 0) is None: yield 0.5
    yield 2.0
    w = ues.get_game_world(); pawn = GS.get_player_pawn(w, 0); pc = GS.get_player_controller(w, 0); hud = pc.get_hud()
    def HV(n):
        try: return hud.get_editor_property(n)
        except Exception: return None
    dc = unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Door.BP_Door_C'); kc = unreal.load_class(None, '/Game/DirectorsCut/Blueprints/BP_Key.BP_Key_C')
    doors = list(GS.get_all_actors_of_class(w, dc)); keys = list(GS.get_all_actors_of_class(w, kc))
    SL.execute_console_command(w, 'set BP_MJHUD_C bTimer true'); SL.execute_console_command(w, 'set BP_MJHUD_C TimeLeft 5000'); yield 0.3
    bonus = HV('Bonus'); say('INFO timer', HV('bTimer'), HV('TimeLeft'))
    say('INFO doors', len(doors), 'keys', len(keys), 'bonus', bonus, 'fg', fg()[:40])
    D = {}
    for d in doors:
        px = d.get_editor_property('MJ_Proxy')
        D[d] = dict(px=px, yaw=px.get_actor_rotation().yaw if px else 0, n=px.get_actor_forward_vector() if px else V(1, 0, 0),
                    fz=px.get_actor_location().z if px else d.get_actor_location().z, kid=str(d.get_editor_property('KeyID')), locked=bool(d.get_editor_property('bLocked')))
    def inv():
        try: return HV('TimeLeft') + HV('T')
        except Exception: return 0
    BON = {}
    def tags(): return set(str(t) for t in pawn.tags if str(t).startswith('HasKey:'))
    def press():
        t0, i0 = tags(), inv()
        t = fg()
        if 'Unreal' not in t and 'DirectorsCut' not in t: raise RuntimeError('ABORT foreground is not Unreal: ' + t[:30])
        u32.keybd_event(0x45, 0x12, 0, 0); yield 0.06; u32.keybd_event(0x45, 0x12, 2, 0); yield 0.35
        new = tags() - t0
        if new: BON[','.join(sorted(x[7:] for x in new))] = round(inv() - i0)
    def goto(loc, look):
        pawn.set_actor_location(loc, False, True)
        mc = pawn.get_movement_component()
        if mc: mc.stop_movement_immediately()
        yield 0.2
        for _ in range(2):
            cam = pc.player_camera_manager.get_camera_location(); pc.set_control_rotation(ML.find_look_at_rotation(cam, look)); yield 0.1
    def try_door(d, want_open):
        i = D[d]; c = d.get_actor_location(); n = i['n']
        for side in ((1, -1) if want_open else (1,)):
            spot = V(c.x + n.x * side * 110, c.y + n.y * side * 110, i['fz'] + 100)
            yield from goto(spot, d.get_actor_location())
            pl = pawn.get_actor_location(); cam = pc.player_camera_manager
            dot = cam.get_actor_forward_vector().dot((d.get_actor_location() - cam.get_camera_location()).normal()) if hasattr(cam, 'get_actor_forward_vector') else 0
            i['diag'] = i.get('diag', '') + 's%d:d%d,dot%.2f ' % (side, (pl - d.get_actor_location()).length(), dot)
            yield from press()
            if d.get_editor_property('bOpen'): break
        return
    def check_open(d):
        i = D[d]; px = i['px']; c = d.get_actor_location(); n = i['n']; res = []
        dy = (px.get_actor_rotation().yaw - i['yaw'] + 540) % 360 - 180
        res.append('swing%d' % round(dy) if abs(abs(dy) - 90) > 6 else 'swingOK')
        o, e = px.get_actor_bounds(False)
        ov = SL.box_overlap_actors(w, o, V(max(e.x - 3, 0.5), max(e.y - 3, 0.5), max(e.z - 3, 0.5)), [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2], None, [px, d, pawn])
        if isinstance(ov, tuple): ov = ov[-1]
        real = []
        for a in (ov or []):
            ao, ae = a.get_actor_bounds(False)
            dx = min(o.x + e.x, ao.x + ae.x) - max(o.x - e.x, ao.x - ae.x); dyy = min(o.y + e.y, ao.y + ae.y) - max(o.y - e.y, ao.y - ae.y)
            if min(dx, dyy) > 8: real.append('%s(%d)' % (lab(a), min(dx, dyy)))
        ov = real
        res.append('leafHits:' + '/'.join(ov[:3]) if ov else 'leafOK')
        z = i['fz'] + 78
        hr = SL.capsule_trace_single(w, V(c.x - n.x * 60, c.y - n.y * 60, z), V(c.x + n.x * 60, c.y + n.y * 60, z), 28, 70, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn, d, px], unreal.DrawDebugTrace.NONE, True)
        h = act_of(hr); res.append('passBlocked:' + lab(h) if h else 'passOK')
        return res
    # sanity: E must work -> open one unlocked door first
    ul = [d for d in doors if not D[d]['locked']]
    if ul:
        yield from try_door(ul[0], True)
        if not ul[0].get_editor_property('bOpen'): say('ABORT E press not registered (click into the Play window?)'); return
        say('SANITY E ok on', ul[0].get_actor_label())
    done = set(ul[:1])
    nk_ok, nk_bad = [], []
    for d in doors:
        if not D[d]['locked']: continue
        yield from try_door(d, False)
        (nk_ok if d.get_editor_property('bLocked') and not d.get_editor_property('bOpen') else nk_bad).append(d.get_actor_label()[5:])
    say('NOKEY prepass (no key held) stayed locked:', len(nk_ok), 'opened:', nk_bad, 'tags', sorted(tags()))
    for ki, kid in enumerate(KEYS):
        kd = [d for d in doors if D[d]['locked'] and D[d]['kid'] == kid]; ka = [k for k in keys if str(k.get_editor_property('KeyID')) == kid]
        r = ['K%d %s doors%d keys%d' % (ki, kid, len(kd), len(ka))]
        for d in kd:
            yield from try_door(d, False)
            ok_ = d.get_editor_property('bLocked') and not d.get_editor_property('bOpen')
            r.append('noKeyLocked' if ok_ else 'OPENED_WITHOUT_KEY:%s locked=%s tags=%s' % (d.get_actor_label(), d.get_editor_property('bLocked'), sorted(x[7:] for x in tags())))
        if ka:
            k = ka[0]; kl = k.get_actor_location(); kp = k.get_editor_property('MJ_Proxy'); i0 = inv(); got = False
            if pawn.actor_has_tag('HasKey:' + kid): r.append('alreadyHeld')
            for dx, dy in ((90, 0), (-90, 0), (0, 90), (0, -90), (60, 60), (-60, -60)):
                spot = V(kl.x + dx, kl.y + dy, kl.z + 30)
                if SL.line_trace_single(w, V(kl.x, kl.y, kl.z + 30), spot, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [k, kp, pawn] if kp else [k, pawn], unreal.DrawDebugTrace.NONE, True): continue
                yield from goto(spot, kl); yield from press(); yield 0.3
                if pawn.actor_has_tag('HasKey:' + kid): got = True; break
            gain = inv() - i0
            r.append('pickupOK' if got else 'PICKUP_FAIL'); r.append('bonus+%d' % round(gain))
            yield 1.0; r.append('once' if abs(inv() - i0 - gain) < 1.5 else 'BONUS_REPEATS')
        for d in kd:
            yield from try_door(d, True); done.add(d)
            if not d.get_editor_property('bOpen'): r.append('NOT_OPEN:' + d.get_actor_label() + ' ' + D[d].get('diag', '')); continue
            yield 1.8; r.append(d.get_actor_label().replace('Door_', '') + ':' + ','.join(check_open(d)))
        say(' | '.join(r))
    bad = []; okd = []
    for d in doors:
        if d in done: continue
        if D[d]['locked']:
            yield from try_door(d, False)
            bad.append('STUCK_OK:' + d.get_actor_label()[5:] if not d.get_editor_property('bOpen') else 'OPENED_STUCK:' + d.get_actor_label()); continue
        yield from try_door(d, True)
        if not d.get_editor_property('bOpen'): bad.append('NOT_OPEN:' + d.get_actor_label() + ' ' + D[d].get('diag', '')); continue
        yield 1.8; c = check_open(d)
        if c == ['swingOK', 'leafOK', 'passOK']: okd.append(d.get_actor_label()[5:])
        else: bad.append(d.get_actor_label() + ':' + ','.join(c))
    say('UNLOCKED', len([d for d in doors if not D[d]['locked']]), 'ok', len(okd), 'other', len(bad)); [say('U', b) for b in bad]
    say('BONUS per press', BON)
    # walking test: real movement input up the new stairs, into every flat entry
    O = (13376, 6430, 15)
    def walk(x, y, tmax=6.0):
        t0 = time.time()
        while time.time() - t0 < tmax:
            p = pawn.get_actor_location(); dx, dy = x + O[0] - p.x, y + O[1] - p.y
            if (dx * dx + dy * dy) ** 0.5 < 35: return True
            pawn.add_movement_input(V(dx, dy, 0).normal(), 1.0); yield 0.0
        return False
    pawn.set_actor_location(V(420 + O[0], 1250 + O[1], 110 + O[2]), False, True); yield 0.5
    wl = []
    for k in range(4):
        okw = True
        route = (((520, 1230),) if k == 0 else ()) + ((575, 1175), (930, 1175), (930, 1335), (575, 1335), (560, 1175))
        if k == 3: route = ((480, 1175), (160, 1175), (160, 1335), (520, 1335), (560, 1200))
        for (x, y) in route:
            r_ = yield from walk(x, y)
            if not r_: wl.append('STUCK f%d->(%d,%d) at %s' % (k, x, y, [round(v) for v in (pawn.get_actor_location().x - O[0], pawn.get_actor_location().y - O[1], pawn.get_actor_location().z - O[2])])); okw = False; break
        if not okw: break
        z = pawn.get_actor_location().z - O[2]; fl = k + 1
        r_ = yield from walk(560, 1040)
        r2 = yield from walk(560, 1175)
        wl.append('F%d z%d entry%s' % (fl, z, 'OK' if r_ and r2 else 'BLOCKED'))
    if len(wl) == 4 and 'STUCK' not in wl[-1]:
        a1 = yield from walk(700, 1250); a2 = yield from walk(870, 1250)
        wl.append('HiddenRoom walk-in %s' % ('OK' if a1 and a2 else 'BLOCKED at %s' % [round(v) for v in (pawn.get_actor_location().x - O[0], pawn.get_actor_location().y - O[1])]))
    say('WALK', ' | '.join(wl))
    say('KEYTAGS', [k for k in KEYS if not pawn.actor_has_tag('HasKey:' + k)], 'bK', [HV('bK%d' % i) for i in range(8)])
G = run(); WAKE = [0.0]; T0 = time.time(); H = [None]
def tick(dt):
    if time.time() < WAKE[0]: return
    try:
        if time.time() - T0 > 600: raise RuntimeError('ABORT timeout')
        WAKE[0] = time.time() + next(G)
    except StopIteration:
        say('DONE'); unreal.unregister_slate_post_tick_callback(H[0]); les.editor_request_end_play()
    except Exception as e:
        say('ERR', str(e)[:200]); unreal.unregister_slate_post_tick_callback(H[0]); les.editor_request_end_play()
assert len(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) == 0
open(OUT, 'w').write('START\n')
if not les.is_in_play_in_editor(): les.editor_request_begin_play()
H[0] = unreal.register_slate_post_tick_callback(tick)
print('KEYTEST started')
