
# BP_MJHUD: day/timer/desk/envelope/game-over/ending logic drawn on the HUD canvas (no UMG). BP_MJGameMode (child of BP_FirstPersonGameMode) uses it.
HUDP = '/Game/DirectorsCut/Blueprints/BP_MJHUD'
GMP = '/Game/DirectorsCut/Blueprints/BP_MJGameMode'
HUDF = '/Script/Engine.HUD.'
if unreal.EditorAssetLibrary.does_asset_exist(HUDP):
    h = unreal.load_asset(HUDP)
else:
    h = BEL.create_blueprint_asset_with_parent(HUDP, unreal.HUD)
eg = BEL.find_event_graph(h); g = G(h, eg)
old = list(g.ed.list_all_nodes())
if old: g.ed.remove_nodes(old)
V = [('StartTime', 'real', 180, True), ('Bonus', 'real', 60, True), ('TimeLeft', 'real', 180, False), ('T', 'real', 0, False), ('MsgT', 'real', 0, False),
     ('Msg', 'string', '', False), ('bTimer', 'bool', 'false', False), ('bOver', 'bool', 'false', False), ('bEnd', 'bool', 'false', False), ('bDesk', 'bool', 'false', False),
     ('bInit', 'bool', 'false', False), ('bLookDesk', 'bool', 'false', False), ('bLookEnv', 'bool', 'false', False), ('LastTags', 'int', 0, False),
     ('Day', 'int', 1, False), ('Deaths', 'int', 0, False)]
for n, t, d, e in V: ensure_var(h, g, n, t, d, e)
AR = BEL.get_object_reference_type(unreal.Actor)
for n in ('DeskRef', 'EnvRef', 'TimerRef', 'DayRef'): ensure_var(h, g, n, AR, '')
def link(outs, node):
    for o in outs: g.connect(o, node.find_execute_pin(), 'x')
    return [node.find_then_pin()]
def when(outs, cond, nodes):
    br = g.ed.add_branch_node(); g._pos(br); g.y = 600
    g.connect(cond if isinstance(cond, unreal.BlueprintGraphPin) else g.pin_out(cond), br.find_condition_pin(), 'cond')
    outs = link(outs, br); t = [br.find_then_pin()]
    for n in nodes: t = link(t, n)
    return t + [br.find_else_pin()]
def steps(outs, nodes):
    for n in nodes: outs = link(outs, n)
    return outs
AND = lambda a, b: g.fn(KML + 'BooleanAND', A=a, B=b)
NOT = lambda a: g.fn(KML + 'Not_PreBool', A=a)
GET = lambda v: g.get(v)
# ---- BeginPlay: options (day, deaths), cache tagged actors
g.x, g.y = 400, 0
bp_ev = BEL.add_event_override(h, 'ReceiveBeginPlay', unreal.IntPoint(0, 0))
gm = g.fn(GPS + 'GetGameMode')
opts = g.get('OptionsString', '/Script/Engine.GameModeBase', target=g.pin_out(gm))
outs = [bp_ev.find_then_pin()]
outs = steps(outs, [g.setv('Day', g.fn(GPS + 'GetIntOption', Options=opts, Key='day', DefaultValue='1')),
                    g.setv('Deaths', g.fn(GPS + 'GetIntOption', Options=g.get('OptionsString', '/Script/Engine.GameModeBase', target=g.pin_out(g.fn(GPS + 'GetGameMode'))), Key='deaths', DefaultValue='0'))])
def cache(outs, tagpin, var):
    fa = g.fn(GPS + 'GetAllActorsWithTag', Tag=tagpin)
    arr = g.by_menu(['Utilities|Array|Get (a copy)', 'Utilities|Array|Get'], ['Array', 'Get'])
    ins = [str(p.get_pin_name()) for p in arr.list_input_pins()]
    fo = [str(p.get_pin_name()) for p in fa.list_output_pins()]
    g.connect(fa.find_output_pin([n for n in fo if 'ctor' in n][0]), arr.find_input_pin([n for n in ins if 'rray' in n][0]), 'arr')
    outs = link(outs, fa)
    return link(outs, g.setv(var, arr.find_output_pin(str(arr.list_output_pins()[0].get_pin_name()))))
outs = cache(outs, 'MJ_EditDesk', 'DeskRef'); outs = cache(outs, 'MJ_BlueEnvelope', 'EnvRef'); outs = cache(outs, 'MJ_TimerStart', 'TimerRef')
dtag = g.fn(KSTR + 'Conv_StringToName', InString=g.fn(KSTR + 'Concat_StrStr', A='MJ_DayStart_', B=g.fn(KSTR + 'Conv_IntToString', InInt=GET('Day'))))
outs = cache(outs, g.pin_out(dtag), 'DayRef')
outs = steps(outs, [g.setv('TimeLeft', GET('StartTime')), g.setv('Msg', 'Kart: "Zaman senin icin isliyor, hizli olman gerekiyor."'), g.setv('MsgT', '6')])
# ---- Tick
g.x, g.y = 400, 1500
tk = BEL.add_event_override(h, 'ReceiveTick', unreal.IntPoint(0, 1500)); dt = tk.find_output_pin('DeltaSeconds')
pawn = lambda: g.pin_out(g.fn(GPS + 'GetPlayerPawn', PlayerIndex='0'))
def dist_lt(ref, d):
    return AND(g.fn(KSL + 'IsValid', Object=GET(ref)), g.fn(KML + 'Less_DoubleDouble', A=g.fn(KML + 'Vector_Distance', V1=g.fn(ACT + 'K2_GetActorLocation', self=pawn()), V2=g.fn(ACT + 'K2_GetActorLocation', self=g.pin_out(GET(ref)))), B=str(d)))
def look(ref, d, facing):
    pcm = g.fn(GPS + 'GetPlayerCameraManager', PlayerIndex='0')
    cl = g.fn('/Script/Engine.PlayerCameraManager.GetCameraLocation', self=pcm)
    fwd = g.fn(KML + 'GetForwardVector', InRot=g.fn('/Script/Engine.PlayerCameraManager.GetCameraRotation', self=g.fn(GPS + 'GetPlayerCameraManager', PlayerIndex='0')))
    nrm = g.fn(KML + 'Normal', A=g.fn(KML + 'Subtract_VectorVector', A=g.fn(ACT + 'K2_GetActorLocation', self=g.pin_out(GET(ref))), B=cl))
    return AND(dist_lt(ref, d), g.fn(KML + 'Greater_DoubleDouble', A=g.fn(KML + 'Dot_VectorVector', A=fwd, B=nrm), B=str(facing)))
E = lambda: g.fn('/Script/Engine.PlayerController.WasInputKeyJustPressed', self=g.fn(GPS + 'GetPlayerController', PlayerIndex='0'), Key='E')
ntags = lambda: g.fn('/Script/Engine.KismetArrayLibrary.Array_Length', TargetArray=g.get('Tags', '/Script/Engine.Pawn', target=pawn())) if False else None
def tag_len():
    ln = g.by_menu(['Utilities|Array|Length'], ['Array', 'Length'])
    g.connect(g.pin_out(g.get('Tags', '/Script/Engine.Pawn', target=pawn())), ln.find_input_pin([str(p.get_pin_name()) for p in ln.list_input_pins()][0]), 'len')
    return g.pin_out(ln, [str(p.get_pin_name()) for p in ln.list_output_pins()][0])
outs = [tk.find_then_pin()]
outs = steps(outs, [g.setv('MsgT', g.fn(KML + 'Subtract_DoubleDouble', A=GET('MsgT'), B=dt)), g.setv('T', g.fn(KML + 'Add_DoubleDouble', A=GET('T'), B=dt))])
vp = g.fn(KSL + 'IsValid', Object=g.fn(GPS + 'GetPlayerPawn', PlayerIndex='0'))
# init: day start teleport for days > 1, remember tag count
outs = when(outs, AND(NOT(GET('bInit')), vp), [g.setv('bInit', 'true')])
# timer start on building entry
outs = when(outs, AND(AND(NOT(GET('bTimer')), NOT(GET('bOver'))), dist_lt('TimerRef', 300)),
            [g.setv('bTimer', 'true'), g.setv('TimeLeft', GET('StartTime')), g.setv('Msg', 'Binaya girdin. Sure basladi!'), g.setv('MsgT', '3')])
outs = when(outs, AND(AND(GET('bTimer'), NOT(GET('bOver'))), NOT(GET('bEnd'))), [g.setv('TimeLeft', g.fn(KML + 'Subtract_DoubleDouble', A=GET('TimeLeft'), B=dt))])
outs = when(outs, AND(AND(GET('bTimer'), NOT(GET('bOver'))), g.fn(KML + 'LessEqual_DoubleDouble', A=GET('TimeLeft'), B='0')), [g.setv('bOver', 'true'), g.setv('T', '0'), g.setv('bDesk', 'false')])
# checkpoints: every new pawn tag (key picked) = bonus time
KEYS = ['Key_Building_Front', 'Key_Doorman', 'Key_Boiler', 'Key_Manager', 'Key_Flat1', 'Key_Flat2', 'Key_Flat3', 'HiddenRoom']
for i, kid in enumerate(KEYS):
    ensure_var(h, g, 'bK%d' % i, 'bool', 'false')
    has = lambda: AND(g.fn(ACT + 'ActorHasTag', self=pawn(), Tag='HasKey:' + kid), NOT(GET('bK%d' % i)))
    outs = when(outs, AND(has(), GET('bTimer')), [g.setv('TimeLeft', g.fn(KML + 'Add_DoubleDouble', A=GET('TimeLeft'), B=GET('Bonus'))), g.setv('Msg', '+60 sn - anahtar bulundu'), g.setv('MsgT', '3')])
    outs = when(outs, AND(has(), vp), [g.setv('bK%d' % i, 'true')])
# desk / envelope
outs = steps(outs, [g.setv('bLookEnv', look('EnvRef', 170, 0.93)), g.setv('bLookDesk', AND(look('DeskRef', 260, 0.55), NOT(GET('bLookEnv'))))])
outs = when(outs, NOT(dist_lt('DeskRef', 320)), [g.setv('bDesk', 'false')])
outs = when(outs, AND(GET('bLookDesk'), E()), [g.setv('bDesk', NOT(GET('bDesk')))])
b_env = g.ed.add_branch_node(); g.connect(g.pin_out(AND(AND(GET('bLookEnv'), E()), NOT(GET('bEnd')))), b_env.find_condition_pin(), 'env')
outs = link(outs, b_env)
b_d = g.ed.add_branch_node(); g.connect(g.pin_out(g.fn(KML + 'GreaterEqual_IntInt', A=GET('Deaths'), B='1')), b_d.find_condition_pin(), 'deaths')
g.connect(b_env.find_then_pin(), b_d.find_execute_pin(), 'x')
e1 = steps([b_d.find_then_pin()], [g.setv('bEnd', 'true'), g.setv('T', '0'), g.setv('bDesk', 'false')])
e2 = steps([b_d.find_else_pin()], [g.setv('Msg', 'Mavi bir zarf... Simdi degil, zaman isliyor.'), g.setv('MsgT', '3')])
outs = e1 + e2 + [b_env.find_else_pin()]
lvl = lambda: '/Game/DirectorsCut/Maps/L_Town'  # GetCurrentLevelName gave the level-instance map in PIE
optstr = g.fn(KSTR + 'Concat_StrStr', A=g.fn(KSTR + 'Concat_StrStr', A=g.fn(KSTR + 'Concat_StrStr', A='day=', B=g.fn(KSTR + 'Conv_IntToString', InInt=GET('Day'))), B='?deaths='),
              B=g.fn(KSTR + 'Conv_IntToString', InInt=g.fn(KML + 'Add_IntInt', A=GET('Deaths'), B='1')))
outs = when(outs, AND(GET('bOver'), g.fn(KML + 'Greater_DoubleDouble', A=GET('T'), B='4')), [g.fn(GPS + 'OpenLevel', LevelName=lvl(), Options=optstr)])
outs = when(outs, AND(GET('bEnd'), g.fn(KML + 'Greater_DoubleDouble', A=GET('T'), B='20')), [g.fn(GPS + 'OpenLevel', LevelName=lvl(), Options='day=1?deaths=0')])
# ---- DrawHUD
g.x, g.y = 400, 4000
dh = BEL.add_event_override(h, 'ReceiveDrawHUD', unreal.IntPoint(0, 4000))
SX = lambda f: g.fn(KML + 'Multiply_DoubleDouble', A=g.fn(KML + 'Conv_IntToDouble', InInt=dh.find_output_pin('SizeX')), B=str(f))
SY = lambda f: g.fn(KML + 'Multiply_DoubleDouble', A=g.fn(KML + 'Conv_IntToDouble', InInt=dh.find_output_pin('SizeY')), B=str(f))
def txt(t, x, y, sc, col='(R=1,G=1,B=1,A=1)'):
    return g.fn(HUDF + 'DrawText', Text=t, TextColor=col, ScreenX=x, ScreenY=y, Scale=str(sc))
def rect(a):
    return g.fn(HUDF + 'DrawRect', RectColor='(R=0,G=0,B=0,A=%s)' % a, ScreenX='0', ScreenY='0', ScreenW=SX(1), ScreenH=SY(1))
def lines(L, x, y0, dy, sc, col='(R=1,G=1,B=1,A=1)'):
    return [txt(s, SX(x), g.fn(KML + 'Add_DoubleDouble', A=SY(y0), B=str(i * dy)), sc, col) for i, s in enumerate(L)]
outs = [dh.find_then_pin()]
tstr = g.fn(KSTR + 'Concat_StrStr', A='SURE  ', B=g.fn(KSTR + 'TimeSecondsToString', InSeconds=g.fn(KML + 'FMax', A=GET('TimeLeft'), B='0')))
outs = when(outs, AND(GET('bTimer'), NOT(GET('bEnd'))), [txt(g.pin_out(tstr), SX(0.44), '30', 2.2, '(R=1,G=0.85,B=0.3,A=1)')])
outs = when(outs, g.fn(KML + 'Greater_DoubleDouble', A=GET('MsgT'), B='0'), [txt(g.pin_out(GET('Msg')), SX(0.08), SY(0.78), 1.6, '(R=1,G=0.95,B=0.6,A=1)')])
outs = when(outs, AND(GET('bLookEnv'), NOT(GET('bEnd'))), [txt('[E] Mavi zarf', SX(0.46), SY(0.56), 1.5)])
outs = when(outs, AND(GET('bLookDesk'), NOT(GET('bDesk'))), [txt('[E] Kurgu masasi', SX(0.45), SY(0.56), 1.5)])
DESK = ['KURGU MASASI  -  HARD DISK', '', 'Klip_03.mp4  +  Ses_07.wav    [ESLESTI]', '', 'Videonun sonunda bir adres veriliyor:',
        'Eski apartman  -  Bahar Sokak No:5', '', 'Detay: Bina kapisinin anahtari, karsi kaldirimdaki sandigin ustunde.',
        'Binaya girince sure baslar. Her bulunan anahtar ek sure kazandirir.', '', 'Notlarini al. Sure biterse gun yeniden baslar.', '', '[E] Kapat']
outs = when(outs, GET('bDesk'), [rect('0.88')] + lines(DESK, 0.12, 0.14, 38, 1.6))
outs = when(outs, GET('bOver'), [rect('0.92')] + lines(['SURE DOLDU', 'Gun yeniden basliyor...'], 0.36, 0.40, 70, 3.0, '(R=1,G=0.2,B=0.2,A=1)'))
END = ['Mavi zarfi actin.', '', 'Icinde kusursuz bir cinayet plani vardi.', 'Ve planin son satirinda senin adin yaziyordu.', '', '', "DIRECTOR'S CUT", 'MegaJam 2026']
outs = when(outs, GET('bEnd'), [rect('1')] + lines(END, 0.30, 0.25, 48, 2.0))
ok = finish(h, HUDP)
say('hud ok', ok)
if ok:
    if unreal.EditorAssetLibrary.does_asset_exist(GMP):
        gmb = unreal.load_asset(GMP)
    else:
        gmb = BEL.create_blueprint_asset_with_parent(GMP, unreal.load_class(None, '/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode.BP_FirstPersonGameMode_C'))
    BEL.compile_blueprint(gmb)
    unreal.get_default_object(gmb.generated_class()).set_editor_property('hud_class', unreal.load_class(None, HUDP + '.BP_MJHUD_C'))
    BEL.compile_blueprint(gmb); unreal.EditorAssetLibrary.save_loaded_asset(gmb, only_if_is_dirty=False)
    say('gm hud', unreal.get_default_object(gmb.generated_class()).get_editor_property('hud_class').get_name())
